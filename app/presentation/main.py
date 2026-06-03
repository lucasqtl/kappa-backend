from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.exceptions import DomainError
from app.presentation.api.v1.router import api_router
from core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API da Plataforma Kappa — ensino gamificado de programação",
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.exception_handler(DomainError)
async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.message})


@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    """Página inicial da API — evita 404 ao abrir http://127.0.0.1:8000 no browser."""
    return {
        "service": "kappa-backend",
        "message": "Plataforma Kappa API em execução.",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "api_v1": settings.api_v1_prefix,
    }


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "kappa-backend"}
