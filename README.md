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

## Web Application Stack (New)

This repository now includes a full web application for scheme-aware conversations:

- Frontend: React + Tailwind CSS (`frontend/`)
- Backend API: FastAPI (`backend/`)
- Relational DB: MySQL (chat sessions + scheme master data)
- Vector DB: Chroma (scheme retrieval for contextual answers)

### 1) Configure environment

Copy `.env.example` to `.env` and set:

- `MYSQL_URL`
- `GROQ_API_KEY`
- `SCHEME_CSV_PATH` (defaults to generated TN schemes CSV)

If MySQL auth fails with error `1045 Access denied`, use either:

- `MYSQL_URL=mysql+pymysql://<user>:<password>@localhost:3306/tn_scheme_compass`
- Or set `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` (leave `MYSQL_URL` empty)

Create DB and user (run in MySQL shell as an admin user):

```sql
CREATE DATABASE IF NOT EXISTS tn_scheme_compass CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'tn_user'@'localhost' IDENTIFIED BY 'StrongPassword123!';
GRANT ALL PRIVILEGES ON tn_scheme_compass.* TO 'tn_user'@'localhost';
FLUSH PRIVILEGES;
```

Then set:

```env
MYSQL_USER=tn_user
MYSQL_PASSWORD=StrongPassword123!
MYSQL_DATABASE=tn_scheme_compass
```

### 2) Install backend dependencies

```bash
pip install -r requirements.txt
```

### 3) Run FastAPI server

```bash
python run_api.py
```

API endpoints:

- `POST /api/chat/session` to create a chat session
- `POST /api/chat/message` to send a user message and get dynamic follow-up + scheme details
- `GET /api/chat/history/{session_id}` to fetch full conversation history

### 4) Run React frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.
