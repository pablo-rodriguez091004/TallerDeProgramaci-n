# Video Script (English) — MecaTrack, Lab Guide 5

**Target length:** 2:30–3:00 · **Speaking pace:** ~140 words/min.
**Before recording:** run `./scripts/capture_screenshots.sh` once (or start the backend with
`./scripts/start-backend.sh`), open `http://127.0.0.1:5000/docs`, and have
`evidence/prompt_eval/results.csv` and `evidence/cost_estimate_EN.md` ready in another tab.

> Numbers in this script come from the real runs stored in `evidence/`. If you re-run the
> experiment, update them from `evidence/prompt_eval/results.json` → `summary`.

---

## 0. Intro — 0:00–0:15

**On screen:** Swagger UI landing page (`/docs`).

> Hi, I'm **[YOUR NAME]**. This is MecaTrack, a booking and vehicle-tracking system for a car
> repair workshop. For this lab I added a versioned REST API documented with OpenAPI 3, and an
> AI assistant that suggests workshop services from a symptom described by the customer.

## 1. API demo in Swagger UI — 0:15–1:05

**On screen:** expand `POST /auth/login` → *Execute* (200).

> The API lives under `/api/v1`, separate from the routes the existing frontend uses, so nothing
> broke. First I log in; the session cookie is reused by Swagger for the protected calls.

**On screen:** `GET /api/v1/services` → *Execute* (200, list).

> Reading the catalog is public. Every endpoint has a summary, a description and examples.

**On screen:** `GET /api/v1/services/{service_id}` with `9999` → 404.

> Errors always share one format: a machine-readable `code`, a human `message`, and `details`.
> Here, a 404 for a service that does not exist.

**On screen:** `POST /api/v1/services` with an invalid body → 422.

> Invalid input returns 422 with the error of each field. Creating, replacing or deleting
> requires the owner or admin role; and deleting a service that already has appointments
> returns 409 instead of leaving orphan bookings.

**On screen (optional, 3 s):** GitHub Actions run in green.

> Thirty-one integration tests run against a real PostgreSQL database in GitHub Actions;
> the LLM is mocked there, so CI never needs the API key.

## 2. The AI endpoint and the prompt experiment — 1:05–2:00

**On screen:** `POST /api/v1/ai/suggest-service` with
`"Siento olor dulce dentro del carro y la temperatura sube cuando hay trancon"`, technique `cot` → 200.

> The AI endpoint uses retrieval-augmented generation. First it retrieves the relevant services
> from the database by keyword, then it puts them in the prompt, and the model may choose
> **only** among them. The model returns ids; prices and durations come from the database,
> so it cannot invent a price. Timeouts map to 504, rate limits are retried with exponential
> backoff and then return 429, and every call is logged in an `ai_calls` table.

**On screen:** `results.csv` or the comparison table from the report.

> I compared three prompting techniques on ten real symptoms with Gemini 3.5 Flash-Lite,
> thirty real calls in total. Zero-shot, few-shot and chain-of-thought all reached
> **90 % top-1 precision**. The difference was cost and latency: zero-shot averaged
> **356 input and 76 output tokens** and about **1.0 seconds**; few-shot more than doubled the
> input, to **790 tokens**, because the examples travel in every prompt; chain-of-thought
> produced **184 output tokens** — its written reasoning — which makes it the most expensive.
> At fifty queries a day that is **$0.44, $0.66 and $0.88 per month** respectively.

> The one failure was the same in all three: a clutch problem. The keyword retrieval did not
> bring the clutch service into the context, and the model, correctly following the rules,
> said the workshop did not offer it. So the weak link was retrieval, not the prompt —
> which is the main lesson of the experiment.

## 3. Critical evaluation of a Copilot suggestion — 2:00–2:30

**On screen:** the code you are talking about, in VS Code.

> **[TO COMPLETE WITH YOUR OWN REAL EXPERIENCE — do not read this placeholder.]**
> Structure suggestion (about 70 words):
> 1. What you asked Copilot for, and in which file.
> 2. What it suggested (show it).
> 3. What was wrong or risky about it (e.g. a hard-coded secret, a missing error case,
>    an outdated API, a wrong HTTP code) and how you noticed.
> 4. What you kept, what you changed, and why.

## 4. Key concepts — 2:30–2:55

**On screen:** Swagger landing page or the architecture diagram from the report.

> To sum up: **REST** means resources, HTTP verbs and meaningful status codes. **OpenAPI** is the
> contract: one JSON file that documents the API and powers Swagger UI. **Prompt engineering**
> is how you ask: examples help consistency, step-by-step reasoning helps explanation, and both
> cost tokens. And **RAG** grounds the model in our own data, so its answer is only as good as
> what we retrieve. Thank you.

---

### Checklist before recording
- [ ] Replace **[YOUR NAME]** and complete section 3 with a real experience.
- [ ] Backend running and logged in; one AI call uses one request of the per-user hourly limit (20).
- [ ] Rehearse once with a timer; cut the optional CI line if you go over 3:00.
