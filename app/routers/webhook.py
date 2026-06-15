import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import bot_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _extrair_texto(message: dict) -> str | None:
    """Extrai o texto de uma mensagem do WhatsApp independente do tipo."""
    return (
        message.get("conversation")
        or message.get("extendedTextMessage", {}).get("text")
        or message.get("imageMessage", {}).get("caption")
        or None
    )


@router.post("/webhook/whatsapp")
async def receber_mensagem(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        return {"status": "ignored"}

    event = payload.get("event", "")
    if event != "messages.upsert":
        return {"status": "ignored"}

    data = payload.get("data", {})
    key = data.get("key", {})

    # Ignorar mensagens enviadas pelo próprio bot e mensagens de grupo
    if key.get("fromMe"):
        return {"status": "ignored"}
    remote_jid = key.get("remoteJid", "")
    if "@g.us" in remote_jid:
        return {"status": "ignored"}

    telefone = remote_jid.replace("@s.whatsapp.net", "")
    nome_push = data.get("pushName", "")
    message = data.get("message", {})
    texto = _extrair_texto(message)

    if not texto or not telefone:
        return {"status": "ignored"}

    logger.info("Mensagem de %s (%s): %s", telefone, nome_push, texto[:80])

    await bot_service.processar_mensagem(db, telefone, texto, nome_push)
    return {"status": "ok"}
