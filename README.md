# Learnify

An AI-powered teaching web app built with Flask and the Anthropic Claude API. Give it a topic and a difficulty level; it streams a structured, "aha-moment" explanation, then generates an adaptive quiz with per-option feedback and personalized study insights.

> **Scope note (honest framing):** Learnify is a straightforward LLM *application* - each feature is a single, well-prompted Claude call (teach → quiz → insights). It is **not** an autonomous agent: there is no tool use, planning, or multi-step control loop. The code is named to reflect that (see `teaching_service.py`).

## Features

- **Streaming explanations** - real-time token streaming over Server-Sent Events
- **Adaptive quizzes** - Claude generates 4-option questions, each with feedback and the concept it tests
- **Performance insights** - score breakdown, concept-level strengths/weaknesses, study recommendations
- **Session history** - SQLite-backed history and aggregate stats
- **Input hardening** - rate limiting, input sanitization/validation, and security headers on every response

## Architecture

```
Flask routes (app.py)
  ├── teaching_service.py   # one streaming Claude call: (topic, difficulty) -> explanation
  ├── quiz_manager.py       # quiz generation, scoring, and performance analysis
  ├── prompt_templates.py   # all prompt construction (teaching / quiz / insights)
  ├── claude_client.py      # thin Anthropic SDK wrapper + token accounting
  ├── session_manager.py    # SQLAlchemy persistence (sessions, scores, history)
  └── security.py           # rate limiting, sanitization, validation, headers
```

Prompt construction lives in `prompt_templates.py` and does no I/O, which is what keeps the quiz/scoring/prompt/validation logic unit-testable without hitting the API (see `tests/`).

## Quick Start

```bash
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                # then add your ANTHROPIC_API_KEY

python app.py                       # http://localhost:5001
```

## Testing & CI

The API-free logic (prompt construction, quiz scoring, validation, rate limiting) is covered by unit tests that run with **no API key required**:

```bash
pip install -r requirements.txt -r requirements-dev.txt
ruff check .
pytest -q
```

GitHub Actions runs ruff + pytest on every push and pull request - see [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | - | **Required.** Your Claude API key. |
| `DEFAULT_MODEL` | `claude-sonnet-5` | Model used for all calls. |
| `MAX_TOKENS_TEACHING` | `4096` | Max output tokens for explanations. |
| `MAX_TOKENS_QUIZ` | `2048` | Max output tokens for quiz generation. |
| `DATABASE_URL` | `sqlite:///learnify.db` | SQLAlchemy connection string. |
| `SECRET_KEY` | `dev-secret-key` | Flask secret - set a real value in production. |

## Deployment (Docker)

```bash
docker build -t learnify .
docker run -p 5000:5000 -e ANTHROPIC_API_KEY=your_key learnify
```

The container serves with Gunicorn on port 5000.

> **State & scaling:** active quiz/teaching session state is held in-process, so the
> container runs a **single** Gunicorn worker (with multiple threads). Running more
> than one worker would make the quiz submit/complete flow 404 non-deterministically,
> because that state is not shared across processes. The rate limiter and token
> counters are likewise in-process (per-worker, reset on restart). To scale to
> multiple workers/replicas, move session state and rate limiting into a shared
> store (Redis, or the existing SQLAlchemy database) first.

## Tech Stack

- **Backend:** Flask, SQLAlchemy, Gunicorn
- **AI:** Anthropic Claude API (streaming Messages API)
- **Frontend:** server-rendered templates + vanilla JS
- **Database:** SQLite (any SQLAlchemy URL)

## License

MIT - see [LICENSE](LICENSE). © 2026 Anup Meshram.
