"""
Serviço de gestão de carrinho de compras web.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models import CarrinhoWeb, Produto
import secrets


def gerar_sessao_id() -> str:
    """Gera um ID de sessão único para o carrinho."""
    return secrets.token_urlsafe(32)


def obter_ou_criar_carrinho(db: Session, sessao_id: Optional[str] = None) -> tuple[CarrinhoWeb, str]:
    """Obtém carrinho existente ou cria um novo."""
    if sessao_id:
        carrinho = db.query(CarrinhoWeb).filter(CarrinhoWeb.sessao_id == sessao_id).first()
        if carrinho:
            return carrinho, sessao_id
        # Cria com o mesmo sessao_id passado para manter consistência com o cookie
        carrinho = CarrinhoWeb(sessao_id=sessao_id, itens=[], created_at=datetime.now())
        db.add(carrinho)
        db.commit()
        db.refresh(carrinho)
        return carrinho, sessao_id

    # Nenhum sessao_id fornecido — gera um novo
    novo_sessao_id = gerar_sessao_id()
    carrinho = CarrinhoWeb(sessao_id=novo_sessao_id, itens=[], created_at=datetime.now())
    db.add(carrinho)
    db.commit()
    db.refresh(carrinho)
    return carrinho, novo_sessao_id


def adicionar_item(db: Session, sessao_id: str, produto_id: int, quantidade: int = 1) -> CarrinhoWeb:
    """Adiciona um item ao carrinho."""
    carrinho = db.query(CarrinhoWeb).filter(CarrinhoWeb.sessao_id == sessao_id).first()
    if not carrinho:
        carrinho, _ = obter_ou_criar_carrinho(db, sessao_id)
    
    produto = db.get(Produto, produto_id)
    if not produto:
        raise ValueError("Produto não encontrado")
    
    if produto.quantidade_estoque < quantidade:
        raise ValueError(f"Estoque insuficiente. Disponível: {produto.quantidade_estoque}")
    
    itens = list(carrinho.itens or [])
    
    # Verificar se produto já está no carrinho
    for item in itens:
        if item["produto_id"] == produto_id:
            nova_qtd = item["quantidade"] + quantidade
            if produto.quantidade_estoque < nova_qtd:
                raise ValueError(f"Estoque insuficiente. Disponível: {produto.quantidade_estoque}")
            item["quantidade"] = nova_qtd
            item["subtotal"] = item["preco"] * nova_qtd
            carrinho.itens = itens
            carrinho.updated_at = datetime.now()
            db.commit()
            db.refresh(carrinho)
            return carrinho
    
    # Adicionar novo item
    novo_item = {
        "produto_id": produto_id,
        "nome": produto.nome,
        "preco": produto.preco,
        "quantidade": quantidade,
        "subtotal": produto.preco * quantidade
    }
    itens.append(novo_item)
    carrinho.itens = itens
    carrinho.updated_at = datetime.now()
    db.commit()
    db.refresh(carrinho)
    return carrinho


def remover_item(db: Session, sessao_id: str, produto_id: int) -> CarrinhoWeb:
    """Remove um item do carrinho."""
    carrinho = db.query(CarrinhoWeb).filter(CarrinhoWeb.sessao_id == sessao_id).first()
    if not carrinho:
        raise ValueError("Carrinho não encontrado")
    
    itens = list(carrinho.itens or [])
    itens = [item for item in itens if item["produto_id"] != produto_id]
    carrinho.itens = itens
    carrinho.updated_at = datetime.now()
    db.commit()
    db.refresh(carrinho)
    return carrinho


def atualizar_quantidade(db: Session, sessao_id: str, produto_id: int, quantidade: int) -> CarrinhoWeb:
    """Atualiza a quantidade de um item no carrinho."""
    carrinho = db.query(CarrinhoWeb).filter(CarrinhoWeb.sessao_id == sessao_id).first()
    if not carrinho:
        raise ValueError("Carrinho não encontrado")
    
    if quantidade <= 0:
        return remover_item(db, sessao_id, produto_id)
    
    produto = db.get(Produto, produto_id)
    if not produto:
        raise ValueError("Produto não encontrado")
    
    if produto.quantidade_estoque < quantidade:
        raise ValueError(f"Estoque insuficiente. Disponível: {produto.quantidade_estoque}")
    
    itens = list(carrinho.itens or [])
    for item in itens:
        if item["produto_id"] == produto_id:
            item["quantidade"] = quantidade
            item["subtotal"] = item["preco"] * quantidade
            carrinho.itens = itens
            carrinho.updated_at = datetime.now()
            db.commit()
            db.refresh(carrinho)
            return carrinho
    
    raise ValueError("Produto não encontrado no carrinho")


def limpar_carrinho(db: Session, sessao_id: str) -> CarrinhoWeb:
    """Remove todos os itens do carrinho."""
    carrinho = db.query(CarrinhoWeb).filter(CarrinhoWeb.sessao_id == sessao_id).first()
    if not carrinho:
        raise ValueError("Carrinho não encontrado")
    
    carrinho.itens = []
    carrinho.updated_at = datetime.now()
    db.commit()
    db.refresh(carrinho)
    return carrinho


def calcular_total(itens: list) -> float:
    """Calcula o total do carrinho."""
    return sum(item["subtotal"] for item in itens)


def obter_carrinho_com_total(db: Session, sessao_id: str) -> tuple[CarrinhoWeb, float]:
    """Obtém o carrinho com o total calculado."""
    carrinho = db.query(CarrinhoWeb).filter(CarrinhoWeb.sessao_id == sessao_id).first()
    if not carrinho:
        carrinho, _ = obter_ou_criar_carrinho(db, sessao_id)
    
    total = calcular_total(carrinho.itens or [])
    return carrinho, total