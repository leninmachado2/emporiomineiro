from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Cliente, Pedido, PedidoItem, Produto


def buscar_ou_criar_cliente(
    db: Session, nome: str, telefone: str, ponto_retirada: str
) -> Cliente:
    telefone_limpo = "".join(c for c in telefone if c.isdigit())

    cliente = db.query(Cliente).filter(
        Cliente.telefone_whatsapp == telefone_limpo
    ).first()

    if cliente:
        cliente.nome = nome
        cliente.ponto_retirada_preferido = ponto_retirada
        return cliente

    codigo = _gerar_codigo_cliente(db)
    cliente = Cliente(
        codigo_cliente=codigo,
        nome=nome,
        telefone_whatsapp=telefone_limpo,
        data_cadastro=datetime.now(),
        ponto_retirada_preferido=ponto_retirada,
    )
    db.add(cliente)
    db.flush()
    return cliente


def _gerar_codigo_cliente(db: Session) -> str:
    from sqlalchemy import func, Integer, cast
    ultimo = db.query(func.max(
        cast(func.substr(Cliente.codigo_cliente, 5), Integer)
    )).scalar() or 0
    return f"CDC-{ultimo + 1:05d}"


def criar_pedido(
    db: Session,
    cliente: Cliente,
    carrinho: list[dict],
    ponto_retirada: str,
    data_agendada: datetime | None,
    pix_txid: str,
) -> Pedido:
    pedido = Pedido(
        cliente_id=cliente.id,
        ponto_retirada=ponto_retirada,
        valor_total=0.0,
        data_pedido=datetime.now(),
        data_agendada=data_agendada,
        status_pagamento="AGUARDANDO_PIX",
        status_entrega="RESERVADO",
        pix_txid=pix_txid,
    )
    db.add(pedido)
    db.flush()

    total = 0.0
    for item in carrinho:
        produto = db.get(Produto, item["produto_id"])
        if not produto or produto.quantidade_estoque < item["quantidade"]:
            raise ValueError(f"Estoque insuficiente para {item['nome']}")

        produto.quantidade_estoque -= item["quantidade"]
        subtotal = item["preco"] * item["quantidade"]
        total += subtotal

        db.add(PedidoItem(
            pedido_id=pedido.id,
            produto_id=item["produto_id"],
            nome_produto=item["nome"],
            preco_unitario=item["preco"],
            quantidade=item["quantidade"],
            subtotal=subtotal,
        ))

    pedido.valor_total = total
    return pedido
