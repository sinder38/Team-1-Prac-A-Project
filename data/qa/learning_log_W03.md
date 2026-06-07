# Learning Log - Week 3

Role: R10 QA and Learning Log Lead  
Date checked: 7 June 2026

## What did we predict?

The team prediction for Week 3 is **Neutral-Bearish**.

| Asset | Direction | Predicted range | Confidence |
| --- | --- | ---: | --- |
| SPX | Down | -1.0% to -3.0% | Medium |
| NDX | Down | -1.5% to -4.0% | Medium |
| IWM | Down | -1.0% to -3.5% | Medium |

The main reason is that several pieces of evidence point in the same direction: weak June seasonality, higher Treasury yields, a stronger US dollar, higher oil prices, and technical weakness after Friday's sell-off.

## What actually happened?

For this Week 3 prediction, the matching actual result has not happened yet. The file `data/evidence/actuals_W3.md` records the market evidence from the week ended Friday 5 June, which is the evidence base for the new prediction. I am not treating that file as the result of the new W3 prediction.

The correct actuals for this prediction should be checked after the predicted market week closes.

## What surprised me?

I expected some disagreement between the models because CPI is a major wildcard, but all four models still reached a bearish regime. The useful part is that the team did not turn that into High confidence. R7 kept the final call at Medium confidence because one CPI report could change the whole setup.

## What did we learn?

The biggest QA lesson this week is that the prediction window and evidence window must be kept separate. A file can be useful evidence without being the final result for scoring. If we mix those two things, the calibration score becomes misleading.

I also learned that R10 should check the final prediction file before submission, not only after everything is merged. It is easier to fix missing direction, range, confidence, or invalidation conditions before the release tag is created.

## One change next sprint

Next sprint, R10 will do a quick pre-submission QA check before the final tag is created. The locked prediction file must clearly show:

- SPX, NDX, and IWM direction
- percentage range for each index
- confidence level for each index
- prediction week
- main invalidation condition

This should make the later calibration step cleaner and reduce confusion between evidence files and actual result files.
