from fastapi import APIRouter, HTTPException
from schemas import ZApiWebhookPayload, WebhookResponse
from services.agent_service import run_agent
import logging

webhook_router = APIRouter()
logger = logging.getLogger(__name__)

@webhook_router.put("/webhook", response_model=WebhookResponse)
async def handle_webhook(payload: ZApiWebhookPayload):
  logger.info(f"Webhook recebido para chatId: {payload.chatId}, fromMe: {payload.fromMe}, body: \'{payload.body}\'")

  if payload.fromMe:
    logger.info(f"Ignorando mensagem enviada pelo bot para chatId: {payload.chatId}")
    return WebhookResponse(status="ignored", response="Mensagem enviada pelo bot, ignorada.")

  try:
    agent_response = await run_agent(chat_id=payload.chatId, message=payload.body)
    return WebhookResponse(status="success", response=agent_response)
  except Exception as e:
    logger.error(f"Erro ao processar webhook para chatId {payload.chatId}: {e}")
    raise HTTPException(status_code=500, detail="Erro interno ao processar a solicitação.")
