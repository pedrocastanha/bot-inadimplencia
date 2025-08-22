from fastapi import APIRouter, HTTPException
from schemas import ZApiWebhookPayload, WebhookResponse
from services.agent_service import run_agent
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.put("/webhook", response_model=WebhookResponse)
async def handle_webhook(payload: ZApiWebhookPayload):
  logger.info(f"Webhook recebido para chatId: {payload.chatId}, fromMe: {payload.fromMe}, body: \'{payload.body}\'")

  try:
    agent_response = run_agent(chat_id=payload.chatId, message=payload.body)
    return WebhookResponse(status="success", response=agent_response)
  except Exception as e:
    logger.error(f"Erro ao processar webhook para chatId {payload.chatId}: {e}")
    raise HTTPException(status_code=500, detail="Erro interno ao processar a solicitação.")
