"""Requirement tests for F.1 to F.5, the historical-data contract and the approved configuration.

Test names start with the requirement they check: 1.4.1 to 1.4.5 are the
function requirements of F.1 to F.5 in the Innoslate model, SR-09 and SR-10 are
the historical-data requirements in SPEC.md. All prices are synthetic
(tests/synthetic_market.py). The rules are the placeholder config/rules.json,
so these tests check that the code applies the rules, not that the rules are
right.
"""

import copy
import json
from dataclasses import replace

import pytest
from synthetic_market import synthetic_rows, write_snapshot_files

from allocation_engine import determine_target_asset_allocation, request_historical_market_data
from historical_analysis import mix_value_path, worst_one_year_return
from investor_interface import InvestorInputError, collect_investor_information, requests_for_investor_input
from market_data_provider import provide_historical_market_data
from model_flows import MarketDataRequest
from portfolio_construction_engine import generate_investment_recommendations
from risk_engine import assess_investor_risk_profile
from screening_engine import screen_candidate_securities
from system_administration import DEFAULT_RULES_PATH, load_configuration
from wealthpilot_service import Planner, PlanWithheld

ALL_SYMBOLS = ["VTI", "AAPL", "MSFT", "TQQQ", "VXUS", "BND", "AGG", "BIL"]


def collect(configuration, investor):
    return collect_investor_information(
        investor["financial_profile"],
        investor["risk_questionnaire_responses"],
        investor["current_holdings"],
        investment_planning_constraints=configuration.investment_planning_constraints,
        session_initiation_command="session-test",
    )


def assess(configuration, investor):
    return assess_investor_risk_profile(collect(configuration, investor), risk_scoring_rules=configuration.risk_scoring_rules)


def market_data(snapshot_directory, symbols=ALL_SYMBOLS):
    return provide_historical_market_data(MarketDataRequest(symbols), snapshot_directory=snapshot_directory)


def allocate(configuration, risk, data):
    return determine_target_asset_allocation(
        risk,
        data,
        allocation_rules=configuration.allocation_rules,
        investment_planning_constraints=configuration.investment_planning_constraints,
        profile_interpretation_confirmed=True,
    )


def screen(configuration, target, data):
    return screen_candidate_securities(
        target,
        data,
        market_and_regulatory_constraints=configuration.market_and_regulatory_constraints,
        security_screening_criteria=configuration.security_screening_criteria,
    )


def most(investor, configuration, end):
    """Answer every question with its most cautious (end=0) or most risk-tolerant (end=-1) option."""
    for question in configuration.investment_planning_constraints["risk_questionnaire"]:
        investor["risk_questionnaire_responses"][question["id"]] = list(question["options"])[end]
    return investor


# F.1 Collect Investor Information

def test_1_4_1_requests_cover_every_configured_question(configuration):
    requests = requests_for_investor_input(investment_planning_constraints=configuration.investment_planning_constraints)
    constraints = configuration.investment_planning_constraints
    assert requests["financial_profile_fields"] == constraints["financial_profile_fields"]
    assert requests["risk_questionnaire"] == constraints["risk_questionnaire"]
    assert requests["current_holdings"]["max_holdings"] == constraints["max_holdings"]


def test_1_4_1_valid_information_is_consolidated_unchanged(configuration, investor):
    collected = collect(configuration, investor)

    assert collected.session_id == "session-test"
    assert collected.financial_profile == investor["financial_profile"]
    assert collected.risk_questionnaire_responses == investor["risk_questionnaire_responses"]
    assert [(h.symbol, h.value) for h in collected.current_holdings] == [("VTI", 5000.0)]
    assert collected.answer_labels["goal"] == "Retirement"


def test_1_4_1_every_problem_is_reported_at_once(configuration, investor):
    investor["financial_profile"].update(age=12, goal="lottery", horizon_years=2.5)
    del investor["financial_profile"]["annual_income"]
    investor["risk_questionnaire_responses"]["experience"] = "expert"
    investor["current_holdings"] = [{"symbol": "vti", "value": 10}, {"symbol": "BND", "value": -1}, {"symbol": "BND", "value": 1}]

    with pytest.raises(InvestorInputError) as raised:
        collect(configuration, investor)

    text = " | ".join(raised.value.errors)
    for expected in ("Age", "Goal", "whole number", "Annual income", "investing experience", "'vti'", "value must be", "listed twice"):
        assert expected.lower() in text.lower(), expected


@pytest.mark.parametrize("bad", [True, "34", float("nan"), None, [34]])
def test_1_4_1_non_numbers_are_refused(configuration, investor, bad):
    investor["financial_profile"]["age"] = bad
    with pytest.raises(InvestorInputError):
        collect(configuration, investor)


def test_1_4_1_session_must_be_started(configuration, investor):
    with pytest.raises(InvestorInputError):
        collect_investor_information(
            investor["financial_profile"],
            investor["risk_questionnaire_responses"],
            [],
            investment_planning_constraints=configuration.investment_planning_constraints,
            session_initiation_command="",
        )


# F.2 Assess Investor Risk Profile

def test_1_4_2_sample_investor_scores_as_the_rules_say(configuration, investor):
    risk = assess(configuration, investor)
    # points 3+2+3+3+3 for the answers, 4 for 25 years, 3 for low liquidity: (21-7)/(27-7) = 70
    assert (risk.risk_score, risk.risk_category) == (70, "Moderately Aggressive")
    assert risk.max_one_year_loss == 0.2
    assert risk.rules_version == configuration.risk_scoring_rules["version"]
    assert len(risk.factors) == 7


def test_1_4_2_extremes_map_to_the_end_categories(configuration, investor):
    cautious = most(copy.deepcopy(investor), configuration, 0)
    cautious["financial_profile"].update(horizon_years=1, liquidity_needs="high")
    tolerant = most(copy.deepcopy(investor), configuration, -1)
    tolerant["financial_profile"].update(horizon_years=30, liquidity_needs="low")

    assert (assess(configuration, cautious).risk_score, assess(configuration, cautious).risk_category) == (0, "Conservative")
    assert (assess(configuration, tolerant).risk_score, assess(configuration, tolerant).risk_category) == (100, "Aggressive")


def test_1_4_2_a_more_tolerant_answer_never_lowers_the_score(configuration, investor):
    base = assess(configuration, investor).risk_score
    for question in configuration.investment_planning_constraints["risk_questionnaire"]:
        changed = copy.deepcopy(investor)
        changed["risk_questionnaire_responses"][question["id"]] = list(question["options"])[-1]
        assert assess(configuration, changed).risk_score >= base


def test_1_4_2_profile_basis_carries_the_planning_inputs(configuration, investor):
    basis = assess(configuration, investor).profile_basis
    assert basis["goal_label"] == "Retirement"
    assert basis["horizon_years"] == 25
    assert basis["investable_savings"] == 25000
    assert basis["current_holdings"] == [{"symbol": "VTI", "value": 5000.0}]


# F.3 Determine Target Asset Allocation

def test_1_4_3_no_allocation_without_profile_interpretation_confirmation(configuration, investor, snapshot_directory):
    with pytest.raises(ValueError):
        determine_target_asset_allocation(
            assess(configuration, investor),
            market_data(snapshot_directory),
            allocation_rules=configuration.allocation_rules,
            investment_planning_constraints=configuration.investment_planning_constraints,
            profile_interpretation_confirmed=False,
        )


def test_1_4_3_market_data_request_covers_the_categorys_instruments(configuration, investor):
    request = request_historical_market_data(assess(configuration, investor), allocation_rules=configuration.allocation_rules)
    assert request.symbols == ALL_SYMBOLS


def test_1_4_3_allocation_starts_from_the_category_mix_and_adds_to_one(configuration, investor, snapshot_directory):
    investor["risk_questionnaire_responses"]["max_loss"] = "loss_30"  # no loss-tolerance move
    risk = assess(configuration, investor)
    target = allocate(configuration, risk, market_data(snapshot_directory))

    assert target.base_weights == configuration.allocation_rules["by_category"][risk.risk_category]
    assert sum(target.weights.values()) == pytest.approx(1)
    assert all(weight >= 0 for weight in target.weights.values())


def test_1_4_3_short_horizon_caps_stocks(configuration, investor, snapshot_directory):
    investor["financial_profile"]["horizon_years"] = 2
    investor["risk_questionnaire_responses"]["max_loss"] = "loss_30"
    target = allocate(configuration, assess(configuration, investor), market_data(snapshot_directory))

    equity = sum(w for c, w in target.weights.items() if configuration.allocation_rules["asset_classes"][c]["equity"])
    assert equity <= configuration.investment_planning_constraints["short_horizon_max_equity"] + 1e-9
    assert "short_horizon" in target.planning_flags
    assert any("2 years" in note for note in target.adjustments)


def test_1_4_3_likely_early_need_keeps_cash(configuration, investor, snapshot_directory):
    investor["financial_profile"]["liquidity_needs"] = "high"
    target = allocate(configuration, assess(configuration, investor), market_data(snapshot_directory))

    assert target.weights["Cash"] >= configuration.investment_planning_constraints["min_cash_by_liquidity"]["high"] - 1e-9
    assert any("cash" in note for note in target.adjustments)


def test_1_4_3_loss_tolerance_moves_stocks_to_bonds(configuration, investor, snapshot_directory):
    investor["risk_questionnaire_responses"]["max_loss"] = "loss_10"
    risk = assess(configuration, investor)
    data = market_data(snapshot_directory)
    target = allocate(configuration, risk, data)
    rules = configuration.allocation_rules

    def worst(weights):
        mix = {rules["asset_classes"][c]["benchmark"]: w for c, w in weights.items() if w > 0}
        return worst_one_year_return(mix_value_path(data.series, mix)[1])

    assert worst(target.base_weights) < -risk.max_one_year_loss  # the synthetic crash breaks the 10% limit
    assert target.weights["Bonds"] > target.base_weights["Bonds"]
    assert worst(target.weights) > worst(target.base_weights)
    moved = target.weights["Bonds"] - target.base_weights["Bonds"]
    assert moved <= rules["loss_tolerance_max_shift"] + 1e-4
    assert any(f"moved from stocks to {rules['defensive_class']}" in note for note in target.adjustments)


def test_1_4_3_missing_benchmark_skips_the_loss_check_with_a_limitation(configuration, investor, snapshot_directory):
    data = market_data(snapshot_directory, [s for s in ALL_SYMBOLS if s != "BND"])
    target = allocate(configuration, assess(configuration, investor), data)
    assert any("loss-tolerance check was skipped" in line for line in target.limitations)


# F.4 Screen Candidate Securities

def test_1_4_4_leveraged_products_are_excluded(configuration, investor, snapshot_directory):
    data = market_data(snapshot_directory)
    screened = screen(configuration, allocate(configuration, assess(configuration, investor), data), data)

    assert "TQQQ" not in {c.symbol for c in screened.candidates}
    assert any(e.symbol == "TQQQ" and "leveraged" in e.reason for e in screened.exclusions)
    assert {"VTI", "BND", "BIL"} <= {c.symbol for c in screened.candidates}


def test_1_4_4_individual_stocks_are_not_offered_to_cautious_categories(configuration, investor, snapshot_directory):
    most(investor, configuration, 0)
    investor["risk_questionnaire_responses"]["max_loss"] = "loss_30"  # keeps some stocks in the mix to screen
    data = market_data(snapshot_directory)
    risk = assess(configuration, investor)
    screened = screen(configuration, allocate(configuration, risk, data), data)

    assert risk.risk_category in ("Conservative", "Moderately Conservative")
    assert {"AAPL", "MSFT"} <= {e.symbol for e in screened.exclusions}


def test_1_4_4_short_history_and_high_volatility_are_excluded(configuration, investor, tmp_path):
    rows = [r for r in synthetic_rows() if not (r["symbol"] == "VXUS" and r["date"] < "2026-01-01")]
    write_snapshot_files(tmp_path, rows)
    data = market_data(tmp_path)
    criteria = copy.deepcopy(configuration.security_screening_criteria)
    criteria["max_annualized_volatility"]["US Stocks"] = 0.05
    target = allocate(configuration, assess(configuration, investor), data)

    screened = screen_candidate_securities(
        target, data, market_and_regulatory_constraints=configuration.market_and_regulatory_constraints,
        security_screening_criteria=criteria,
    )

    reasons = {e.symbol: e.reason for e in screened.exclusions}
    assert "fewer than" in reasons["VXUS"]
    assert all("volatility" in reasons[s] for s in ("VTI", "AAPL", "MSFT"))


# F.5 Generate Investment Recommendations

def build(configuration, investor, snapshot_directory):
    data = market_data(snapshot_directory)
    target = allocate(configuration, assess(configuration, investor), data)
    screened = screen(configuration, target, data)
    plan = generate_investment_recommendations(
        screened, target_asset_allocation=target, portfolio_construction_rules=configuration.portfolio_construction_rules
    )
    return target, screened, plan


def test_1_4_5_weights_add_to_one_and_match_the_target_by_class(configuration, investor, snapshot_directory):
    target, _, plan = build(configuration, investor, snapshot_directory)

    assert sum(r.weight for r in plan.recommendations) == pytest.approx(1, abs=1e-9)
    for asset_class, share in target.weights.items():
        held = sum(r.weight for r in plan.recommendations if r.asset_class == asset_class)
        assert held == pytest.approx(share, abs=2e-4)


def test_1_4_5_single_stocks_stay_within_the_cap(configuration, investor, snapshot_directory):
    _, _, plan = build(configuration, investor, snapshot_directory)
    cap = configuration.portfolio_construction_rules["single_stock_max_weight"]
    stocks = [r for r in plan.recommendations if r.instrument_type == "Stock"]
    assert stocks and all(r.weight <= cap + 1e-9 for r in stocks)


def test_1_4_5_plan_carries_its_evidence(configuration, investor, snapshot_directory):
    target, screened, plan = build(configuration, investor, snapshot_directory)

    assert {"market_volatility", "interest_rate"} <= set(plan.identified_risks)
    assert plan.plan_metrics.observations > 750
    assert len(plan.risk_drivers) == 2
    assert plan.allocation_adjustments == target.adjustments
    assert plan.data_snapshot_id == screened.snapshot_id == "synthetic-test"
    assert plan.rules_configuration_id == configuration.configuration_id


def test_1_4_5_class_without_candidates_is_spread_with_a_limitation(configuration, investor, snapshot_directory):
    data = market_data(snapshot_directory)
    target = allocate(configuration, assess(configuration, investor), data)
    screened = screen(configuration, target, data)
    no_cash = replace(screened, candidates=[c for c in screened.candidates if c.asset_class != "Cash"])

    plan = generate_investment_recommendations(
        no_cash, target_asset_allocation=target, portfolio_construction_rules=configuration.portfolio_construction_rules
    )

    assert "Cash" not in plan.target_allocation
    assert sum(plan.target_allocation.values()) == pytest.approx(1, abs=1e-3)
    assert any("No Cash security passed screening" in line for line in plan.data_limitations)


def test_1_4_5_no_candidates_means_no_plan(configuration, investor, snapshot_directory):
    data = market_data(snapshot_directory)
    target = allocate(configuration, assess(configuration, investor), data)
    empty = replace(screen(configuration, target, data), candidates=[])
    with pytest.raises(ValueError):
        generate_investment_recommendations(
            empty, target_asset_allocation=target, portfolio_construction_rules=configuration.portfolio_construction_rules
        )


# SR-09 Historical Data Admission and SR-10 Historical Data Limitation Disclosure

def test_SR_09_valid_series_are_admitted_in_date_order(snapshot_directory):
    data = market_data(snapshot_directory)
    assert set(data.series) == set(ALL_SYMBOLS)
    assert data.limitations == []
    series = data.series["VTI"]
    assert series.dates == sorted(series.dates) and len(series.dates) == len(set(series.dates))


@pytest.mark.parametrize(
    "corrupt",
    [
        lambda row: {**row, "date": "03/11/2025"},
        lambda row: {**row, "adjusted_close": "-1"},
        lambda row: {**row, "adjusted_close": "0"},
        lambda row: {**row, "adjusted_close": "nan"},
        lambda row: {**row, "adjusted_close": ""},
    ],
    ids=["non-iso-date", "negative", "zero", "not-finite", "missing"],
)
def test_SR_09_a_series_with_a_bad_row_is_not_admitted(tmp_path, corrupt):
    rows = synthetic_rows()
    index = next(i for i, r in enumerate(rows) if r["symbol"] == "AAPL") + 100
    rows[index] = corrupt(rows[index])
    write_snapshot_files(tmp_path, rows)

    data = market_data(tmp_path)

    assert "AAPL" not in data.series
    assert set(data.series) == set(ALL_SYMBOLS) - {"AAPL"}
    assert any(line.startswith("AAPL:") and "not used" in line for line in data.limitations)


def test_SR_09_duplicate_dates_are_not_admitted(tmp_path):
    rows = synthetic_rows()
    first_bnd = next(r for r in rows if r["symbol"] == "BND")
    rows.append(dict(first_bnd))
    write_snapshot_files(tmp_path, rows)
    data = market_data(tmp_path)
    assert "BND" not in data.series
    assert any("duplicate" in line for line in data.limitations)


def test_SR_10_no_snapshot_means_no_data_and_a_limitation(tmp_path):
    data = market_data(tmp_path)
    assert data.series == {} and data.snapshot_id is None
    assert "No historical price snapshot" in data.limitations[0]


def test_SR_10_altered_snapshot_is_not_used(tmp_path):
    write_snapshot_files(tmp_path, synthetic_rows(days=300))
    with (tmp_path / "prices-synthetic.csv").open("a") as handle:
        handle.write("VTI,2026-11-02,999.0\n")
    data = market_data(tmp_path)
    assert data.series == {}
    assert "fingerprint" in data.limitations[0]


def test_SR_10_unreadable_manifest_is_reported(tmp_path):
    (tmp_path / "manifest.json").write_text("{not json")
    data = market_data(tmp_path)
    assert data.series == {} and "manifest" in data.limitations[0]


def test_SR_10_plan_is_withheld_when_no_data_are_admitted(tmp_path, investor):
    planner = Planner(snapshot_directory=tmp_path / "empty", database_path=tmp_path / "wealthpilot.db")
    session = planner.start_session()
    planner.submit_investor_information(
        session.session_id,
        financial_profile=investor["financial_profile"],
        risk_questionnaire_responses=investor["risk_questionnaire_responses"],
        current_holdings=investor["current_holdings"],
    )
    with pytest.raises(PlanWithheld) as withheld:
        planner.build_plan(session.session_id, profile_interpretation_confirmed=True)
    assert "No historical price snapshot" in withheld.value.limitations[0]
    assert session.presented is None and planner.saved_plans() == []


# The approved configuration (X.3)

def test_configuration_loads_and_every_control_carries_its_identifier(configuration):
    for control in (
        configuration.investment_planning_constraints,
        configuration.risk_scoring_rules,
        configuration.allocation_rules,
        configuration.security_screening_criteria,
        configuration.market_and_regulatory_constraints,
        configuration.portfolio_construction_rules,
    ):
        assert control["configuration_id"] == configuration.configuration_id


@pytest.mark.parametrize(
    "edit",
    [
        lambda raw: raw["allocation_rules"]["by_category"]["Moderate"].update({"Cash": 0.5}),
        lambda raw: raw["explanation_rules"]["risk_language"].pop("interest_rate"),
        lambda raw: raw["risk_scoring_rules"]["question_points"]["experience"].pop("a_lot"),
        lambda raw: raw["security_screening_criteria"]["instruments"].pop("BND"),
        lambda raw: raw["allocation_rules"].update({"defensive_class": "Gold"}),
        lambda raw: raw.pop("portfolio_construction_rules"),
    ],
    ids=["mix-not-100", "risk-without-wording", "option-without-points", "instrument-without-metadata",
         "unknown-defensive-class", "missing-section"],
)
def test_configuration_that_contradicts_itself_is_refused(tmp_path, edit):
    raw = json.loads(DEFAULT_RULES_PATH.read_text())
    edit(raw)
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError):
        load_configuration(path)
