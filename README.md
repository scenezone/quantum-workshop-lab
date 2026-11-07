# Quantum Workshop Lab

An interactive quantum computing learning platform that combines guided lessons, circuit simulations, measurement visualizations, and a context-aware assistant. Learners can explore quantum concepts in the browser without writing Python, then run the same approved circuits on IBM Quantum hardware when access is enabled.

The project includes a React frontend, a FastAPI backend, and MongoDB persistence. Local simulation uses Qiskit Aer. IBM Quantum execution and live AI responses are optional integrations; the assistant can also answer from the built-in workshop guide.

## Contents

- [Features](#features)
- [Technology stack](#technology-stack)
- [Architecture and project structure](#architecture-and-project-structure)
- [Requirements](#requirements)
- [Local setup](#local-setup)
- [Using the workshop](#using-the-workshop)
- [Lessons and experiments](#lessons-and-experiments)
- [Configuration reference](#configuration-reference)
- [Optional integrations](#optional-integrations)
- [API reference](#api-reference)
- [Testing and development](#testing-and-development)
- [Deployment](#deployment)
- [Data and operational behavior](#data-and-operational-behavior)
- [Troubleshooting](#troubleshooting)
- [Extending the project](#extending-the-project)
- [License](#license)

## Features

- **14 lessons:** A learning path from qubits and gates to quantum algorithms, teleportation, error correction, and variational methods. Lessons include objectives, prerequisites, further reading, full-text search, and difficulty filters.
- **Lesson practice:** Multiple-choice questions return correctness and explanations. Written questions show a sample answer and key points; when live AI is configured, the assistant also says which key points an answer covered.
- **11 guided circuits:** Inspect gate diagrams, explanations, ideal distributions, and equivalent Qiskit code. Execution accepts predefined experiment IDs rather than arbitrary user code.
- **Measurement bases:** Measure guided or custom circuits in the X, Y, or Z basis. Ideal probabilities are recomputed for the chosen basis, so phase differences that a Z histogram hides become visible.
- **Local quantum simulation:** Configure the number of shots and run circuits on Qiskit Aer. Inspect counts, observed probabilities, complex amplitudes, and relative phases. Step through gates with per-qubit Bloch vectors; a vector shorter than 1 marks an entangled qubit.
- **Noise lab:** Compare ideal runs with low, medium, and high preset noise, or with calibration snapshots of IBM Manila, Nairobi, and Sherbrooke processors. Device noise needs no IBM account.
- **Result statistics:** Error bars (±2 standard errors), distance from the ideal distribution, the distance expected from sampling alone, fidelity, and a plain-language verdict on whether differences exceed sampling noise.
- **Visual circuit builder:** Click gates onto wires for up to 5 qubits and 40 gates from `H`, `X`, `Y`, `Z`, `S`, `T`, `SX`, `RX`, `RY`, `RZ`, `U`, `CX`, `CZ`, `CP`, `SWAP`, and `CCX`. Angles accept π expressions such as `pi/3`. Edit, reorder, undo, and redo gates; watch Bloch spheres update live; import OpenQASM 2; export Qiskit or OpenQASM.
- **Challenges:** Eight build challenges (Bell states, GHZ, a 75/25 coin, Toffoli AND, and more) are graded on the server against a target state or distribution, alongside three playground challenges.
- **Labs:** A CHSH Bell test reports S with its standard error against the classical bound 2 and the quantum bound 2√2. A variational eigensolver optimizes a one-qubit Hamiltonian or the hydrogen molecule with parameter-shift gradients and charts its convergence.
- **Progress and badges:** Lesson, challenge, and practice progress is stored in the browser, with badges and JSON export and import.
- **Facilitator mode:** Facilitators create a session code; participants join with a nickname and their progress syncs to a live dashboard with lesson completion, challenge completion, and session feedback. Feedback can be exported as CSV.
- **Save, share, and export:** Save custom circuits locally, share experiment and circuit setups by URL, and export results as CSV.
- **Assistant:** Streaming answers in explain, hint, or quiz style, aware of the selected lesson, circuit, or results. The conversation survives a page reload. Missing credentials and supported provider failures fall back to an explicitly labeled workshop-guide response.
- **Optional IBM Quantum execution:** Submit approved circuits, view hardware quotas, and track asynchronous jobs with backoff polling. A job history page shows each job's device, compiled depth, and two-qubit gate count. Submission retries use idempotency keys to avoid duplicate jobs.
- **Simulator-only mode:** Leave `MONGODB_URI` empty to run lessons, simulations, the builder, labs, and the assistant without a database.
- **Offline support:** A service worker caches the app and opened lessons so they work on poor venue Wi-Fi; the app can be installed as a PWA.
- **Responsive, accessible interface:** Keyboard-operable circuit editor, Markdown and math rendering, and an i18n layer for the application shell.

## Technology stack

| Area | Technologies |
| --- | --- |
| Frontend | React 18, TypeScript, Vite 6, React Router 7 |
| Styling and UI | Tailwind CSS 4, Lucide icons |
| API access and state | Axios, TanStack React Query |
| Charts and content | Recharts, React Markdown, remark/rehype plugins, KaTeX |
| Backend | Python, FastAPI, Uvicorn, Pydantic 2, pydantic-settings |
| Quantum execution | Qiskit 1.4.2, Qiskit Aer 0.17.2, Qiskit IBM Runtime 0.40.1 |
| Database | MongoDB through PyMongo |
| External AI | HTTPX requests to a configurable chat-completions API |
| Rate limiting | SlowAPI; in-memory storage locally, optional Redis storage |
| Testing | pytest, pytest-asyncio, pytest-cov, mongomock; Vitest, React Testing Library, jsdom, Playwright |
| Code checks | Ruff, TypeScript compiler, ESLint, pip-audit, npm audit |

Runtime backend versions are pinned in [backend/requirements.txt](backend/requirements.txt); development and test dependencies are in [backend/requirements-dev.txt](backend/requirements-dev.txt). Frontend dependencies and scripts are defined in [frontend/package.json](frontend/package.json), with resolved versions in [frontend/package-lock.json](frontend/package-lock.json).

## Architecture and project structure

```text
Browser / React frontend
          |
          | /api requests through Vite proxy or configured backend URL
          v
      FastAPI backend
          |
          +-- MongoDB (optional): jobs, quotas, feedback, workshop sessions
          +-- Qiskit Aer: local simulation and statevector analysis
          +-- IBM Quantum Runtime: optional hardware submissions
          +-- Chat-completions API: optional live assistant
              Built-in workshop guide: assistant fallback
```

Lessons, experiments, and challenges are served from the canonical Python content. When `MONGODB_URI` is set, the backend connects to MongoDB at startup, creates indexes, and starts a hardware-job reconciliation loop; the database must then be reachable. When `MONGODB_URI` is empty, the backend runs in simulator-only mode: hardware jobs, feedback, and workshop sessions are disabled and everything else works.

Background hardware reconciliation uses a MongoDB lease so that only one API worker performs each reconciliation pass. The lease renews while a pass is active and expires if a worker stops unexpectedly.

```text
Quantum-Workshop-Lab/
|-- README.md
|-- .gitignore
|-- docker-compose.yml       # Local app, API, and MongoDB stack
|-- .github/workflows/ci.yml # Automated backend and frontend checks
|-- backend/
|   |-- .dockerignore
|   |-- Dockerfile
|   |-- .env.example          # Backend configuration template
|   |-- requirements.txt     # Pinned Python dependencies
|   |-- requirements-dev.txt # Test and lint dependencies
|   |-- app/
|   |   |-- main.py          # FastAPI application and startup/shutdown lifecycle
|   |   |-- config.py        # Environment settings and validation
|   |   |-- api/             # HTTP routes
|   |   |-- ai/              # Assistant, prompts, and context assembly
|   |   |-- content/         # Canonical lessons, experiments, practice, and build challenges
|   |   |-- database/        # MongoDB connection, indexes, models, and seed logic
|   |   |-- quantum/         # Gate catalog, circuits, simulator, labs, QASM import, IBM client, jobs
|   |   |-- schemas/         # Request and response model exports
|   |   |-- services/        # Hardware quota and workshop sessions
|   |   |-- errors.py        # Application errors and HTTP handlers
|   |   |-- logging_config.py
|   |   `-- rate_limit.py
|   |-- scripts/             # export_catalog.py writes the shared frontend catalog
|   `-- test/                # Backend tests
`-- frontend/
    |-- .dockerignore
    |-- Dockerfile
    |-- nginx.conf           # Static hosting, API proxy, and SPA fallback
    |-- .env.example         # Frontend URL and development proxy template
    |-- package.json
    |-- package-lock.json
    |-- vite.config.ts
    |-- vitest.config.ts
    `-- src/
        |-- App.tsx          # Page routes and layout
        |-- main.tsx         # Application bootstrap and providers
        |-- pages/           # Learn, Playground, Builder, Labs, Challenges, Progress, Jobs, Facilitator, Assistant, About
        |-- components/      # Circuit diagrams, Bloch spheres, charts, practice, chat, feedback
        |-- context/         # Shared assistant and study context
        |-- hooks/           # Hardware submission and job polling
        |-- i18n/            # Interface text and locale provider
        |-- services/        # API client, experiment helpers, hardware storage
        |-- types/           # API types and catalog.generated.ts (from the backend)
        `-- test/            # Frontend tests and setup
```

## Requirements

- **Python 3.11 to 3.13** (CI uses 3.12). The backend requires at least Python 3.11 because it uses `enum.StrEnum`; installed packages must also support the selected Python version.
- **Node.js 22.x and npm** for the frontend and its test tooling.
- **MongoDB** for hardware jobs, feedback, and workshop sessions, running locally or through a connection URI (port `27017` by default). Leave `MONGODB_URI` empty to run a simulator-only workshop without it.
- **Optional:** IBM Quantum credentials for hardware execution, a compatible AI provider API key for live chat, and Redis for shared rate-limit storage.

The default configuration supports simulation and guide-based assistant replies without IBM or AI credentials.

## Local setup

Run the commands below from your local checkout. Keep the backend and frontend running in separate terminals.

### 1. Configure environment files

Copy the example files only when the corresponding `.env` files do not already exist. Preserve any existing configuration.

**PowerShell, from the repository root:**

```powershell
if (-not (Test-Path backend/.env)) { Copy-Item backend/.env.example backend/.env }
if (-not (Test-Path frontend/.env)) { Copy-Item frontend/.env.example frontend/.env }
```

**macOS/Linux:**

```bash
test -f backend/.env || cp backend/.env.example backend/.env
test -f frontend/.env || cp frontend/.env.example frontend/.env
```

Set `MONGODB_URI` in `backend/.env` to a reachable database, or set it to an empty value to skip MongoDB entirely. Leave `IBM_HARDWARE_ENABLED=false` for a local simulator workshop. Leave `LLM_API_KEY` empty to use the built-in guide. Set `ADMIN_TOKEN` (16 or more characters) to enable the facilitator dashboard.

### 2. Start MongoDB (optional)

Skip this step for a simulator-only workshop. Otherwise, start your existing MongoDB service, or configure a hosted database URI. If Docker is available, an optional local database can be started with:

```bash
docker run --name quantum-workshop-mongo -d -p 127.0.0.1:27017:27017 -v quantum-workshop-mongo-data:/data/db mongo:7
```

For subsequent runs of this container, use `docker start quantum-workshop-mongo`. Its named volume preserves database data.

### 3. Install and start the backend

**PowerShell:**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**macOS/Linux:**

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Using the virtual environment's Python directly avoids needing to activate it. Startup creates database indexes and seeds the curriculum automatically; no separate seed command is required.

### 4. Install and start the frontend

In a second terminal, from the repository root:

```bash
cd frontend
npm ci
npm run dev
```

The default frontend configuration leaves `VITE_API_BASE_URL` empty and proxies `/api` requests to `http://127.0.0.1:8000` through Vite.

### 5. Open the application

| Service | Local address |
| --- | --- |
| Web application | http://localhost:5173 |
| Backend health | http://127.0.0.1:8000/api/health |
| Swagger API documentation | http://127.0.0.1:8000/docs |
| ReDoc API documentation | http://127.0.0.1:8000/redoc |
| OpenAPI schema | http://127.0.0.1:8000/openapi.json |

A healthy response from `/api/health` includes `"status": "ok"` and `"database": "connected"`, or `"database": "disabled"` in simulator-only mode.

## Using the workshop

1. If a facilitator shares a session code, open **Progress** and join with a nickname.
2. Open **Learn** and select a lesson. Use the difficulty filters or search, read its objectives, and complete the practice questions.
3. Follow a related experiment link or open **Playground**. Inspect the circuit gates, expected behavior, and Qiskit code.
4. Step through the gate-by-gate Bloch view. Choose a shot count, a noise profile (preset or device snapshot), and optionally an X or Y measurement basis, then select **Run Simulator**.
5. Compare observed counts with ideal probabilities. The statistics panel says whether differences exceed sampling noise.
6. Open **Circuit Builder** to place gates, watch the state evolve, solve build challenges, and export Qiskit or OpenQASM.
7. Open **Labs** for the CHSH Bell test and the variational eigensolver.
8. Review badges on **Progress**, and export your progress if you want to keep it.
9. Open **Assistant** or the playground chat to ask for an explanation, hint, or quiz about the selected material.
10. If hardware access is enabled and quota is available, submit an approved guided circuit to IBM Quantum and follow it on **Hardware jobs**.
11. Open **Workshop Guide** to review the workflow and leave optional feedback.

Facilitators open **/facilitator**, enter the `ADMIN_TOKEN`, create a session code, and share the join link. The dashboard refreshes every 10 seconds.

| Page | Route |
| --- | --- |
| Home | `/` |
| Lessons | `/learn` |
| Quantum Playground | `/playground` |
| Circuit Builder | `/builder` |
| Labs (CHSH and VQE) | `/labs` |
| Quantum Challenges | `/challenges` |
| Progress, badges, and session join | `/progress` |
| Hardware job history | `/jobs` |
| Facilitator dashboard | `/facilitator` |
| Assistant | `/assistant` |
| Workshop Guide and feedback | `/about` |

Specific topics can be linked directly, for example `/learn?lesson=entanglement`, `/playground?experiment=bell_entanglement&bases=XX`, `/builder?challenge=ghz-three`, `/labs?lab=vqe`, and `/progress?session=ABC234`.

## Lessons and experiments

### Curriculum

| Level | Lessons |
| --- | --- |
| Beginner | Introduction to Quantum Computing; Superposition and the Hadamard Gate; Entanglement and Bell States; Quantum Gates; Quantum Hardware and Noise |
| Intermediate | Statevectors, Complex Amplitudes, and Measurement; Relative Phase and Phase Kickback; GHZ States, Correlations, and Coherence |
| Advanced | Deutsch-Jozsa and Quantum Oracle Queries; Grover Search and Amplitude Amplification; Quantum Fourier Transform and Phase Encoding; Teleportation and Deferred Measurement; Repetition Codes, Syndromes, and Error Correction; Variational Algorithms and Expectation Values |

### Approved circuit experiments

The following expectations describe the bundled ideal circuits. Finite sampling can change observed frequencies, and hardware noise can introduce additional deviations.

| Experiment ID | Qubits | Level | Ideal measured outcome |
| --- | --- | --- | --- |
| `superposition` | 1 | Beginner | `0` and `1`, each with probability 0.5 |
| `quantum_random_number` | 1 | Beginner | `0` and `1`, each with probability 0.5 |
| `bell_entanglement` | 2 | Beginner | `00` and `11`, each with probability 0.5 |
| `interference` | 1 | Beginner | `0` with probability 1 |
| `phase_kickback` | 2 | Intermediate | `1` with probability 1 |
| `ghz_entanglement` | 3 | Intermediate | `000` and `111`, each with probability 0.5 |
| `deutsch_jozsa` | 3 | Advanced | `01` with probability 1 for the bundled balanced oracle |
| `grover_search` | 2 | Advanced | `11` with probability 1 |
| `qft_phase` | 2 | Advanced | `00`, `01`, `10`, and `11`, each with probability 0.25 |
| `quantum_teleportation` | 3 | Advanced | `0` with probability 1 in the bundled verification circuit |
| `bit_flip_correction` | 3 | Advanced | `1` with probability 1 after correcting the chosen bit flip |

Measured bitstrings describe classical measurement registers; some experiments measure fewer bits than the total qubit count. Interpret bit order using each circuit's measurement mapping and Qiskit's bitstring conventions.

The teleportation demonstration uses deferred measurement. The bit-flip circuit demonstrates a specific ideal recovery rather than a complete fault-tolerant error-correction cycle. The variational optimization loop runs in **Labs**, and custom circuits are built in **Circuit Builder**. A backend test checks every listed ideal distribution against its circuit.

## Configuration reference

The backend loads `backend/.env` using an absolute path derived from `app/config.py`. Process environment variables take precedence. Restart the backend after changing settings.

### Backend: application and database

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_ENV` | `development` | Environment label returned by the health endpoint |
| `LOG_LEVEL` | `INFO` | Backend logging level |
| `MONGODB_URI` | `mongodb://localhost:27017` | Database connection URI; empty runs simulator-only mode |
| `MONGODB_DATABASE` | `quantum_workshop` | Application database name |
| `MONGODB_TIMEOUT_MS` | `5000` | Connection and server-selection timeout in milliseconds |
| `MONGODB_CONNECT_ATTEMPTS` | `5` | Startup connection attempts, from 1 to 20 |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed frontend origins |
| `RATE_LIMIT_STORAGE_URI` | `memory://` | SlowAPI storage URI; use a shared Redis URI for multiple workers or instances |
| `ADMIN_TOKEN` | Empty | Facilitator dashboard and feedback export token, at least 16 characters; empty disables them |
| `FEEDBACK_RETENTION_DAYS` | `0` | Days to keep feedback through a MongoDB TTL index; `0` keeps it indefinitely |
| `SESSION_RETENTION_HOURS` | `72` | Lifetime of workshop session codes and participant progress, from 1 to 720 |

### Backend: execution and hardware

| Variable | Default | Purpose |
| --- | --- | --- |
| `DEFAULT_SHOTS` | `1024` | Default shot count exposed to the frontend |
| `MAX_SIMULATOR_SHOTS` | `10000` | Maximum shots per simulator request |
| `IBM_HARDWARE_ENABLED` | `false` | Enables new hardware submissions |
| `IBM_QUANTUM_API_KEY` | Empty | IBM Quantum credential, used only by the backend |
| `IBM_QUANTUM_INSTANCE` | Empty | Optional runtime instance identifier passed to the IBM service |
| `IBM_QUANTUM_ACCOUNTS` | Empty | Optional JSON array of named IBM credentials; the backend checks all accounts and selects the eligible backend with the shortest queue |
| `IBM_MAX_DAILY_JOBS` | `25` | Global daily hardware reservation/submission limit, using UTC dates |
| `IBM_MAX_ACTIVE_JOBS` | `3` | Global active hardware job limit, including earlier UTC days |
| `IBM_MAX_SHOTS` | `4096` | Maximum shots per hardware request |
| `JOB_POLL_SECONDS` | `15` | Background hardware reconciliation interval in seconds |
| `JOB_RETENTION_DAYS` | `7` | Retention after a terminal job's quota accounting is settled |

`DEFAULT_SHOTS` must not exceed `MAX_SIMULATOR_SHOTS`. Hardware and simulator request schemas default omitted `shots` to `1024`; clients can read `/api/config/public` and send the configured default explicitly.

### Backend: assistant

| Variable | Default | Purpose |
| --- | --- | --- |
| `LLM_API_KEY` | Empty | Credential for live assistant responses; empty selects the workshop guide |
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` | API base URL; the backend appends `/chat/completions` |
| `LLM_MODEL` | `openai/gpt-oss-20b` | Model identifier sent to the configured provider |
| `LLM_MAX_REQUESTS_PER_MINUTE` | `10` | Assistant request limit per client IP |
| `LLM_TIMEOUT_SECONDS` | `25` | External assistant request timeout in seconds |

The provider URL and model above are repository defaults. Model access and compatibility depend on the configured provider and account.

### Frontend

| Variable | Default | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | Empty | Backend origin for browser requests, such as `https://api.example.com`; omit a trailing `/api` because request paths already include it |
| `API_PROXY_TARGET` | `http://127.0.0.1:8000` | Backend target for the Vite development and preview `/api` proxy |

Vite embeds `VITE_*` values into the browser build. Keep credentials in the backend configuration. Restart Vite after development environment changes and rebuild after changing production frontend variables.

## Optional integrations

### Live assistant

Set `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL` in `backend/.env`, then restart the backend. The service sends the conversation and selected workshop context to the configured provider.

Responses identify their origin using `source: "llm"` or `source: "fallback"`. Guide replies include a notice explaining that live AI is unavailable. The backend falls back for missing API credentials, provider HTTP errors, timeouts, transport failures, and supported malformed-response cases.

### IBM Quantum hardware

Configure the following backend variables with credentials and an instance accessible to your account:

```dotenv
IBM_HARDWARE_ENABLED=true
IBM_QUANTUM_API_KEY=your_ibm_quantum_api_key
IBM_QUANTUM_INSTANCE=your_runtime_instance_identifier
IBM_MAX_DAILY_JOBS=25
IBM_MAX_ACTIVE_JOBS=3
IBM_MAX_SHOTS=4096
```

For multiple pre-configured IBM accounts, set `IBM_QUANTUM_ACCOUNTS` to a JSON array instead of the single key, for example `[{"name":"primary","api_key":"...","instance":"..."},{"name":"backup","api_key":"...","instance":"..."}]`. Keep these credentials in the backend secret store and never in frontend variables. Hardware results from completed jobs are saved as the latest recorded result for each experiment; the playground labels this data as recorded when a live result is waiting, unavailable, or failed.

The implementation uses the `ibm_quantum_platform` channel, selects an operational nonsimulator backend with enough qubits and the fewest pending jobs among the returned candidates, transpiles the approved circuit, and submits through `SamplerV2`.

Hardware access depends on account permissions, provider capacity, and configured quotas. The application quotas are global to the deployment. A local simulation does not require IBM access.

Clients must send an `idempotency_key` of 16 to 128 characters. Reusing it with the same experiment and shots retrieves the existing submission; using it with different parameters returns HTTP `409`. Retain the returned tracking ID to query results. Disabling new submissions does not stop reconciliation of existing jobs; that still requires usable IBM credentials.

## API reference

Use the running backend's `/docs` for interactive request schemas and validation details. Application errors generally return a `detail` field; FastAPI validation errors use its standard validation response.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Database health and environment; HTTP `503` if the database health check fails |
| `GET` | `/api/config/public` | Public hardware flag and shot limits |
| `GET` | `/api/lessons` | Ordered lessons with public practice questions |
| `GET` | `/api/lessons/{lesson_id}` | One lesson and its practice questions |
| `POST` | `/api/lessons/{lesson_id}/practice/check` | Check a multiple-choice selection or retrieve a written-answer comparison |
| `GET` | `/api/experiments` | All approved circuit metadata |
| `GET` | `/api/experiments/{experiment_id}` | One circuit's metadata |
| `GET` | `/api/experiments/{experiment_id}/evolution` | Gate-by-gate per-qubit Bloch vectors for a guided circuit |
| `POST` | `/api/experiments/simulate` | Execute an approved circuit on Qiskit Aer with a noise profile and optional measurement bases |
| `POST` | `/api/experiments/custom/simulate` | Execute a validated custom gate sequence on Qiskit Aer |
| `POST` | `/api/experiments/custom/evolution` | Gate-by-gate Bloch vectors for a custom circuit |
| `POST` | `/api/experiments/custom/qasm` | Convert an OpenQASM 2 program into builder gates |
| `GET` | `/api/challenges` | Build challenges (without targets) and playground challenge IDs |
| `POST` | `/api/challenges/{challenge_id}/check` | Grade a custom circuit against a build challenge |
| `POST` | `/api/labs/chsh` | Run the four-setting CHSH Bell test |
| `POST` | `/api/labs/vqe` | Run a parameter-shift variational eigensolver |
| `POST` | `/api/experiments/hardware` | Submit an approved circuit to IBM Quantum |
| `GET` | `/api/experiments/jobs/{tracking_id}` | Refresh job status and return any available results |
| `GET` | `/api/hardware/status` | Hardware flag, shot cap, daily capacity, and active jobs |
| `GET` | `/api/hardware/saved/{experiment_id}` | Latest completed IBM result saved for fallback/comparison |
| `POST` | `/api/assistant/chat` | Ask the assistant with optional lesson, experiment, and result context |
| `POST` | `/api/assistant/chat/stream` | The same request, answered as server-sent events (`meta`, `delta`, `done`) |
| `POST` | `/api/feedback` | Save anonymous workshop feedback, optionally tagged with a session code |
| `GET` | `/api/sessions/{code}` | Look up an active workshop session |
| `POST` | `/api/sessions/{code}/join` | Join a session with a nickname; returns a participant token |
| `PUT` | `/api/sessions/{code}/progress` | Sync a participant's progress |
| `GET`, `POST` | `/api/admin/sessions` | List or create sessions (facilitator token) |
| `GET` | `/api/admin/sessions/{code}` | Session dashboard (facilitator token) |
| `GET` | `/api/admin/feedback`, `/api/admin/feedback/export` | Feedback summary or CSV (facilitator token) |

Facilitator endpoints require `Authorization: Bearer <ADMIN_TOKEN>`.

Lesson and challenge completion is stored locally in browser storage, not sent to the backend. Shared guided experiment links preserve the selected experiment, shot count, and noise profile. Custom circuit links store the circuit draft in the URL; CSV exports are generated in the browser.

### Example: simulation

Send this JSON body to `POST /api/experiments/simulate`:

```json
{
  "experiment_id": "bell_entanglement",
  "shots": 1024,
  "noise_profile": "medium"
}
```

PowerShell example:

```powershell
$simulationBody = @{ experiment_id = 'bell_entanglement'; shots = 1024 } | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/experiments/simulate' -Method Post -ContentType 'application/json' -Body $simulationBody
```

The optional `noise_profile` accepts `ideal` (the default), `low`, `medium`, `high`, or a device snapshot: `device_manila`, `device_nairobi`, or `device_sherbrooke`. The optional `measurement_bases` lists `Z`, `X`, or `Y` for each circuit qubit; ideal probabilities are then computed for those bases. The response includes `experiment_id`, `backend`, `backend_name`, `shots`, `noise_profile`, `counts`, `observed_probabilities`, `ideal_probabilities`, and simulator `amplitudes`. Each amplitude includes its basis outcome, real and imaginary parts, probability, and phase in degrees. Hardware responses expose counts and probabilities rather than a measured statevector.

### Example: assistant

Send this JSON body to `POST /api/assistant/chat`:

```json
{
  "messages": [
    { "role": "user", "content": "Why does this circuit measure only 00 and 11?" }
  ],
  "experiment_id": "bell_entanglement",
  "lesson_id": "entanglement",
  "mode": "hint"
}
```

`result_context` can optionally carry recorded experiment results. Requests accept 1 to 12 messages; user messages are limited to 2,000 characters each. `mode` may be `explain`, `hint`, or `quiz` and defaults to `explain`.

### Circuit builder limits

The custom simulator accepts 1 to 5 qubits and up to 40 gates from `H`, `X`, `Y`, `Z`, `S`, `T`, `SX`, `RX`, `RY`, `RZ`, `U`, `CX`, `CZ`, `CP`, `SWAP`, and `CCX`. `RX`, `RY`, `RZ`, and `CP` take `angle`; `U` takes `angle` (θ), `phi`, and `lam`. Angles must be between -2π and 2π radians. Multi-qubit gates list controls first. The server validates each gate and qubit index, applies any measurement-basis rotations, and appends measurement. OpenQASM import accepts only `include "qelib1.inc"`, never reads files, and rejects gates after a measurement. The offline assistant can ask a quiz question but cannot grade a free-form response.

Example request for `POST /api/experiments/custom/simulate`:

```json
{
  "qubits": 2,
  "gates": [
    { "name": "H", "qubits": [0] },
    { "name": "CX", "qubits": [0, 1] }
  ],
  "shots": 512,
  "noise_profile": "medium"
}
```

### Example: feedback

Send this JSON body to `POST /api/feedback`:

```json
{
  "rating": 5,
  "clarity_rating": 4,
  "completed_workshop": true,
  "comments": "The circuit diagrams helped explain entanglement."
}
```

Both ratings must be from 1 to 5; comments are optional and limited to 1,000 characters.

### Request limits

SlowAPI keys limits by the request's remote address. Configured limits are:

| Operation | Limit |
| --- | --- |
| Default for routes without an explicit override | 120 requests/minute |
| Simulation | 20 requests/minute |
| Custom circuit simulation | 20 requests/minute |
| Hardware submission | 5 requests/minute |
| Hardware job lookup | 60 requests/minute |
| Assistant | `LLM_MAX_REQUESTS_PER_MINUTE`, default 10 |
| Feedback | 5 requests/minute |
| Custom evolution | 40 requests/minute |
| QASM import, CHSH lab, challenge checks (30) | 20 to 30 requests/minute |
| VQE lab | 6 requests/minute |
| Practice checks | 30 requests/minute |
| Session join / progress sync | 10 / 60 requests/minute |
| Facilitator endpoints | 10 to 60 requests/minute |

Rate-limit and hardware-quota exhaustion both return HTTP `429`; inspect the response detail to distinguish them. Rate-limit responses include a `Retry-After` header.

## Testing and development

### Backend

From `backend/`, using the virtual environment created above:

```powershell
# Windows PowerShell
.\.venv\Scripts\python.exe -m pytest test -q
```

```bash
# macOS/Linux
.venv/bin/python -m pytest test -q
```

Tests cover circuits, simulations, measurement bases, device noise, the curriculum's ideal distributions, API behavior, lesson practice and AI grading, build challenges, the CHSH and VQE labs, QASM import safety, hardware job lifecycle, quotas, assistant responses, streaming and failure handling, workshop sessions, facilitator authorization, simulator-only mode, system endpoints, and single-owner hardware reconciliation leases. Test fixtures use mongomock and service mocks, disable live hardware, clear the assistant API key, and use in-memory rate limiting. The suite is designed to run without a live MongoDB, IBM, or AI service.

Use Ruff to check and format backend code, and pip-audit to check dependencies:

```bash
ruff check app test scripts
ruff format app test scripts
python -m pytest test -q --cov=app --cov-fail-under=85
pip-audit -r requirements.txt
```

Gate names, limits, noise profiles, measurement bases, and experiment IDs are defined once in `app/quantum/catalog.py` and the curriculum. After changing them, regenerate the frontend copy; a backend test fails when it is stale:

```bash
python scripts/export_catalog.py
```

### Frontend

From `frontend/`:

```bash
npm test
npm run lint
npm run build
```

Tests use Vitest and React Testing Library with jsdom. Coverage includes workshop flows, the circuit builder, challenges, labs, the facilitator dashboard, session joining, progress import and export, statistics, angle parsing, assistant streaming, practice, navigation, and Markdown rendering. The build runs TypeScript checks before generating static assets in `frontend/dist/`.

The Playwright browser smoke test runs the lesson, practice, and simulator flow against deterministic API fixtures. Install Chromium once with `npx playwright install chromium`, then run:

```bash
npm run test:e2e
```

GitHub Actions runs backend lint, tests with an 85% coverage floor, and pip-audit; frontend npm audit, tests, the Playwright smoke test, ESLint, and the production build; and finally validates the Compose file and builds both Docker images. Dependabot proposes weekly dependency updates.

To inspect the production bundle locally:

```bash
npm run preview
```

The preview server also proxies `/api` using `API_PROXY_TARGET`. It is intended for local inspection.

## Deployment

For a reproducible local deployment, copy `backend/.env.example` to `backend/.env` only if it does not already exist, then run:

```bash
docker compose up --build
```

Open http://localhost:8080. The stack includes MongoDB with a persistent volume, an API container running as a non-root user, an Nginx frontend/API proxy with security headers, gzip, and long-lived caching for fingerprinted assets, health checks, and the SPA route fallback. MongoDB sits on an internal network reachable only from the API, and the API is only exposed inside the Compose networks. Optional IBM and AI credentials can be set in `backend/.env`; leave them empty for simulator and guide-only use. Stop the stack with `docker compose down`; data remains in the named `mongo-data` volume. Remove that volume only when you intend to delete local database data.

For hosted deployments, deploy the backend and frontend as separate services, or place them behind one reverse proxy.

1. Provision MongoDB and configure backend environment variables. The backend database user must be able to write application collections and create indexes.
2. Install `backend/requirements.txt` and run Uvicorn from `backend/` without development reload:

   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

3. Set `CORS_ORIGINS` to the frontend origins when browsers call the backend directly. If deploying multiple backend workers or instances, configure shared rate-limit storage, such as `RATE_LIMIT_STORAGE_URI=redis://your-redis-host:6379/0`.
4. Build the frontend with `npm ci` and `npm run build`. For separate origins, set `VITE_API_BASE_URL` before building. For a shared origin, leave it empty and configure the reverse proxy to forward `/api` to the backend.
5. Serve `frontend/dist/` through a static host. Configure SPA fallback so browser visits to `/learn`, `/playground`, `/assistant`, and `/about` return `index.html`.
6. Use `/api/health` for backend health checks. When behind a proxy, configure trusted forwarded addresses so per-client rate limiting sees the intended client IP.

The Vite proxy configuration applies to development and local preview. For production, the included Nginx config serves the static bundle, forwards `/api` to the backend, and applies the SPA fallback. The Compose API trusts forwarded client addresses only from the proxy network; configure trusted proxy addresses explicitly for other hosting setups rather than trusting arbitrary forwarded headers. The bundled Content-Security-Policy allows API calls to the same origin only; if you serve the frontend with a separate `VITE_API_BASE_URL`, add that origin to `connect-src`. Proxies in front of the API must not buffer `/api/assistant/chat/stream`.

## Data and operational behavior

- **MongoDB collections:** `quantum_jobs`, `hardware_quota`, `hardware_results`, `feedback`, `workshop_sessions`, `session_participants`, and `runtime_locks`, plus `lessons` and `experiments` copies for operators.
- **Content source:** The API always serves lessons, experiments, and challenges from the canonical Python definitions. Startup also upserts copies into MongoDB, but edits to those copies are never served.
- **Job tracking:** Job states include `queued`, `running`, `completed`, `failed`, `cancelled`, and `unknown`. A background loop reconciles unfinished jobs; status requests also refresh the requested job.
- **Retry recovery:** Ambiguous IBM submissions are searched by provider job tags rather than automatically submitted again. An uncertain submission can retain its reservation while reconciliation continues.
- **Retention:** Terminal hardware jobs receive a MongoDB TTL expiry after quota settlement, using `JOB_RETENTION_DAYS`. MongoDB removes expired records asynchronously. Active and unresolved jobs are retained for reconciliation.
- **Browser storage:** Hardware submission keys, shot counts, and tracking IDs are stored in local storage when available. Lesson and challenge progress and saved custom circuits are also stored locally and are not tied to an account. Clearing browser data can remove this information. Chat context lives in application memory and resets on a full page reload.
- **Feedback retention:** Feedback ratings, completion status, optional comments, any joined session code, and creation timestamps are stored in MongoDB. Set `FEEDBACK_RETENTION_DAYS` to expire feedback automatically; with the default `0`, the operator must remove it. Users should avoid entering personal or sensitive information in comments.
- **Workshop sessions:** Session codes and participant records (nickname, completed lesson and challenge IDs, practice counts, and a hashed participant token) expire after `SESSION_RETENTION_HOURS`.
- **Offline cache:** The service worker caches the app shell, fingerprinted assets, and read-only content responses (lessons, experiments, challenges, public config). Simulations, hardware jobs, sessions, and the assistant always use the network.
- **Access model:** The application has no learner accounts. Facilitator endpoints use a single shared `ADMIN_TOKEN`, compared in constant time; the dashboard keeps it in the browser tab's session storage. Hardware tracking IDs grant access to their job lookup and should be treated as private. Hardware tracking and idempotency keys are stored as hashes in MongoDB; the frontend retains the values needed to resume requests.
- **External data flow:** Live assistant requests send conversation and selected context, and written practice answers, to the configured AI provider. IBM submissions send approved circuits and execution settings to IBM Quantum. Guide-based assistant replies require no external AI request.
- **Secrets:** Keep provider keys and database credentials in backend environment variables. `.env` files are ignored by Git; `.env.example` templates are tracked.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Backend exits during startup | Confirm MongoDB is running, `MONGODB_URI` is correct, and the database user can create indexes. Startup retries are controlled by `MONGODB_CONNECT_ATTEMPTS`. To run without MongoDB, set `MONGODB_URI` to an empty value. |
| Feedback or sessions return HTTP `503` | The backend is in simulator-only mode, or `ADMIN_TOKEN` is not set for facilitator endpoints. |
| A backend test says the frontend catalog is stale | Run `python scripts/export_catalog.py` from `backend/` and commit the regenerated file. |
| Old interface after a deployment | The service worker shows a "new version" banner; select **Reload**. |
| Assistant answers appear all at once behind a proxy | Disable response buffering for `/api/assistant/chat/stream` (Nginx: `proxy_buffering off`). |
| `ModuleNotFoundError: app` | Run Uvicorn or pytest from `backend/` using the installed virtual environment. |
| Lessons or experiments fail to load | Check that the backend is listening on port 8000, then check `/api/health`. Verify `API_PROXY_TARGET` or `VITE_API_BASE_URL`. |
| Requests go to `/api/api/...` | Set `VITE_API_BASE_URL` to the backend origin without an `/api` suffix. |
| Browser reports a CORS error | For direct backend requests, add the exact frontend scheme, host, and port to `CORS_ORIGINS`, then restart the backend. |
| Assistant says live AI is unavailable | Check `LLM_API_KEY`, the provider base URL, model access, and backend logs. Guide replies remain available during supported provider failures. |
| Hardware control is unavailable | Check the hardware flag, credentials, selected shot count, active jobs, and remaining daily quota through `/api/hardware/status`. |
| Hardware job stays `unknown` | The provider may be unavailable or submission acceptance may be uncertain. Retain the existing tracking ID and allow reconciliation to continue. |
| Job lookup returns `404` | The tracking ID may be invalid, or the completed job may have expired under the retention policy. |
| HTTP `409` on submission | The idempotency key was reused with different experiment parameters. Use the original parameters for a retry, or a new key for a new job. |
| HTTP `429` | A client request limit or deployment-wide hardware quota has been reached; inspect the response detail. |
| Frontend tests fail due to Node compatibility | Use Node.js 22.x and reinstall from the frontend lockfile with `npm ci`. |
| Refreshing a deployed page returns `404` | Configure the static host's SPA fallback to serve `index.html` for frontend routes. |

## Extending the project

- **Lessons and experiments:** Edit [backend/app/content/curriculum.py](backend/app/content/curriculum.py). Keep experiment IDs, gate definitions, Qiskit examples, classical mappings, and ideal distributions consistent.
- **Practice questions:** Edit [backend/app/content/practice.py](backend/app/content/practice.py). Public questions omit answer keys; answer checking returns explanations or self-assessment material.
- **New circuit support:** Add guided experiments to the curriculum and its `ExperimentId` enum; add builder gates or noise profiles in [backend/app/quantum/catalog.py](backend/app/quantum/catalog.py). Then run `python scripts/export_catalog.py` so the frontend picks them up.
- **Build challenges:** Add entries to [backend/app/content/challenges.py](backend/app/content/challenges.py) with a target state or distribution, and add a known solution to `backend/test/test_features.py`.
- **Interface languages:** Copy the `en` messages in [frontend/src/i18n/messages.ts](frontend/src/i18n/messages.ts), translate them, and register the locale in `LOCALES`; a language menu appears automatically once there are two.
- **Assistant behavior:** Adjust [backend/app/ai/prompts.py](backend/app/ai/prompts.py), the knowledge-base context builder, and guide replies to match new content.
- **Verification:** Run the relevant existing tests and frontend checks when changing behavior. Restart the backend to synchronize seeded content.

## License

No license is included. This repository does not grant permission to reuse, modify, or distribute the code.
