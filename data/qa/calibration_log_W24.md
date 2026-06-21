# Calibration Log - Week 24

Role: R10 QA and Learning Log Lead  
Checked by: QA Lead  
Date checked: 21 June 2026

## Evidence checked

- `data/final prediction/prediction_2026-W24_Team1.md`
- `data/human/human_score_W24.md`
- `data/llm/llm_comparison_W24.md`
- `data/evidence/actuals_W25.md`
- `data/almanac/almanac_agent_W24.md`
- `data/macro/macro_agent_W24.md`
- `data/technical/technical_agent_W24.md`

Note: `actuals_W25.md` is the correct actuals file for scoring the Week 24 prediction because the Week 24 prediction covered the market week of 15-19 June 2026.

## W24 prediction checked

The Week 24 final prediction file gave these calls for the next market week:

| Asset | Direction | Predicted range | Confidence |
| --- | --- | ---: | --- |
| SPX | Flat-Up | -0.5% to +1.2% | Medium |
| NDX | Flat-Up | -0.5% to +2.0% | Medium |
| IWM | Up | +0.5% to +3.0% | Medium |

Final regime call: **Neutral-Bullish**

Main invalidation: A hawkish FOMC surprise on June 18 (higher-for-longer signal or upward dot plot revision) that drives Treasury yields higher and pushes SPX back below the 7,017 support zone.

## Actual result

From the Week 25 actuals file, all three indexes finished higher during the matching prediction week:

| Asset | Actual move | Actual direction |
| --- | ---: | --- |
| SPX | +0.93% | Up |
| NDX | +2.60% | Up |
| IWM | +1.14% | Up |

The team expected a Neutral-Bullish week with small caps leading. Direction was correct across all three indexes. NDX outperformed expectations as the chip rally continued, while IWM gains were softer than the team's bullish range implied — the leadership baton passed from small caps to tech.

## Calibration result

| Asset | Confidence | Direction correct? | Range hit? | Error size | Score |
| --- | --- | --- | --- | ---: | ---: |
| SPX | Medium | Yes | Yes | Within range | +3 |
| NDX | Medium | Yes | No | 0.60 pp | +1 |
| IWM | Medium | Yes | Yes | Within range | +3 |

Total calibration score: **+7 / +9**

Direction accuracy: **3 / 3**

Range accuracy: **2 / 3**

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

The W24 prediction had the required structure and the result was strong across all three indexes. Direction was correct for SPX, NDX, and IWM, and both SPX and IWM finished inside the predicted range. NDX overshot the upper bound by 0.60 pp as the chip rally extended into a second week.

The lesson from W23 was applied well. After leaning too bearish the prior week, the team did not overcorrect or chase the bounce. Instead, the human override pulled the regime to Neutral-Bullish while keeping confidence at Medium and leaving room in the ranges for a flat outcome. The triple-loosening wild card observation (oil, yields, and DXY all falling) and the chip-sector callout proved to be the right reads. The FOMC binary risk was the main reason confidence was held at Medium rather than raised, and that judgement looks correct given how concentrated the gains were in tech rather than spread evenly.

For the next sprint, R10 should note that the IWM range was a touch wide on the upside (+0.5% to +3.0%) while the NDX range was a touch narrow on the upside (capped at +2.0% despite an active chip-led rally already in motion). When a specific sub-sector trend is flagged in the wild card section, the matching index range should be widened to reflect it.
