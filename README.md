# AI Resume Builder

Build a resume from a form or an uploaded PDF, preview it in three ATS-safe themes, score it against a job description, let Claude tailor it to the job, and email yourself the PDF.

| Layer | Tech |
|---|---|
| Backend | Python 3.11, FastAPI, Pydantic |
| Frontend | React 19 (Vite), Tailwind CSS 4 |
| Database | MongoDB via `motor` |
| PDF | Jinja2 HTML/CSS templates → WeasyPrint |
| Resume import | `pdfplumber` text extraction → LLM structuring |
| LLM | Claude (`claude-opus-5`) by default; Groq, OpenRouter and OpenAI adapters included |
| Email | Gmail SMTP with an App Password |

## Quick start (Docker)

```bash
cp .env.example .env        # then fill in ANTHROPIC_API_KEY, GMAIL_ADDRESS, GMAIL_APP_PASSWORD
docker compose up --build
```

- App: http://localhost:8080
- API docs (Swagger): http://localhost:8000/docs

## Local development (without Docker)

You need Python 3.11+, Node 20.19+ or 22.12+, and a MongoDB server on `localhost:27017`.

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload            # reads ../.env

# Frontend (second terminal)
cd frontend
npm install
npm run dev                              # http://localhost:5173, proxies /api -> :8000
```

PDF output needs WeasyPrint's system libraries. On macOS run `brew install pango`; on Debian/Ubuntu run `apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0`. Without them, everything except PDF download and email still works; those two return a clear 503 error.

## Getting a Gmail App Password

Gmail won't accept your normal password over SMTP. Create an App Password instead:

1. Turn on **2-Step Verification** for your Google account (Google Account → Security). App Passwords only exist when it's on.
2. Open https://myaccount.google.com/apppasswords.
3. Enter a name such as "Resume Builder" and click **Create**.
4. Copy the 16-character password into `GMAIL_APP_PASSWORD`. The spaces Google shows are optional. Set `GMAIL_ADDRESS` to the same Gmail account.

To use the Gmail API with OAuth2 instead, see the step-by-step note at the top of `backend/app/services/emailer.py`.

## Running the AI locally for free (Ollama)

```bash
brew install ollama
brew services start ollama
ollama pull qwen2.5:7b          # ~4.7 GB; fits comfortably in 16 GB RAM
```

Then set `LLM_PROVIDER=ollama` in `.env` and run `docker compose up --build`. The backend container reaches Ollama on your Mac through `host.docker.internal`. A local model is slower than a cloud API: expect around a minute per AI step, and several minutes for **Optimize**.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `MONGODB_URI` | `mongodb://localhost:27017/resume_builder` | Mongo connection string. docker-compose overrides it. |
| `LLM_PROVIDER` | `anthropic` | `anthropic`, `openrouter`, `groq` or `openai` |
| `ANTHROPIC_API_KEY` | – | Required for AI features with Claude |
| `ANTHROPIC_MODEL` | `claude-opus-5` | Claude model id |
| `OPENROUTER_API_KEY` | – | Required when `LLM_PROVIDER=openrouter` |
| `OPENROUTER_MODEL` | – | OpenRouter model slug, e.g. `anthropic/claude-opus-5` (see openrouter.ai/models). Pick a model that supports structured outputs. |
| `GROQ_API_KEY` | – | Required when `LLM_PROVIDER=groq` (free tier at console.groq.com/keys) |
| `GROQ_MODEL` | – | Groq model slug (see console.groq.com for current models) |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Local model when `LLM_PROVIDER=ollama` |
| `OLLAMA_NUM_CTX` | `16384` | Context window for the local model |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Where Ollama runs. docker-compose sets it to `host.docker.internal`. |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | – | Required when `LLM_PROVIDER=openai` |
| `ATS_THRESHOLD` | `90` | Target score (0–100) |
| `OPTIMIZE_MODE` | `improve` | `improve` or `gate` (see below) |
| `MAX_OPTIMIZE_ITERATIONS` | `3` | Max rewrite → re-score rounds |
| `ATS_KEYWORD_WEIGHT` / `ATS_SEMANTIC_WEIGHT` | `0.7` / `0.3` | Score weighting |
| `EMBEDDINGS_PROVIDER` | `local` | `local` (built-in) or `openai` (embeddings API) |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Used when `EMBEDDINGS_PROVIDER=openai` |
| `ATS_SEMANTIC_FLOOR` / `ATS_SEMANTIC_CEILING` | per provider | Calibrates raw cosine similarity onto 0–100 |
| `GMAIL_ADDRESS` / `GMAIL_APP_PASSWORD` | – | Sender account. It is also the default recipient. |

## How it works

### ATS score

`overall = (keyword_weight × keyword_coverage + semantic_weight × semantic_similarity) / (sum of weights)`

- **Keyword coverage.** Claude extracts 10–30 skills, tools and responsibilities from the JD, each tagged required or preferred. The app then checks which ones appear in the resume. Matching is whole-word, case- and punctuation-insensitive, and accepts synonyms and plurals. Required terms count double. The extracted keywords are cached per JD, so re-scoring the same JD is consistent.
- **Semantic similarity.** By default this is a dependency-free term-vector cosine. Claude has no embeddings endpoint, and `sentence-transformers` would add about 2 GB to the image. Set `EMBEDDINGS_PROVIDER=openai` for true embeddings.
- The response includes `overall_score`, `matched_keywords`, `missing_keywords` and 3–5 `suggestions`.

### Optimization: `OPTIMIZE_MODE`

The original requirement ("if score > 90%, create the new resume") can be read two ways, so it's configurable:

- **`improve` (default).** If the resume scores **below** `ATS_THRESHOLD`, Claude rewrites it and it is re-scored, for up to `MAX_OPTIMIZE_ITERATIONS` rounds. The loop stops early once the threshold is met and returns the best-scoring version. A resume that already meets the threshold is left alone.
- **`gate`.** The threshold is a quality gate. A resume must already score at or above it to get one polish pass, and the polished version is kept only if it still passes. Below the gate the request is declined with suggestions.

**Truthfulness.** The rewrite prompt forbids inventing employers, titles, dates, degrees or metrics. The code also enforces this: after every rewrite, contact details, employers, titles, dates, locations, project names and education are copied back from the source resume. Claude can only change wording in the summary, skills, bullets and project stacks.

### Storage

MongoDB keeps exactly one document per user in each collection. Every write replaces the previous one and no history is kept.

```
resumes:          { user_id, resume, theme, updated_at }
job_descriptions: { user_id, jd_text, last_score, updated_at }
```

The resume is written by `POST /resume` (the **Save** button). The JD and its score are written on every score or optimize call.

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/resume/parse` | Upload a PDF (multipart `file`) and get the structured resume back |
| `POST` | `/resume` | Save the latest resume and theme (upsert) |
| `GET` | `/resume` | Latest saved resume (404 if none) |
| `GET` | `/job-description` | Last JD scored or optimized (404 if none). *Added so the UI can restore it.* |
| `GET` | `/themes` | Available themes |
| `POST` | `/resume/preview` | `{resume, theme, format: "html" \| "pdf"}` → HTML or PDF |
| `POST` | `/ats/score` | `{resume, job_description}` → score breakdown |
| `POST` | `/ats/optimize` | `{resume, job_description}` → optimized resume, original and final scores |
| `POST` | `/resume/section/edit` | `{section_name, section_data, instruction}` → the same section with the instruction applied. `section_name` is `summary`, `skills`, `experience_entry`, `project_entry`, `education` or `accomplishments`. |
| `POST` | `/resume/email` | `{resume, theme, to?}` → renders the PDF and emails it |
| `GET` | `/health` | Liveness check |

Errors always have the shape `{"error": {"code": "...", "message": "..."}}`.

## Assumptions

- **No authentication.** The spec doesn't define users, so the app is single-user (`user_id = "default"`). Clients may send an `X-User-Id` header to keep separate records. Add real authentication before exposing the app on the internet.
- **Email recipient.** "The user's Gmail" is taken to mean `GMAIL_ADDRESS`. The UI lets you enter a different recipient.
- **Refusal fallback.** With `claude-opus-5`, requests enable Anthropic's server-side refusal fallback (`fallbacks: "default"`). If the model declines a request, the API retries it on a fallback model within the same call.
- **Themes.** The themes are original designs inspired by the clean two-column and sidebar style of resumebuilder.com. No code or assets are copied. All of them use real selectable text, standard section headings and no layout tables.
