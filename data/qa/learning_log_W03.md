# Learning Log - Week 3

Role: R10 QA and Learning Log Lead  
Date checked: 13 June 2026

## What did we predict?

The team prediction for Week 3 was **Neutral-Bearish**.

| Asset | Direction | Predicted range | Confidence |
| --- | --- | ---: | --- |
| SPX | Down | -1.0% to -3.0% | Medium |
| NDX | Down | -1.5% to -4.0% | Medium |
| IWM | Down | -1.0% to -3.5% | Medium |

The main reason was that several pieces of evidence pointed in the same direction: weak June seasonality, higher Treasury yields, a stronger US dollar, higher oil prices, and technical weakness after the previous Friday selloff.

## What actually happened?

The matching actual result is in `data/evidence/actuals_W4.md`, because that file covers the week ended Friday 12 June 2026.

| Asset | Actual move | Direction result | Range result |
| --- | ---: | --- | --- |
| SPX | +0.46% | Wrong | Miss |
| NDX | +2.17% | Wrong | Miss |
| IWM | +3.93% | Wrong | Miss |

All three indexes went up instead of down. The miss was largest in IWM because small caps had the strongest rebound.

## Calibration result

The W3 calibration score is **0 / +9**.

All three predictions used Medium confidence. Under the scoring rule, Medium confidence with the wrong direction scores 0. This means the team did not gain calibration points, but it also did not get a negative score.

## What surprised me?

The biggest surprise was how one-sided the model agreement looked before the week. All four LLMs were bearish, and the human score also supported a bearish call. In the actual result, the market recovered instead, especially in small caps.

This makes me think the team may have overweighted the previous Friday selloff and the CPI risk. The bearish evidence was real, but it was not enough to stop a relief bounce.

## What did we learn?

The main QA lesson is that agreement is not the same as certainty. Even when all four models agree, the team still needs to check whether the predicted range leaves enough room for a reversal.

I also learned that the correct actuals file matters a lot. `actuals_W3.md` was evidence for the prediction, while `actuals_W4.md` was the result of that prediction. Keeping that timeline clear made the scoring more honest.

## One change next sprint

Next sprint, R10 should check two things before the final prediction is locked:

- whether the final range includes both the main thesis and a realistic relief-bounce scenario,
- whether confidence is low enough when the week depends on one major macro event like CPI.

This should make the team's calibration more balanced, especially when the models all agree too strongly.
