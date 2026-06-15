import base64
import uuid
from pathlib import Path
from app.config import settings


def gerar_txid() -> str:
    return uuid.uuid4().hex[:25]


def gerar_pix_copia_cola(valor: float, txid: str) -> str:
    """Gera o payload PIX no formato EMV (BR Code) para cópia e cola."""
    chave = settings.pix_chave
    nome = settings.pix_nome[:25]
    cidade = settings.pix_cidade[:15]

    def campo(id_: str, val: str) -> str:
        return f"{id_}{len(val):02d}{val}"

    gui = campo("00", "BR.GOV.BCB.PIX")
    chave_f = campo("01", chave)
    mai = campo("26", gui + chave_f)

    txid_limpo = "".join(c for c in txid if c.isalnum())[:25] or "EMPORIO"
    adf = campo("62", campo("05", txid_limpo))

    payload = (
        campo("00", "01")
        + mai
        + campo("52", "0000")
        + campo("53", "986")
        + campo("54", f"{valor:.2f}")
        + campo("58", "BR")
        + campo("59", nome)
        + campo("60", cidade)
        + adf
        + "6304"
    )

    crc = _crc16(payload)
    return payload + f"{crc:04X}"


def _crc16(data: str) -> int:
    """CRC-16/CCITT-FALSE conforme especificação do BR Code."""
    crc = 0xFFFF
    for char in data:
        crc ^= ord(char) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def qrcode_como_base64() -> str | None:
    """Lê o QR code estático e retorna como string base64 para envio via WhatsApp."""
    path = Path(settings.pix_qrcode_path)
    if not path.exists():
        return None
    return base64.b64encode(path.read_bytes()).decode()
