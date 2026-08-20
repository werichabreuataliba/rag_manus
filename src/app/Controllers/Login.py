from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter
from src.app.HELPERS.Chaves import chave_secreta_manus, senha_manus, usuario_rag_manus

router = APIRouter()

SECRET_KEY = chave_secreta_manus
ALGORITHM = "HS256"


# Objeto Login
class Login(BaseModel):
    usuario: str
    senha: str


# Usuário fictício para teste
USUARIO = usuario_rag_manus
SENHA = senha_manus


@router.post("/login")
def login(dados: Login):

    # Validação do usuário
    if dados.usuario != USUARIO or dados.senha != SENHA:
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha inválidos"
        )

    # Expiração do token: 30 minutos
    expiracao = datetime.now(timezone.utc) + timedelta(minutes=30)

    payload = {
        "sub": dados.usuario,
        "exp": expiracao
    }

    # Geração do JWT
    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }