from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import assistant, experiments, feedback, hardware, lessons, system
from app.config import get_settings
from app.database.mongodb import Mongo
from app.database.seed import seed_database
from app.errors import AppError, app_error_handler, unhandled_error_handler
from app.logging_config import configure_logging
from app.rate_limit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    Mongo.connect()
    seed_database()
    yield
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