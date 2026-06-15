from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def criar_tabelas():
    # Importar modelos aqui para evitar circular import
    from app.models import Produto, Cliente, Pedido, PedidoItem, SessaoBot, AdminUser, CarrinhoWeb
    Base.metadata.create_all(bind=engine)
