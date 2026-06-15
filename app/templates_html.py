"""
Funções auxiliares para gerar HTML - alternativa simples aos templates Jinja2.
"""

def render_catalogo_index(request, produtos_destaque, categorias, contagem_categorias, carrinho_itens, carrinho_total):
    """Renderiza página inicial do catálogo."""
    produtos_html = "".join([f"""
        <div class="product-card">
            <h3>{p.nome}</h3>
            <p class="category">{p.categoria}</p>
            {f'<p class="description">{p.descricao}</p>' if p.descricao else ''}
            <p class="price">R$ {p.preco:.2f}</p>
            <p class="stock">Estoque: {p.quantidade_estoque}</p>
            <form action="/produto/{p.id}/adicionar" method="POST" class="add-to-cart-form">
                <button type="submit" class="btn">Adicionar +</button>
            </form>
        </div>
        """ for p in produtos_destaque])
    
    categorias_html = "".join([f"""
        <a href="/categoria/{cat}" class="category-card">
            <span class="category-icon">
                {'🧀' if cat == "Queijos" else '🥓' if cat == "Embutidos" else '🍯'}
            </span>
            <span class="category-name">{cat}</span>
            <span class="category-count">{contagem_categorias.get(cat, 0)} produtos</span>
        </a>
        """ for cat in categorias])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Empório Canastra - Catálogo</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: Arial, sans-serif; line-height: 1.6; background: #f8f9fa; }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            .header {{ text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #f39c12, #e67e22); color: white; position: relative; }}
            .header h1 {{ font-size: 2rem; margin-bottom: 10px; }}
            .cart-icon {{ position: absolute; top: 20px; right: 20px; background: rgba(255,255,255,0.2); padding: 10px 20px; border-radius: 20px; text-decoration: none; color: white; font-weight: bold; }}
            .cart-icon:hover {{ background: rgba(255,255,255,0.3); }}
            .products-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; margin: 30px 0; }}
            .product-card {{ background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: flex; flex-direction: column; }}
            .product-card h3 {{ color: #2c3e50; margin-bottom: 10px; }}
            .category {{ color: #f39c12; font-weight: 600; margin-bottom: 5px; }}
            .price {{ font-size: 1.2em; font-weight: bold; color: #2c3e50; margin: 10px 0; }}
            .stock {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 10px; }}
            .btn {{ background: #f39c12; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; transition: background 0.3s; font-size: 1em; margin-top: auto; }}
            .btn:hover {{ background: #e67e22; }}
            .add-to-cart-form {{ margin-top: auto; }}
            .categories-section {{ margin: 30px 0; }}
            .categories-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }}
            .category-card {{ background: white; padding: 20px; border-radius: 8px; text-align: center; text-decoration: none; color: inherit; box-shadow: 0 2px 8px rgba(0,0,0,0.1); transition: transform 0.3s; }}
            .category-card:hover {{ transform: translateY(-5px); }}
            .category-icon {{ font-size: 2.5rem; display: block; margin-bottom: 10px; }}
            .category-name {{ font-weight: 600; color: #2c3e50; }}
            .category-count {{ color: #7f8c8d; font-size: 0.9rem; }}
            .admin-link {{ text-align: center; margin: 30px 0; padding: 20px; background: white; border-radius: 8px; }}
            .admin-link a {{ color: #667eea; text-decoration: none; font-weight: 600; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🧀 Empório Canastra</h1>
            <p>Selecione seus produtos artesanais da Serra da Canastra</p>
            <a href="/carrinho" class="cart-icon">🛒 Carrinho ({carrinho_itens})</a>
        </div>
        
        <div class="container">
            <div class="products-grid">
                {produtos_html if produtos_html else '<p>Nenhum produto disponível no momento.</p>'}
            </div>
            
            <div class="categories-section">
                <h2 style="margin-bottom: 20px; color: #2c3e50;">📦 Categorias</h2>
                <div class="categories-grid">
                    {categorias_html}
                </div>
            </div>
            
            <div class="admin-link">
                <h3 style="margin-bottom: 15px; color: #2c3e50;">🎉 Sistema Funcional!</h3>
                <p><a href="/admin/login">Acessar Painel Admin (usuário: admin, senha: admin123)</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def render_admin_login(error_message=None):
    """Renderiza página de login do admin."""
    error_html = f'<div class="error-message">{error_message}</div>' if error_message else ''
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Admin Empório</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ display: flex; justify-content: center; align-items: center; min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; font-family: Arial, sans-serif; }}
            .login-container {{ background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }}
            .login-header {{ text-align: center; margin-bottom: 30px; }}
            .login-header h1 {{ color: #2c3e50; margin-bottom: 10px; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 8px; color: #2c3e50; font-weight: 600; }}
            .form-input {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; box-sizing: border-box; }}
            .btn-login {{ width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 5px; font-size: 16px; font-weight: 600; cursor: pointer; transition: background 0.3s; }}
            .btn-login:hover {{ background: #5568d3; }}
            .error-message {{ background: #fee; color: #c33; padding: 10px; border-radius: 5px; margin-bottom: 20px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-header">
                <h1>🧀 Admin Login</h1>
                <p>Empório Canastra</p>
            </div>
            {error_html}
            <form method="POST">
                <div class="form-group">
                    <label for="username">Usuário</label>
                    <input type="text" id="username" name="username" required class="form-input">
                </div>
                <div class="form-group">
                    <label for="senha">Senha</label>
                    <input type="password" id="senha" name="senha" required class="form-input">
                </div>
                <button type="submit" class="btn-login">Entrar</button>
            </form>
        </div>
    </body>
    </html>
    """
    return html


def render_admin_dashboard(admin, vendas_hoje, vendas_semana, pedidos_pendentes, pedidos_hoje):
    """Renderiza dashboard do admin."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - Admin Empório</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }}
            .dashboard-header {{ margin-bottom: 30px; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            .stat-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            .stat-value {{ font-size: 1.5rem; font-weight: bold; color: #2c3e50; }}
            .stat-label {{ color: #7f8c8d; font-size: 0.9rem; margin-bottom: 5px; }}
            .section {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            .btn {{ background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px; display: inline-block; }}
            .btn:hover {{ background: #5568d3; }}
            .logout {{ background: #e74c3c; }}
            .logout:hover {{ background: #c0392b; }}
        </style>
    </head>
    <body>
        <div class="dashboard-header">
            <h1>📊 Dashboard - Empório Canastra</h1>
            <p>Bem-vindo, {admin.username}!</p>
            <a href="/admin/produtos" class="btn">📦 Gerenciar Produtos</a>
            <a href="/admin/logout" class="btn logout">🚪 Sair</a>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <p class="stat-label">💰 Vendas Hoje</p>
                <p class="stat-value">R$ {vendas_hoje:.2f}</p>
            </div>
            <div class="stat-card">
                <p class="stat-label">📈 Vendas Semana</p>
                <p class="stat-value">R$ {vendas_semana:.2f}</p>
            </div>
            <div class="stat-card">
                <p class="stat-label">⏳ Pedidos Pendentes</p>
                <p class="stat-value">{pedidos_pendentes}</p>
            </div>
            <div class="stat-card">
                <p class="stat-label">📦 Pedidos Hoje</p>
                <p class="stat-value">{pedidos_hoje}</p>
            </div>
        </div>
        
        <div class="section">
            <h3>🎉 Sistema Funcionando!</h3>
            <p>Use os botões acima para gerenciar produtos.</p>
        </div>
    </body>
    </html>
    """
    return html


def render_admin_produtos(produtos):
    """Renderiza listagem de produtos do admin."""
    produtos_html = "".join([f"""
        <tr>
            <td>{p.nome}</td>
            <td>{p.categoria}</td>
            <td>R$ {p.preco:.2f}</td>
            <td>{p.quantidade_estoque}</td>
            <td>{'✅ Ativo' if p.ativo else '❌ Inativo'}</td>
            <td>
                <a href="/admin/produtos/editar/{p.id}" class="btn-small btn-edit">✏️</a>
                <a href="/admin/produtos/deletar/{p.id}" class="btn-small btn-delete">🗑️</a>
            </td>
        </tr>
        """ for p in produtos])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Produtos - Admin Empório</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }}
            .header {{ margin-bottom: 30px; }}
            table {{ width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ecf0f1; }}
            th {{ background: #f8f9fa; }}
            .btn {{ background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-right: 10px; display: inline-block; }}
            .btn:hover {{ background: #5568d3; }}
            .btn-primary {{ background: #27ae60; }}
            .btn-primary:hover {{ background: #219150; }}
            .logout {{ background: #e74c3c; }}
            .logout:hover {{ background: #c0392b; }}
            .btn-small {{ padding: 5px 10px; font-size: 0.9em; margin-right: 5px; }}
            .btn-edit {{ background: #3498db; }}
            .btn-delete {{ background: #e74c3c; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📦 Produtos - Empório Canastra</h1>
            <a href="/admin/produtos/novo" class="btn btn-primary">➕ Novo Produto</a>
            <a href="/admin/dashboard" class="btn">← Voltar ao Dashboard</a>
            <a href="/admin/logout" class="btn logout">🚪 Sair</a>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Nome</th>
                    <th>Categoria</th>
                    <th>Preço</th>
                    <th>Estoque</th>
                    <th>Status</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
                {produtos_html if produtos_html else '<tr><td colspan="6">Nenhum produto cadastrado</td></tr>'}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html


def render_carrinho(carrinho_itens, total, CATEGORIAS):
    """Renderiza página do carrinho."""
    itens_html = ""
    if carrinho_itens:
        for item in carrinho_itens:
            pid = item['produto_id']
            nome = item['nome']
            qtd = item['quantidade']
            subtotal = item['subtotal']
            itens_html += f"""
            <div class="carrinho-item">
                <h4>{nome}</h4>
                <div class="item-controls">
                    <div class="quantity-control">
                        <button onclick="atualizarQuantidade({pid}, {qtd - 1})" class="btn-small">-</button>
                        <span>{qtd}</span>
                        <button onclick="atualizarQuantidade({pid}, {qtd + 1})" class="btn-small">+</button>
                    </div>
                    <p class="item-price">R$ {subtotal:.2f}</p>
                    <button onclick="removerItem({pid})" class="btn-small btn-delete">🗑️</button>
                </div>
            </div>
            """
    else:
        itens_html = '<p class="empty-cart">🛒 Seu carrinho está vazio</p>'
    
    categorias_html = "".join([f'<option value="{cat}">{cat}</option>' for cat in CATEGORIAS])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Carrinho - Empório Canastra</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: Arial, sans-serif; line-height: 1.6; background: #f8f9fa; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #f39c12, #e67e22); color: white; padding: 40px 20px; text-align: center; }}
            .cart-items {{ background: white; border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .carrinho-item {{ border-bottom: 1px solid #ecf0f1; padding: 15px 0; display: flex; gap: 20px; align-items: center; }}
            .carrinho-item:last-child {{ border-bottom: none; }}
            .carrinho-item > div {{ flex: 1; }}
            .item-controls {{ display: flex; align-items: center; justify-content: space-between; margin-top: 10px; }}
            .quantity-control {{ display: flex; align-items: center; gap: 10px; }}
            .btn-small {{ background: #f39c12; color: white; border: none; padding: 5px 15px; border-radius: 3px; cursor: pointer; }}
            .btn-small:hover {{ background: #e67e22; }}
            .btn-delete {{ background: #e74c3c; }}
            .btn-delete:hover {{ background: #c0392b; }}
            .item-price {{ font-weight: bold; color: #2c3e50; }}
            .empty-cart {{ text-align: center; padding: 40px; color: #7f8c8d; }}
            .cart-summary {{ background: white; border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .total {{ font-size: 1.5em; font-weight: bold; color: #2c3e50; text-align: right; }}
            .checkout-btn {{ background: #27ae60; color: white; border: none; padding: 15px 30px; border-radius: 5px; font-size: 1.1em; cursor: pointer; width: 100%; margin-top: 20px; }}
            .checkout-btn:hover {{ background: #219150; }}
            .btn {{ background: #f39c12; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; }}
            .btn:hover {{ background: #e67e22; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛒 Carrinho de Compras</h1>
        </div>
        
        <div class="container">
            <a href="/catalogo" class="btn">← Continuar Comprando</a>
            
            <div class="cart-items">
                <h2>Seus Itens</h2>
                {itens_html}
            </div>
            
            {f'''
            <div class="cart-summary">
                <p class="total">Total: R$ {total:.2f}</p>
                <button onclick="irParaCheckout()" class="checkout-btn">✅ Finalizar Pedido</button>
            </div>
            ''' if carrinho_itens else '<div style="text-align: center; padding: 20px;"><a href="/catalogo" class="btn">🛍️ Começar a Comprar</a></div>'}
        </div>
        
        <script>
        function atualizarQuantidade(produtoId, novaQuantidade) {{
            if (novaQuantidade <= 0) {{
                removerItem(produtoId);
                return;
            }}
            fetch(`/carrinho/atualizar`, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                body: `produto_id=${{produtoId}}&quantidade=${{novaQuantidade}}`
            }}).then(() => location.reload());
        }}
        
        function removerItem(produtoId) {{
            if (confirm('Deseja remover este item?')) {{
                fetch(`/carrinho/remover`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                    body: `produto_id=${{produtoId}}`
                }}).then(() => location.reload());
            }}
        }}
        
        function irParaCheckout() {{
            window.location.href = '/checkout';
        }}
        </script>
    </body>
    </html>
    """
    return html


def render_checkout(carrinho_itens, total, pontos_retirada, datas_disponiveis):
    """Renderiza página de checkout."""
    itens_html = "".join([f'<li>{item.quantidade}x {item.produto.nome} - R$ {item.quantidade * item.produto.preco:.2f}</li>' for item in carrinho_itens])
    
    pontos_html = "".join([f'<option value="{ponto}">{ponto}</option>' for ponto in pontos_retirada])
    
    datas_html = "".join([f'<option value="{data}">{data}</option>' for data in datas_disponiveis])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Checkout - Empório Canastra</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: Arial, sans-serif; line-height: 1.6; background: #f8f9fa; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #27ae60, #219150); color: white; padding: 40px 20px; text-align: center; }}
            .form-section {{ background: white; border-radius: 8px; padding: 30px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 8px; color: #2c3e50; font-weight: 600; }}
            .form-input, .form-select {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }}
            .order-summary {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .order-summary h3 {{ color: #2c3e50; margin-bottom: 15px; }}
            .order-summary ul {{ list-style: none; padding: 0; }}
            .order-summary li {{ padding: 8px 0; border-bottom: 1px solid #ecf0f1; }}
            .total {{ font-size: 1.5em; font-weight: bold; color: #2c3e50; text-align: right; }}
            .checkout-btn {{ background: #27ae60; color: white; border: none; padding: 15px 30px; border-radius: 5px; font-size: 1.1em; cursor: pointer; width: 100%; }}
            .checkout-btn:hover {{ background: #219150; }}
            .btn {{ background: #27ae60; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; }}
            .btn:hover {{ background: #219150; }}
            .back {{ background: #95a5a6; }}
            .back:hover {{ background: #7f8c8d; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>✅ Finalizar Pedido</h1>
            <p>Complete seu pedido e escolha a data de retirada</p>
        </div>
        
        <div class="container">
            <a href="/carrinho" class="btn back">← Voltar ao Carrinho</a>
            
            <div class="form-section">
                <h2>📝 Dados do Pedido</h2>
                
                <form method="POST">
                    <div class="form-group">
                        <label for="nome">Nome Completo</label>
                        <input type="text" id="nome" name="nome" required class="form-input" placeholder="Seu nome">
                    </div>
                    
                    <div class="form-group">
                        <label for="telefone">WhatsApp</label>
                        <input type="tel" id="telefone" name="telefone" required class="form-input" placeholder="(XX) XXXXX-XXXX">
                    </div>
                    
                    <div class="form-group">
                        <label for="ponto_retirada">Ponto de Retirada</label>
                        <select id="ponto_retirada" name="ponto_retirada" required class="form-select">
                            <option value="">Selecione um ponto</option>
                            {pontos_html}
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="data_retirada">Data de Retirada</label>
                        <select id="data_retirada" name="data_retirada" required class="form-select">
                            <option value="">Selecione uma data</option>
                            {datas_html}
                        </select>
                        <small>Dias disponíveis: quarta, quinta e sexta</small>
                    </div>
                    
                    <div class="order-summary">
                        <h3>📦 Resumo do Pedido</h3>
                        <ul>
                            {itens_html}
                        </ul>
                        <p class="total">Total: R$ {total:.2f}</p>
                    </div>
                    
                    <button type="submit" class="checkout-btn">💳 Gerar PIX e Finalizar</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def render_checkout_sucesso(pedido_id, qr_code, valor, data_retirada, ponto_retirada):
    """Renderiza página de sucesso do checkout."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pedido Realizado - Empório Canastra</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: Arial, sans-serif; line-height: 1.6; background: #f8f9fa; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .success-header {{ background: linear-gradient(135deg, #27ae60, #219150); color: white; padding: 40px 20px; text-align: center; }}
            .success-content {{ background: white; border-radius: 8px; padding: 30px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .qr-code {{ text-align: center; margin: 20px 0; }}
            .qr-code img {{ max-width: 300px; }}
            .info-box {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
            .btn {{ background: #27ae60; color: white; padding: 15px 30px; border-radius: 5px; text-decoration: none; display: block; text-align: center; margin: 20px 0; }}
            .btn:hover {{ background: #219150; }}
        </style>
    </head>
    <body>
        <div class="success-header">
            <h1>✅ Pedido Realizado!</h1>
            <p>Pedido #{pedido_id}</p>
        </div>
        
        <div class="container">
            <div class="success-content">
                <h2>🎉 Parabéns!</h2>
                <p>Seu pedido foi criado com sucesso.</p>
                
                <div class="info-box">
                    <h3>💰 Valor a Pagar</h3>
                    <p style="font-size: 1.5em; font-weight: bold; color: #27ae60;">R$ {valor:.2f}</p>
                </div>
                
                <div class="info-box">
                    <h3>📅 Data de Retirada</h3>
                    <p>{data_retirada}</p>
                </div>
                
                <div class="info-box">
                    <h3>📍 Ponto de Retirada</h3>
                    <p>{ponto_retirada}</p>
                </div>
                
                <div class="qr-code">
                    <h3>📱 Escaneie para Pagar</h3>
                    <pre style="background: white; padding: 15px; border-radius: 5px; font-size: 0.8em; word-break: break-all;">{qr_code}</pre>
                </div>
                
                <p style="text-align: center; color: #7f8c8d;">
                    Aguardamos seu pagamento para confirmar o pedido.
                </p>
            </div>
            
            <a href="/catalogo" class="btn">🛍️ Continuar Comprando</a>
        </div>
    </body>
    </html>
    """
    return html


def render_produto_form(produto=None, categorias=None):
    """Renderiza formulário de criação/edição de produto."""
    if categorias is None:
        categorias = ["Queijos", "Embutidos", "Doces"]
    
    if produto:
        titulo = "Editar Produto"
        action_url = f"/admin/produtos/editar/{produto.id}"
        nome = produto.nome
        categoria = produto.categoria
        descricao = produto.descricao or ""
        preco = produto.preco
        estoque = produto.quantidade_estoque
        ativo = produto.ativo
        imagem = produto.caminho_imagem or ""
        submit_text = "💾 Atualizar Produto"
    else:
        titulo = "Novo Produto"
        action_url = "/admin/produtos/novo"
        nome = ""
        categoria = ""
        descricao = ""
        preco = ""
        estoque = ""
        ativo = True
        imagem = ""
        submit_text = "➕ Criar Produto"
    
    categorias_html = "".join([f'<option value="{cat}" {("selected" if cat == categoria else "")}>{cat}</option>' for cat in categorias])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{titulo} - Admin Empório</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }}
            .form-container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .header {{ margin-bottom: 30px; }}
            .form-group {{ margin-bottom: 20px; }}
            .form-group label {{ display: block; margin-bottom: 8px; color: #2c3e50; font-weight: 600; }}
            .form-input, .form-select, .form-textarea {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; box-sizing: border-box; }}
            .form-textarea {{ min-height: 100px; resize: vertical; }}
            .checkbox-group {{ display: flex; align-items: center; gap: 10px; }}
            .btn {{ background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; border: none; cursor: pointer; font-size: 16px; }}
            .btn:hover {{ background: #5568d3; }}
            .btn-cancel {{ background: #95a5a6; }}
            .btn-cancel:hover {{ background: #7f8c8d; }}
            .preview {{ margin-top: 10px; max-width: 200px; }}
            .preview img {{ max-width: 100%; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="form-container">
            <div class="header">
                <h1>{titulo}</h1>
                <a href="/admin/produtos" class="btn btn-cancel">← Voltar</a>
            </div>
            
            <form method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="nome">Nome do Produto</label>
                    <input type="text" id="nome" name="nome" required class="form-input" value="{nome}">
                </div>
                
                <div class="form-group">
                    <label for="categoria">Categoria</label>
                    <select id="categoria" name="categoria" required class="form-select">
                        <option value="">Selecione uma categoria</option>
                        {categorias_html}
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="descricao">Descrição</label>
                    <textarea id="descricao" name="descricao" class="form-textarea">{descricao}</textarea>
                </div>
                
                <div class="form-group">
                    <label for="preco">Preço (R$)</label>
                    <input type="number" id="preco" name="preco" required step="0.01" min="0" class="form-input" value="{preco}">
                </div>
                
                <div class="form-group">
                    <label for="quantidade_estoque">Quantidade em Estoque</label>
                    <input type="number" id="quantidade_estoque" name="quantidade_estoque" required min="0" class="form-input" value="{estoque}">
                </div>
                
                <div class="form-group">
                    <label for="imagem">Imagem do Produto</label>
                    <input type="file" id="imagem" name="imagem" class="form-input" accept="image/*">
                    {f'<div class="preview"><img src="{imagem}" alt="Preview"></div>' if imagem else ''}
                </div>
                
                <div class="form-group checkbox-group">
                    <input type="checkbox" id="ativo" name="ativo" {("checked" if ativo else "")}>
                    <label for="ativo">Produto Ativo</label>
                </div>
                
                <button type="submit" class="btn">{submit_text}</button>
            </form>
        </div>
    </body>
    </html>
    """
    return html