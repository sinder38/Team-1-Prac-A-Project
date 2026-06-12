# Calibration Suite - Week 4 Draft

Role: R10 Calibration Lead  
Date checked: 12 June 2026  
Status: Draft for Sprint 4

## What this file tracks

This file is the R10 calibration suite for Sprint 4. It tracks prediction accuracy, LLM model performance, and process notes that should feed into R7's Human Score discussion.

## Latest completed calibration

The latest completed score is still Week 2 because Week 3's matching actual result is not available until after the week of 8-12 June closes.

| Week | SPX | NDX | IWM | Total |
| --- | ---: | ---: | ---: | ---: |
| W2 | +2 | +2 | +1 | +5 / +9 |
| W3 | Pending | Pending | Pending | Pending |

## W3 prediction awaiting score

| Asset | Direction | Range | Confidence |
| --- | --- | ---: | --- |
| SPX | Down | -1.0% to -3.0% | Medium |
| NDX | Down | -1.5% to -4.0% | Medium |
| IWM | Down | -1.0% to -3.5% | Medium |

## LLM track record

| Week | Closest model | Reason |
| --- | --- | --- |
| W2 | DeepSeek | It covered the actual SPX move and had the closest midpoint among the models that included the result. |
| W3 | Pending | Needs the actual SPX result for the week of 8-12 June 2026. |

## Directional accuracy tracker

| Week | SPX correct? | NDX correct? | IWM correct? | Note |
| --- | --- | --- | --- | --- |
| W2 | Yes | Yes | Yes | Direction was correct across all three indexes, but ranges were too conservative. |
| W3 | Pending | Pending | Pending | Prediction was bearish with Medium confidence. |

## Possible model or process bias

- Week 2 showed that the team got direction right but underestimated upside strength.
- Week 3 cannot be judged yet, but all four models were bearish, so R10 should watch for possible over-agreement around macro fear.
- If W3 actuals are not as bearish as predicted, the team should be careful about overweighting one major event such as CPI.

## Input for R7 Human Score

For the next Human Score discussion, R10 should remind the team to check:

- whether the AI consensus is too one-sided,
- whether the range is wide enough for event risk,
- whether confidence matches the real uncertainty,
- whether the final prediction week and actuals week are clearly matched.

## One process change

Before the W4 release tag is created, R10 should confirm that the final prediction file includes direction, range, confidence, prediction week, and invalidation condition for SPX, NDX, IWM, and the required sector predictions.
