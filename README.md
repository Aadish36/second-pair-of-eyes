# Second Pair of Eyes

Second Pair of Eyes is a code review mentor that analyzes Python pull request changes, adds educational AI context, verifies historical commit evidence, and can post evidence-based inline comments to GitHub. The React dashboard reads completed GitHub reviews and calculated issue trends from PostgreSQL through FastAPI.

## Problem and objectives

Code review feedback often identifies a defect without teaching why it is risky or how to improve it. This project combines static analysis, optional AI explanations, and verifiable historical examples, while keeping generated AI prose out of GitHub comments.

## Features and current status

- GitHub App webhooks for pull request `opened` and `synchronize` events, verified using `X-Hub-Signature-256`.
- GitHub App authentication, changed-file/diff/source retrieval, retry-safe webhook processing, and inline comments restricted to added Python lines.
- Pylint static analysis. Submitted source is analyzed as text and is never imported or executed.
- LangGraph Retriever, Explainer, and Verifier stages; mock mode works without an LLM key, and live mode uses a configured OpenAI model.
- Optional local-Git-history retrieval with ChromaDB. Historical commits are included only when commit and patch evidence validate.
- PostgreSQL storage for webhook delivery state and per-repository/PR/head review JSON, including findings and AI metadata.
- Database-backed dashboard endpoint for persisted review revisions, issue counts, severity totals, category counts, and eight-week trends. Category labels are simple rules over finding type/message, not a learned taxonomy.
- React dashboard uses the API and PostgreSQL instead of fixture data. Unknown author and resolution data are shown as unavailable.
- Optional shared dashboard token with an HttpOnly, SameSite=Strict cookie session. The GitHub webhook uses its separate HMAC signature.
- Docker Compose for PostgreSQL, backend, and frontend.

## Architecture and workflow

```text
GitHub PR webhook
  -> HMAC signature + payload validation
  -> PostgreSQL delivery/revision claim
  -> GitHub App installation token
  -> PR files, diff, and source
  -> Pylint findings on changed lines
  -> LangGraph retrieval / explanation / evidence verification
  -> PostgreSQL JSON review record
  -> deterministic static-evidence inline comment

React dashboard -> FastAPI /api/dashboard/summary -> PostgreSQL completed reviews
```

AI descriptions and historical references are stored for the dashboard/API. GitHub review comments contain static analyzer evidence and deterministic next-step guidance only. Webhook review processing is synchronous.

## Technology stack

- Backend: Python 3.10+, FastAPI, Pydantic, Pylint, LangGraph, ChromaDB, SQLAlchemy, PostgreSQL/psycopg, PyJWT
- Frontend: React, Vite, Tailwind CSS, Recharts
- Tests: pytest, FastAPI TestClient/HTTPX, Vitest
- Local deployment: Docker Compose and PostgreSQL

## Project structure

```text
backend/
  main.py, config.py
  routers/       # health, auth, dashboard, reviews, pull requests, webhooks
  schemas/       # validated API models
  services/      # static analysis, agents, GitHub, database, review orchestration
  tests/         # backend and mocked integration tests
  Dockerfile
frontend/
  src/           # React dashboard, API adapter, components, frontend tests
  Dockerfile
  nginx.conf     # same-origin API proxy in Compose
history/         # optional read-only Git repository mount point
docker-compose.yml
.env.example
README.md
CHANGELOG.md
```

## Requirements and installation

### Recommended: Docker Compose

Install Docker Desktop with Compose, then from the project root:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open the dashboard at `http://localhost:8080`, API docs at `http://localhost:8000/docs`, and PostgreSQL is available inside the Compose network. The frontend proxies `/api` to the backend, so browser calls and the session cookie are same-origin.

Stop with `Ctrl+C`, or run `docker compose down`. `docker compose down -v` also deletes the local PostgreSQL and ChromaDB volumes.

The Compose file uses the development-only default PostgreSQL password `local-demo-password` when `POSTGRES_PASSWORD` is absent. Set a different value in `.env` for local use. Never expose this Compose setup directly to the public internet.

### Run without Docker

Prerequisites: Python 3.10+, Node.js 20.19+ (or 22.12+) with npm, and a PostgreSQL server/database.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
Copy-Item .env.example .env
```

Set `DATABASE_URL` in `.env` for the local PostgreSQL instance. Run the API from the project root:

```powershell
python -m uvicorn main:app --reload --app-dir backend --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies API requests to `127.0.0.1:8000`. The dashboard endpoint creates the SQLAlchemy tables when first called. Schema changes are not yet managed with Alembic migrations.

## Environment variables

Copy `.env.example` to `.env`; it contains placeholders only. Docker Compose reads the file for interpolation and passes required settings into the backend.

| Variable | Default/example | Purpose |
|---|---|---|
| `DATABASE_URL` | Compose supplies internal Postgres URL; native example uses localhost | PostgreSQL SQLAlchemy URL. Required for persisted dashboard and GitHub webhook reviews. |
| `POSTGRES_PASSWORD` | `local-demo-password` in Compose | Local Compose database password; change it outside a throwaway demo. |
| `FRONTEND_ORIGIN` | localhost Vite and Compose origins | Comma-separated CORS origins for direct cross-origin API use. |
| `DASHBOARD_API_TOKEN` | unset | Optional shared dashboard/review API login token. Leave unset for unauthenticated local demo. Use a long random value when enabled. |
| `DASHBOARD_COOKIE_SECURE` | `false` | Set `true` behind HTTPS; keep `false` for local HTTP. |
| `MAX_SOURCE_CHARS` | `100000` | Maximum submitted source size. |
| `AI_REVIEW_MODE` | `mock` | `mock`, `live`, or `off`. Mock mode does not call an LLM. |
| `OPENAI_API_KEY` | unset | Required for `live` model explanations; never put a real key in source control. |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model used in live mode. |
| `HISTORY_REPO_PATH` | unset native; `/history` Compose | Local Git checkout indexed for historical retrieval. In Compose, mount it read-only using `HISTORY_HOST_PATH`. |
| `HISTORY_HOST_PATH` | `./history` | Host Git checkout mounted read-only at `/history` in Compose. |
| `HISTORY_MAX_COMMITS` | `500` | Maximum recent commits read for retrieval. |
| `CHROMA_PATH` | `.data/chroma` | Persistent ChromaDB location; Compose uses a named volume. |
| `GITHUB_WEBHOOK_SECRET` | unset | Shared secret for verifying GitHub webhook HMAC signatures. |
| `GITHUB_APP_ID` | unset | GitHub App ID used to create short-lived App JWTs. |
| `GITHUB_APP_PRIVATE_KEY` | unset | PEM contents, with newlines encoded as `\\n`; keep it private. |
| `GITHUB_APP_PRIVATE_KEY_PATH` | unset | Alternative private-key file path for native runs. Configure exactly one key source. |
| `GITHUB_API_URL` | `https://api.github.com` | GitHub API base URL; change for GitHub Enterprise. |
| `GITHUB_API_VERSION` | `2026-03-10` | API version request header. |
| `GITHUB_REQUEST_TIMEOUT_SECONDS` | `20` | GitHub API request timeout. |
| `GITHUB_MAX_RETRIES` | `3` | Bounded retry count for transient and rate-limit failures. |
| `FRONTEND_PORT` | `8080` | Host port for the Compose frontend. |

## API endpoints

Interactive schema: `/docs` when the backend is reachable.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Public liveness response. |
| `GET` | `/api/auth/status` | Reports whether dashboard token auth is enabled. |
| `POST` | `/api/auth/login` | Accepts `{"token":"..."}` and sets an HttpOnly session cookie when configured. |
| `POST` | `/api/auth/logout` | Clears the dashboard session cookie. |
| `GET` | `/api/dashboard/summary` | Completed PostgreSQL review rows, metrics, categories, and weekly trend data. |
| `POST` | `/api/reviews` | Analyze JSON `{ "code": "...", "filename": "sample.py" }`; static/manual result is process-local. |
| `GET` | `/api/reviews/{review_id}` | Retrieve a manual review in the current backend process. |
| `GET` | `/api/pull-requests` | Lists persisted GitHub PR reviews plus in-memory manual submissions. |
| `POST` | `/api/webhooks/github` | GitHub App webhook receiver; requires GitHub signature/event/delivery headers. |

Example manual review:

```bash
curl -X POST http://127.0.0.1:8000/api/reviews \
  -H "Content-Type: application/json" \
  -d '{"code":"pass","filename":"sample.py","pull_request_number":7}'
```

The dashboard API is read-only. With `DASHBOARD_API_TOKEN` set, dashboard and manual review endpoints require a valid session cookie or bearer token. Invalid inputs return FastAPI `422`; oversized source returns `413`; unknown review IDs return `404`; database/service failures return `503`.

## PostgreSQL and data behavior

`webhook_deliveries` stores delivery status, attempts, and retry information. `pull_request_reviews` stores repository, PR number, head SHA, status, static/AI findings JSON, and posted GitHub review ID. Its unique key prevents duplicate analysis of the same PR head. The dashboard reads completed rows, calculates totals and category counts, and buckets findings by stored review time into eight weeks.

There is no separate developer identity/progress model: GitHub author is not currently persisted, and resolution state is not tracked. Consequently, the dashboard does not claim developer-level progress or resolved-issue totals. The current “PR revisions reviewed” count counts completed pull request heads; a new push to the same PR creates another revision row. Manual `/api/reviews` submissions remain in memory; only webhook-originated PR review records persist.

## GitHub App and webhook demo

1. Create a GitHub App on a test repository. Subscribe to **Pull request** events and grant **Contents: Read-only** and **Pull requests: Read and write**.
2. Set `GITHUB_APP_ID`, exactly one private key source, and `GITHUB_WEBHOOK_SECRET`. Set `DATABASE_URL` and start the backend/Compose services.
3. Expose the backend with a HTTPS development tunnel. Configure the GitHub App webhook URL as `https://YOUR-TUNNEL/api/webhooks/github` and use the same webhook secret.
4. Install the App on the test repository, create a Python PR with a static issue on a new line (such as an undefined name), and open or synchronize it.
5. Confirm the delivery returns `200`, check the GitHub review/comment, then refresh the dashboard at `http://localhost:8080`.
6. Re-deliver a delivery or send a repeated PR head to demonstrate idempotency. Push a new commit to demonstrate revision processing.

The webhook is synchronous and may take longer than ideal for large PRs. A queue is not implemented. GitHub returns a maximum of 300 changed files per request, and only Python findings on added lines are comment candidates. AI text and historical citations are not included in posted comments.

## AI agents and historical retrieval

- **Retriever:** optionally searches patches from a configured local Git repository using ChromaDB. Empty history is reported explicitly.
- **Explainer:** mock mode returns deterministic template explanations; live mode calls the configured OpenAI model.
- **Verifier:** checks that a cited commit exists and that supporting patch text appears before including the example.
- **Orchestrator:** LangGraph passes structured findings through retrieval, explanation, and verification.

Set `AI_REVIEW_MODE=live` and `OPENAI_API_KEY` to use the model. To enable history, set `HISTORY_REPO_PATH` to an actual local Git checkout (or mount one with `HISTORY_HOST_PATH` in Compose). ChromaDB may need to download its embedding model on first use. These integrations require internet access as applicable.

## Tests and validation

From project root:

```powershell
python -m pytest backend/tests -q
cd frontend
npm install
npm test
npm run build
```

Backend tests use mocks and SQLite for database behavior; they do not require GitHub, PostgreSQL, or a live model key. A mocked end-to-end workflow test sends a signed PR event through the webhook handler, mock-mode agent graph, review-comment construction, SQLite persistence, and dashboard read. Frontend tests cover API response mapping and error handling. For a live workflow demo, use the GitHub App steps above.

## Deployment and security

Compose is for local development and presentations. For hosting, use HTTPS, a secret manager, a strong database credential, set `DASHBOARD_COOKIE_SECURE=true`, restrict CORS origins, protect the service with an identity provider/role-based access control, and use a managed PostgreSQL database. The shared dashboard token is a simple single-viewer gate, not production user authentication. No login rate limit, account system, or granular roles are implemented. Keep webhook processing network-accessible only over HTTPS.

## Known limitations and next steps

- Only Python is analyzed, using Pylint; ESLint and Bandit are not integrated.
- Manual submissions are process-local and are not included in persistent dashboard trends.
- Developer identity and issue resolution events are not stored, so developer progress and resolved counts are unavailable.
- Category assignment uses basic keyword rules; category labels are approximate.
- GitHub webhook processing is synchronous; no durable queue is implemented.
- Database schema migrations/Alembic are not configured.
- Shared-token auth is suitable only for a local/private demo; production needs real identity and authorization.
- Chroma history retrieval requires a local repository and may download an embedding model.
- Live OpenAI and real GitHub webhook execution were not performed by the unit tests.
