# delta_W32.md

Role: Delta Engine / Calibration
Status: Generated from a locked prediction and completed actuals

## Files compared

- Locked prediction: vW31
- Completed actuals: W32

## Current-week score

| Asset | Predicted direction | Predicted range | Confidence | Actual move | Actual direction | Direction correct? | Range hit? | Range error |
| --- | --- | ---: | --- | ---: | --- | --- | --- | ---: |
| S&P 500 (SPX) | FLAT | -1.5% to +1.5% | Medium | +3.58% | UP | N | N | 2.08% |
| Nasdaq 100 (NDX) | FLAT | -2.0% to +2.0% | Medium | +5.12% | UP | N | N | 3.12% |
| Russell 2000 (IWM) | DOWN | -2.0% to +0.5% | Medium | +3.56% | UP | N | N | 3.06% |

## Current-week summary

- Direction accuracy: 0 / 3
- Range accuracy: 0 / 3
- Average range error: 2.75%
- Sector coverage: 0 / 11

## Cumulative accuracy

This history only uses locked predictions with the matching completed actuals. Missing weeks are not estimated.

| Prediction | Actuals | Assets scored | Direction accuracy | Range accuracy | Average range error |
| --- | --- | ---: | ---: | ---: | ---: |
| vW22 | W23 | 3 | 0.0% | 0.0% | 3.61% |
| vW23 | W24 | 3 | 0.0% | 0.0% | 3.35% |
| vW24 | W25 | 3 | 100.0% | 66.7% | 0.20% |
| vW28 | W29 | 3 | 0.0% | 33.3% | 1.66% |
| vW29 | W30 | 3 | 100.0% | 100.0% | 0.00% |
| vW30 | W31 | 3 | 0.0% | 100.0% | 0.00% |
| vW31 | W32 | 3 | 0.0% | 0.0% | 2.75% |

- Cumulative direction accuracy: 28.6%
- Cumulative range accuracy: 42.9%

## Coverage gaps

- Missing prediction rows: Technology (XLK), Health Care (XLV), Financials (XLF), Consumer Discretionary (XLY), Communication Services (XLC), Industrials (XLI), Consumer Staples (XLP), Energy (XLE), Materials (XLB), Real Estate (XLRE) and Utilities (XLU)

## History notes

- W25 was not scored because actuals_W26.md is missing.

## Suggested weights for next sprint

These are small trial adjustments from the measured delta, not proof that one agent caused the final result. The team should review them before using them.

| Agent | Current weight | Suggested weight | Reason |
| --- | ---: | ---: | --- |
| almanac | 0.10 | 0.05 | Cumulative range accuracy is below 60%, so broad seasonality receives a small trial reduction. |
| macro | 0.20 | 0.20 | No change from the previous reviewed weights. |
| technical | 0.35 | 0.40 | Cumulative range accuracy is below 60%, so support, resistance, and volatility checks receive a small trial increase. |
| llm | 0.10 | 0.05 | Cumulative direction accuracy is below 60%, so automated consensus receives a small trial reduction. |
| human_score | 0.25 | 0.30 | Cumulative direction accuracy is below 60%, so final human challenge and review receive a small trial increase. |

## Prescription for next sprint

Review the direction logic for S&P 500 (SPX), Nasdaq 100 (NDX) and Russell 2000 (IWM) before the next lock. Recheck volatility and range width for S&P 500 (SPX), Nasdaq 100 (NDX) and Russell 2000 (IWM). Add explicit direction rows for Technology (XLK), Health Care (XLV), Financials (XLF), Consumer Discretionary (XLY), Communication Services (XLC), Industrials (XLI), Consumer Staples (XLP), Energy (XLE), Materials (XLB), Real Estate (XLRE) and Utilities (XLU) so every required sector can be scored. Use these small trial weights next sprint: almanac 0.10 to 0.05, technical 0.35 to 0.40, llm 0.10 to 0.05, human_score 0.25 to 0.30.
