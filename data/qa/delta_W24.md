# delta_W24.md

Role: Delta Engine / R10 support
Status: Draft for team review

## What this checks

This file compares the locked vW24 prediction with the matching W25 actuals. The goal is simple: check whether the team got the direction right and how far the actual move was from the predicted range.

## Delta table

| Asset | Predicted direction | Predicted range | Confidence | Actual move | Actual direction | Direction correct? | Range hit? | Error % |
| --- | --- | ---: | --- | ---: | --- | --- | --- | ---: |
| SPX | FLAT-UP | -0.5% to +1.2% | Medium | +0.93% | UP | Y | Y | 0.00% |
| NDX | FLAT-UP | -0.5% to +2.0% | Medium | +2.60% | UP | Y | N | 0.60% |
| IWM | UP | +0.5% to +3.0% | Medium | +1.14% | UP | Y | Y | 0.00% |

## Summary

- Direction accuracy: 3 / 3
- Range accuracy: 2 / 3
- Average range error: 0.20%

## Short note

The team got the broad direction right across all three indexes. SPX and IWM landed inside the predicted range, while NDX finished outside the range. My main takeaway is that the direction call was useful, but the range still needs checking when one index moves more strongly than the others.

## Weight adjustment draft

This is the Delta Engine's first draft of how the next sprint weights could change. It is not meant to replace R7 or the team discussion; it is a starting point for the retrospective.

| Agent | Current weight | Suggested weight | Reason |
| --- | ---: | ---: | --- |
| almanac | 0.20 | 0.15 | Seasonality stays useful, but delta did not show it should dominate. |
| macro | 0.25 | 0.25 | Macro stays important because weekly moves can still depend on rates, oil, and event risk. |
| technical | 0.25 | 0.30 | Technical gets a range-check boost because direction was right but one range was too tight. |
| llm | 0.20 | 0.15 | LLM weight stays stable until we have more weekly history. |
| human_score | 0.10 | 0.15 | Human Score gets a small boost because the final direction call worked. |

## Prescription for next sprint

Direction was right, but NDX moved outside the range. Next sprint should widen range checks and use these draft weights: almanac 0.20->0.15, technical 0.25->0.30, llm 0.20->0.15, human_score 0.10->0.15.
