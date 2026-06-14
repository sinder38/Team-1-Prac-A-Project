# Calibration Log - Week 23

Role: R10 QA and Learning Log Lead  
Checked by: QA Lead  
Date checked: 13 June 2026

## Evidence checked

- `data/final prediction/prediction_2026-W03_Team1.md`
- `data/human/human_score_W3.md`
- `data/llm/llm_comparison_W3.md`
- `data/evidence/actuals_W4.md`
- `data/almanac/almanac_agent_W03.md`
- `data/macro/macro_agent_W3.md`
- `data/technical/technnical_agent_W3.md`

Note: `actuals_W4.md` is the correct actuals file for scoring the Week 23 prediction because the Week 23 prediction covered the market week of 8-12 June 2026.

## W23 prediction checked

The Week 23 final prediction file gave these calls for the next market week:

| Asset | Direction | Predicted range | Confidence |
| --- | --- | ---: | --- |
| SPX | Down | -1.0% to -3.0% | Medium |
| NDX | Down | -1.5% to -4.0% | Medium |
| IWM | Down | -1.0% to -3.5% | Medium |

Final regime call: **Neutral-Bearish**

Main invalidation: A cooler-than-expected CPI report, falling Treasury yields, and SPX reclaiming the 8 EMA.

## Actual result

From the Week 24 actuals file, all three indexes finished higher during the matching prediction week:

| Asset | Actual move | Actual direction |
| --- | ---: | --- |
| SPX | +0.46% | Up |
| NDX | +2.17% | Up |
| IWM | +3.93% | Up |

The team expected a bearish week, but the market bounced instead. Small caps were the strongest, which went against the team's bearish call.

## Calibration result

| Asset | Confidence | Direction correct? | Range hit? | Error size | Score |
| --- | --- | --- | --- | ---: | ---: |
| SPX | Medium | No | No | 1.46 pp | 0 |
| NDX | Medium | No | No | 3.67 pp | 0 |
| IWM | Medium | No | No | 4.93 pp | 0 |

Total calibration score: **0 / +9**

Direction accuracy: **0 / 3**

Range accuracy: **0 / 3**

## QA checks

| Check | Result |
| --- | --- |
| SPX, NDX, and IWM all have direction | Pass |
| SPX, NDX, and IWM all have percentage ranges | Pass |
| Confidence level is included | Pass |
| Human Score and override are included | Pass |
| Four-model LLM comparison is included | Pass |
| Main invalidation condition is included | Pass |
| Actuals week matches prediction week | Pass |

## QA decision

The W23 prediction had the required structure, but the result was wrong across all three indexes. The main issue was not formatting. The issue was that the team and the LLMs leaned too bearish after the previous selloff, while the actual week became a risk-on rebound.

For the next sprint, R10 should remind the team to avoid treating one strong bearish setup as certain. If CPI or rates are the main risk, the final range should leave enough room for a relief bounce.
