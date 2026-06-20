# LLM Horse Race - Week 22

Role: R10 QA and Learning Log Lead  
Date checked: 6 June 2026

## What this file is for

This file tracks which AI model gave the closest SPX forecast. Over the sprint weeks, this should help the team see whether ChatGPT, Claude, Gemini, or DeepSeek is giving the most useful market forecast.

## Evidence used

I used the merged R6 comparison table:

`data/llm/llm_comparison_W2.md`

The actual SPX result from `data/evidence/actuals_W2.md` was:

| Asset | Actual result |
| --- | ---: |
| SPX | +1.40% |

## Week 22 comparison

| Model | SPX estimate | Compared with actual +1.40% |
| --- | ---: | --- |
| Claude | +0.3% to +1.2% | Slightly low |
| ChatGPT | +0.3% to +1.5% | Hit range |
| Gemini | +0.5% to +1.2% | Slightly low |
| DeepSeek | +0.5% to +1.5% | Hit range and closest midpoint |

## Week 22 winner

Winner: **DeepSeek**

DeepSeek and ChatGPT both included the actual +1.40% result inside their predicted SPX ranges. I chose DeepSeek as the winner because its midpoint was slightly closer to the actual result.

## Running record

| Sprint | Actual SPX result | Winner | Reason |
| --- | ---: | --- | --- |
| Week 22 | +1.40% | DeepSeek | Hit range and closest midpoint |

## QA note

Next sprint, the comparison table should clearly state the prediction week and should be committed before the final prediction is locked. This will make the LLM horse race easier to check.
