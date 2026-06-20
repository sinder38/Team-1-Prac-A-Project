# W23 Delta Report - Week 4 Final

Role: R10 Calibration Lead  
Date checked: 20 June 2026
Status: Ready for review

## Purpose

This report compares the team's locked W23 prediction with the matching actual market result. The W23 prediction was filed on Sunday 7 June 2026 and covered the market week ending Friday 12 June 2026, so the correct actuals file is `data/evidence/actuals_W24.md`.

## Source files

| Item | File | QA status |
| --- | --- | --- |
| W23 final prediction | `data/final prediction/prediction_2026-W23_Team1.md` | Available |
| W23 Human Score | `data/human/human_score_W23.md` | Available |
| W23 LLM comparison | `data/llm/llm_comparison_W23.md` | Available |
| Matching actuals | `data/evidence/actuals_W24.md` | Available |

## W23 prediction scored

| Asset | Predicted direction | Predicted range | Confidence |
| --- | --- | ---: | --- |
| SPX | Down | -1.0% to -3.0% | Medium |
| NDX | Down | -1.5% to -4.0% | Medium |
| IWM | Down | -1.0% to -3.5% | Medium |

## Matching actual result

| Asset | Actual weekly move | Actual direction |
| --- | ---: | --- |
| SPX | +0.46% | Up |
| NDX | +2.17% | Up |
| IWM | +3.93% | Up |

## Delta table

| Asset | Predicted direction | Actual move | Direction correct? | Range hit? | Error size | Score |
| --- | --- | ---: | --- | --- | ---: | ---: |
| SPX | Down | +0.46% | No | No | 1.46 pp above range | 0 |
| NDX | Down | +2.17% | No | No | 3.67 pp above range | 0 |
| IWM | Down | +3.93% | No | No | 4.93 pp above range | 0 |

## Score summary

- Direction accuracy: 0 / 3
- Range accuracy: 0 / 3
- Total calibration score: 0 / +9

The team expected a bearish week, but all three indexes finished higher. The largest miss was IWM, because small caps had the strongest rebound. Under the R10 scoring rule, Medium confidence with the wrong direction scores 0, so all three assets scored 0.

## QA note

The main issue was not the document format. The prediction included direction, range, confidence, evidence, and invalidation conditions. The problem was that the team and the LLMs leaned too bearish after the previous selloff, while the actual week turned into a relief rally. For the next sprint, I would keep the same evidence checks but leave more room for a bounce when the week depends heavily on one macro event.
