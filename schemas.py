from pydantic import BaseModel
from typing import Optional

class Sender(BaseModel):
    name: Optional[str] = None
    isMyContact: Optional[bool] = None

class ZApiWebhookPayload(BaseModel):
    messageId: str
    timestamp: int
    chatId: str
    fromMe: bool
    body: str
    author: Optional[str] = None
    type: str
    sender: Optional[Sender] = None

class WebhookResponse(BaseModel):
    status: str
    response: Optional[str] = None
