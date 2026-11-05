# Rules rationale (WP-RULES-0.2)

`config/rules.json` holds every control that X.3 System Administrator and ENV.1 supply to F.1 to F.6. The AI assistant proposed the values on 2026-11-04 (WP-RULES-0.1-PLACEHOLDER). This review on 2026-11-05 checks each value against the installed price snapshot `yahoo-2026-11-04` (2021-11-04 to 2026-11-04, 1,254 trading days per fund) and records why it was kept.

- **Status:** reviewed 2026-11-05, team sign-off pending. The status line in `config/rules.json` is shown at the bottom of every page.
- **What changed from 0.1:** no value. The loss-tolerance stop rule added on 2026-11-04 (`loss_tolerance_min_improvement`) is now versioned as AR-0.2, and the configuration is renamed WP-RULES-0.2.
- **Scope:** these rules drive an educational simulation. They are not investment advice and have not been reviewed by a financial professional.

## Decision: where the loss-tolerance check moves money

When a starting mix's worst one-year loss in the historical sample is larger than the loss the investor said they could accept, F.3 moves money from stocks, 5 points at a time and at most 25 points, into `defensive_class`. The question was whether that class should be Bonds or Cash.

Worst one-year loss of each starting mix in the snapshot, measured with the benchmark funds, before and after moving 25 points of stocks (20 for Conservative, which has only 20):

| Category | Starting mix | After moving to Bonds | After moving to Cash |
| --- | --- | --- | --- |
| Conservative | -14.1% | -13.5% | -10.1% |
| Moderately Conservative | -15.5% | -14.6% | -10.4% |
| Moderate | -17.4% | -16.1% | -12.0% |
| Moderately Aggressive | -19.1% | -17.6% | -13.7% |
| Aggressive | -20.1% | -18.5% | -14.6% |

In this window bonds fell almost as far as stocks: BND's worst one-year return was -16.8%, against -21.4% for VTI and +0.8% for BIL. Each 5-point move into bonds cut the loss by 0.1 to 0.4 points; each move into cash cut it by about 1 point.

**Decision: keep Bonds**, with the rule that a move must cut the worst one-year loss by at least 0.5 points. In this snapshot no move passes that test. The mix therefore stays as its category sets it, and when the stated limit is exceeded the plan says so and lists the loss-tolerance risk.

Reasons:

1. The stated loss limit already shapes the plan. It is one of the seven scored answers that set the risk category; this check is a safeguard on top of it.
2. The snapshot starts in November 2021, just before the 2022 rate rise in which bonds and stocks fell together. Choosing cash because of this one window would teach learners that bonds never cushion stock losses, which is not true in general. With the 0.5-point rule, bonds are used in samples where they do help.
3. Moving up to 25 points into cash would give plans with a low stated limit 30 to 40% cash, and a Conservative plan would hold no stocks at all. That trades a historical one-year loss for inflation and shortfall risk over the horizon.

Revisit if a longer snapshot is installed (`python scripts/fetch_price_snapshot.py --years 10`), or if the team wants the stated limit to be enforced even at the cost of large cash holdings. In that case, set `"defensive_class": "Cash"`. The tests pass either way.

## Values reviewed

### Investment Planning Constraints (IPC-0.1): F.1, F.3

| Rule | Value | Reason |
| --- | --- | --- |
| Profile ranges | age 18 to 100; income $0 to $10M; cash $100 to $10M; monthly contribution $0 to $100k; horizon 1 to 50 years | Wide enough for any hypothetical learner, narrow enough to catch a typing error such as an extra zero |
| Holdings listed | at most 20 | Enough for a practice portfolio; keeps the form short |
| Short horizon | under 3 years: stocks capped at 30% | Money needed soon cannot wait out a stock decline; VTI's worst one-year loss in the snapshot was 21.4% |
| Early-access cash | unlikely 0%, possible 10%, likely 20% | Money that may be needed early sits in the cash fund, whose worst one-year result in the snapshot was a 0.8% gain |
| Loss-tolerance check | on | See the decision above |

### Risk Scoring Rules (RSR-0.1): F.2

| Rule | Value | Reason |
| --- | --- | --- |
| Scored answers | five questionnaire answers, 1 to 4 points each; horizon 1 to 4 (up to 2, 5, 10 years, then longer); early-access need 1 to 3 | Equal weights keep the score explainable: the plan can name the two answers that moved it most (SR-02) |
| Score | (points - 7) / (27 - 7) x 100 | Most cautious answers give 0, most risk-tolerant give 100 |
| Categories | Conservative to 30, Moderately Conservative to 45, Moderate to 60, Moderately Aggressive to 75, Aggressive to 100 | The middle bands are 15 points wide; the end bands are wider, so only consistently cautious or consistently bold answers reach them. The sample investor (middle answers, 25-year horizon) scores 70 |
| Loss limit | the stated 5, 10, 20 or 30% | Used as given by the loss-tolerance check and in the explanation |

### Allocation Rules (AR-0.2): F.3

Starting mix for each category, and how that mix (benchmark funds) did in the snapshot:

| Category | US / International / Bonds / Cash | Return a year | Volatility | Worst one-year |
| --- | --- | --- | --- | --- |
| Conservative | 15 / 5 / 60 / 20 | 2.6% | 5.5% | -14.1% |
| Moderately Conservative | 25 / 10 / 50 / 15 | 4.0% | 7.2% | -15.5% |
| Moderate | 40 / 15 / 35 / 10 | 5.9% | 9.9% | -17.4% |
| Moderately Aggressive | 50 / 20 / 25 / 5 | 7.2% | 12.0% | -19.1% |
| Aggressive | 60 / 25 / 10 / 5 | 8.6% | 14.2% | -20.1% |

- **The mixes.** Stocks rise from 20% to 85% across the categories, with international at about a quarter to 30% of the stock part. Every step up the scale raised both the average return and the worst one-year loss in the sample, which is the trade-off the learner is meant to see. Kept.
- **Benchmarks.** VTI, VXUS, BND and BIL: one broad, low-cost index fund per asset class. They are used to measure each mix.
- **Loss-tolerance check.** Moves 5 points at a time, at most 25 points, and each move must cut the worst one-year loss by at least 0.5 points (see the decision above).

### Security Screening Criteria (SSC-0.1): F.4

| Rule | Value | Reason |
| --- | --- | --- |
| Minimum history | 750 trading days (about three years) | Long enough to measure one-year results and include a market decline; every fund in the snapshot has 1,254 days |
| Individual stocks | offered from the Moderate category up | Single stocks moved far more than the market fund (volatility: AAPL 28.0%, MSFT 28.2%, VTI 17.5%) |
| Volatility limit per class | US stocks 45%, international stocks 35%, bonds 12%, cash 3% | Well above each benchmark's own volatility (17.5%, 16.4%, 6.1%, 0.3%), so they exclude outliers, not mainstream funds |

### Market and Regulatory Constraints (MRC-0.1): F.4, from ENV.1

| Rule | Value | Reason |
| --- | --- | --- |
| Product types | ETFs and individual stocks only | The products a novice is most likely to meet |
| Leveraged and inverse products | excluded (TQQQ is listed only to show the screen excluding it) | They reset daily; FINRA has warned that they are typically unsuitable for retail investors who hold them longer than one trading session ([Regulatory Notice 09-31](https://www.finra.org/rules-guidance/notices/09-31)) |

### Portfolio Construction Rules (PCR-0.1): F.5

| Rule | Value | Reason |
| --- | --- | --- |
| Single stock | at most 5% each, and stocks at most half of their asset class | Learners see individual companies without any one dominating the plan |
| Concentration risk | listed when one stock is above 10% | Can only happen when a class has no fund left after screening |
| Inflation risk | listed when cash is 20% or more | Large cash holdings lose purchasing power over long horizons |
| Risks by class | stocks: market volatility; international: also currency; bonds: interest rate | BND's worst one-year loss in the snapshot (-16.8%) came during the 2022 rate rise |

### Explanation Rules (ER-0.1): F.6.1, F.6.2

| Rule | Value | Reason |
| --- | --- | --- |
| Scope notice | "Educational simulation only. No real trade is placed and no money moves." | SR-13, on every view |
| Prohibited phrases | guaranteed, risk-free, order placed, funds transferred, buy now | Wording that would suggest advice, certainty or a real transaction |
| Learner action | "Save this simulated plan" only | SR-14: no brokerage controls |
| Risk wording | one plain sentence per risk key | Reviewed for novice language; no figures that could go stale |

## Considered and not changed

- **The goal is shown but has no rule of its own.** The horizon and the early-access answer carry what the goal implies; a separate goal rule would count the same thing twice.
- **BND and AGG are near-duplicates.** Their daily returns correlated at 0.996 in the snapshot. Both are kept so the screen and the weighting have two candidates in the class. Replacing AGG with a different kind of bond fund would need a new snapshot.
- **A low stated limit does not cap the category.** For example, the most risk-tolerant answers combined with a 10% limit still score 90 (Aggressive), and the plan lists the loss-tolerance risk. If the team wants the stated limit to cap the category, that is a new rule.

## Signing off

When the team agrees, change `status` in `config/rules.json` to `approved by the team on <date>` and add the disposition to the 2026-11-05 entry in `docs/prompt-log.md`. Changing any value should raise the version of its section (for example AR-0.3) and the configuration ID, so saved plans record which rules produced them.
