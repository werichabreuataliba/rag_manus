from fastapi import FastAPI
from src.app.Controllers import Login, AnalisarController


app = FastAPI(
    title="API de Produção",
    version="1.0.0"
)

app.include_router(Login.router)
app.include_router(AnalisarController.router)