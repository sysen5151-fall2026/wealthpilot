"""UC.3/UC.4 educational prototypes; cloud model allocation still needs review."""
import hashlib
import json
import math
from contextlib import closing
from datetime import datetime, timezone


def plan_fingerprint(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()


def compare_goal_scenario(record, *, monthly_contribution=None, horizon_years=None, goal_target=100000):
    """Same zero-return resource calculation for baseline and scenario; no forecast."""
    basis = record["profile_basis"]
    old_monthly, old_years = float(basis["monthly_contribution"]), int(basis["horizon_years"])
    monthly = old_monthly if monthly_contribution is None else float(monthly_contribution)
    years = old_years if horizon_years is None else horizon_years
    if not math.isfinite(monthly) or not 0 <= monthly <= 100000:
        raise ValueError("Monthly contribution must be finite and between 0 and 100000")
    if type(years) is not int or not 1 <= years <= 50:
        raise ValueError("Horizon must be a whole number from 1 to 50 years")
    if not math.isfinite(goal_target) or goal_target <= 0:
        raise ValueError("The educational goal target must be finite and positive")
    if monthly == old_monthly and years == old_years:
        raise ValueError("Change at least one planning assumption")
    opening = float(record["simulated_amounts"]["total"])
    def result(m, y):
        resources = round(opening + 12 * m * y, 2)
        return {"monthly_contribution": m, "horizon_years": y, "planned_resources": resources,
                "goal_target": goal_target, "goal_coverage": resources / goal_target}
    baseline, scenario = result(old_monthly, old_years), result(monthly, years)
    delta = round(scenario["planned_resources"] - baseline["planned_resources"], 2)
    direction = "higher" if delta > 0 else "lower" if delta < 0 else "unchanged"
    return {"baseline_plan_id": record["plan_id"], "baseline_fingerprint": plan_fingerprint(record),
            "method": "opening resources + 12 × monthly contribution × years; zero assumed return on both sides",
            "scope_notice": "Educational comparison only; no return forecast or portfolio change.",
            "goal": basis["goal"], "baseline": baseline, "scenario": scenario,
            "difference": delta, "direction": direction,
            "explanation": f"Using the same zero-return method and goal target, planned resources are {direction} by ${abs(delta):,.2f}. The saved baseline is unchanged."}


def apply_approved_change(planner, session_id, *, plan_id, action, approval_id):
    """Separate explicit approval writes only an internal educational ledger."""
    session = planner.session(session_id)
    record = planner.saved_plan(plan_id)
    if session.snapshot is None or session.snapshot.plan_id != plan_id or record is None:
        return {"status": "not_authorized", "detail": "Save and review the current plan first."}
    if action != "approve_simulated_change" or not isinstance(approval_id, str) or not approval_id.strip():
        return {"status": "not_authorized", "detail": "A distinct explicit simulated-change approval is required. Saving is not approval."}
    store = planner.portfolio_store
    with closing(store._connect()) as connection, connection:
        connection.execute("CREATE TABLE IF NOT EXISTS simulated_ledger (approval_id TEXT PRIMARY KEY, session_id TEXT NOT NULL, plan_id TEXT NOT NULL, before_json TEXT NOT NULL, after_json TEXT NOT NULL)")
        old = connection.execute("SELECT session_id,plan_id,before_json,after_json FROM simulated_ledger WHERE approval_id=?", (approval_id,)).fetchone()
        if old:
            if old[0] != session_id or old[1] != plan_id:
                return {"status": "not_authorized", "detail": "Approval ID belongs to another request."}
            return {"status": "already_applied", "before": json.loads(old[2]), "after": json.loads(old[3])}
        row = connection.execute("SELECT cash,holdings FROM simulated_portfolios WHERE session_id=?", (session_id,)).fetchone()
        before = {"cash": row[0], "holdings": json.loads(row[1])}
        total = before["cash"] + sum(h["value"] for h in before["holdings"])
        weights = record["recommendations"]
        amounts = [round(total * r["weight"], 2) for r in weights]
        after = {"cash": round(total - sum(amounts), 2), "holdings": [{"symbol": r["symbol"], "value": value} for r,value in zip(weights,amounts)]}
        if after["cash"] < 0:
            after["holdings"][-1]["value"] = round(after["holdings"][-1]["value"] + after["cash"],2)
            after["cash"] = 0.0
        connection.execute("UPDATE simulated_portfolios SET cash=?,holdings=?,recorded_at=? WHERE session_id=?", (after["cash"],json.dumps(after["holdings"],sort_keys=True),datetime.now(timezone.utc).isoformat(),session_id))
        connection.execute("INSERT INTO simulated_ledger VALUES (?,?,?,?,?)",(approval_id,session_id,plan_id,json.dumps(before,sort_keys=True),json.dumps(after,sort_keys=True)))
    return {"status": "applied", "before": before, "after": after, "scope_notice": "Internal educational ledger only. No real trade or money movement."}
