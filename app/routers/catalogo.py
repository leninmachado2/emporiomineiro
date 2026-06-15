"""
Router do catálogo web - páginas para clientes visualizarem e comprarem produtos.
"""

from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Produto, Pedido
from app.services import carrinho_service, pedido_service, pagamento_service
from app.services.bot_service import PONTOS_RETIRADA, _proximas_datas_sede_i
from app.templates_html import render_catalogo_index, render_carrinho, render_checkout_sucesso
from app.config import settings

router = APIRouter()
CATEGORIAS = ["Queijos", "Embutidos", "Doces"]

templates = Jinja2Templates(directory="templates")


def get_sessao_id(request: Request) -> str:
    """Obtém ou cria sessao_id do cookie."""
    sessao_id = request.cookies.get("sessao_id")
    if not sessao_id:
        return carrinho_service.gerar_sessao_id()
    return sessao_id


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return RedirectResponse(url="/catalogo", status_code=303)


@router.get("/catalogo", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    """Página inicial do catálogo."""
    produtos_destaque = db.query(Produto).filter(
        Produto.ativo == True,
        Produto.quantidade_estoque > 0
    ).order_by(Produto.preco.desc()).limit(6).all()

    contagem_categorias = {}
    for cat in CATEGORIAS:
        count = db.query(Produto).filter(
            Produto.categoria == cat,
            Produto.ativo == True,
            Produto.quantidade_estoque > 0
        ).count()
        contagem_categorias[cat] = count

    sessao_id = get_sessao_id(request)
    carrinho, total = carrinho_service.obter_carrinho_com_total(db, sessao_id)
    carrinho_itens = len(carrinho.itens or [])

    html = render_catalogo_index(
        request, produtos_destaque, CATEGORIAS, contagem_categorias, carrinho_itens, total
    )
    response = HTMLResponse(content=html)
    response.set_cookie(key="sessao_id", value=sessao_id, max_age=3600 * 24 * 7)
    return response


@router.get("/categoria/{nome}", response_class=HTMLResponse)
async def categoria(nome: str, request: Request, db: Session = Depends(get_db)):
    """Página de produtos por categoria."""
    if nome not in CATEGORIAS:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    produtos = db.query(Produto).filter(
        Produto.categoria == nome,
        Produto.ativo == True,
        Produto.quantidade_estoque > 0
    ).all()

    sessao_id = get_sessao_id(request)
    carrinho, total = carrinho_service.obter_carrinho_com_total(db, sessao_id)

    return templates.TemplateResponse(request, "catalogo/categoria.html", {
        "categoria": nome,
        "produtos": produtos,
        "categorias": CATEGORIAS,
        "carrinho_itens": len(carrinho.itens or []),
        "carrinho_total": total
    })


@router.get("/produto/{id}", response_class=HTMLResponse)
async def produto(id: int, request: Request, db: Session = Depends(get_db)):
    """Página de detalhes do produto."""
    prod = db.get(Produto, id)
    if not prod or not prod.ativo:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    relacionados = db.query(Produto).filter(
        Produto.categoria == prod.categoria,
        Produto.id != id,
        Produto.ativo == True,
        Produto.quantidade_estoque > 0
    ).limit(4).all()

    sessao_id = get_sessao_id(request)
    carrinho, total = carrinho_service.obter_carrinho_com_total(db, sessao_id)

    return templates.TemplateResponse(request, "catalogo/produto.html", {
        "produto": prod,
        "relacionados": relacionados,
        "categorias": CATEGORIAS,
        "carrinho_itens": len(carrinho.itens or []),
        "carrinho_total": total
    })


@router.post("/produto/{produto_id}/adicionar")
async def produto_adicionar(
    produto_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Adiciona produto ao carrinho via botão no catálogo (redireciona)."""
    sessao_id = get_sessao_id(request)
    try:
        carrinho_service.adicionar_item(db, sessao_id, produto_id, 1)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    response = RedirectResponse(url="/catalogo", status_code=303)
    response.set_cookie(key="sessao_id", value=sessao_id, max_age=3600 * 24 * 7)
    return response


@router.post("/carrinho/adicionar")
async def carrinho_adicionar(
    produto_id: int = Form(...),
    quantidade: int = Form(1),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Adiciona item ao carrinho (API AJAX)."""
    sessao_id = get_sessao_id(request)
    try:
        carrinho = carrinho_service.adicionar_item(db, sessao_id, produto_id, quantidade)
        resp = Response(
            content=f'{{"success": true, "itens": {len(carrinho.itens or [])}}}',
            media_type="application/json"
        )
        resp.set_cookie(key="sessao_id", value=sessao_id, max_age=3600 * 24 * 7)
        return resp
    except ValueError as e:
        return Response(
            content=f'{{"success": false, "error": "{e}"}}',
            media_type="application/json",
            status_code=400
        )


@router.post("/carrinho/remover")
async def carrinho_remover(
    produto_id: int = Form(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Remove item do carrinho (API AJAX)."""
    sessao_id = get_sessao_id(request)
    try:
        carrinho = carrinho_service.remover_item(db, sessao_id, produto_id)
        total = carrinho_service.calcular_total(carrinho.itens or [])
        return {"success": True, "itens": len(carrinho.itens or []), "total": total}
    except ValueError as e:
        return {"success": False, "error": str(e)}


@router.post("/carrinho/atualizar")
async def carrinho_atualizar(
    produto_id: int = Form(...),
    quantidade: int = Form(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Atualiza quantidade de item no carrinho (API AJAX)."""
    sessao_id = get_sessao_id(request)
    try:
        carrinho = carrinho_service.atualizar_quantidade(db, sessao_id, produto_id, quantidade)
        total = carrinho_service.calcular_total(carrinho.itens or [])
        return {"success": True, "itens": len(carrinho.itens or []), "total": total}
    except ValueError as e:
        return {"success": False, "error": str(e)}


@router.get("/carrinho", response_class=HTMLResponse)
async def carrinho_view(request: Request, db: Session = Depends(get_db)):
    """Página do carrinho."""
    sessao_id = get_sessao_id(request)
    carrinho, total = carrinho_service.obter_carrinho_com_total(db, sessao_id)

    html = render_carrinho(carrinho.itens or [], total, CATEGORIAS)
    return HTMLResponse(content=html)


@router.get("/checkout", response_class=HTMLResponse)
async def checkout(request: Request, db: Session = Depends(get_db)):
    """Página de checkout."""
    sessao_id = get_sessao_id(request)
    carrinho, total = carrinho_service.obter_carrinho_com_total(db, sessao_id)

    if not carrinho.itens:
        return RedirectResponse(url="/catalogo", status_code=303)

    datas_sede_i = _proximas_datas_sede_i()

    return templates.TemplateResponse(request, "catalogo/checkout.html", {
        "itens": carrinho.itens,
        "total": total,
        "pontos_retirada": PONTOS_RETIRADA,
        "datas_sede_i": datas_sede_i,
        "categorias": CATEGORIAS,
        "carrinho_itens": len(carrinho.itens or []),
        "carrinho_total": total
    })


@router.post("/checkout")
async def processar_checkout(
    nome: str = Form(...),
    telefone: str = Form(...),
    ponto_retirada: str = Form(...),
    data_retirada: Optional[str] = Form(None),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Processa o checkout, cria pedido e retorna PIX payload como JSON."""
    sessao_id = get_sessao_id(request)
    carrinho, total = carrinho_service.obter_carrinho_com_total(db, sessao_id)

    if not carrinho.itens:
        return {"success": False, "error": "Carrinho vazio"}

    data_agendada = None
    if data_retirada and data_retirada.strip():
        try:
            data_agendada = datetime.combine(
                date.fromisoformat(data_retirada), datetime.min.time()
            )
        except ValueError:
            return {"success": False, "error": "Data de retirada inválida"}

    txid = pagamento_service.gerar_txid()

    try:
        cliente = pedido_service.buscar_ou_criar_cliente(
            db, nome=nome, telefone=telefone, ponto_retirada=ponto_retirada
        )
        pedido = pedido_service.criar_pedido(
            db=db,
            cliente=cliente,
            carrinho=carrinho.itens,
            ponto_retirada=ponto_retirada,
            data_agendada=data_agendada,
            pix_txid=txid
        )

        carrinho_service.limpar_carrinho(db, sessao_id)
        db.commit()

        pix_payload = pagamento_service.gerar_pix_copia_cola(total, txid)

        return {
            "success": True,
            "pedido_id": pedido.id,
            "total": total,
            "pix_payload": pix_payload,
            "pix_chave": settings.pix_chave
        }
    except ValueError as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    except Exception:
        db.rollback()
        return {"success": False, "error": "Erro interno ao processar pedido"}


@router.get("/checkout/sucesso/{pedido_id}", response_class=HTMLResponse)
async def checkout_sucesso(pedido_id: int, request: Request, db: Session = Depends(get_db)):
    """Página de confirmação após pagamento PIX."""
    pedido = db.get(Pedido, pedido_id)
    if not pedido:
        return RedirectResponse(url="/catalogo", status_code=303)

    pix_payload = pagamento_service.gerar_pix_copia_cola(pedido.valor_total, pedido.pix_txid)
    data_str = (
        pedido.data_agendada.strftime("%d/%m/%Y") if pedido.data_agendada else "A confirmar"
    )

    html = render_checkout_sucesso(
        pedido.id, pix_payload, pedido.valor_total, data_str, pedido.ponto_retirada
    )
    return HTMLResponse(content=html)
