# TN Scheme Compass

A Python pipeline that builds a structured CSV of welfare schemes relevant to Tamil Nadu residents.

The pipeline follows these guardrails:
- Uses official government sources as source-of-truth.
- Uses Tavily for discovery of candidate official links.
- Uses Groq or Ollama LLM for schema-based extraction from official page text.
- Rejects rows without official URL evidence.
- Produces accepted and review CSV files.
- Streams rows to CSV immediately as each page is processed.

## What this project generates

- `outputs/welfare_schemes_tamil_nadu.csv` (accepted rows)
- `outputs/review_queue.csv` (rejected/needs-review rows)
- `outputs/run_metadata.json` (coverage and run diagnostics)

## Setup

1. Create and activate a virtual environment.
2. Install dependencies.
3. Fill `.env` with your local API keys.

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

## Run

```bash
python -m src.pipeline --output-file outputs/welfare_schemes_tamil_nadu.csv
```

Optional controls:

```bash
python -m src.pipeline --max-results-per-query 25 --max-pages 300 --min-confidence 0.6
```

Use Ollama locally (for example when Groq is rate-limited):

```bash
python -m src.pipeline --llm-provider ollama --ollama-model llama3:8b --ollama-base-url http://localhost:11434 --max-pages 80 --min-confidence 0.01
```

If you use Ollama, ensure the model is available:

```bash
ollama pull llama3:8b
```

## Safety and trust notes

- Never hardcode API keys.
- Keep `.env` local only.
- The final accepted CSV only includes rows backed by official source URLs.
- Low-confidence or contradictory rows are routed to the review queue.

## Scope notes

- This is a one-time extraction pipeline by default.
- It prioritizes Tamil Nadu state schemes and central schemes applicable to Tamil Nadu residents.
- It stores only public scheme metadata, not personal beneficiary data.
