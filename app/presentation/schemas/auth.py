from pydantic import BaseModel, EmailStr, Field


class RegistroAlunoRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    senha: str = Field(..., min_length=6)


class RegistroProfessorRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    senha: str = Field(..., min_length=6)
    departamento: str | None = Field(None, max_length=128)


class LoginRequest(BaseModel):
    email: str
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str
