import asyncio
import logging
import secrets
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import assistant, experiments, feedback, hardware, lessons, system
from app.config import get_settings
from app.database.mongodb import Mongo
from app.database.seed import seed_database
from app.errors import AppError, app_error_handler, unhandled_error_handler
from app.logging_config import configure_logging
from app.quantum.job_manager import JobManager
from app.rate_limit import limiter


async def reconcile_jobs():
    while True:
        owner = secrets.token_hex(16)
        has_lease = False
        try:
            has_lease = await asyncio.to_thread(
                Mongo.acquire_lease, "hardware-job-reconciliation", owner
            )
            if has_lease:
                reconciliation = asyncio.create_task(asyncio.to_thread(JobManager.reconcile))
                lease_valid = True
                while not reconciliation.done():
                    await asyncio.wait({reconciliation}, timeout=20)
                    if reconciliation.done():
                        break
                    lease_valid = await asyncio.to_thread(
                        Mongo.renew_lease, "hardware-job-reconciliation", owner
                    )
                    if not lease_valid:
                        logging.getLogger(__name__).error(
                            "Hardware reconciliation lease was lost; waiting for the current pass to finish"
                        )
                        break
                await reconciliation
                if not lease_valid:
                    has_lease = False
        except Exception:
            logging.getLogger(__name__).exception("Hardware reconciliation failed")
        finally:
            if has_lease:
                try:
                    await asyncio.to_thread(
                        Mongo.release_lease, "hardware-job-reconciliation", owner
                    )
                except Exception:
                    logging.getLogger(__name__).exception(
                        "Unable to release hardware reconciliation lease"
                    )
        await asyncio.sleep(get_settings().job_poll_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await asyncio.to_thread(Mongo.connect)
    task = None
    try:
        await asyncio.to_thread(seed_database)
        task = asyncio.create_task(reconcile_jobs())
        yield
    finally:
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        Mongo.close()


app = FastAPI(
    title="Quantum Workshop Lab API",
    version="1.0.0",
    description="Educational quantum computing workshop platform API.",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)
app.add_exception_handler(
    RateLimitExceeded,
    lambda request, exc: JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please wait a moment."},
    ),
)
app.include_router(system.router)
app.include_router(lessons.router)
app.include_router(experiments.router)
app.include_router(hardware.router)
app.include_router(assistant.router)
app.include_router(feedback.router)
