# Quantum Workshop Lab

Guided quantum lessons, Qiskit Aer experiments, optional IBM Quantum hardware, and an optional AI teaching assistant.

## Learning path and circuit labs

The course contains 14 lessons across beginner, intermediate, and advanced levels. Use the level filters, concept search, prerequisite links, and related-circuit links on the Learn page.

Each lesson includes four interactive multiple-choice questions and two written questions: 56 MCQs and 28 written prompts in total. Select an option and click **Check answer** to see correctness, the correct option, and an explanation. Written practice requires an attempt before showing a sample answer and self-review points; it is not automatically graded. Answer keys stay on the backend and are omitted from public lesson responses. Practice attempts are not saved to MongoDB, and changing lessons or refreshing resets the current practice progress.

| Level | Topics |
| --- | --- |
| Beginner | Qubits, superposition, Bell states, gates, measurement, and hardware noise |
| Intermediate | Complex amplitudes, Born probabilities, Bloch-sphere coordinates, global and relative phase, phase kickback, and GHZ coherence |
| Advanced | Deutsch–Jozsa, Grover amplitude amplification, QFT, deferred-measurement teleportation, repetition-code error correction, and variational expectation estimation |

The Playground provides 10 approved circuits: superposition, Bell entanglement, interference, phase kickback, a three-qubit GHZ state, a balanced Deutsch–Jozsa oracle, Grover search for 11, QFT phase encoding, coherent teleportation verification, and single-bit-flip recovery. Gate definitions, diagrams, explanations, and simulator construction share one catalog in `backend/app/content/curriculum.py`.

Open each circuit's gate walkthrough and Qiskit example, then inspect its histogram and ideal complex-amplitude table. Histograms use measured classical bits, while the amplitude table describes the full ideal quantum register. A uniform QFT histogram can still carry distinct relative phases. The assistant retrieves these lessons by topic and uses them for offline guide answers too.

During in-app navigation, the assistant keeps the selected lesson or experiment and its available measurement results. Opening the AI Assistant page automatically introduces that topic once, shows the current study context, and offers relevant follow-up questions. Returning to the same topic preserves the conversation; selecting a different topic starts a fresh conversation and cancels any pending reply about the previous topic. Clearing chat keeps the selected topic. The workshop guide also provides contextual circuit overviews when live AI is unavailable.

Assistant answers support headings, spaced paragraphs and lists, Markdown tables, code blocks, and inline or display equations. Wide tables, code, and equations scroll within their own containers on small screens. Long replies open at their beginning and do not move the view while someone is reading earlier messages. Generated answers keep their full formatting instead of being cut at 2,000 characters; provider token limits still apply, and user questions remain limited to 2,000 characters.

The advanced lessons explicitly describe demonstration limits: Z-basis GHZ counts alone do not certify coherence; coherent teleportation is not separated-party classical feed-forward; a repetition code does not correct arbitrary phase errors; and fixed circuit labs do not implement a VQE optimizer. Lessons include links to [IBM Quantum Learning](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information), its [algorithms course](https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms), and its [error-correction course](https://quantum.cloud.ibm.com/learning/en/courses/foundations-of-quantum-error-correction).

## Local development

Use Python 3.11–3.13, Node.js 22.12+ or 24+, and MongoDB 7. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd frontend
npm ci
```

On a fresh checkout, copy `backend/.env.example` to `backend/.env`. Preserve an existing `.env`. Set `MONGODB_URI` to a reachable local MongoDB or Atlas database. Hardware requires `IBM_HARDWARE_ENABLED=true` and IBM Cloud credentials. Without `LLM_API_KEY`, the assistant returns an educational fallback.

The backend loads `backend/.env` independently of the launch directory. To start from its directory:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Alternatively, from the repository root use `.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --port 8000`.

The default Groq model is `openai/gpt-oss-20b`. `LLM_MODEL` must name a model available to your account; check the provider's model list if live responses stop working. Restart the backend after editing `.env`. The chat labels live AI responses and offline workshop guide answers separately. Guide answers respond to the question and available measurements when the provider is unavailable. Failed requests can be retried without duplicating the question, and navigation keeps an in-flight request active.

In another terminal:

```powershell
cd frontend
npm run dev
```

Open http://localhost:5173. Empty or absent `VITE_API_BASE_URL` uses the Vite `/api` proxy to port 8000. Existing frontend environment values take precedence; use an empty value to use the proxy. `API_PROXY_TARGET` changes the proxy destination. `npm run preview` uses the same proxy after a production build.

## Hosting

For separate frontend hosting, set `VITE_API_BASE_URL` to the public HTTPS API URL at build time and add the frontend origin to backend `CORS_ORIGINS`. Configure the frontend host to serve `index.html` for React routes such as `/learn` and `/playground`. Never put backend secrets in Vite variables.

MongoDB must be available through the configured `MONGODB_URI`, using a local installation or Atlas. For one API worker, `RATE_LIMIT_STORAGE_URI=memory://` is sufficient. Multiple workers or instances require shared Redis storage; configure its connection URL in `RATE_LIMIT_STORAGE_URI`.

## Hardware jobs

Daily quota uses UTC. Atomic reservations include outstanding submissions and active jobs from previous days. Retries use the same idempotency key and tracking ID. Reusing a key with different parameters returns HTTP 409. The database stores a tracking-token hash and nonce, not the original tracking credential.

Tracking IDs and pending submission keys are saved in browser local storage per experiment. The Playground can clear an expired tracking ID. Active jobs do not expire; terminal records expire after `JOB_RETENTION_DAYS` (default seven). A background task checks jobs every `JOB_POLL_SECONDS` (default fifteen), independently of browser polling.

IBM submissions carry a correlation tag. After a network interruption, reconciliation searches for that tag instead of submitting another paid job. Uncertain submissions retain their reservations until reconciled. If IBM persistently reports no matching tagged job, an operator must verify the provider account before clearing the reservation; the application does not assume a timed-out submission was rejected.

## Verification

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
cd ..\frontend
npm run lint
npm test
npm run build
```

Backend tests use an isolated MongoDB mock and fake IBM/LLM responses. They never use credentials or submit real jobs. Coverage includes quota limits, concurrent completion, idempotency, interrupted submission recovery, assistant fallbacks, result extraction, health checks, and simulations. Frontend tests cover experiment selection, configured shot options, persisted retries, result switching, assistant context, feedback errors, SVG attributes, and math rendering.

Styling uses Tailwind CSS 4 and requires modern browsers (Safari 16.4+, Chrome 111+, Firefox 128+). Run `npm audit` to check dependency advisories against the current registry.
