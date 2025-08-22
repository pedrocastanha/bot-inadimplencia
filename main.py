import logging
from fastapi import FastAPI
from api.router import webhook_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Bot de Cobrança de Inadimplência",
    description="API para processar mensagens de inadimplência via webhook e gerenciar interações com agente LangChain",
    version="1.0.0"
)

app.include_router(webhook_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    logger.info("Aplicação iniciada. Inicializando serviços...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Aplicação encerrada. Finalizando serviços...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
