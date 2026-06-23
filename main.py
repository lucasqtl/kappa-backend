import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.domain.exceptions import (
    DomainError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    UnauthorizedActionError,
)
from app.presentation.api.v1.router import api_router
from core.config import get_settings
from core.database import engine
from core.logging_config import get_logger, setup_logging

settings = get_settings()
setup_logging()
logger = get_logger("http")

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/", include_in_schema=False)
@app.get("/lab", include_in_schema=False)
def backend_lab() -> FileResponse:
    return FileResponse(Path(__file__).with_name("index.html"))


@app.middleware("http")
async def log_request_timing(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response


def _domain_status(exc: DomainError) -> int:
    if isinstance(exc, EntityNotFoundError):
        return 404
    if isinstance(exc, InvalidStateTransitionError):
        return 409
    if isinstance(exc, UnauthorizedActionError):
        return 403
    return 400


@app.exception_handler(DomainError)
async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    status_code = _domain_status(exc)
    logger.warning(
        "domain_error",
        error_type=type(exc).__name__,
        message=exc.message,
        status_code=status_code,
    )
    return JSONResponse(status_code=status_code, content={"detail": exc.message})


@app.get("/health", tags=["Health"])
def health_check() -> JSONResponse:
    db_status = "ok"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = "error"
        logger.error(
            "health_check_db_failed",
            error_type=type(exc).__name__,
            message=str(exc),
        )

    payload = {
        "status": "ok" if db_status == "ok" else "degraded",
        "db_status": db_status,
        "service": "kappa-backend",
    }
    status_code = 200 if db_status == "ok" else 503
    return JSONResponse(status_code=status_code, content=payload)
