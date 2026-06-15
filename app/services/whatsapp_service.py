import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

_BASE = "{url}/message/{endpoint}/{instance}"


def _url(endpoint: str) -> str:
    return _BASE.format(
        url=settings.evolution_api_url,
        endpoint=endpoint,
        instance=settings.evolution_instance,
    )


def _headers() -> dict:
    return {"apikey": settings.evolution_api_key, "Content-Type": "application/json"}


async def enviar_texto(telefone: str, texto: str) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(
                _url("sendText"),
                headers=_headers(),
                json={"number": telefone, "text": texto},
            )
        except Exception as e:
            logger.error("Erro ao enviar texto para %s: %s", telefone, e)


async def enviar_imagem(telefone: str, base64_str: str, legenda: str = "") -> None:
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            await client.post(
                _url("sendMedia"),
                headers=_headers(),
                json={
                    "number": telefone,
                    "mediatype": "image",
                    "caption": legenda,
                    "media": f"data:image/png;base64,{base64_str}",
                },
            )
        except Exception as e:
            logger.error("Erro ao enviar imagem para %s: %s", telefone, e)


async def enviar_lista(telefone: str, titulo: str, corpo: str, botao: str, secoes: list) -> None:
    """Envia uma lista interativa do WhatsApp (melhor UX para menus)."""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(
                _url("sendList"),
                headers=_headers(),
                json={
                    "number": telefone,
                    "title": titulo,
                    "description": corpo,
                    "buttonText": botao,
                    "sections": secoes,
                },
            )
        except Exception as e:
            # Lista interativa pode não ser suportada em todos os clientes; cai para texto
            logger.warning("Lista interativa falhou (%s), usando texto simples.", e)
