# LLM Horse Race - Week 3

Role: R10 QA and Learning Log Lead  
Date checked: 7 June 2026

## Source checked

- `data/llm/llm_comparison_W3.md`
- `data/llm/synthesis_chatgpt_W3.txt`
- `data/llm/synthesis_claude_W3.txt`
- `data/llm/synthesis_gemini_W3.txt`
- `data/llm/synthesis_deepseek_W3.txt`

## Model comparison

All four models gave a bearish weekly regime for Week 3.

| Model | Weekly regime | Confidence | SPX estimate |
| --- | --- | --- | ---: |
| Claude | Bearish | Medium | -3.5% to +1.5% |
| ChatGPT | Bearish | High | -0.8% to -3.0% |
| Gemini | Bearish | Medium | -1.0% to -3.0% |
| DeepSeek | Bearish | Medium | -3.0% to +1.5% |

## Latest completed result

The latest completed LLM horse race is still Week 2, because Week 3 has not reached its matching Friday close yet.

| Sprint | Actual SPX result | Winner | Reason |
| --- | ---: | --- | --- |
| Week 2 | +1.40% | DeepSeek | DeepSeek and ChatGPT both covered the actual SPX move, but DeepSeek's midpoint was closer to the actual result. |

## Horse race status

Week 3 winner: **Not applicable at filing time**

This is intentional. The LLM horse race should be scored against the actual SPX result for the same prediction week. Since the Week 3 prediction is being filed before that week has happened, I can record the model calls now but I should not choose a winner yet.

## QA observation

The models agree on direction, but they do not agree equally on risk. ChatGPT and Gemini give narrower downside ranges, while Claude and DeepSeek leave more room for a relief bounce. The main shared caveat is CPI: if CPI is cooler than expected, the bearish call could reverse quickly.

## Scoring method for later

After the matching actual SPX result is available, I will choose the winner using this order:

1. Did the model get the SPX direction right?
2. Did the actual SPX result fall inside the model's range?
3. If more than one model qualifies, which model midpoint was closest to the actual SPX result?
4. If there is still a tie, I will prefer the model with clearer caveat language and less overconfidence.
