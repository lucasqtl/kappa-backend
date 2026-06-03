from fastapi import APIRouter

from app.presentation.api.v1.routers import alunos, missoes

api_router = APIRouter()
api_router.include_router(alunos.router)
api_router.include_router(missoes.router)
