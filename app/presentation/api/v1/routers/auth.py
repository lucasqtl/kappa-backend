import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.entities import Aluno, Professor
from app.domain.enums import PerfilUsuario
from app.infrastructure.database.models import UsuarioModel
from app.infrastructure.repositories.sqlalchemy_aluno_repository import (
    SqlAlchemyAlunoRepository,
)
from app.infrastructure.repositories.sqlalchemy_professor_repository import (
    SqlAlchemyProfessorRepository,
)
from app.presentation.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegistroAlunoRequest,
    RegistroProfessorRequest,
    TokenResponse,
)
from core.database import get_db
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/registro/aluno",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo aluno",
)
def registrar_aluno(
    body: RegistroAlunoRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    repo = SqlAlchemyAlunoRepository(db)
    aluno = Aluno(
        id=uuid.uuid4(),
        username=body.username,
        email=body.email,
        senha_hash=hash_password(body.senha),
        perfil=PerfilUsuario.ALUNO,
    )
    try:
        aluno = repo.criar(aluno)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail ou username ja cadastrado",
        )
    subject = str(aluno.id)
    return TokenResponse(
        access_token=create_access_token(subject, {"perfil": aluno.perfil.value}),
        refresh_token=create_refresh_token(subject),
    )


@router.post(
    "/registro/professor",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo professor",
)
def registrar_professor(
    body: RegistroProfessorRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    repo = SqlAlchemyProfessorRepository(db)
    professor = Professor(
        id=uuid.uuid4(),
        username=body.username,
        email=body.email,
        senha_hash=hash_password(body.senha),
        perfil=PerfilUsuario.PROFESSOR,
        departamento=body.departamento,
    )
    try:
        professor = repo.criar(professor)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail ou username ja cadastrado",
        )
    subject = str(professor.id)
    return TokenResponse(
        access_token=create_access_token(subject, {"perfil": professor.perfil.value}),
        refresh_token=create_refresh_token(subject),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autenticar usuario",
)
def login(
    body: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    usuario = db.query(UsuarioModel).filter(UsuarioModel.email == body.email).one_or_none()
    if usuario is None or not verify_password(body.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
        )
    subject = str(usuario.id)
    return TokenResponse(
        access_token=create_access_token(subject, {"perfil": usuario.perfil.value}),
        refresh_token=create_refresh_token(subject),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar access token via refresh token",
)
def refresh_token(
    body: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    payload = decode_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido ou expirado",
        )

    subject = payload.get("sub", "")
    try:
        usuario_id = uuid.UUID(subject)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido ou expirado",
        )

    usuario = db.get(UsuarioModel, usuario_id)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido ou expirado",
        )

    return TokenResponse(
        access_token=create_access_token(subject, {"perfil": usuario.perfil.value}),
        refresh_token=create_refresh_token(subject),
    )
