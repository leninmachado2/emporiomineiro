import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import criar_tabelas
from app.routers import webhook, catalogo, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    criar_tabelas()
    logging.getLogger(__name__).info("Tabelas criadas. Bot pronto. 🧀")
    yield


app = FastAPI(
    title="Empório Canastra — Bot WhatsApp",
    description="Bot de vendas via WhatsApp com PIX integrado e catálogo web.",
    version="2.0.0",
    lifespan=lifespan,
)

# Servir arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Incluir routers
app.include_router(webhook.router)
app.include_router(catalogo.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
