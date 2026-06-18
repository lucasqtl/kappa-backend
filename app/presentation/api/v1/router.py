from fastapi import APIRouter

from app.presentation.api.v1.routers import alunos, missoes
from app.presentation.api.v1.routers import auth, submissoes

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(alunos.router)
api_router.include_router(missoes.router)
api_router.include_router(submissoes.router)
