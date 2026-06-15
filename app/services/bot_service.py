"""
Máquina de estados da conversa do bot Empório Canastra no WhatsApp.

Estados:
  MENU              → menu principal
  CATALOGO          → escolha de categoria
  PRODUTOS          → lista produtos da categoria
  QUANTIDADE        → aguarda quantidade do item selecionado
  CARRINHO          → opções do carrinho (continuar / finalizar / limpar)
  AGUARDANDO_NOME   → coleta nome do cliente
  AGUARDANDO_PONTO  → coleta ponto de retirada
  AGUARDANDO_DATA   → coleta data (só Sede I)
  CONFIRMACAO       → resumo do pedido para aprovação
  PAGAMENTO         → pedido criado, aguardando pagamento
"""

import logging
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

from app.models import Produto, SessaoBot
from app.config import settings
from app.services import pagamento_service, pedido_service, whatsapp_service

logger = logging.getLogger(__name__)

# ── Constantes ────────────────────────────────────────────────────────────────

PONTOS_RETIRADA = ["BB Sede I", "BB Sede III"]
DIAS_SEDE_I = {2, 3, 4}  # quarta, quinta, sexta (weekday: 0=seg)

MENU_TEXT = (
    "Olá{nome}! 👋 Bem-vindo ao *Empório Canastra*! 🧀\n\n"
    "O que deseja fazer?\n\n"
    "1️⃣  Ver catálogo web 🛒\n"
    "2️⃣  Ver status do pedido 📋\n"
    "0️⃣  Falar com atendente 📞"
)

CATEGORIAS = ["Queijos", "Embutidos", "Doces"]

REINICIAR_PALAVRAS = {"oi", "olá", "ola", "menu", "início", "inicio", "voltar", "cancelar"}


# ── Entrada pública ───────────────────────────────────────────────────────────

async def processar_mensagem(
    db: Session, telefone: str, texto: str, nome_push: str
) -> None:
    texto = texto.strip()

    sessao = _get_ou_criar_sessao(db, telefone, nome_push)
    sessao.ultima_atividade = datetime.now()

    if texto.lower() in REINICIAR_PALAVRAS:
        await _ir_para_menu(db, sessao)
        return

    handlers = {
        "MENU": _handle_menu,
        "CATALOGO": _handle_catalogo,
        "PRODUTOS": _handle_produtos,
        "QUANTIDADE": _handle_quantidade,
        "CARRINHO": _handle_carrinho,
        "AGUARDANDO_NOME": _handle_nome,
        "AGUARDANDO_PONTO": _handle_ponto,
        "AGUARDANDO_DATA": _handle_data,
        "CONFIRMACAO": _handle_confirmacao,
        "PAGAMENTO": _handle_pagamento,
    }

    handler = handlers.get(sessao.estado, _handle_menu)
    await handler(db, sessao, texto)


# ── Helpers de sessão ─────────────────────────────────────────────────────────

def _get_ou_criar_sessao(db: Session, telefone: str, nome_push: str) -> SessaoBot:
    sessao = db.get(SessaoBot, telefone)
    if not sessao:
        sessao = SessaoBot(
            telefone=telefone,
            nome_push=nome_push,
            estado="MENU",
            carrinho=[],
            dados_temp={},
        )
        db.add(sessao)
        db.flush()
    else:
        sessao.nome_push = nome_push
    return sessao


def _set_estado(sessao: SessaoBot, estado: str) -> None:
    sessao.estado = estado


# ── Helpers de formatação ─────────────────────────────────────────────────────

def _formatar_carrinho(carrinho: list) -> str:
    if not carrinho:
        return "Seu carrinho está vazio."
    linhas = ["🛒 *Seu carrinho:*\n"]
    total = 0.0
    for i, item in enumerate(carrinho, 1):
        subtotal = item["preco"] * item["quantidade"]
        total += subtotal
        linhas.append(f"{i}. {item['nome']} x{item['quantidade']} — R$ {subtotal:.2f}")
    linhas.append(f"\n💰 *Total: R$ {total:.2f}*")
    return "\n".join(linhas)


def _proximas_datas_sede_i(n: int = 5) -> list[date]:
    datas = []
    d = date.today() + timedelta(days=1)
    while len(datas) < n:
        if d.weekday() in DIAS_SEDE_I:
            datas.append(d)
        d += timedelta(days=1)
    return datas


def _formatar_data(d: date) -> str:
    dias_pt = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    return f"{dias_pt[d.weekday()]} {d.strftime('%d/%m')}"


# ── Handlers de estado ────────────────────────────────────────────────────────

async def _ir_para_menu(db: Session, sessao: SessaoBot) -> None:
    _set_estado(sessao, "MENU")
    nome = f", {sessao.nome_push}" if sessao.nome_push else ""
    await whatsapp_service.enviar_texto(
        sessao.telefone, MENU_TEXT.format(nome=nome)
    )


async def _handle_menu(db: Session, sessao: SessaoBot, texto: str) -> None:
    if texto == "1":
        # Enviar link do catálogo web
        from app.config import settings
        url_catalogo = f"http://localhost:{settings.app_port}/"
        await whatsapp_service.enviar_texto(
            sessao.telefone,
            f"🛒 *Acesse nosso catálogo web!*\n\n"
            f"📲 {url_catalogo}\n\n"
            f"No site você pode ver fotos dos produtos, montar seu carrinho "
            f"e escolher o dia de retirada (qua/qui/sex) na BB Sede I.\n\n"
            f"0️⃣  Voltar ao menu"
        )
    elif texto == "2":
        # Ver status do pedido (simplificado por enquanto)
        await whatsapp_service.enviar_texto(
            sessao.telefone,
            "📋 Para verificar o status do seu pedido, por favor forneça o número do pedido "
            "ou aguarde, estamos implementando esta funcionalidade.\n\n"
            "0️⃣  Voltar ao menu"
        )
    elif texto == "0":
        await whatsapp_service.enviar_texto(
            sessao.telefone,
            "📞 Aguarde, um atendente entrará em contato em breve!"
        )
    else:
        await _ir_para_menu(db, sessao)


async def _handle_catalogo(db: Session, sessao: SessaoBot, texto: str) -> None:
    if texto == "0":
        await _ir_para_menu(db, sessao)
        return

    try:
        idx = int(texto) - 1
        categoria = CATEGORIAS[idx]
    except (ValueError, IndexError):
        await whatsapp_service.enviar_texto(
            sessao.telefone, "Digite o número da categoria ou *0* para voltar."
        )
        return

    produtos = (
        db.query(Produto)
        .filter(Produto.categoria == categoria, Produto.ativo == True, Produto.quantidade_estoque > 0)
        .all()
    )

    if not produtos:
        await whatsapp_service.enviar_texto(
            sessao.telefone, f"😔 Não há produtos disponíveis em *{categoria}* no momento."
        )
        return

    linhas = [f"🧀 *{categoria.upper()}*\n"]
    for i, p in enumerate(produtos, 1):
        linhas.append(f"{i}. *{p.nome}* — R$ {p.preco:.2f}")
        if p.descricao:
            linhas.append(f"   _{p.descricao}_")
    linhas.append("\nDigite o *número* do produto para adicionar ao carrinho.")
    linhas.append("0️⃣  Voltar às categorias")

    dados = sessao.dados_temp or {}
    dados["categoria"] = categoria
    dados["produtos_ids"] = [p.id for p in produtos]
    sessao.dados_temp = dados

    _set_estado(sessao, "PRODUTOS")
    await whatsapp_service.enviar_texto(sessao.telefone, "\n".join(linhas))


async def _handle_produtos(db: Session, sessao: SessaoBot, texto: str) -> None:
    if texto == "0":
        _set_estado(sessao, "CATALOGO")
        cats = "\n".join(f"{i+1}️⃣  {c}" for i, c in enumerate(CATEGORIAS))
        await whatsapp_service.enviar_texto(
            sessao.telefone,
            f"📦 *Escolha uma categoria:*\n\n{cats}\n\n0️⃣  Voltar ao menu"
        )
        return

    ids = (sessao.dados_temp or {}).get("produtos_ids", [])
    try:
        idx = int(texto) - 1
        produto_id = ids[idx]
    except (ValueError, IndexError):
        await whatsapp_service.enviar_texto(
            sessao.telefone, "Digite o número do produto ou *0* para voltar."
        )
        return

    produto = db.get(Produto, produto_id)
    if not produto:
        await whatsapp_service.enviar_texto(sessao.telefone, "Produto não encontrado.")
        return

    dados = sessao.dados_temp or {}
    dados["produto_selecionado"] = {
        "produto_id": produto.id,
        "nome": produto.nome,
        "preco": produto.preco,
    }
    sessao.dados_temp = dados

    _set_estado(sessao, "QUANTIDADE")
    await whatsapp_service.enviar_texto(
        sessao.telefone,
        f"Quantas unidades de *{produto.nome}* (R$ {produto.preco:.2f} cada)?\n\n"
        f"Estoque disponível: {produto.quantidade_estoque} un.\n\n"
        "0️⃣  Cancelar"
    )


async def _handle_quantidade(db: Session, sessao: SessaoBot, texto: str) -> None:
    if texto == "0":
        _set_estado(sessao, "PRODUTOS")
        await whatsapp_service.enviar_texto(
            sessao.telefone, "Ok! Escolha outro produto ou *0* para voltar às categorias."
        )
        return

    try:
        qtd = int(texto)
        if qtd <= 0:
            raise ValueError
    except ValueError:
        await whatsapp_service.enviar_texto(
            sessao.telefone, "Por favor, informe uma quantidade válida (número inteiro positivo)."
        )
        return

    produto_sel = (sessao.dados_temp or {}).get("produto_selecionado")
    if not produto_sel:
        await _ir_para_menu(db, sessao)
        return

    produto = db.get(Produto, produto_sel["produto_id"])
    if not produto or produto.quantidade_estoque < qtd:
        await whatsapp_service.enviar_texto(
            sessao.telefone,
            f"😔 Estoque insuficiente. Disponível: {produto.quantidade_estoque if produto else 0} un."
        )
        return

    carrinho = list(sessao.carrinho or [])
    for item in carrinho:
        if item["produto_id"] == produto_sel["produto_id"]:
            item["quantidade"] += qtd
            break
    else:
        carrinho.append({**produto_sel, "quantidade": qtd})
    sessao.carrinho = carrinho

    _set_estado(sessao, "CARRINHO")
    await whatsapp_service.enviar_texto(
        sessao.telefone,
        f"✅ *{produto_sel['nome']}* x{qtd} adicionado!\n\n"
        + _formatar_carrinho(carrinho)
        + "\n\nO que deseja?\n\n1️⃣  Continuar comprando\n2️⃣  Finalizar pedido\n3️⃣  Limpar carrinho"
    )


async def _handle_carrinho(db: Session, sessao: SessaoBot, texto: str) -> None:
    if texto == "1":
        _set_estado(sessao, "CATALOGO")
        cats = "\n".join(f"{i+1}️⃣  {c}" for i, c in enumerate(CATEGORIAS))
        await whatsapp_service.enviar_texto(
            sessao.telefone,
            f"📦 *Escolha uma categoria:*\n\n{cats}\n\n0️⃣  Voltar ao menu"
        )
    elif texto == "2":
        if not sessao.carrinho:
            await whatsapp_service.enviar_texto(
                sessao.telefone, "Seu carrinho está vazio. Adicione produtos antes de finalizar."
            )
            return
        _set_estado(sessao, "AGUARDANDO_NOME")
        nome_salvo = (sessao.dados_temp or {}).get("nome_salvo", "")
        dica = f" (último: *{nome_salvo}*, pressione 1 para usar)" if nome_salvo else ""
        await whatsapp_service.enviar_texto(
            sessao.telefone,
            f"📝 Para finalizar, preciso de alguns dados.\n\nQual é o seu *nome completo*?{dica}"
        )
    elif texto == "3":
        sessao.carrinho = []
        await whatsapp_service.enviar_texto(
            sessao.telefone, "🗑️ Carrinho limpo! Voltando ao menu..."
        )
        await _ir_para_menu(db, sessao)
    else:
        await whatsapp_service.enviar_texto(
            sessao.telefone,
            "1️⃣  Continuar comprando\n2️⃣  Finalizar pedido\n3️⃣  Limpar carrinho"
        )


async def _handle_nome(db: Session, sessao: SessaoBot, texto: str) -> None:
    dados = sessao.dados_temp or {}
    nome_salvo = dados.get("nome_salvo", "")

    if texto == "1" and nome_salvo:
        nome = nome_salvo
    elif len(texto) < 3:
        await whatsapp_service.enviar_texto(
            sessao.telefone, "Por favor, informe seu nome completo."
        )
        return
    else:
        nome = texto.title()

    dados["nome"] = nome
    dados["nome_salvo"] = nome
    sessao.dados_temp = dados

    _set_estado(sessao, "AGUARDANDO_PONTO")
    pontos = "\n".join(f"{i+1}️⃣  {p}" for i, p in enumerate(PONTOS_RETIRADA))
    await whatsapp_service.enviar_texto(
        sessao.telefone,
        f"📍 Qual o ponto de retirada, *{nome}*?\n\n{pontos}"
    )


async def _handle_ponto(db: Session, sessao: SessaoBot, texto: str) -> None:
    try:
        idx = int(texto) - 1
        ponto = PONTOS_RETIRADA[idx]
    except (ValueError, IndexError):
        pontos = "\n".join(f"{i+1}️⃣  {p}" for i, p in enumerate(PONTOS_RETIRADA))
        await whatsapp_service.enviar_texto(
            sessao.telefone, f"Escolha um ponto de retirada:\n\n{pontos}"
        )
        return

    dados = sessao.dados_temp or {}
    dados["ponto_retirada"] = ponto
    sessao.dados_temp = dados

    if ponto == "BB Sede I":
        datas = _proximas_datas_sede_i()
        dados["datas_disponiveis"] = [str(d) for d in datas]
        sessao.dados_temp = dados
        opcoes = "\n".join(f"{i+1}️⃣  {_formatar_data(d)}" for i, d in enumerate(datas))
        _set_estado(sessao, "AGUARDANDO_DATA")
        await whatsapp_service.enviar_texto(
            sessao.telefone,
            f"📅 Escolha a data de retirada em *BB Sede I* (qua/qui/sex):\n\n{opcoes}"
        )
    else:
        dados["data_agendada"] = None
        sessao.dados_temp = dados
        _set_estado(sessao, "CONFIRMACAO")
        await _enviar_confirmacao(sessao)


async def _handle_data(db: Session, sessao: SessaoBot, texto: str) -> None:
    dados = sessao.dados_temp or {}
    datas_str = dados.get("datas_disponiveis", [])
    try:
        idx = int(texto) - 1
        data_escolhida = date.fromisoformat(datas_str[idx])
    except (ValueError, IndexError):
        datas = [date.fromisoformat(d) for d in datas_str]
        opcoes = "\n".join(f"{i+1}️⃣  {_formatar_data(d)}" for i, d in enumerate(datas))
        await whatsapp_service.enviar_texto(
            sessao.telefone, f"Escolha uma data válida:\n\n{opcoes}"
        )
        return

    dados["data_agendada"] = str(data_escolhida)
    sessao.dados_temp = dados
    _set_estado(sessao, "CONFIRMACAO")
    await _enviar_confirmacao(sessao)


async def _enviar_confirmacao(sessao: SessaoBot) -> None:
    dados = sessao.dados_temp or {}
    carrinho = sessao.carrinho or []

    data_str = ""
    if dados.get("data_agendada"):
        d = date.fromisoformat(dados["data_agendada"])
        data_str = f"\n📅 Data de retirada: *{_formatar_data(d)} ({d.strftime('%d/%m/%Y')})*"

    total = sum(i["preco"] * i["quantidade"] for i in carrinho)
    itens = "\n".join(
        f"  • {i['nome']} x{i['quantidade']} — R$ {i['preco'] * i['quantidade']:.2f}"
        for i in carrinho
    )

    msg = (
        f"📋 *Resumo do pedido:*\n\n"
        f"👤 Nome: *{dados.get('nome', '')}*\n"
        f"📍 Retirada: *{dados.get('ponto_retirada', '')}*"
        f"{data_str}\n\n"
        f"🛒 *Itens:*\n{itens}\n\n"
        f"💰 *Total: R$ {total:.2f}*\n\n"
        "Confirmar pedido?\n\n1️⃣  ✅ Confirmar\n2️⃣  ❌ Cancelar"
    )
    await whatsapp_service.enviar_texto(sessao.telefone, msg)


async def _handle_confirmacao(db: Session, sessao: SessaoBot, texto: str) -> None:
    if texto == "2":
        sessao.carrinho = []
        await whatsapp_service.enviar_texto(
            sessao.telefone, "Pedido cancelado. Voltando ao menu..."
        )
        await _ir_para_menu(db, sessao)
        return

    if texto != "1":
        await _enviar_confirmacao(sessao)
        return

    dados = sessao.dados_temp or {}
    data_agendada = None
    if dados.get("data_agendada"):
        data_agendada = datetime.combine(
            date.fromisoformat(dados["data_agendada"]), datetime.min.time()
        )

    txid = pagamento_service.gerar_txid()

    try:
        cliente = pedido_service.buscar_ou_criar_cliente(
            db,
            nome=dados["nome"],
            telefone=sessao.telefone,
            ponto_retirada=dados["ponto_retirada"],
        )
        pedido = pedido_service.criar_pedido(
            db,
            cliente=cliente,
            carrinho=sessao.carrinho or [],
            ponto_retirada=dados["ponto_retirada"],
            data_agendada=data_agendada,
            pix_txid=txid,
        )
        db.commit()
    except ValueError as e:
        await whatsapp_service.enviar_texto(sessao.telefone, f"❌ {e}")
        return
    except Exception as e:
        logger.error("Erro ao criar pedido: %s", e)
        db.rollback()
        await whatsapp_service.enviar_texto(
            sessao.telefone, "❌ Erro ao registrar pedido. Tente novamente."
        )
        return

    total = pedido.valor_total
    pix_payload = pagamento_service.gerar_pix_copia_cola(total, txid)
    qrcode_b64 = pagamento_service.qrcode_como_base64()

    sessao.carrinho = []
    dados["pedido_id"] = pedido.id
    dados["valor_total"] = total
    sessao.dados_temp = dados
    _set_estado(sessao, "PAGAMENTO")
    db.commit()

    if qrcode_b64:
        await whatsapp_service.enviar_imagem(
            sessao.telefone,
            qrcode_b64,
            legenda=f"QR Code PIX — R$ {total:.2f}",
        )

    await whatsapp_service.enviar_texto(
        sessao.telefone,
        f"✅ *Pedido #{pedido.id} registrado!*\n\n"
        f"💰 Valor: *R$ {total:.2f}*\n\n"
        f"📲 *Pague via PIX:*\n"
        f"Chave: `{settings.pix_chave}`\n\n"
        f"Ou use o *Pix Copia e Cola* abaixo:\n\n"
        f"`{pix_payload}`\n\n"
        "Após o pagamento, envie o comprovante ou aguarde a confirmação. 🙏"
    )


async def _handle_pagamento(db: Session, sessao: SessaoBot, texto: str) -> None:
    dados = sessao.dados_temp or {}
    pedido_id = dados.get("pedido_id", "")
    valor = dados.get("valor_total", 0.0)

    if texto.lower() in {"pago", "paguei", "feito", "ok", "confirmado"}:
        await whatsapp_service.enviar_texto(
            sessao.telefone,
            f"🎉 Ótimo! Assim que confirmarmos o pagamento do pedido *#{pedido_id}*, "
            "você receberá uma mensagem de confirmação. Obrigado! 🧀"
        )
        await _ir_para_menu(db, sessao)
    else:
        txid = (sessao.dados_temp or {}).get("pix_txid") or pagamento_service.gerar_txid()
        pix_payload = pagamento_service.gerar_pix_copia_cola(valor, txid)
        await whatsapp_service.enviar_texto(
            sessao.telefone,
            f"⏳ Pedido *#{pedido_id}* aguardando pagamento de *R$ {valor:.2f}*.\n\n"
            f"Chave PIX: `{settings.pix_chave}`\n\n"
            f"Pix Copia e Cola:\n`{pix_payload}`\n\n"
            "Envie *pago* quando efetuar o pagamento, ou *cancelar* para voltar ao menu."
        )
