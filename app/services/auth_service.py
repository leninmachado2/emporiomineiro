"""
Serviço de autenticação para administradores.
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
import bcrypt
import hashlib
from itsdangerous import URLSafeTimedSerializer
from app.models import AdminUser
from app.config import settings

# Serializer para tokens de sessão
serializer = URLSafeTimedSerializer(settings.app_port if hasattr(settings, 'secret_key') else "emporio-secret-key-change-in-production")


def hash_senha(senha: str) -> str:
    """Gera hash da senha usando bcrypt."""
    # Truncar senha se for muito longa (bcrypt tem limite de 72 bytes)
    if len(senha.encode('utf-8')) > 72:
        senha = senha[:72]
    senha_bytes = senha.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(senha_bytes, salt)
    return hashed.decode('utf-8')


def verificar_senha(senha: str, hash_senha: str) -> bool:
    """Verifica se a senha corresponde ao hash."""
    try:
        # Truncar senha se for muito longa
        if len(senha.encode('utf-8')) > 72:
            senha = senha[:72]
        senha_bytes = senha.encode('utf-8')
        hash_bytes = hash_senha.encode('utf-8')
        return bcrypt.checkpw(senha_bytes, hash_bytes)
    except Exception:
        return False


def criar_admin_user(db: Session, username: str, senha: str) -> AdminUser:
    """Cria um novo usuário administrativo."""
    senha_hash = hash_senha(senha)
    admin = AdminUser(
        username=username,
        password_hash=senha_hash,
        created_at=datetime.now()
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def autenticar_admin(db: Session, username: str, senha: str) -> Optional[AdminUser]:
    """Autentica um administrativo pelo username e senha."""
    admin = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not admin:
        return None
    if not verificar_senha(senha, admin.password_hash):
        return None
    return admin


def gerar_token_sessao(user_id: int) -> str:
    """Gera um token de sessão para o administrador."""
    return serializer.dumps(str(user_id))


def verificar_token_sessao(token: str, max_age: int = 3600 * 24) -> Optional[int]:
    """Verifica um token de sessão e retorna o user_id se válido."""
    try:
        user_id_str = serializer.loads(token, max_age=max_age)
        return int(user_id_str)
    except Exception:
        return None