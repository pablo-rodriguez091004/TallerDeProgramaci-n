# LLM Cost Estimate - MecaTrack AI Assistant

**Model:** `gemini-3.5-flash-lite` (Google Gemini API). **Price (paid tier, Standard):** $0.30 per 1M input tokens and $2.50 per 1M output tokens (thinking tokens are billed as output). Source: Google AI for Developers, *Gemini Developer API pricing*, https://ai.google.dev/gemini-api/docs/pricing (page last updated 2026-10-19, accessed 2026-10-20).

## Formula

```
cost_per_call = avg_input_tokens x input_price / 1,000,000
              + (avg_output_tokens + avg_thinking_tokens) x output_price / 1,000,000
monthly_cost  = cost_per_call x queries_per_day x days_per_month
```

## Assumptions

- 50 queries per day x 30 days = **1,500 calls per month**.
- Average tokens are measured, not estimated: they come from the 30 real calls of the prompt experiment (10 cases x 3 techniques).
- One LLM call per customer query. Retries after a 429/503 happened in 1 of 30 calls of the experiment; the failed attempt reported no token usage, so nothing is added for it.
- The retrieval step (keyword matching) runs in our server and has no API cost.

## Results

| Technique | Avg input tokens | Avg output tokens | Cost per call (USD) | Cost per 1,000 calls (USD) | Monthly cost (USD) | Top-1 precision |
|---|---:|---:|---:|---:|---:|---:|
| zero_shot | 356.3 | 75.5 | 0.000296 | 0.2956 | 0.4435 | 90% |
| few_shot | 790.3 | 81.3 | 0.000440 | 0.4403 | 0.6605 | 90% |
| cot | 425.3 | 184 | 0.000588 | 0.5876 | 0.8814 | 90% |

## Reading the numbers

- Every technique costs **less than one US dollar per month** at this volume. `cot` is about 2.0x more expensive per call than `zero_shot`.
- Few-shot uses 2.2x the **input** tokens of zero-shot (the three examples travel in every prompt); chain-of-thought uses 2.4x the **output** tokens (the written reasoning), and output tokens cost 8.3x more than input tokens with this model.
- The free tier of this model costs $0, but it has stricter rate limits and Google states that free-tier content is *used to improve our products*; for real customer data the paid tier (not used for that purpose) is the safer choice.
