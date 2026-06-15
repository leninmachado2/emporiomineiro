from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    categoria: Mapped[str] = mapped_column(String(100), nullable=False)
    preco: Mapped[float] = mapped_column(Float, nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(String(500))
    quantidade_estoque: Mapped[int] = mapped_column(Integer, default=0)
    caminho_imagem: Mapped[Optional[str]] = mapped_column(String(300))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo_cliente: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    telefone_whatsapp: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    data_cadastro: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    ponto_retirada_preferido: Mapped[Optional[str]] = mapped_column(String(50))

    pedidos: Mapped[list["Pedido"]] = relationship(
        "Pedido", back_populates="cliente", cascade="all, delete-orphan"
    )


class Pedido(Base):
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), nullable=False)
    ponto_retirada: Mapped[str] = mapped_column(String(50), nullable=False)
    valor_total: Mapped[float] = mapped_column(Float, nullable=False)
    data_pedido: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    data_agendada: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status_pagamento: Mapped[str] = mapped_column(String(30), default="AGUARDANDO_PIX")
    status_entrega: Mapped[str] = mapped_column(String(30), default="RESERVADO")
    contador_faltas: Mapped[int] = mapped_column(Integer, default=0)
    pix_txid: Mapped[Optional[str]] = mapped_column(String(100))

    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="pedidos")
    itens: Mapped[list["PedidoItem"]] = relationship(
        "PedidoItem", back_populates="pedido", cascade="all, delete-orphan"
    )


class PedidoItem(Base):
    __tablename__ = "pedido_itens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"), nullable=False)
    produto_id: Mapped[int] = mapped_column(Integer, nullable=False)
    nome_produto: Mapped[str] = mapped_column(String(200), nullable=False)
    preco_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)

    pedido: Mapped["Pedido"] = relationship("Pedido", back_populates="itens")


class SessaoBot(Base):
    """Estado da conversa de cada cliente no WhatsApp."""

    __tablename__ = "sessoes_bot"

    telefone: Mapped[str] = mapped_column(String(20), primary_key=True)
    nome_push: Mapped[Optional[str]] = mapped_column(String(200))
    estado: Mapped[str] = mapped_column(String(50), default="MENU")
    # [{produto_id, nome, preco, quantidade}]
    carrinho: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    # dados temporários coletados durante o fluxo de pedido
    dados_temp: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    ultima_atividade: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class AdminUser(Base):
    """Usuários administrativos do painel web."""

    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class CarrinhoWeb(Base):
    """Carrinho de compras web (sessão-based)."""

    __tablename__ = "carrinhos_web"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sessao_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    # [{produto_id, nome, preco, quantidade}]
    itens: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
