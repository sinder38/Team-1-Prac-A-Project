# W3 Delta Report - W4 Draft

Role: R10 Calibration Lead  
Date checked: 12 June 2026  
Status: Draft until the Week 3 prediction week closes

## Purpose

This report will compare the team's Week 3 prediction against the matching actual market result. It is prepared for the Sprint 4 submission because the teacher's W4 template asks for W3 SPX, NDX, and IWM accuracy.

## Source files

| Item | File | QA status |
| --- | --- | --- |
| W3 final prediction | `data/final prediction/prediction_2026-W03_Team1.md` | Available |
| W3 LLM comparison | `data/llm/llm_comparison_W3.md` | Available |
| W3 Human Score | `data/human/human_score_W3.md` | Available |
| Matching actuals for W3 prediction week | Pending after Friday 12 June 2026 close | Not available yet |

Important note: `data/evidence/actuals_W3.md` records the evidence week ending Friday 5 June 2026. It is not the matching result for the Week 3 prediction, which covers the week of 8-12 June 2026.

## W3 prediction to score

| Asset | Predicted direction | Predicted range | Confidence |
| --- | --- | ---: | --- |
| SPX | Down | -1.0% to -3.0% | Medium |
| NDX | Down | -1.5% to -4.0% | Medium |
| IWM | Down | -1.0% to -3.5% | Medium |

## Delta table

| Asset | Predicted direction | Actual move | Direction correct? | Range hit? | Error size |
| --- | --- | ---: | --- | --- | ---: |
| SPX | Down | Pending | Pending | Pending | Pending |
| NDX | Down | Pending | Pending | Pending | Pending |
| IWM | Down | Pending | Pending | Pending | Pending |

## Current QA note

The delta report is ready in structure, but the actual result should not be filled in before the correct market week closes. After Friday 12 June 2026 close, R8 should provide the matching actuals. Then R10 can calculate direction accuracy, range hit, and error size.

## To complete after actuals arrive

- Add actual SPX, NDX, and IWM weekly percentage moves.
- Mark whether each direction was correct.
- Mark whether each result landed inside the predicted range.
- Calculate error size using the closest edge of the predicted range if the actual is outside the range.
- Use the result in the calibration suite and Monday presentation.
