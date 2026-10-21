# Changelog

## [2026-10-21] — Connect dashboard and add local full-stack deployment

### Added
- `backend/routers/dashboard.py`: PostgreSQL-backed review revision summary, issue/severity counts, rule-based categories, and weekly finding trends.
- `backend/routers/auth.py` and `backend/services/auth.py`: optional shared-token login and read API gate using an HttpOnly, SameSite=Strict cookie or bearer token.
- `backend/tests/test_dashboard.py` and `backend/tests/test_workflow.py`: SQLite persistence/auth checks and mocked webhook-to-agent-to-comment-to-dashboard flow.
- `frontend/src/api.js` and `frontend/src/api.test.js`: dashboard API integration, response mapping, error reporting, and Vitest coverage.
- `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`, and `docker-compose.yml`: containerized backend, frontend/API proxy, and PostgreSQL services.
- `history/.gitkeep`: default read-only Compose history mount point.
- Deleted `frontend/src/data/mockReviews.js`, the now-unused illustrative dashboard dataset.

### Changed
- `backend/config.py`, `backend/main.py`: configure dashboard token/cookie settings, allow Authorization CORS headers, and register dashboard/auth routes.
- `backend/services/database.py`: expose completed persisted PR review revisions for dashboard reads.
- `backend/routers/pull_requests.py` and `backend/routers/reviews.py`: include persisted GitHub review records in PR listing and apply optional dashboard access control.
- `frontend/src/App.jsx`, `DashboardView.jsx`, `MistakeTrendsChart.jsx`, `SectionPages.jsx`, `ReviewTable.jsx`, `ReviewDetails.jsx`, and `StatCard.jsx`: replace mock data with API results and display empty/error/unavailable values honestly.
- `frontend/package.json`: add Vitest test command and dependency.
- `.env.example`, `README.md`, and `CHANGELOG.md`: document full-stack setup, configuration, API, GitHub demo, architecture, auth limits, tests, and unfinished features.
- `CHANGELOG.md`: record this implementation and actual validation outcomes below.

### Fixed
- Dashboard reviews and learning metrics no longer use fabricated fixture rows or trend values.
- Historical-context UI now displays verified stored examples when available, with the recorded no-history message otherwise.
- Browser UI does not embed the shared dashboard token in a Vite build; login uses an HttpOnly cookie.
- Removed the unused mock dashboard dataset so fixtures cannot be mistaken for live review records.

### Dependencies
- Added frontend development dependency `vitest` and `npm test` script.
- No backend dependencies added or removed.

### Tests
- Not run: Python/`py`, Node.js, and npm are unavailable on PATH, so pytest, Vitest, and the Vite build could not execute.
- Passed: `docker compose config --quiet` parsed the Compose configuration (Docker emitted a local config-file access warning but returned exit code 0).
- Passed: PowerShell parsed `frontend/package.json`; static relative-import scan found all frontend imports resolve; no stale mock-data references remain in the frontend or README.
- Not run: Docker image builds or container workflow because Docker Engine is not running (`//./pipe/docker_engine` is unavailable).

### Remaining Issues
- The dashboard reflects completed webhook review heads; each new PR head is a separate row.
- No author identity or issue resolution state is stored, so developer progress and resolved counts remain unavailable.
- Shared-token auth is for a local/private demo and is not a replacement for production identity/roles. Configure HTTPS and `DASHBOARD_COOKIE_SECURE=true` when hosted.
- Real GitHub webhook, live OpenAI calls, and production PostgreSQL behavior require external credentials/services and are not covered by automated tests.
- Backend and frontend automated test results remain unknown until run on a machine with Python/Node dependencies installed.
- Deleted `frontend/src/data/mockReviews.js` because the dashboard has been switched to API-backed records.

## [2026-10-20] — Integrate GitHub Pull Request reviews

### Added
- `backend/services/github_app.py`: GitHub App JWT and repository-scoped installation-token authentication, PR/files/diff/content retrieval, review posting, and bounded retries for transient/rate-limit errors.
- `backend/services/github_review.py`: changed-line mapping, Python static analysis plus AI enrichment, persisted review metadata, and inline comment generation restricted to static analyzer evidence.
- `backend/services/database.py`: PostgreSQL webhook-delivery and PR-revision records with lease-based processing claims and duplicate prevention.
- `backend/routers/github_webhooks.py`: raw-body HMAC SHA-256 validation and `pull_request.opened`/`synchronize` handling.
- `backend/tests/test_github_webhook.py`, `test_github_app.py`, `test_github_review.py`, and `test_database.py`: separate mocked checks for signature/routing, GitHub retrieval and posting, review generation, retries, and persistence claims.
- Local GitHub App setup, permissions, PostgreSQL configuration, and tunnel-based test instructions.

### Changed
- `backend/config.py`: added GitHub App, webhook, database, API timeout, and retry settings.
- `backend/main.py`: registered the GitHub webhook router.
- `backend/schemas/reviews.py`: added optional source path metadata to review findings.
- `backend/requirements.txt`: added SQLAlchemy, psycopg, and PyJWT.
- `.env.example`: added placeholders for GitHub App, webhook, PostgreSQL, and retry configuration.
- `README.md`: updated implementation status, architecture, endpoint/environment docs, least-privilege permissions, local testing guide, and limitations.

### Fixed
- Repeated webhook deliveries and repeated PR head SHAs are claimed idempotently; failed/stale attempts can be retried.
- GitHub comments are attached only to added lines and contain deterministic Pylint output; generated explanations and historical citations are not published.

### Dependencies
- Added `SQLAlchemy>=2.0,<3.0`, `psycopg[binary]>=3.2,<4.0`, and `PyJWT[crypto]>=2.9,<3.0`.

### Tests
- Added unit tests for webhook signature/routing, diff retrieval, review generation/comment filtering, transient retries, duplicate comment suppression, and SQLite-backed idempotency.
- Not run: Python and the `py` launcher are unavailable on PATH in this environment. No GitHub App, PostgreSQL server, tunnel, or real repository was contacted.

### Remaining Issues
- Webhook handling is synchronous and could exceed GitHub's preferred response window for large or slow reviews; a durable background queue is a future improvement.
- Manual review endpoints and the dashboard's pull request listing are still process-local; only webhook-originated PR reviews are persisted in PostgreSQL.
- SQLAlchemy creates the initial tables automatically; schema migrations are not yet managed by Alembic.
- No files were deleted.

## [2026-10-20] — Add LangGraph AI review pipeline

### Added
- `backend/services/ai_review.py`: LangGraph Retriever, Explainer, and Verifier with ChromaDB-backed local Git history search, mock/live/off modes, and graceful enrichment fallback.
- `backend/tests/test_ai_review.py`: mock, disabled, and missing live API key behavior tests.
- Structured educational fields and verified historical example metadata in review responses.

### Changed
- `backend/config.py`: added AI mode, OpenAI model/key, Git history, Chroma storage, and commit-limit settings.
- `backend/schemas/reviews.py` and `backend/services/review_service.py`: added enrichment fields and invoked the graph after Pylint analysis.
- `backend/requirements.txt`: added LangGraph, LangChain OpenAI, and ChromaDB.
- `backend/tests/test_api.py`: asserts mock explanations and explicit empty-history behavior.
- `.gitignore`, `README.md`: ignore local vector data and document agent setup, workflow, API fields, and limitations.

### Fixed
- Unverified or unavailable agent evidence no longer blocks the original static review findings; unsupported historical citations are omitted.

### Dependencies
- Added `langgraph`, `langchain-openai`, and `chromadb`.

### Tests
- Added unit tests for mock-mode enrichment, no-history responses, off mode, and missing-key live-mode fallback. Not run: `python` and `py` are unavailable on PATH in this environment.

### Remaining Issues
- Live mode requires a valid OpenAI key and external model access. ChromaDB's default embedding model may need to be downloaded on first use.
- History retrieval requires a local Git repository path; GitHub ingestion and remote commit fetching are not implemented.
- No files were deleted.

## [2026-10-20] — Implement modular review APIs and Pylint analysis

### Added
- `backend/config.py`: environment-backed frontend origin and maximum source-size settings.
- `backend/routers/`: health, review submission/retrieval, and in-memory pull request listing endpoints.
- `backend/schemas/`: validated review request, structured issue/result, health, and pull request response models.
- `backend/services/`: Pylint static analysis, review orchestration, and process-local result store.
- `backend/tests/`: endpoint tests for health, submissions, retrieval, pull request listing, validation, 404 behavior, and OpenAPI.

### Changed
- `backend/main.py`: registers modular routers and configures FastAPI metadata, Swagger, and CORS.
- `backend/requirements.txt`: added pytest and HTTPX test dependencies; Pylint was already present.
- `.env.example`: documents the source-size limit and both local Vite origin forms.
- `README.md`: documented backend architecture, endpoints, examples, validation behavior, setup, tests, and implementation limits.

### Fixed
- Replaced the previous backend-only liveness scaffold with the requested review API surface.

### Dependencies
- Added `pytest>=8.0,<9.0` and `httpx>=0.27,<1.0`.
- No dependencies removed or upgraded.

### Tests
- Added tests using sample Python source that contains an undefined name. Submitted source is analyzed statically and is not run.
- Not run in this environment: `python`, `py`, and `pylint` are unavailable on PATH, so the FastAPI test suite could not be executed.

### Remaining Issues
- Review results are held in process memory and are lost on restart; multiple server workers do not share data.
- Pull request listings are based only on submitted metadata and are not connected to GitHub.
- No files were deleted.

## [2026-10-20] — Build the mock code review dashboard

### Added
- `frontend/src/components/`: reusable sidebar, metric cards, review table, trends chart, detail view, section pages, dashboard view, icon set, and loading skeleton.
- `frontend/src/data/mockReviews.js`: realistic sample pull requests, findings, summary metrics, and trend series.
- Responsive dashboard navigation for Dashboard, Pull Requests, Code Reviews, Mistake History, and Settings, with review details, mock search, loading, and no-results states.

### Changed
- `frontend/src/App.jsx`: replaced the scaffold landing page with local page navigation and dashboard composition. The UI uses mock data and does not request backend endpoints.
- `frontend/package.json`: added Recharts and matching React peer helper for the trends chart.
- `README.md`: updated implementation status, project structure, features, data flow, dependency list, and frontend test instructions.

### Fixed
- None.

### Dependencies
- Added `recharts` and `react-is` to the frontend dependencies. No lockfile was generated because npm is unavailable in this environment.

### Tests
- Not run: Node.js and npm are not installed or available on PATH, so the Vite development server and production build could not be executed.
- Static checks passed: `package.json` parses, the Vite build script is present, all relative JavaScript/JSX imports resolve to existing files, and the documented component/data files exist.
- Do not treat this dashboard as runtime-verified until `npm run build` and a browser smoke check succeed.

### Remaining Issues
- Dashboard values and settings are local mock data only. No backend, GitHub, database, or AI integration is connected.
- Run `npm install`, `npm run dev`, and `npm run build` in `frontend/` after installing Node.js and npm.
- No files were deleted.

## [2026-10-20] — Add initial application scaffold

### Added
- `backend/main.py`: minimal FastAPI app with root and health routes plus configurable local CORS.
- `backend/requirements.txt`: FastAPI, Uvicorn, python-dotenv, and Pylint dependencies.
- `frontend/package.json`, `frontend/index.html`, `frontend/vite.config.js`, `frontend/src/main.jsx`, `frontend/src/App.jsx`, and `frontend/src/index.css`: React/Vite homepage styled with Tailwind CSS and a health check through the Vite proxy.
- `.env.example`: documents the frontend origin setting without credentials.
- `.gitignore`: excludes local environment files, Python/Node build artifacts, and editor metadata.

### Changed
- `README.md`: replaced the empty-workspace baseline with actual scaffold structure, setup/run instructions, endpoint examples, and explicit implementation limits.

### Fixed
- None.

### Dependencies
- Added FastAPI, Uvicorn, python-dotenv, Pylint, React, React DOM, Vite, the React Vite plugin, and Tailwind CSS with its Vite plugin. No lockfiles have been generated.

### Tests
- Runtime/backend/frontend tests could not be run: Python, Node.js, and npm are not installed or available on PATH in this environment.
- Inspected the created files and verified the documented project tree. This is not a substitute for running the applications.

### Remaining Issues
- Install Python 3.10+ and Node.js 20.19+ (or 22.12+) with npm, install dependencies, then run the documented smoke checks and frontend build.
- PostgreSQL, LangGraph, ChromaDB, GitHub integration, and AI review features are not implemented.
- No files were deleted.

## [2026-10-20] — Establish project documentation baseline

### Added
- `README.md`: documented the project goal and the verified empty-workspace status, including planned architecture and features clearly labeled as unimplemented.
- `CHANGELOG.md`: started this change log.

### Changed
- None.

### Fixed
- None.

### Dependencies
- None added, removed, or updated.

### Tests
- Not run. This change only adds documentation; there is no application or test suite in the workspace.

### Remaining Issues
- Application implementation, dependency manifests, tests, and Git repository metadata are absent. README setup and run instructions will need updating when those components are added.
- No files were deleted.
