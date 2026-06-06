# Calibration Log - Week 2

Role: R10 QA and Learning Log Lead  
Checked by: QA Lead  
Date checked: 6 June 2026

## Evidence checked

- `data/final prediction/prediction_2026-W02_Team1.md`
- `data/evidence/actuals_W2.md`
- `data/human/human_score_W2.md`
- `data/llm/llm_comparison_W2.md`

## Scoring rule

Scoring rule used: `data/qa/calibration_scoring_rule.md`

## Team prediction

The locked Week 2 prediction file gave these calls:

| Asset | Direction | Predicted range | Confidence |
| --- | --- | ---: | --- |
| SPX | Up | +0.2% to +1.0% | Medium |
| NDX | Up | +0.5% to +1.5% | Medium |
| IWM | Up | 0.0% to +1.2% | Low-Medium |

## Actual result

From `data/evidence/actuals_W2.md`, all three tracked indexes finished higher:

| Asset | Actual result | Direction result |
| --- | ---: | --- |
| SPX | +1.40% | Correct |
| NDX | +2.86% | Correct |
| IWM | +1.82% | Correct |

## Calibration score

| Asset | Confidence used for scoring | Direction correct? | Score |
| --- | --- | --- | ---: |
| SPX | Medium | Yes | +2 |
| NDX | Medium | Yes | +2 |
| IWM | Low / Uncertain | Yes | +1 |

Total calibration score: **+5 / +9**

## QA note

I counted IWM as Low / Uncertain because the prediction file used `Low-Medium`, which is not one of the exact score labels in the teacher's table. To avoid overstating the result, I used the lower score bucket.

The team got the direction correct for all three indexes. The main improvement is that next sprint the confidence labels should use the same categories as the scoring table: High, Medium, or Low.
