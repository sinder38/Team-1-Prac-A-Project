# Learning Log - Week 24

Role: R10 QA and Learning Log Lead  
Date checked: 21 June 2026

## What did we predict?

The team prediction for Week 24 was **Neutral-Bullish**.

| Asset | Direction | Predicted range | Confidence |
| --- | --- | ---: | --- |
| SPX | Flat-Up | -0.5% to +1.2% | Medium |
| NDX | Flat-Up | -0.5% to +2.0% | Medium |
| IWM | Up | +0.5% to +3.0% | Medium |

The main reason was a triple-loosening in macro conditions (oil, Treasury yields, and the US dollar all falling), a recovering technical picture, and a strong chip sector rally. The team also kept confidence at Medium because the FOMC decision on June 18 was a binary event risk.

## What actually happened?

The matching actual result is in `data/evidence/actuals_W25.md`, because that file covers the week ended Friday 19 June 2026.

| Asset | Actual move | Direction result | Range result |
| --- | ---: | --- | --- |
| SPX | +0.93% | Right | Hit |
| NDX | +2.60% | Right | Miss (0.60 pp over) |
| IWM | +1.14% | Right | Hit |

All three indexes went up, matching the team's direction call. NDX overshot the top of the predicted range by 0.60 pp as the chip rally extended into a second week. SPX and IWM both closed inside the predicted range.

## Calibration result

The W24 calibration score is **+7 / +9**.

Direction accuracy: 3 / 3.  
Range accuracy: 2 / 3.

This is a big jump from the W23 score of 0 / +9. The team got direction right across all three indexes and only missed the NDX range by a small amount.

## What surprised me?

The biggest surprise was that the leadership flipped. The team predicted IWM as the strongest mover (+0.5% to +3.0%), but tech ended up leading instead. NDX finished up 2.60% while IWM only managed +1.14%. Small caps did not lead the way as expected.

The chip rally was the main driver. Intel, KLA, Applied Materials, and Micron continued to run hard, which lifted NDX more than the team's range allowed for. IWM's bounce was real but quieter than the W4 actuals had implied it would be.

The FOMC decision on Thursday did not cause the binary shock the team had been worried about, which helped the Neutral-Bullish call hold.

## What did we learn?

The main QA lesson is that wild card observations should flow through to the ranges. The team correctly identified the chip rally as a momentum trend in the wild card section, but the NDX range was still capped at +2.0%. When a specific sub-sector trend is flagged in the human override, the matching index range should be widened to reflect it.

The second lesson is that the team did not overcorrect after the W23 miss. After being wrong and bearish the previous week, it would have been easy to either chase the bounce with a bullish High-confidence call or stay cautious and keep predicting Down. The team did neither — they leaned Neutral-Bullish but kept confidence at Medium and left room in the ranges for a flat outcome. That balance is what produced the +7 score.

## One change next sprint

Next sprint, R10 should check two things before the final prediction is locked:

- whether each index range is wide enough to cover any momentum trend flagged in the wild card section,
- whether the predicted leadership order (IWM vs NDX vs SPX) is consistent with the sector callouts in the human override.

This should reduce the chance of getting direction right but missing the range, especially when one sub-sector is clearly running.
