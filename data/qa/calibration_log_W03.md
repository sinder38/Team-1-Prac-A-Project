# Calibration Log - Week 3

Role: R10 QA and Learning Log Lead  
Checked by: QA Lead  
Date checked: 7 June 2026

## Evidence checked

- `data/final prediction/final_prediction_W3.md`
- `data/human/human_score_W3.md`
- `data/llm/llm_comparison_W3.md`
- `data/evidence/actuals_W3.md`
- `data/almanac/almanac_agent_W03.md`
- `data/macro/macro_agent_W3.md`
- `data/technical/technnical_agent_W3.md`

## W3 prediction checked

The Week 3 final prediction file gives these calls for the next market week:

| Asset | Direction | Predicted range | Confidence |
| --- | --- | ---: | --- |
| SPX | Down | -1.0% to -3.0% | Medium |
| NDX | Down | -1.5% to -4.0% | Medium |
| IWM | Down | -1.0% to -3.5% | Medium |

Final regime call: **Neutral-Bearish**

Main invalidation: A cooler-than-expected CPI report, falling Treasury yields, and SPX reclaiming the 8 EMA.

## QA checks

| Check | Result |
| --- | --- |
| SPX, NDX, and IWM all have direction | Pass |
| SPX, NDX, and IWM all have percentage ranges | Pass |
| Confidence level is included | Pass |
| Human Score and override are included | Pass |
| Four-model LLM comparison is included | Pass |
| Main invalidation condition is included | Pass |
| Evidence is separated from final prediction | Pass |

## Calibration status

W3 prediction score: **Not scored yet by design**

I am not giving a W3 calibration score in this file because the W3 prediction was filed on Sunday 7 June for the market week after this submission. The matching actual result is only available after that week closes. Scoring it now would mix the evidence week with the prediction week.

The latest completed calibration score available for presentation is the Week 2 score: **+5 / +9** from `data/qa/calibration_log_W2.md`.

## QA decision

The W3 prediction is ready from a QA point of view because it includes the required direction, range, confidence, reasoning, and invalidation condition. My main note is that the team should keep the prediction file and the later actuals file clearly separated, so the calibration score can be checked honestly after the correct market week ends.
