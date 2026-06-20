# Calibration Suite - Week 4 Final

Role: R10 Calibration Lead  
Date checked: 20 June 2026
Status: Ready for review

## What this file tracks

This file is my Week 4 R10 calibration suite. It tracks the completed prediction score, LLM performance notes, and process feedback for the next Human Score discussion.

## Latest completed calibration

| Prediction week | Actuals used | SPX | NDX | IWM | Total |
| --- | --- | ---: | ---: | ---: | ---: |
| W22 | `data/evidence/actuals_W22.md` | +2 | +2 | +1 | +5 / +9 |
| W23 | `data/evidence/actuals_W24.md` | 0 | 0 | 0 | 0 / +9 |

## W23 prediction scored

| Asset | Direction | Range | Confidence | Actual move | Result |
| --- | --- | ---: | --- | ---: | --- |
| SPX | Down | -1.0% to -3.0% | Medium | +0.46% | Direction wrong, range miss |
| NDX | Down | -1.5% to -4.0% | Medium | +2.17% | Direction wrong, range miss |
| IWM | Down | -1.0% to -3.5% | Medium | +3.93% | Direction wrong, range miss |

## LLM track record

| Prediction week | Closest model | Reason |
| --- | --- | --- |
| W22 | DeepSeek | It covered the actual SPX move and had the closest midpoint among the models that included the result. |
| W23 | No clear winner | The actual result moved opposite to the team's bearish call, so I would not count any model as a strong winner for that week. |

## Directional accuracy tracker

| Prediction week | SPX correct? | NDX correct? | IWM correct? | Note |
| --- | --- | --- | --- | --- |
| W22 | Yes | Yes | Yes | Direction was correct across all three indexes, but ranges were still a bit conservative. |
| W23 | No | No | No | The bearish call did not match the actual relief rally. |

## Possible model or process bias

- W23 showed that strong model agreement can still be wrong.
- The team may have overweighted the previous selloff, CPI risk, and bearish June seasonality.
- The final prediction had the required structure, but the range did not leave room for a risk-on rebound.

## Input for R7 Human Score

For the next Human Score discussion, I would suggest checking:

- whether all models are repeating the same risk instead of adding new evidence,
- whether the team is too confident after one sharp selloff,
- whether the final range includes both the main thesis and a realistic reversal case,
- whether the prediction week and actuals week are clearly matched before scoring.

## One process change

Before the next release tag, R10 should confirm that the final prediction file includes the prediction week, direction, range, confidence, and invalidation condition for SPX, NDX, and IWM. I would also write down which actuals file will be used later, because that is where week-matching mistakes are easiest to make.
