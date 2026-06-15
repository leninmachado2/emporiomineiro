// Funções do Carrinho de Compras

async function adicionarAoCarrinho(produtoId, quantidade = 1) {
    const feedback = document.getElementById('feedback');
    
    try {
        const response = await fetch('/carrinho/adicionar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `produto_id=${produtoId}&quantidade=${quantidade}`
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Atualizar contador do carrinho no header
            const cartCount = document.querySelector('.cart-count');
            if (cartCount) {
                cartCount.textContent = result.itens;
                cartCount.style.transform = 'scale(1.2)';
                setTimeout(() => {
                    cartCount.style.transform = 'scale(1)';
                }, 200);
            }
            
            // Mostrar feedback
            mostrarFeedback('✅ Produto adicionado ao carrinho!', 'success');
        } else {
            mostrarFeedback('❌ ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        mostrarFeedback('❌ Erro ao adicionar produto', 'error');
    }
}

async function removerDoCarrinho(produtoId) {
    if (!confirm('Remover este item do carrinho?')) {
        return;
    }
    
    try {
        const response = await fetch('/carrinho/remover', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `produto_id=${produtoId}`
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Remover item da UI
            const cartItem = document.querySelector(`[data-product-id="${produtoId}"]`);
            if (cartItem) {
                cartItem.style.opacity = '0';
                setTimeout(() => {
                    cartItem.remove();
                    // Se não houver mais itens, mostrar carrinho vazio
                    const remainingItems = document.querySelectorAll('.cart-item');
                    if (remainingItems.length === 0) {
                        window.location.reload();
                    }
                }, 300);
            }
            
            // Atualizar total
            atualizarTotal(result.total);
            atualizarContador(result.itens);
        } else {
            mostrarFeedback('❌ ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        mostrarFeedback('❌ Erro ao remover produto', 'error');
    }
}

async function atualizarQuantidade(produtoId, quantidade) {
    if (quantidade < 1) {
        removerDoCarrinho(produtoId);
        return;
    }
    
    try {
        const response = await fetch('/carrinho/atualizar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `produto_id=${produtoId}&quantidade=${quantidade}`
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Atualizar UI
            const cartItem = document.querySelector(`[data-product-id="${produtoId}"]`);
            if (cartItem) {
                const qtyDisplay = cartItem.querySelector('.qty-display');
                const subtotal = cartItem.querySelector('.cart-item-subtotal p');
                
                if (qtyDisplay) {
                    qtyDisplay.textContent = quantidade;
                }
                
                if (subtotal) {
                    // Recalcular subtotal na UI (preço * quantidade)
                    const priceText = cartItem.querySelector('.cart-item-price').textContent;
                    const price = parseFloat(priceText.replace('R$ ', ''));
                    subtotal.textContent = 'R$ ' + (price * quantidade).toFixed(2);
                }
            }
            
            atualizarTotal(result.total);
            atualizarContador(result.itens);
        } else {
            mostrarFeedback('❌ ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        mostrarFeedback('❌ Erro ao atualizar quantidade', 'error');
    }
}

function atualizarTotal(total) {
    const totalElements = document.querySelectorAll('.summary-total span:last-child, .cart-summary .total span:last-child');
    totalElements.forEach(el => {
        el.textContent = 'R$ ' + total.toFixed(2);
    });
}

function atualizarContador(itens) {
    const cartCount = document.querySelector('.cart-count');
    if (cartCount) {
        cartCount.textContent = itens;
    }
}

function mostrarFeedback(mensagem, tipo) {
    // Remover feedback anterior se existir
    const feedbackAntigo = document.querySelector('.feedback-message');
    if (feedbackAntigo) {
        feedbackAntigo.remove();
    }
    
    // Criar elemento de feedback
    const feedback = document.createElement('div');
    feedback.className = 'feedback-message';
    feedback.textContent = mensagem;
    feedback.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        z-index: 3000;
        animation: slideIn 0.3s ease;
        ${tipo === 'success' ? 'background: #27ae60;' : 'background: #e74c3c;'}
    `;
    
    document.body.appendChild(feedback);
    
    // Remover após 3 segundos
    setTimeout(() => {
        feedback.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => feedback.remove(), 300);
    }, 3000);
}

// Adicionar animações CSS dinamicamente
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    // Adicionar evento de submit para formulários com AJAX se necessário
    const forms = document.querySelectorAll('form[data-ajax]');
    forms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            // Implementar lógica AJAX para formulários se necessário
        });
    });
    
    // Smooth scroll para links internos
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Lazy loading para imagens
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    }
                    observer.unobserve(img);
                }
            });
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
});