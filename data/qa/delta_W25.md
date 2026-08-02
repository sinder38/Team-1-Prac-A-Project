# delta_W25.md

Role: Delta Engine / Calibration
Status: Generated from a locked prediction and completed actuals

## Files compared

- Locked prediction: vW24
- Completed actuals: W25

## Current-week score

| Asset | Predicted direction | Predicted range | Confidence | Actual move | Actual direction | Direction correct? | Range hit? | Range error |
| --- | --- | ---: | --- | ---: | --- | --- | --- | ---: |
| S&P 500 (SPX) | FLAT-UP | -0.5% to +1.2% | Medium | +0.93% | UP | Y | Y | 0.00% |
| Nasdaq 100 (NDX) | FLAT-UP | -0.5% to +2.0% | Medium | +2.60% | UP | Y | N | 0.60% |
| Russell 2000 (IWM) | UP | +0.5% to +3.0% | Medium | +1.14% | UP | Y | Y | 0.00% |

## Current-week summary

- Direction accuracy: 3 / 3
- Range accuracy: 2 / 3
- Average range error: 0.20%
- Sector coverage: 0 / 11

## Cumulative accuracy

This history only uses locked predictions with the matching completed actuals. Missing weeks are not estimated.

| Prediction | Actuals | Assets scored | Direction accuracy | Range accuracy | Average range error |
| --- | --- | ---: | ---: | ---: | ---: |
| vW22 | W23 | 3 | 0.0% | 0.0% | 3.61% |
| vW23 | W24 | 3 | 0.0% | 0.0% | 3.35% |
| vW24 | W25 | 3 | 100.0% | 66.7% | 0.20% |

- Cumulative direction accuracy: 33.3%
- Cumulative range accuracy: 22.2%

## Coverage gaps

- Missing prediction rows: Technology (XLK), Health Care (XLV), Financials (XLF), Consumer Discretionary (XLY), Communication Services (XLC), Industrials (XLI), Consumer Staples (XLP), Energy (XLE), Materials (XLB), Real Estate (XLRE) and Utilities (XLU)

## Suggested weights for next sprint

These are small trial adjustments from the measured delta, not proof that one agent caused the final result. The team should review them before using them.

| Agent | Current weight | Suggested weight | Reason |
| --- | ---: | ---: | --- |
| almanac | 0.20 | 0.15 | Cumulative range accuracy is below 60%, so broad seasonality receives a small trial reduction. |
| macro | 0.20 | 0.20 | The latest direction score was stable, so macro weight stays unchanged until another completed week is available. |
| technical | 0.25 | 0.30 | Cumulative range accuracy is below 60%, so support, resistance, and volatility checks receive a small trial increase. |
| llm | 0.20 | 0.15 | Cumulative direction accuracy is below 60%, so automated consensus receives a small trial reduction. |
| human_score | 0.15 | 0.20 | Cumulative direction accuracy is below 60%, so final human challenge and review receive a small trial increase. |

## Prescription for next sprint

Recheck volatility and range width for Nasdaq 100 (NDX). Add explicit direction rows for Technology (XLK), Health Care (XLV), Financials (XLF), Consumer Discretionary (XLY), Communication Services (XLC), Industrials (XLI), Consumer Staples (XLP), Energy (XLE), Materials (XLB), Real Estate (XLRE) and Utilities (XLU) so every required sector can be scored. Use these small trial weights next sprint: almanac 0.20 to 0.15, technical 0.25 to 0.30, llm 0.20 to 0.15, human_score 0.15 to 0.20.
