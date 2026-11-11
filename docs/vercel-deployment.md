# Vercel backend migration and Hostinger domain

Use two Vercel projects in the same team: the existing Vite frontend and a new FastAPI backend. The examples below use `example.com`; replace it with your domain. Keep the Render service available until the replacement has passed end-to-end checks.

## 1. Push the deployment changes

The backend includes `vercel.json` for the FastAPI preset, a 300-second function limit, runtime bundle exclusions, and `.python-version` for Python 3.12. `.vercelignore` keeps local environment files and development files out of CLI uploads. Runtime dependencies remain in `requirements.txt`; `pyproject.toml` retains the existing Ruff settings.

The application now supports `JOB_RECONCILIATION_ENABLED=false`, which skips its continuous polling loop while retaining MongoDB initialization, curriculum seeding, and API routes. This flag defaults to true for existing local and Render deployments. Disabling it does not replace polling with a scheduled job.

## 2. Create the backend Vercel project

Import `scenezone/quantum-workshop-lab` again. Select **Import single project** for **backend / FastAPI**. Use:

| Setting | Value |
| --- | --- |
| Team | The same team as the frontend |
| Project name | `quantum-workshop-api` or an available alternative |
| Branch | `main` |
| Root directory | `backend` |
| Framework preset | FastAPI |
| Build / install / output overrides | Leave disabled; use framework defaults |

Do not enter a Uvicorn start command or `$PORT`. Vercel loads `app/main.py:app` itself. Enable Fluid compute if the project does not already use it. Choose a function region near MongoDB and the users when available; use the same region for Redis.

Add backend production environment variables in the dashboard:

```dotenv
APP_ENV=production
LOG_LEVEL=INFO
MONGODB_URI=YOUR_ATLAS_CONNECTION_STRING
MONGODB_DATABASE=quantum_workshop
CORS_ORIGINS=https://quantum-workshop-lab.vercel.app
IBM_HARDWARE_ENABLED=false
JOB_RECONCILIATION_ENABLED=false
RATE_LIMIT_STORAGE_URI=YOUR_REDIS_CONNECTION_URL
```

Use an actual Redis connection URL such as `rediss://...` supplied by your Redis provider, not an HTTPS REST endpoint. This application uses SlowAPI's Redis storage. Vercel can create multiple function instances, so `memory://` cannot enforce a shared quota; it is suitable only for initial smoke testing. Do not publish a busy workshop or live AI endpoint with independent per-instance limits.

For live AI, also configure `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL`. Copy any other intentional backend settings from Render, including `ADMIN_TOKEN` if facilitator administration is in use. Do not copy the entire local environment blindly, and use replacement credentials for any previously exposed secrets. Keep backend secrets out of frontend `VITE_` variables.

Atlas must permit connections from Vercel; allowing only Render outbound addresses will not work. Deployment environment variables are separate from your local `.env`.

Deploy and copy the actual production domain from the project's Domains page. The name below is an example, not a reserved hostname:

```text
https://YOUR-BACKEND.vercel.app/api/health
https://YOUR-BACKEND.vercel.app/docs
https://YOUR-BACKEND.vercel.app/api/lessons
```

Confirm health reports `status: ok` and `database: connected`, lessons return JSON, and the browser can access the production API without a Vercel sign-in challenge. A missing `/` route can return 404 even when `/api/health` works.

Vercel must build and load the complete Linux Qiskit dependency bundle before compatibility is confirmed. If deployment reports an oversized function, review its dependency sizes and Vercel Large Functions eligibility; paying for Pro alone does not remove the normal bundle-size limit. Check function logs for missing native libraries or import failures. Do not switch frontend traffic until the backend works.

Keep real IBM hardware disabled in this first migration. Its durable periodic reconciliation must move to authenticated scheduled requests, a queue, or a worker before it is re-enabled. Do not simply turn the infinite startup loop back on in Vercel Functions. Lessons, simulations, AI, feedback, and sessions can be validated in the initial migration; database features require MongoDB.

## 3. Connect the existing frontend

In the frontend Vercel project's production environment, set:

```dotenv
VITE_API_BASE_URL=https://YOUR-BACKEND.vercel.app
```

Use the actual backend origin with no `/api` suffix. Redeploy the frontend because Vite embeds this setting at build time. Test lessons, a simulation, AI, and database features you use. Confirm production CORS preflight responses permit the frontend origin. If a feature fails, check its browser Network request and backend logs before changing plans.

Hardware tracking keys are stored in browser local storage by frontend origin. Existing tracking IDs and other locally saved progress will not automatically transfer from the `vercel.app` frontend to the custom domain. Finish or retain recovery details for active jobs before the switch.

## 4. Upgrade the team

After validating the migration, upgrade the team containing both projects through **Team Settings > Billing > Upgrade to Pro**. Review the displayed price and configure spend alerts/actions. The Pro platform fee is currently $20/month with one deploying seat and $20 usage credit; excess compute, extra seats, add-ons, MongoDB, Redis, and AI can add costs. Confirm prices in the dashboard before purchase.

Pro applies to both projects in that team; it is not a separate subscription for each project. Recheck deployment protection and function settings after the upgrade. Pro does not guarantee zero startup or database latency.

## 5. Add the Hostinger domain

Add `example.com` and `www.example.com` in the **frontend** project's **Settings > Domains > Add Existing**. Choose a primary domain and redirect the other to it. Add `api.example.com` in the **backend** project's domain settings.

Keep the domain registered at Hostinger. If Hostinger currently manages its DNS, open **Domains > Domain portfolio > Manage > DNS / Nameservers**. If nameservers point elsewhere, edit DNS at that provider instead.

Copy the exact records displayed by Vercel for each project:

| Type | Name at Hostinger | Value |
| --- | --- | --- |
| A | `@` | Exact apex IP displayed by the frontend Vercel project |
| CNAME | `www` | Exact CNAME target displayed for `www.example.com` |
| CNAME | `api` | Exact CNAME target displayed by the backend Vercel project |
| TXT, if requested | Name displayed by Vercel | Exact ownership-verification value |

CNAME values are hostnames without `https://` or paths. Replace only conflicting records for the selected web hostnames; preserve MX, SPF, DKIM, DMARC, and other unrelated records. A nameserver transfer is not necessary for this setup. Wait until Vercel reports valid DNS configuration and HTTPS works for both frontend and API.

Then update the backend production environment:

```dotenv
CORS_ORIGINS=https://example.com,https://www.example.com,https://quantum-workshop-lab.vercel.app
```

Redeploy the backend. Update and redeploy the frontend with:

```dotenv
VITE_API_BASE_URL=https://api.example.com
```

Verify `https://api.example.com/api/health`, `https://example.com/learn`, refreshing frontend routes, simulation, AI, and the features you use. Remove Render only after these checks pass. The custom domain can be added before upgrading if desired; it does not require Pro.

## Official references

- [FastAPI deployment](https://vercel.com/docs/frameworks/backend/fastapi)
- [Python runtime and versions](https://vercel.com/docs/functions/runtimes/python)
- [Pro billing](https://vercel.com/docs/plans/pro-plan)
- [Vercel custom domains](https://vercel.com/docs/domains/working-with-domains/add-a-domain)
- [Hostinger CNAME records](https://www.hostinger.com/support/4738777-how-to-manage-cname-records-at-hostinger/)
