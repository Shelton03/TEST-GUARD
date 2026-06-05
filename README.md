# AI Guard Safety – Test LLM App

A minimal **FastAPI** application designed to generate LLM traces so the
**AI Guard Safety** observability and evaluation pipeline can be verified
end-to-end.

> **This is not a production app.** It exists purely to produce traffic that
> exercises queues, evaluation workers, storage, and the monitoring UI.

---

## Project structure

```
test_llm_app/
├── main.py           # FastAPI server with /chat endpoint
├── test_client.py    # Batch test-prompt script
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

---

## Prerequisites

| Tool | Purpose |
|------|---------|
| Python ≥ 3.10 | Runtime |
| `pip` | Package manager |
| An OpenAI API key | LLM provider |
| AI Guard Safety installed | Monitoring daemon |

---

## Quick start

### 1 – Install AI Guard Safety (once)

```bash
pip install aiguard-safety
```

### 2 – Install app dependencies

```bash
cd test_llm_app
pip install -r requirements.txt
```

### 3 – Configure environment variables

Create a `.env` file in `test_llm_app/`:

```dotenv
# Required – your OpenAI API key (forwarded to LiteLLM / OpenAI)
OPENAI_API_KEY=sk-...

# Optional – model to use (default: gpt-4o-mini)
LLM_MODEL=gpt-4o-mini
```

> **Never commit `.env` to version control.**

### 4 – Start AI Guard

In a separate terminal:

```bash
aiguard dev
```

This starts the local monitoring daemon and opens the dashboard at
`http://localhost:3000`.

### 5 – Run the FastAPI server

```bash
uvicorn main:app --reload --port 8002
```

The server listens on `http://localhost:8002`.  
Swagger UI: `http://localhost:8002/docs`

### 6 – Generate traffic

```bash
python test_client.py
```

Optional flags:

```bash
# Custom server URL
python test_client.py --url http://localhost:8000

# Custom delay between requests (seconds)
python test_client.py --delay 2.0
```

### 7 – Open the monitoring dashboard

```
http://localhost:3000
```

You should see traces appearing in real-time as the test client sends prompts.

---

## API reference

### `POST /chat`

Send a user message and receive an LLM response.

**Request body**

```json
{
  "message": "Explain why the sky is blue"
}
```

**Response**

```json
{
  "response": "The sky appears blue because..."
}
```

### `GET /health`

Returns `{"status": "ok"}` — useful for readiness checks.

---

## Test prompts

`test_client.py` sends 9 prompts covering three categories:

| Category | Purpose |
|----------|---------|
| Normal / factual | Baseline traces |
| Hallucination bait | Tests hallucination-detection workers |
| Adversarial / prompt injection | Tests safety policy evaluation |
| Creative / open-ended | Tests response-quality evaluation |

---

## How tracing works

```
User
 │
 ▼
POST /chat  (FastAPI)
 │
 ▼
AIGuardClient.chat.completions.create(...)
 │          │
 │          └─► AI Guard Safety SDK
 │                  • logs prompt + response
 │                  • runs policy evaluations
 │                  • pushes trace to pipeline queue
 │
 ▼
OpenAI API  (underlying LLM provider)
 │
 ▼
Response returned to user
```
GGGGGggh
---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Import "aiguard_safety" could not be resolved` | Run `pip install aiguard-safety` |
| `502 LLM call failed` | Check `OPENAI_API_KEY` and `AIGUARD_API_KEY` in `.env` |
| No traces in dashboard | Make sure `aiguard dev` is running before the server |
| Connection refused on port 8002 | Make sure `uvicorn main:app --reload --port 8002` is running |

---

## CI / GitHub Actions

AIGuard evaluation runs automatically on every push and pull request via `.github/workflows/aiguard-eval.yml`.

**Requirements:**
- Set the `OPENAI_API_KEY` secret in your repository settings (Settings → Secrets and variables → Actions)

**What it does:**
1. Installs `aiguard-safety` and app dependencies
2. Runs `aiguard evaluate --project llm_test`
3. Uploads the AIGuard report as the `aiguard-report` artifact (retained for 30 days)

The evaluation step uses `continue-on-error: true` so the artifact still uploads even if evaluation fails.
