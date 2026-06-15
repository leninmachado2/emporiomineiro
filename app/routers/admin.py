"""
Router do painel administrativo - gestão de produtos e pedidos.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Produto, Pedido, PedidoItem, Cliente, AdminUser
from app.services import auth_service
from app.templates_html import render_admin_login, render_admin_dashboard, render_admin_produtos, render_produto_form
import shutil
import os
from pathlib import Path

router = APIRouter()

# Templates será injetado pelo main.py (se necessário)
templates = None


def get_current_admin(request: Request) -> Optional[AdminUser]:
    """Verifica se há um admin logado via cookie."""
    token = request.cookies.get("admin_token")
    if not token:
        return None
    user_id = auth_service.verificar_token_sessao(token)
    if not user_id:
        return None
    
    # Aqui você precisaria do banco de dados, mas vamos simplificar
    # Na prática, você injetaria o db aqui também
    return {"id": user_id}  # Simplificado


def require_admin(request: Request, db: Session = Depends(get_db)) -> AdminUser:
    """Middleware que requer login de admin."""
    token = request.cookies.get("admin_token")
    if not token:
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})
    
    user_id = auth_service.verificar_token_sessao(token)
    if not user_id:
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})
    
    admin = db.get(AdminUser, user_id)
    if not admin:
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})
    
    return admin


@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login(request: Request):
    """Página de login do admin."""
    html = render_admin_login()
    return HTMLResponse(content=html)


@router.post("/admin/login")
async def admin_login_post(
    username: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Processa login do admin."""
    admin = auth_service.autenticar_admin(db, username, senha)
    if not admin:
        html = render_admin_login("Credenciais inválidas!")
        return HTMLResponse(content=html)
    
    token = auth_service.gerar_token_sessao(admin.id)
    response = RedirectResponse(url="/admin/dashboard", status_code=303)
    response.set_cookie(key="admin_token", value=token, max_age=3600 * 24)
    return response


@router.get("/admin/logout")
async def admin_logout():
    """Logout do admin."""
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie(key="admin_token")
    return response


@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    admin: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Dashboard do admin."""
    # Estatísticas
    hoje = datetime.now().date()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    
    vendas_hoje = db.query(func.sum(Pedido.valor_total)).filter(
        Pedido.data_pedido >= datetime.combine(hoje, datetime.min.time()),
        Pedido.status_pagamento == "PAGO"
    ).scalar() or 0
    
    vendas_semana = db.query(func.sum(Pedido.valor_total)).filter(
        Pedido.data_pedido >= datetime.combine(inicio_semana, datetime.min.time()),
        Pedido.status_pagamento == "PAGO"
    ).scalar() or 0
    
    pedidos_pendentes = db.query(Pedido).filter(
        Pedido.status_pagamento == "AGUARDANDO_PIX"
    ).count()
    
    pedidos_hoje = db.query(Pedido).filter(
        Pedido.data_pedido >= datetime.combine(hoje, datetime.min.time())
    ).count()
    
    html = render_admin_dashboard(
        admin, vendas_hoje, vendas_semana, pedidos_pendentes, pedidos_hoje
    )
    return HTMLResponse(content=html)


@router.get("/admin/produtos", response_class=HTMLResponse)
async def admin_produtos(
    request: Request,
    admin: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Lista de produtos."""
    produtos = db.query(Produto).order_by(Produto.categoria, Produto.nome).all()
    html = render_admin_produtos(produtos)
    return HTMLResponse(content=html)


@router.get("/admin/produtos/novo", response_class=HTMLResponse)
async def admin_produto_novo(
    request: Request,
    admin: AdminUser = Depends(require_admin)
):
    """Formulário de novo produto."""
    html = render_produto_form(categorias=["Queijos", "Embutidos", "Doces"])
    return HTMLResponse(content=html)


@router.post("/admin/produtos/novo")
async def admin_produto_criar(
    nome: str = Form(...),
    categoria: str = Form(...),
    preco: float = Form(...),
    quantidade_estoque: int = Form(...),
    descricao: str = Form(""),
    imagem: UploadFile = File(None),
    ativo: bool = Form(True),
    admin: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Cria novo produto."""
    imagem_url = None
    
    if imagem and imagem.filename:
        # Criar diretório se não existir
        upload_dir = Path("static/img/produtos")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Gerar nome seguro
        filename = f"{int(datetime.now().timestamp())}_{imagem.filename}"
        file_path = upload_dir / filename
        
        # Salvar arquivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(imagem.file, buffer)
        
        imagem_url = f"/static/img/produtos/{filename}"
    
    produto = Produto(
        nome=nome,
        categoria=categoria,
        preco=preco,
        descricao=descricao,
        quantidade_estoque=quantidade_estoque,
        caminho_imagem=imagem_url,
        ativo=ativo
    )
    
    db.add(produto)
    db.commit()
    
    return RedirectResponse(url="/admin/produtos", status_code=303)


@router.get("/admin/produtos/{id}/editar", response_class=HTMLResponse)
async def admin_produto_editar(
    id: int,
    request: Request,
    admin: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Formulário de edição de produto."""
    produto = db.get(Produto, id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    html = render_produto_form(produto=produto, categorias=["Queijos", "Embutidos", "Doces"])
    return HTMLResponse(content=html)


@router.post("/admin/produtos/{id}/editar")
async def admin_produto_atualizar(
    id: int,
    nome: str = Form(...),
    categoria: str = Form(...),
    preco: float = Form(...),
    quantidade_estoque: int = Form(...),
    descricao: str = Form(""),
    ativo: bool = Form(False),
    imagem: UploadFile = File(None),
    admin: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Atualiza produto."""
    produto = db.get(Produto, id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    produto.nome = nome
    produto.categoria = categoria
    produto.preco = preco
    produto.quantidade_estoque = quantidade_estoque
    produto.descricao = descricao
    produto.ativo = ativo
    
    if imagem and imagem.filename:
        # Criar diretório se não existir
        upload_dir = Path("static/img/produtos")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Gerar nome seguro
        filename = f"{int(datetime.now().timestamp())}_{imagem.filename}"
        file_path = upload_dir / filename
        
        # Salvar arquivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(imagem.file, buffer)
        
        # Remover imagem antiga se existir
        if produto.caminho_imagem:
            old_path = Path(produto.caminho_imagem.lstrip('/'))
            if old_path.exists():
                old_path.unlink()
        
        produto.caminho_imagem = f"/static/img/produtos/{filename}"
    
    db.commit()
    
    return RedirectResponse(url="/admin/produtos", status_code=303)


@router.post("/admin/produtos/{id}/deletar")
async def admin_produto_deletar(
    id: int,
    admin: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Deleta produto."""
    produto = db.get(Produto, id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    # Remover imagem se existir
    if produto.caminho_imagem:
        image_path = Path(produto.caminho_imagem.lstrip('/'))
        if image_path.exists():
            image_path.unlink()
    
    db.delete(produto)
    db.commit()
    
    return RedirectResponse(url="/admin/produtos", status_code=303)


@router.get("/admin/pedidos", response_class=HTMLResponse)
async def admin_pedidos(
    request: Request,
    admin: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Lista de pedidos."""
    pedidos = db.query(Pedido).order_by(Pedido.data_pedido.desc()).all()
    return templates.TemplateResponse(request, "admin/pedidos.html", {
        "admin": admin,
        "pedidos": pedidos
    })


@router.get("/admin/pedidos/{id}", response_class=HTMLResponse)
async def admin_pedido_detalhes(
    id: int,
    request: Request,
    admin: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Detalhes do pedido."""
    pedido = db.get(Pedido, id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    return templates.TemplateResponse(request, "admin/pedido_detalhes.html", {
        "admin": admin,
        "pedido": pedido
    })


@router.post("/admin/pedidos/{id}/status")
async def admin_pedido_status(
    id: int,
    status_pagamento: str = Form(...),
    status_entrega: str = Form(...),
    admin: AdminUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Atualiza status do pedido."""
    pedido = db.get(Pedido, id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    pedido.status_pagamento = status_pagamento
    pedido.status_entrega = status_entrega
    db.commit()
    
    return RedirectResponse(url=f"/admin/pedidos/{id}", status_code=303)