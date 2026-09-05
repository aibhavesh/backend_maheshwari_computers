# Redeploy the existing Vercel backend

Repository: https://github.com/aibhavesh/backend_maheshwari_computers

## Existing project settings

In the existing Vercel project's Settings, connect this repository and use:

| Setting | Value |
| --- | --- |
| Production branch | `main` |
| Root directory | Repository root (leave blank; do not enter `backend`) |
| Framework preset | FastAPI |
| Entrypoint | `index:app`, configured in `pyproject.toml` |
| Build command | No custom command required |
| Output directory | No custom output directory |

Remove old dashboard build/install overrides that reference the former parent repository. Runtime dependencies are declared in `pyproject.toml`; `requirements.txt` installs that project. The entrypoint exports a FastAPI application and disables the continuous downloader and embedding warmup by default.

## Environment variables

Set these in the existing project's **Production** environment. Set Preview values separately if you use preview deployments. Preserve existing valid secrets and service connections.

```dotenv
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DATABASE
JWT_SECRET=REPLACE_WITH_A_RANDOM_SECRET_AT_LEAST_32_CHARACTERS
CORS_ALLOW_ORIGINS=https://YOUR-EXISTING-SITE.netlify.app
ALLOWED_EMAIL_DOMAINS=maheshwaricomputers.com
ENABLE_DOCUMENT_WORKER=false
WARM_EMBEDDINGS_ON_STARTUP=false
QDRANT_URL=https://YOUR-QDRANT-SERVER
EMBEDDING_BACKEND=hash
```

Use your actual hosted PostgreSQL connection, the Netlify site's exact HTTPS origin (without a trailing slash), and an existing strong signing secret. Do not use the local SQLite file in production. The placeholders above are documentation, not working credentials. `hash` avoids model downloads but provides only offline-style matching quality; use FastEmbed only after verifying its model cache and dependency size work in the deployment.

If already configured, retain `GOOGLE_CLIENT_ID`, `GEMINI_API_KEY`, and the relevant model settings. Google is optional for password login. The frontend's Google client ID must match. Use `ALLOWED_EMAIL_EXCEPTIONS` for individually admitted addresses when needed.

## Database migrations

Before switching production traffic to code that uses the restored password fields, back up the hosted database and apply migrations against that database. In a trusted terminal with the backend dependencies installed, set `DATABASE_URL` to the hosted connection privately, then run from the repository root:

```powershell
.venv/Scripts/python.exe -m alembic upgrade head
```

The command reads `DATABASE_URL` from the process environment before `.env`. Without that override, this checkout uses its local database. Do not paste database passwords into issues, commits, or deployment logs. Do not run database migrations automatically for every preview deployment.

For a fresh database, set `BOOTSTRAP_SUPER_ADMIN_EMAIL` to an admitted address before the initial migration, then register that account. Existing databases need an authorized role assignment; changing the bootstrap variable does not replay an applied migration.

`scripts/create_default_user.py` creates a local test account with a published test password. It is not a production deployment step, and the local account/database is not uploaded to Vercel.

## Document and vector limitations

This repository currently implements document storage using local files. Vercel function storage does not provide durable shared uploads across invocations. A `/tmp` directory is temporary scratch space, not a persistent document store. Full upload/extraction workflows require a durable storage adapter before production use.

The continuous document-download worker is disabled in the Vercel entrypoint. URL downloads need an external worker/queue integration. Remote Qdrant is required for persistent matching; the current client supports a URL but does not yet accept a Qdrant API key setting, so a cluster requiring key authentication needs that integration before use. Embedded local Qdrant is for local development.

These limitations do not prevent deploying the API, but a successful `/health` response does not prove database, document, or vector workflows are configured.

## Deploy and verify

Push to `main` to trigger the connected existing project. If automatic deployments are disabled, select the latest commit in the project's Deployments tab and redeploy it. Confirm that the deployment shows the expected Git commit.

Check:

- `https://YOUR-BACKEND.vercel.app/health`: `{"status":"ok","version":"0.1.0"}`.
- `https://YOUR-BACKEND.vercel.app/docs`: API documentation.
- Password login with an existing production account: verifies database connectivity and migrations.
- Login from the actual Netlify site: verifies the frontend API URL and CORS.

The legacy `/api/health`, `/api/docs`, and `/api/auth/...` routes also work. Prefer the backend origin without `/api` for new frontend configuration.

If a build exceeds Vercel's Python function size limit, inspect the build's dependency report, particularly FastEmbed/ONNX. Do not remove packages needed by active features without configuring an alternative.

References: [Vercel FastAPI deployment](https://vercel.com/docs/frameworks/backend/fastapi), [Python runtime](https://vercel.com/docs/functions/runtimes/python).
