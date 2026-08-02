# delta_W31.md

Role: Delta Engine / Calibration
Status: Generated from a locked prediction and completed actuals

## Files compared

- Locked prediction: vW30
- Completed actuals: W31

## Current-week score

| Asset | Predicted direction | Predicted range | Confidence | Actual move | Actual direction | Direction correct? | Range hit? | Range error |
| --- | --- | ---: | --- | ---: | --- | --- | --- | ---: |
| S&P 500 (SPX) | DOWN | +0.5% to +2.5% | Medium | +1.05% | UP | N | Y | 0.00% |
| Nasdaq 100 (NDX) | DOWN | -4.0% to +1.0% | Medium | +0.52% | UP | N | Y | 0.00% |
| Russell 2000 (IWM) | DOWN | -2.0% to +1.5% | Medium | +0.01% | UP | N | Y | 0.00% |

## Current-week summary

- Direction accuracy: 0 / 3
- Range accuracy: 3 / 3
- Average range error: 0.00%
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

- Cumulative direction accuracy: 33.3%
- Cumulative range accuracy: 50.0%

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

Review the direction logic for S&P 500 (SPX), Nasdaq 100 (NDX) and Russell 2000 (IWM) before the next lock. Add explicit direction rows for Technology (XLK), Health Care (XLV), Financials (XLF), Consumer Discretionary (XLY), Communication Services (XLC), Industrials (XLI), Consumer Staples (XLP), Energy (XLE), Materials (XLB), Real Estate (XLRE) and Utilities (XLU) so every required sector can be scored. Use these small trial weights next sprint: almanac 0.10 to 0.05, technical 0.35 to 0.40, llm 0.10 to 0.05, human_score 0.25 to 0.30.
