from datetime import time, datetime

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
from fastapi import APIRouter

from src.app.HELPERS.Chaves import chave_secreta_manus
from src.app.Services.RAG_Services import carregar_dados, carregar_chunks, carregar_embeddings, carregar_vectorstore, \
    carregar_retriever, carregar_consulta, analisar_manus

# USUARIO = usuario_rag_manus
# SENHA = senha_manus
SECRET_KEY = chave_secreta_manus
ALGORITHM = "HS256"

security = HTTPBearer()

# app = FastAPI()
router = APIRouter()

documentos = carregar_dados()
chunks = carregar_chunks(documentos)
embeddings = carregar_embeddings()
vectorstore = carregar_vectorstore(chunks, embeddings)
retriever = carregar_retriever(vectorstore)

class DadosProducao(BaseModel):
    pecas_boas: int
    refugos: int
    total_produzido: int

def validar_token(
    credenciais: HTTPAuthorizationCredentials = Depends(security)
):
    token = credenciais.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expirado"
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )

@router.post("/analisar_pecas")
def analisar(dados: DadosProducao,
             usuario=Depends(validar_token)):
    print("Dados recebidos:", flush=True)
    print(dados, flush=True)

    inicio = datetime.now()

    try:

        print("Executando análise com Manus...", flush=True)

        result = analisar_manus(
            dados,
            retriever
        )

        provedor = "MANUS"

        print("Manus respondeu com sucesso.", flush=True)

    except Exception as e:

        print(
            f"Manus indisponível: {e}",
            flush=True
        )

        print(
            "Executando fallback para Groq...",
            flush=True
        )

        result = carregar_consulta(
            dados,
            retriever
        )

        provedor = "GROQ"

    tempo = datetime.now() - inicio
    tempo = "".join(f"{tempo} segundos")

    print(
        f"Tempo de execução: {tempo}",
        flush=True
    )

    return {
        "status": "recebido",
        "tempo_ext_exec": tempo,
        "usuario": usuario["sub"],
        "provedor": provedor,
        "dados": dados,
        "resultado": result
    }
    # print("Dados recebidos:", flush=True)
    # print(f"\n{dados}\n", flush=True)
    #
    # #Metodo reponsvael por consultar LLM do GRoq
    # # result = carregar_consulta(dados, retriever)
    # # print("\nRESULTADO LLM GROQ:")
    # # print(f"\n{result}")
    # # print("=" * 70)
    # #Metodo reposnavel por utilizar o agente MAnus(que insiste não funcionar via API)
    #
    # inicio = datetime.now()
    #
    # print("\nRESULTADO LLM MANUS:", flush=True)
    # result = analisar_manus(dados, retriever)
    # termino = datetime.now() - inicio
    # print(f"Tempo de execução:{termino}", flush=True)
    #
    # return {
    #     "status": "recebido",
    #     "usuario": usuario["sub"],
    #     "dados": dados,
    #     "resultado": result
    # }