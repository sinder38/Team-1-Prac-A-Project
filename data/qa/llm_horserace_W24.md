# LLM Horse Race - Week 24

Role: R10 QA and Learning Log Lead  
Date checked: 21 June 2026

## Source checked

- `data/llm/llm_comparison_W24.md`
- `data/llm/synthesis_nemotron_W24.txt`
- `data/llm/synthesis_gptoss_W24.txt`
- `data/llm/synthesis_gemma_W24.txt`
- `data/llm/synthesis_laguna_W24.txt`
- `data/evidence/actuals_W25.md`

## Model comparison

The model lineup changed this sprint. W22 and W23 tracked Claude, ChatGPT, Gemini, and DeepSeek. W24 tracks Nemotron, gpt-oss-120b, Gemma, and Laguna. The four models did not agree on a single direction for Week 24.

| Model | Weekly regime | Confidence | SPX estimate |
| --- | --- | --- | ---: |
| Nemotron | Bullish | Low-Medium | -1.0% to +2.9% |
| gpt-oss-120b | Bullish | Low-Medium | -0.3% to +1.2% |
| Gemma | Neutral | Low-Medium | -1.0% to +1.5% |
| Laguna | Uncertain | Low | -0.97% to +2.91% |

## Actual SPX result

The actual SPX result for the matching prediction week was **+0.93%**.

This means Nemotron and gpt-oss-120b got the bullish direction right. Gemma and Laguna did not make a directional call, so they are scored as Partial. All four models had wide enough SPX ranges to include the actual result.

## Week 24 horse race result

| Model | Direction correct? | Actual inside SPX range? | SPX midpoint error |
| --- | --- | --- | ---: |
| Nemotron | Yes | Yes | 0.02 pp |
| gpt-oss-120b | Yes | Yes | 0.48 pp |
| Gemma | Partial (Neutral) | Yes | 0.68 pp |
| Laguna | Partial (Uncertain) | Yes | 0.04 pp |

Week 24 range winner: **Nemotron**

Important note: this is a clean win. Nemotron got the bullish direction right, included the actual result in its SPX range, and posted the closest midpoint error of any model (0.02 pp). Laguna was second-closest on midpoint but did not make a directional call.

## Running horse race table

| Sprint | Actual SPX result | Winner | Reason |
| --- | ---: | --- | --- |
| Week 22 | +1.40% | DeepSeek | DeepSeek and ChatGPT both covered the actual SPX move, but DeepSeek's midpoint was closer to the actual result. |
| Week 23 | +0.46% | DeepSeek | No model got direction right, but DeepSeek had the closest SPX range midpoint among the models that included the actual result. |
| Week 24 | +0.93% | Nemotron | Nemotron got the bullish direction right, included the actual result in its range, and had the closest midpoint error (0.02 pp). |

Lineup note: W22 and W23 winners are from the prior model lineup (Claude, ChatGPT, Gemini, DeepSeek). W24 onwards uses the new lineup (Nemotron, gpt-oss-120b, Gemma, Laguna). The two rounds cannot be directly compared.

## QA observation

This week was the opposite shape of W23. In W23 all four models agreed on Bearish and all four were wrong on direction. In W24 the models split — two Bullish, one Neutral, one Uncertain — and the two Bullish models got it right. Disagreement was a more useful signal than agreement here, because it forced the team to weigh evidence rather than lean on consensus.

Nemotron also stood out for a reason worth tracking. It made a clear directional call AND kept its range wide enough to include the actual result. That combination is rare. Most models either commit narrowly and miss, or hedge wide and avoid taking a stance. Nemotron did both well this week.

Two structural points for future horse race tracking:

- The change in model lineup between W23 and W24 means the running winner column should not be read as a continuous leaderboard. We should consider keeping a separate running table per lineup, or restarting the table when models change.
- Non-directional regimes (Neutral, Uncertain) need a clear scoring rule. This week I scored them as Partial, which is consistent with the spirit of the W23 method, but a documented rule would remove ambiguity in future sprints.
