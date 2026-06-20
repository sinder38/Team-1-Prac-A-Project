# LLM Horse Race - Week 23

Role: R10 QA and Learning Log Lead  
Date checked: 13 June 2026

## Source checked

- `data/llm/llm_comparison_W3.md`
- `data/llm/synthesis_chatgpt_W3.txt`
- `data/llm/synthesis_claude_W3.txt`
- `data/llm/synthesis_gemini_W3.txt`
- `data/llm/synthesis_deepseek_W3.txt`
- `data/evidence/actuals_W4.md`

## Model comparison

All four models gave a bearish weekly regime for Week 23.

| Model | Weekly regime | Confidence | SPX estimate |
| --- | --- | --- | ---: |
| Claude | Bearish | Medium | -3.5% to +1.5% |
| ChatGPT | Bearish | High | -0.8% to -3.0% |
| Gemini | Bearish | Medium | -1.0% to -3.0% |
| DeepSeek | Bearish | Medium | -3.0% to +1.5% |

## Actual SPX result

The actual SPX result for the matching prediction week was **+0.46%**.

This means the bearish direction was wrong for every model. However, Claude and DeepSeek had wide enough SPX ranges to include the actual result.

## Week 23 horse race result

| Model | Direction correct? | Actual inside SPX range? | SPX midpoint error |
| --- | --- | --- | ---: |
| Claude | No | Yes | 1.46 pp |
| ChatGPT | No | No | 2.36 pp |
| Gemini | No | No | 2.46 pp |
| DeepSeek | No | Yes | 1.21 pp |

Week 23 range winner: **DeepSeek**

Important note: this is not a clean directional win. DeepSeek wins only because its wider SPX range included the actual +0.46% result and its midpoint was closer than Claude's midpoint. No model got the actual SPX direction right.

## Running horse race table

| Sprint | Actual SPX result | Winner | Reason |
| --- | ---: | --- | --- |
| Week 22 | +1.40% | DeepSeek | DeepSeek and ChatGPT both covered the actual SPX move, but DeepSeek's midpoint was closer to the actual result. |
| Week 23 | +0.46% | DeepSeek | No model got direction right, but DeepSeek had the closest SPX range midpoint among the models that included the actual result. |

## QA observation

The models agreed too strongly on the bearish story. The useful warning sign was that Claude and DeepSeek still left room for a bounce in their ranges. ChatGPT was the most confident, but it was also too narrow for the actual result.

For future horse race tracking, I think we should record both direction accuracy and range accuracy. A model can be wrong on direction but still show better uncertainty handling through a wider range.
