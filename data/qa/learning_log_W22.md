# Learning Log - Week 22

Role: R10 QA and Learning Log Lead  
Date checked: 6 June 2026

## What did we predict?

The Week 22 final prediction file gave these calls:

| Asset | Direction | Range | Confidence |
| --- | --- | ---: | --- |
| S&P 500 (SPX) | Up | +0.2% to +1.0% | Medium |
| Nasdaq 100 (NDX) | Up | +0.5% to +1.5% | Medium |
| Russell 2000 (IWM) | Up | 0.0% to +1.2% | Low-Medium |

The Human Score total was 0, so the team adjusted the AI consensus from bullish to neutral-bullish. The main human concern was narrow market breadth: only 57% of S&P 500 stocks were above their 200-day moving average, based on the R5 Technical Agent output.

## What actually happened?

Based on `data/evidence/actuals_W2.md`:

- SPX was +1.40%.
- NDX was +2.86%.
- IWM was +1.82%.
- WTI crude oil was -9.57%.
- VIX was -9.95%.
- Technology was the strongest sector at +5.89%.

The team was correct on direction for SPX, NDX, and IWM.

## Calibration result

Using the teacher's confidence scoring table:

| Asset | Result |
| --- | --- |
| SPX | Medium confidence and correct direction: +2 |
| NDX | Medium confidence and correct direction: +2 |
| IWM | Low-Medium confidence counted as Low / Uncertain and correct direction: +1 |

Calibration score: **+5 / +9**

## LLM horse race update

The R6 LLM comparison table is available in `data/llm/llm_comparison_W2.md`. For SPX, ChatGPT and DeepSeek both included the actual +1.40% result inside their predicted ranges. I recorded DeepSeek as the Week 22 winner because its midpoint was closest to the actual SPX move.

## What surprised me?

NDX was much stronger than SPX and IWM. This shows that the week was mainly led by technology. The team was right to lean bullish, but the NDX move was stronger than the final range.

I also noticed that `Low-Medium` confidence is harder to score because the teacher's table uses High, Medium, and Low / Uncertain. For QA, clear confidence labels make calibration easier.

## What did we learn?

Being right on direction is useful, but the exact range and confidence label still matter. The team got direction correct, but SPX, NDX, and IWM all moved above the predicted ranges.

The LLM horse race was easier to update once the R6 comparison table was merged. The final prediction was also easier to check once the Human Score and prediction file were both in GitHub.

## What will we do differently next sprint?

Next sprint, R10 should check the final prediction file before submission and make sure:

- SPX, NDX, and IWM all have direction, range, and confidence,
- confidence uses High, Medium, or Low,
- the final prediction file is committed before actuals are scored,
- raw LLM outputs and Human Score evidence are easy to find.

My main improvement is to check the confidence labels before calibration, so the final score is not ambiguous.
