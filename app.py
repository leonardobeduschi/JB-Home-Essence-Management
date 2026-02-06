"""
Flask web application for Perfumery Management System.

This module provides the web interface and REST API endpoints.
"""
from pathlib import Path
from dotenv import load_dotenv

"""
Flask web application for Perfumery Management System.
"""

# ⚠️ CRITICAL: Load .env BEFORE any imports!
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Verify DB_TYPE is loaded
print(f"🔧 DB_TYPE loaded: {os.getenv('DB_TYPE', 'NOT SET')}")

# Load .env from project root
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Verify DB_TYPE is loaded
print(f"🔧 DB_TYPE loaded: {os.getenv('DB_TYPE', 'NOT SET')}")

# Now import Flask and other modules
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from functools import wraps
from datetime import datetime, timedelta
import secrets
import os
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

from src.services.product_service import ProductService
from src.services.client_service import ClientService
from src.services.sale_service import SaleService
from src.services.analytics_service import AnalyticsService
from src.services.visualization_service import VisualizationService
from src.services.manual_service import ManualService
from src.services.expense_service import ExpenseService
from src.services.budget_service import BudgetService
from src.services.notification_service import NotificationService


# ========== CONFIGURAÇÃO DO FLASK ==========

# Initialize Flask app
app = Flask(__name__)

# 🔐 Secret key usando variável de ambiente (mais seguro)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))  # Fallback para desenvolvimento

# 🔒 Configurações de segurança de sessão
# Tornar secure cookie condicional: habilitar somente em produção/HTTPS para não quebrar sessões em desenvolvimento local
is_production = os.getenv('FLASK_ENV') == 'production' or os.getenv('USE_HTTPS', 'false').lower() in ('1', 'true', 'yes')
app.config.update(
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    SESSION_COOKIE_SECURE=is_production,      # Apenas HTTPS em produção
    SESSION_COOKIE_HTTPONLY=True,    # Impede acesso via JavaScript
    SESSION_COOKIE_SAMESITE='Lax'    # Proteção contra CSRF
)
# Log (console) para facilitar debug local
print(f"SESSION_COOKIE_SECURE={app.config['SESSION_COOKIE_SECURE']}; FLASK_ENV={os.getenv('FLASK_ENV')}")

# ========== FILTROS JINJA2 ==========

@app.template_filter('currency')
def currency_filter(value):
    """Format currency in Brazilian style (thousands dot, decimal comma)."""
    try:
        v = float(value)
    except (ValueError, TypeError):
        return value
    sign = '-' if v < 0 else ''
    v_abs = abs(v)
    s = f"{v_abs:,.2f}"  # produces '25,300.00'
    # Swap thousands and decimal separators to Brazilian format
    s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"{sign}{s}"

# ========== INICIALIZAÇÃO DE SERVIÇOS ==========

product_service = ProductService()
client_service = ClientService()
sale_service = SaleService()
analytics_service = AnalyticsService()
visualization_service = VisualizationService()
manual_service = ManualService()
expense_service = ExpenseService()
budget_service = BudgetService()
notification_service = NotificationService()

# ========== CACHE DE NOTIFICAÇÕES ==========
notification_cache = {
    'data': None,
    'timestamp': None,
    'ttl': 3 * 3600  # 5 minutos
}

def get_cached_notifications():
    """Get notifications with 5-minute cache."""
    import time
    now = time.time()
    
    if (notification_cache['data'] is None or 
        notification_cache['timestamp'] is None or 
        (now - notification_cache['timestamp']) > notification_cache['ttl']):
        
        # Refresh cache
        notification_cache['data'] = notification_service.get_all_notifications()
        notification_cache['timestamp'] = now
    
    return notification_cache['data']

# ========== DATABASE INITIALIZATION ==========
DB_TYPE = os.getenv('DB_TYPE', 'sqlite').lower()

if DB_TYPE == 'postgresql':
    print("✅ Using PostgreSQL (Supabase)")
    try:
        from src.database.postgres_connection import get_connection
        with get_connection() as conn:
            print("✅ PostgreSQL connection successful")
    except Exception as e:
        print(f"⚠️ PostgreSQL connection error: {e}")
else:
    print("✅ Using SQLite")
    try:
        from src.database.connection import init_db, get_db_path
        SQLITE_DB = os.getenv('SQLITE_DB', None)
        init_db(db_path=SQLITE_DB)
        resolved_db = get_db_path(SQLITE_DB)
        print(f"SQLite DB initialized at: {resolved_db}")
    except Exception as e:
        print(f"Erro ao inicializar o banco SQLite: {e}")

# ========== BANCO DE DADOS DE USUÁRIOS ==========

# ✅ USUÁRIOS JB HOME ESSENCE COM HASH SEGURO
# Em produção, use variáveis de ambiente para os hashes
USERS = {
    'Jeanete': {
        'password_hash': os.getenv('JEANETE_PASSWORD_HASH', 
            'scrypt:32768:8:1$UhDcxbVruYxivOny$8156fad4525d8951b660ba8c6d06f28c427c19bcbe2ce6a6138ee3b3b9447b30f3216075198a8815236a267150e855d00bfdc373a852fed06fd632d0fec855ae'),
        'name': 'Jeanete',
        'role': 'admin'
    },
    'Matheus': {
        'password_hash': os.getenv('MATHEUS_PASSWORD_HASH',
            'scrypt:32768:8:1$SNBtHaT2Vu5XZVWm$ee4793d4b1db8cb67d22a3ed0d2b7329cc67e77cfaa57bd31dc3d7a8bdfa22f9316aed06a37e67aabb6f7122714dcd7419d2e034159b0c81ba2748d1c747270c'),
        'name': 'Matheus',
        'role': 'admin'
    },
    'Leonardo': {
        'password_hash': os.getenv('LEONARDO_PASSWORD_HASH',
            'scrypt:32768:8:1$PwBIrzKgUaD7EmlO$615ef9b1127cf21a02d662f2a64844931cbdc9ed3bf56fc6601585dd0fb9aec98df1c985b11ad755d1fedcdf81c4c09d4721a9870c32a5573f5a9a595e307aa8'),
        'name': 'Leonardo',
        'role': 'admin'
    }
}

# ========== DECORATORS DE AUTENTICAÇÃO ==========

def login_required(f):
    """Require login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Require admin role for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return jsonify({'error': 'Acesso negado. Apenas administradores.'}), 403
        return f(*args, **kwargs)
    return decorated_function


# ========== ROTAS DE AUTENTICAÇÃO ==========

@app.route('/')
def index():
    """Redirect to dashboard or login."""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Verifica se o usuário existe
        if username not in USERS:
            return render_template('login.html', error='Usuário ou senha inválidos')
        
        user = USERS[username]
        
        # Verifica a senha usando hash seguro
        try:
            if check_password_hash(user['password_hash'], password):
                session.permanent = True
                session['username'] = username
                session['name'] = user['name']
                session['role'] = user['role']
                # Tentar construir URL do dashboard; se falhar, usar fallback para path absoluto
                try:
                    dashboard_url = url_for('dashboard')
                except Exception as be:
                    print(f"Erro ao construir URL do dashboard: {be}")
                    dashboard_url = '/dashboard'
                return redirect(dashboard_url)
            else:
                return render_template('login.html', error='Usuário ou senha inválidos')
        except Exception as e:
            # Log do erro (em produção, use logging apropriado) com traceback completo
            import traceback
            print("Erro na verificação de senha:")
            traceback.print_exc()
            return render_template('login.html', error='Erro no sistema. Tente novamente.')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout handler."""
    session.clear()
    return redirect(url_for('login'))


# ========== ROTAS DA APLICAÇÃO ==========

# Adicione aqui as outras rotas do seu sistema...
# Exemplo: (o dashboard completo é definido mais abaixo no arquivo) 


# ========== CONFIGURAÇÃO PARA DESENVOLVIMENTO ==========

# NOTE: O `app.run` fica apenas no final do arquivo para garantir que
# todas as rotas sejam registradas antes de iniciar o servidor.
# (Removido bloco duplicado que iniciava o servidor prematuramente.)

# ========== DASHBOARD ROUTES ==========

# ========== DEBUG: Test database connection ==========
@app.route('/test-db')
def test_db():
    """Test database connection."""
    try:
        from src.repositories.product_repository import ProductRepository
        repo = ProductRepository()
        count = repo.count()
        return f"✅ Database OK! Products: {count}"
    except Exception as e:
        import traceback
        return f"❌ Database Error: {str(e)}<br><pre>{traceback.format_exc()}</pre>"


@app.route('/api/debug/db-check')
@login_required
def api_db_check():
    """Comprehensive database health check."""
    try:
        from src.repositories.client_repository import ClientRepository
        from src.repositories.product_repository import ProductRepository
        
        client_repo = ClientRepository()
        product_repo = ProductRepository()
        
        results = {
            'db_type': os.getenv('DB_TYPE', 'sqlite'),
            'tables': {},
            'connection': 'OK'
        }
        
        # Check clients
        try:
            results['tables']['clients'] = {
                'exists': client_repo._table_exists(),
                'count': client_repo.count() if client_repo._table_exists() else 0
            }
        except Exception as e:
            results['tables']['clients'] = {'error': str(e)}
            
        # Check products
        try:
            results['tables']['products'] = {
                'exists': product_repo._table_exists(),
                'count': product_repo.count() if product_repo._table_exists() else 0
            }
        except Exception as e:
            results['tables']['products'] = {'error': str(e)}
            
        # List all tables in public schema for PG
        if os.getenv('DB_TYPE') == 'postgresql':
            with client_repo.get_conn() as conn:
                cur = client_repo._get_cursor(conn)
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                results['all_public_tables'] = [r['table_name'] if isinstance(r, dict) else r[0] for r in cur.fetchall()]
        
        return jsonify({'success': True, 'data': results})
        
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}), 500


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard route - OTIMIZADO."""
    import time
    
    overall_start = time.perf_counter()
    
    try:
        print("[DASHBOARD] Iniciando carregamento...")
        
        # ── Etapa 1: Resumo de vendas (1 query otimizada)
        step_start = time.perf_counter()
        summary = sale_service.get_sales_summary()
        print(f"[DASHBOARD] get_sales_summary() → {time.perf_counter() - step_start:.4f}s")
        
        # ── Etapa 2: Vendas recentes (1 query com LIMIT)
        step_start = time.perf_counter()
        from src.repositories.sale_repository import SaleRepository
        sale_repo = SaleRepository()
        recent_sales = sale_repo.get_recent_sales(limit=10)
        print(f"[DASHBOARD] get_recent_sales() → {time.perf_counter() - step_start:.4f}s | {len(recent_sales)} registros")
        
        # ── Etapa 3: Top 5 produtos com JOIN (1 query!)
        step_start = time.perf_counter()
        from src.repositories.sale_item_repository import SaleItemRepository
        from src.repositories.product_repository import ProductRepository
        
        item_repo = SaleItemRepository()
        product_repo = ProductRepository()
        
        # OTIMIZADO: Pega stats + custos em 1 query com JOIN
        with item_repo.get_conn() as conn:
            cur = item_repo._get_cursor(conn)
            
            cur.execute('''
                SELECT 
                    si."CODIGO",
                    si."PRODUTO",
                    si."CATEGORIA",
                    SUM(COALESCE(si."QUANTIDADE", 0)) AS qtd_vendida,
                    SUM(COALESCE(si."PRECO_TOTAL", 0)) AS receita,
                    COALESCE(p."CUSTO", 0) AS custo,
                    COALESCE(p."VALOR", 0) AS valor
                FROM sales_items si
                LEFT JOIN products p ON si."CODIGO" = p."CODIGO"
                GROUP BY si."CODIGO", si."PRODUTO", si."CATEGORIA", p."CUSTO", p."VALOR"
                ORDER BY receita DESC
                LIMIT 5
            ''')
            
            top_5_rows = cur.fetchall()
        
        top_products = []
        for row in top_5_rows:
            custo = float(row['custo'] or 0)
            valor = float(row['valor'] or 0)
            profit_margin = 0
            
            if valor > 0:
                profit_margin = ((valor - custo) / valor) * 100
            
            top_products.append({
                'produto': row['PRODUTO'],
                'categoria': row['CATEGORIA'],
                'quantity_sold': int(row['qtd_vendida']),
                'revenue': float(row['receita']),
                'profit_margin': profit_margin
            })
        
        print(f"[DASHBOARD] Top 5 products (JOIN) → {time.perf_counter() - step_start:.4f}s | {len(top_products)} itens")
        
        # ── Etapa 4: Produtos com estoque baixo (1 query otimizada)
        step_start = time.perf_counter()
        try:
            low_stock = product_repo.get_low_stock(threshold=1)
            print(f"[DASHBOARD] get_low_stock() → {time.perf_counter() - step_start:.4f}s | {len(low_stock)} itens")
        except Exception as e:
            print(f"[DASHBOARD] Erro low stock: {e}")
            low_stock = []
        
        # Conversão de tipos (compatibilidade com template)
        if 'by_category' in summary:
            summary['by_category'] = {k: float(v) for k, v in summary['by_category'].items()}
        
        # ── Renderização final
        render_start = time.perf_counter()
        response = render_template(
            'dashboard.html',
            summary=summary,
            recent_sales=recent_sales,
            top_products=top_products,
            low_stock=low_stock
        )
        render_time = time.perf_counter() - render_start
        
        total_time = time.perf_counter() - overall_start
        
        print(f"[DASHBOARD] render_template() → {render_time:.4f}s")
        print(f"[DASHBOARD] ⏱ TEMPO TOTAL DA ROTA: {total_time:.4f}s")
        
        return response
        
    except Exception as e:
        total_time = time.perf_counter() - overall_start
        print(f"[DASHBOARD] ❌ ERRO após {total_time:.4f}s → {str(e)}")
        import traceback
        traceback.print_exc()
        return render_template('error.html', error=str(e)), 500


# Debug: listar endpoints registrados (útil para troubleshooting)
print('Rotas registradas:', sorted([r.endpoint for r in app.url_map.iter_rules()]))

# Handler 404 para log detalhado (ajuda a identificar recursos quebrados)
@app.errorhandler(404)
def page_not_found(e):
    try:
        print(f"404 Not Found -> Method: {request.method}, Path: {request.path}, Referer: {request.headers.get('Referer')}, User-Agent: {request.headers.get('User-Agent')}")
    except Exception:
        print("404 Not Found (não foi possível ler os headers)")
    return render_template('404.html'), 404

@app.route('/products')
@login_required
def products():
    try:
        # Get all products
        products_list = product_service.list_all_products()

        # Calculate CORRECT margins for each product
        for product in products_list:
            custo = float(product.get('CUSTO', 0))
            valor = float(product.get('VALOR', 0))

            if valor > 0:
                # USA O MÉTODO CORRETO (não depende de monthly_sales)
                margin_data = expense_service.calculate_product_margin(
                    sale_price=valor,
                    cost_price=custo,
                    quantity=1,
                    payment_method='pix'  # Assume pix por padrão
                )

                product['gross_margin_pct'] = margin_data['gross_margin_pct']
                product['contribution_margin_pct'] = margin_data['contribution_margin_pct']
                product['variable_costs'] = margin_data['variable_costs_total']

                # Para compatibilidade com template antigo
                product['net_margin_pct'] = margin_data['contribution_margin_pct']
            else:
                product['gross_margin_pct'] = 0
                product['contribution_margin_pct'] = 0
                product['net_margin_pct'] = 0
                product['variable_costs'] = 0

        return render_template(
            'products.html', 
            products=products_list,
            total_expenses=expense_service.get_total_monthly_expenses(),
            user=session
        )

    except Exception as e:
        print(f"Erro na página de produtos: {e}")
        import traceback
        traceback.print_exc()
        return render_template('error.html', error=str(e))


@app.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """Add product page and handler."""
    if request.method == 'POST':
        try:
            product_service.register_product(
                codigo=request.form['codigo'],
                produto=request.form['produto'],
                categoria=request.form['categoria'],
                custo=float(request.form['custo']),
                valor=float(request.form['valor']),
                estoque=int(request.form['estoque'])
            )
            return redirect(url_for('products'))
        except Exception as e:
            return render_template('add_product.html', error=str(e), user=session)
    
    return render_template('add_product.html', user=session)


# ========== CLIENT ROUTES ==========

@app.route('/clients')
@login_required
def clients():
    """Clients management page."""
    clients = client_service.list_all_clients()
    return render_template('clients.html', clients=clients, user=session)


@app.route('/clients/add', methods=['GET', 'POST'])
@login_required
def add_client():
    """Add client page and handler."""
    if request.method == 'POST':
        try:
            client_service.register_client(
                cliente=request.form['cliente'],
                vendedor=request.form.get('vendedor', ''),
                tipo=request.form['tipo'],
                idade=request.form.get('idade', ''),
                genero=request.form.get('genero', ''),
                profissao=request.form.get('profissao', ''),
                cpf_cnpj=request.form.get('cpf_cnpj', ''),
                telefone=request.form.get('telefone', ''),
                endereco=request.form.get('endereco', '')
            )
            return redirect(url_for('clients'))
        except Exception as e:
            return render_template('add_client.html', 
                                 error=str(e),
                                 age_ranges=client_service.get_available_age_ranges(),
                                 user=session)
    
    return render_template('add_client.html',
                         age_ranges=client_service.get_available_age_ranges(),
                         user=session)


@app.route('/clients/edit/<id_cliente>', methods=['GET', 'POST'])
@login_required
def edit_client(id_cliente):
    """Edit client page and handler."""
    client = client_service.get_client(id_cliente)
    if not client:
        return render_template('error.html', error='Cliente não encontrado'), 404

    if request.method == 'POST':
        try:
            updates = {
                'cliente': request.form['cliente'],
                'vendedor': request.form.get('vendedor', ''),
            }

            if request.form.get('telefone'):
                updates['telefone'] = request.form['telefone']
            if request.form.get('endereco'):
                updates['endereco'] = request.form['endereco']
            if request.form.get('profissao'):
                updates['profissao'] = request.form['profissao']

            tipo_lower = str(client.get('TIPO', '')).lower()
            if tipo_lower == 'pessoa':
                updates['idade'] = request.form['idade']
                updates['genero'] = request.form['genero']
                if request.form.get('cpf_cnpj'):
                    updates['cpf_cnpj'] = request.form['cpf_cnpj']
            elif tipo_lower == 'empresa':
                updates['cpf_cnpj'] = request.form['cpf_cnpj']
                updates['endereco'] = request.form['endereco']

            client_service.update_client_info(id_cliente, **updates)
            return redirect(url_for('clients'))

        except Exception as e:
            return render_template('edit_client.html',
                                 client=client,
                                 age_ranges=client_service.get_available_age_ranges(),
                                 error=str(e),
                                 user=session)

    return render_template('edit_client.html',
                         client=client,
                         age_ranges=client_service.get_available_age_ranges(),
                         user=session)


# ========== SALES ROUTES ==========

@app.route('/sales')
@login_required
def sales():
    """Sales page."""
    sales = sale_service.list_all_sales()
    return render_template('sales.html', sales=sales, user=session)


@app.route('/sales/add', methods=['GET', 'POST'])
@login_required
def add_sale():
    """Add sale page and handler - WITH MULTI-ITEM SUPPORT AND DATE."""
    if request.method == 'POST':
        try:
            import json
            
            # Check if it's multi-item sale (new system)
            cart_data_str = request.form.get('cart_data')
            
            if cart_data_str:
                # NEW: Multi-item sale
                cart_data = json.loads(cart_data_str)
                
                # Extract date from cart_data (optional)
                sale_date = cart_data.get('data')  # Will be None if not provided
                
                sales = sale_service.register_sale_multi_item(
                    id_cliente=cart_data['id_cliente'],
                    meio=cart_data['meio'],
                    items=cart_data['items'],
                    data=sale_date  # Pass the date (None = today)
                )
                
                return redirect(url_for('sales'))
            else:
                # LEGACY: Single item sale (for compatibility)
                sale_date = request.form.get('data')  # Optional date field
                
                sale = sale_service.register_sale(
                    id_cliente=request.form['id_cliente'],
                    codigo=request.form['codigo'],
                    quantidade=int(request.form['quantidade']),
                    meio=request.form['meio'],
                    preco_unit=float(request.form.get('preco_unit')) if request.form.get('preco_unit') else None,
                    data=sale_date if sale_date else None
                )
                return redirect(url_for('sales'))
                
        except Exception as e:
            # Em caso de erro no POST, recarrega os dados
            clients = client_service.list_all_clients()
            raw_products = product_service.list_all_products()
            
            products = []
            for p in raw_products:
                try:
                    p_copy = p.copy()
                    p_copy['VALOR'] = float(p['VALOR'])
                    p_copy['ESTOQUE'] = int(p['ESTOQUE'])
                    products.append(p_copy)
                except (ValueError, TypeError, KeyError):
                    p_copy = p.copy()
                    p_copy['VALOR'] = 0.0
                    p_copy['ESTOQUE'] = 0
                    products.append(p_copy)
            
            return render_template('add_sale.html',
                                 error=str(e),
                                 clients=clients,
                                 products=products,
                                 payment_methods=sale_service.get_available_payment_methods(),
                                 now=datetime.now(),  # Para o max date
                                 user=session)
    
    # Método GET - carregamento normal da página
    clients = client_service.list_all_clients()
    raw_products = product_service.list_all_products()
    
    # Converte os tipos numéricos para evitar erro no template
    products = []
    for p in raw_products:
        try:
            p_copy = p.copy()
            p_copy['VALOR'] = float(p['VALOR'])
            p_copy['ESTOQUE'] = int(p['ESTOQUE'])
            products.append(p_copy)
        except (ValueError, TypeError, KeyError):
            p_copy = p.copy()
            p_copy['VALOR'] = 0.0
            p_copy['ESTOQUE'] = 0
            products.append(p_copy)
    
    return render_template('add_sale.html',
                         clients=clients,
                         products=products,
                         payment_methods=sale_service.get_available_payment_methods(),
                         now=datetime.now(),  # Para o max date
                         user=session)

@app.route('/api/sales/summary', methods=['GET'])
@login_required
def api_sales_summary():
    """
    Get sales summary with CORRECT revenue calculation.
    Uses sales.csv (VALOR_TOTAL_VENDA) as the single source of truth.
    """
    try:
        from src.repositories.sale_repository import SaleRepository
        from src.repositories.sale_item_repository import SaleItemRepository
        import pandas as pd
        
        sale_repo = SaleRepository()
        item_repo = SaleItemRepository()
        
        # Get all sales (CORRECT SOURCE)
        sales_df = sale_repo.get_all()
        
        if sales_df.empty:
            return jsonify({
                'success': True,
                'data': {
                    'total_sales': 0,
                    'total_revenue': 0,
                    'total_items': 0,
                    'unique_sales': 0
                }
            })
        
        # Convert columns
        sales_df['VALOR_TOTAL_VENDA'] = pd.to_numeric(
            sales_df['VALOR_TOTAL_VENDA'], 
            errors='coerce'
        ).fillna(0)
        
        # Get items for total quantity
        items_df = item_repo.get_all()
        items_df['QUANTIDADE'] = pd.to_numeric(
            items_df['QUANTIDADE'], 
            errors='coerce'
        ).fillna(0)
        
        # Calculate metrics
        total_sales = len(items_df)  # Total line items
        total_revenue = float(sales_df['VALOR_TOTAL_VENDA'].sum())  # ← CORRECT
        total_items = int(items_df['QUANTIDADE'].sum())
        unique_sales = len(sales_df)  # Unique sale transactions
        
        return jsonify({
            'success': True,
            'data': {
                'total_sales': total_sales,
                'total_revenue': total_revenue,
                'total_items': total_items,
                'unique_sales': unique_sales
            }
        })
        
    except Exception as e:
        print(f"Error in sales summary: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== ANALYTICS ROUTES ==========

@app.route('/analytics')
@login_required
def analytics():
    """Analytics dashboard."""
    return render_template('analytics.html', user=session)


@app.route('/manuals')
@login_required
def manuals():
    """Manuals page."""
    manuals_list = manual_service.get_all_manuals()
    return render_template('manuals.html', manuals=manuals_list, user=session)


@app.route('/api/manuals', methods=['GET'])
@login_required
def api_get_manuals():
    """Get all manuals."""
    try:
        manuals_list = manual_service.get_all_manuals()
        return jsonify({'success': True, 'data': manuals_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/manuals/<manual_id>', methods=['GET'])
@login_required
def api_get_manual(manual_id):
    """Get specific manual by ID."""
    try:
        manual = manual_service.get_manual_by_id(manual_id)
        if manual:
            return jsonify({'success': True, 'data': manual})
        return jsonify({'success': False, 'error': 'Manual não encontrado'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/manuals/search', methods=['GET'])
@login_required
def api_search_manuals():
    """Search manuals."""
    try:
        query = request.args.get('q', '')
        results = manual_service.search_manuals(query)
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== REST API ENDPOINTS ==========

@app.route('/api/products', methods=['GET'])
@login_required
def api_get_products():
    """Get all products."""
    try:
        products = product_service.list_all_products()
        return jsonify({'success': True, 'data': products})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/products/<codigo>', methods=['GET'])
@login_required
def api_get_product(codigo):
    """Get product by code WITH MARGIN CALCULATIONS."""
    try:
        product = product_service.get_product(codigo)
        if product:
            # Calcular margens usando o expense_service
            custo = float(product.get('CUSTO', 0))
            valor = float(product.get('VALOR', 0))
            
            # Calcular margem de contribuição usando o método correto
            margin_data = expense_service.calculate_product_margin(
                sale_price=valor,
                cost_price=custo,
                quantity=1,
                payment_method='pix'  # Usa PIX como padrão (taxa de 3.5%)
            )
            
            # Adicionar dados calculados ao produto
            product['gross_margin_pct'] = margin_data['gross_margin_pct']
            product['contribution_margin_pct'] = margin_data['contribution_margin_pct']
            product['variable_costs'] = margin_data['variable_costs_total']
            
            return jsonify({'success': True, 'data': product})
        return jsonify({'success': False, 'error': 'Produto não encontrado'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/products', methods=['POST'])
@login_required
def api_create_product():
    """Create new product."""
    try:
        data = request.get_json()
        product = product_service.register_product(
            codigo=data['codigo'],
            produto=data['produto'],
            categoria=data['categoria'],
            custo=float(data['custo']),
            valor=float(data['valor']),
            estoque=int(data['estoque'])
        )
        return jsonify({'success': True, 'message': 'Produto criado com sucesso'}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    

@app.route('/api/products/adjust-stock', methods=['POST'])
@login_required
def api_adjust_stock():
    """Ajustar estoque manualmente via API"""
    try:
        data = request.get_json()
        codigo = data['codigo']
        quantity = int(data['quantity'])
        reason = data.get('reason', 'ajuste manual')

        product_service.adjust_stock(codigo, quantity, reason)
        
        return jsonify({'success': True, 'message': 'Estoque ajustado com sucesso'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/products/delete', methods=['POST'])
@login_required
@admin_required
def api_delete_product():
    """Deletar produto via API"""
    try:
        data = request.get_json()
        codigo = data['codigo']
        
        product_service.delete_product(codigo)
        
        return jsonify({'success': True, 'message': 'Produto removido com sucesso'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/clients', methods=['GET'])
@login_required
def api_get_clients():
    """Get all clients."""
    try:
        clients = client_service.list_all_clients()
        return jsonify({'success': True, 'data': clients})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    

@app.route('/api/clients/<id_cliente>', methods=['GET'])
@login_required
def api_get_client(id_cliente):
    """Obter cliente por ID"""
    try:
        client = client_service.get_client(id_cliente)
        if client:
            return jsonify({'success': True, 'data': client})
        return jsonify({'success': False, 'error': 'Cliente não encontrado'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/clients/delete', methods=['POST'])
@login_required
@admin_required
def api_delete_client():
    """Excluir cliente"""
    try:
        data = request.get_json()
        id_cliente = data['id_cliente']
        
        client_service.delete_client(id_cliente)
        
        return jsonify({'success': True, 'message': 'Cliente excluído com sucesso'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clients/paginated', methods=['GET'])
@login_required
def api_clients_paginated():
    """Get paginated clients (50 per page)."""
    try:
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 50))
        
        clients = client_service.list_all_clients()
        
        # Sort by ID descending
        clients.sort(key=lambda x: x.get('ID_CLIENTE', ''), reverse=True)
        
        total = len(clients)
        paginated = clients[offset:offset + limit]
        has_more = (offset + limit) < total
        
        return jsonify({
            'success': True,
            'data': paginated,
            'has_more': has_more,
            'total': total
        })
        
    except Exception as e:
        print(f"Error in paginated clients: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sales', methods=['GET'])
@login_required
def api_get_sales():
    """Get all sales."""
    try:
        sales = sale_service.list_all_sales()
        return jsonify({'success': True, 'data': sales})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sales', methods=['POST'])
@login_required
def api_create_sale():
    """Create new sale."""
    try:
        data = request.get_json()
        sale = sale_service.register_sale(
            id_cliente=data['id_cliente'],
            codigo=data['codigo'],
            quantidade=int(data['quantidade']),
            meio=data['meio'],
            preco_unit=float(data.get('preco_unit')) if data.get('preco_unit') else None
        )
        return jsonify({'success': True, 'message': 'Venda registrada com sucesso'}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/sales/<id_venda>', methods=['GET'])
@login_required
def api_get_sale(id_venda):
    """Obter detalhes de uma venda por ID"""
    try:
        sale = sale_service.get_sale(id_venda)
        if sale:
            return jsonify({'success': True, 'data': sale})
        return jsonify({'success': False, 'error': 'Venda não encontrada'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sales/group/<id_venda>', methods=['GET'])
@login_required
def api_get_sale_group(id_venda):
    """Get ALL items from a sale (for multi-item sales)."""
    try:
        from src.repositories.sale_repository import SaleRepository
        from src.repositories.sale_item_repository import SaleItemRepository
        
        sale_repo = SaleRepository()
        item_repo = SaleItemRepository()
        
        # Get sale header
        sale_header = sale_repo.get_by_id(id_venda)
        if not sale_header:
            return jsonify({'success': False, 'error': 'Venda não encontrada'}), 404
        
        # Get all items
        items = item_repo.get_by_sale_id(id_venda)
        
        # Add sale header data to each item
        for item in items:
            item['DATA'] = sale_header['DATA']
            item['CLIENTE'] = sale_header['CLIENTE']
            item['ID_CLIENTE'] = sale_header['ID_CLIENTE']
            item['MEIO'] = sale_header['MEIO']
            item['VALOR_TOTAL_VENDA'] = sale_header['VALOR_TOTAL_VENDA']
        
        return jsonify({'success': True, 'data': items})
        
    except Exception as e:
        print(f"Error in sale group: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sales/delete', methods=['POST'])
@login_required
@admin_required
def api_delete_sale():
    """Excluir uma venda e restaurar estoque"""
    try:
        data = request.get_json()
        id_venda = data['id_venda']
        
        sale_service.cancel_sale(id_venda, restore_stock=True)
        
        return jsonify({'success': True, 'message': 'Venda excluída com sucesso'})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sales/paginated', methods=['GET'])
@login_required
def api_sales_paginated():
    """Get paginated sales (50 per page)."""
    try:
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 50))
        
        from src.repositories.sale_repository import SaleRepository
        from src.repositories.sale_item_repository import SaleItemRepository
        
        sale_repo = SaleRepository()
        item_repo = SaleItemRepository()
        
        # Get all sales and items
        sales_df = sale_repo.get_all()
        items_df = item_repo.get_all()
        
        if items_df.empty:
            return jsonify({
                'success': True,
                'data': [],
                'has_more': False,
                'total': 0
            })
        
        # Join with sales_df to get DATA
        merged_df = items_df.merge(sales_df[['ID_VENDA', 'DATA']], on='ID_VENDA', how='left')
        
        # Parse dates for accurate sorting
        def safe_parse_date(d):
            try:
                # Try DD/MM/YYYY
                return datetime.strptime(str(d), '%d/%m/%Y')
            except ValueError:
                try:
                    # Try YYYY-MM-DD
                    return datetime.strptime(str(d).split(' ')[0], '%Y-%m-%d')
                except ValueError:
                    return datetime.min

        merged_df['_sort_date'] = merged_df['DATA'].apply(safe_parse_date)
        
        # Sort by date descending (most recent first) and ID_VENDA as tie-breaker
        merged_df = merged_df.sort_values(by=['_sort_date', 'ID_VENDA'], ascending=[False, False])
        
        # Get paginated slice
        total = len(merged_df)
        paginated_items = merged_df.iloc[offset:offset + limit]
        
        # Build result
        results = []
        for _, item in paginated_items.iterrows():
            sale_header = sales_df[sales_df['ID_VENDA'] == item['ID_VENDA']]
            
            if sale_header.empty:
                continue
            
            sale = sale_header.iloc[0]
            
            try:
                results.append({
                    'ID_VENDA': sale['ID_VENDA'],
                    'DATA': sale['DATA'],
                    'CLIENTE': sale['CLIENTE'],
                    'ID_CLIENTE': sale['ID_CLIENTE'],
                    'PRODUTO': str(item.get('PRODUTO', '')).strip().title(),
                    'CODIGO': item['CODIGO'],
                    'CATEGORIA': str(item.get('CATEGORIA', '')).strip().title(),
                    'QUANTIDADE': int(item['QUANTIDADE']),
                    'PRECO_UNIT': float(item['PRECO_UNIT']),
                    'PRECO_TOTAL': float(item['PRECO_TOTAL']),
                    'MEIO': sale['MEIO'],
                    'VALOR_TOTAL_VENDA': float(sale['VALOR_TOTAL_VENDA'])
                })
            except (ValueError, KeyError, TypeError):
                continue
        
        has_more = (offset + limit) < total
        
        return jsonify({
            'success': True,
            'data': results,
            'has_more': has_more,
            'total': total
        })
        
    except Exception as e:
        print(f"Error in paginated sales: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics/summary', methods=['GET'])
@login_required
def api_analytics_summary():
    """Get sales summary."""
    try:
        summary = sale_service.get_sales_summary()
        return jsonify({'success': True, 'data': summary})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/trend', methods=['GET'])
@login_required
def api_sales_trend():
    """Get sales trend."""
    try:
        days = int(request.args.get('days', 30))
        trend = analytics_service.get_sales_trend(days)
        return jsonify({'success': True, 'data': trend})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500





@app.route('/api/analytics/customer-segments', methods=['GET'])
@login_required
def api_customer_segments():
    """Get customer segmentation."""
    try:
        segments = analytics_service.get_customer_segmentation()
        return jsonify({'success': True, 'data': segments})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    

@app.route('/api/analytics/categories', methods=['GET'])
@login_required
def api_categories():
    """Get category analysis - OTIMIZADO."""
    try:
        # OTIMIZADO: get_category_stats() agora retorna List[Dict]
        category_stats = analytics_service.get_category_analysis()
        
        if not category_stats or not category_stats.get('categories'):
            return jsonify({'success': True, 'data': {'categories': []}})
        
        return jsonify({
            'success': True,
            'data': category_stats
        })
        
    except Exception as e:
        print(f"Error in categories: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/payment-methods', methods=['GET'])
@login_required
def api_payment_methods():
    """Get payment methods analysis - FIXED."""
    try:
        # Log para debug
        from src.repositories.sale_repository import SaleRepository
        sale_repo = SaleRepository()
        sales_count = sale_repo.count()
        print(f"[ANALYTICS] payment_methods: total sales={sales_count}")
        
        # Usa analytics_service que já retorna dados corretos
        payment_data = analytics_service.get_payment_method_analysis()
        
        return jsonify({'success': True, 'data': payment_data})
        
    except Exception as e:
        print(f"Error in payment methods: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== NEW API ENDPOINTS FOR DASHBOARD/ANALYTICS ==========

@app.route('/api/analytics/monthly-revenue', methods=['GET'])
@login_required
def api_monthly_revenue():
    """Get monthly revenue for last 12 months - FIXED."""
    try:
        from collections import defaultdict
        from src.repositories.sale_repository import SaleRepository
        
        sale_repo = SaleRepository()
        
        # OTIMIZADO: Pega apenas colunas necessárias
        sales = sale_repo.find_all(columns=['ID_VENDA', 'DATA', 'VALOR_TOTAL_VENDA'])
        
        print(f"[ANALYTICS] monthly_revenue: sales rows={len(sales)}")
        
        if not sales:
            return jsonify({
                'success': True,
                'data': {
                    'months': [],
                    'revenues': []
                }
            })
        
        # Parse dates
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                try:
                    return datetime.strptime(date_str, '%d/%m/%Y')
                except ValueError:
                    return None
        
        # Get last 12 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        monthly_data = defaultdict(float)
        
        for sale in sales:
            sale_date = parse_date(sale.get('DATA'))
            if not sale_date or sale_date < start_date:
                continue
            
            month_key = sale_date.strftime('%Y-%m')
            monthly_data[month_key] += float(sale.get('VALOR_TOTAL_VENDA', 0))
        
        # Generate last 12 months with data
        months = []
        revenues = []
        
        for i in range(11, -1, -1):
            month_date = end_date - timedelta(days=30*i)
            month_key = month_date.strftime('%Y-%m')
            month_label = month_date.strftime('%b/%y')
            
            months.append(month_label)
            revenues.append(round(monthly_data.get(month_key, 0), 2))
        
        return jsonify({
            'success': True,
            'data': {
                'months': months,
                'revenues': revenues
            }
        })
    except Exception as e:
        print(f"Error in monthly revenue: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/analytics/monthly-financial-summary', methods=['GET'])
@login_required
def api_monthly_financial_summary():
    """Resumo financeiro do mês atual - FIXED."""
    try:
        from src.repositories.sale_repository import SaleRepository
        from src.repositories.sale_item_repository import SaleItemRepository
        from src.repositories.product_repository import ProductRepository
        from datetime import datetime, timedelta
        
        sale_repo = SaleRepository()
        item_repo = SaleItemRepository()
        product_repo = ProductRepository()
        
        # Mês atual
        current_month = datetime.now().strftime('%m/%Y')
        
        # Pegar vendas do mês com SQL direto
        with sale_repo.get_conn() as conn:
            cur = sale_repo._get_cursor(conn)
            cur.execute('SELECT "ID_VENDA", "DATA", "VALOR_TOTAL_VENDA" FROM sales')
            all_sales = cur.fetchall()
        
        # Filtrar vendas do mês atual em Python
        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                try:
                    return datetime.strptime(date_str, '%d/%m/%Y')
                except ValueError:
                    return None
        
        month_sales = []
        for sale in all_sales:
            sale_date = parse_date(sale['DATA'])
            if sale_date and sale_date.strftime('%m/%Y') == current_month:
                month_sales.append(sale)
        
        print(f"[ANALYTICS] monthly_financial_summary: month_sales count={len(month_sales)}")
        
        if not month_sales:
            return jsonify({
                'success': True,
                'data': {
                    'total_revenue': 0,
                    'gross_margin_pct': 0,
                    'contribution_margin_pct': 0,
                    'fixed_expenses': expense_service.get_total_monthly_expenses(),
                    'net_profit': 0
                }
            })
        
        # Calcular receita total
        total_revenue = sum(float(s['VALOR_TOTAL_VENDA'] or 0) for s in month_sales)
        sale_ids = [s['ID_VENDA'] for s in month_sales]
        
        # Pegar itens do mês (SQL direto)
        with item_repo.get_conn() as conn:
            cur = item_repo._get_cursor(conn)
            
            placeholders = ','.join(['%s' if item_repo.db_type == 'postgresql' else '?' for _ in sale_ids])
            
            cur.execute(f'''
                SELECT 
                    "CODIGO",
                    "QUANTIDADE"
                FROM sales_items
                WHERE "ID_VENDA" IN ({placeholders})
            ''', sale_ids)
            
            month_items = cur.fetchall()
        
        print(f"[ANALYTICS] monthly_financial_summary: month_items count={len(month_items)}")
        
        # Pegar custos dos produtos (JOIN SQL)
        with product_repo.get_conn() as conn:
            cur = product_repo._get_cursor(conn)
            cur.execute('SELECT "CODIGO", "CUSTO" FROM products')
            product_costs = {row['CODIGO']: float(row['CUSTO'] or 0) for row in cur.fetchall()}
        
        # Calcular COGS
        total_cogs = 0
        total_units = 0
        
        for item in month_items:
            codigo = item['CODIGO']
            quantidade = int(item['QUANTIDADE'] or 0)
            custo = product_costs.get(codigo, 0)
            
            total_cogs += custo * quantidade
            total_units += quantidade
        
        # Calcular custos variáveis (IGUAL À VERSÃO ANTES)
        payment_fees = total_revenue * 0.035
        packaging_costs = total_units * 3.0
        total_variable_costs = payment_fees + packaging_costs
        
        # Margens
        gross_profit = total_revenue - total_cogs
        gross_margin_pct = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        contribution_margin = gross_profit - total_variable_costs
        contribution_margin_pct = (contribution_margin / total_revenue * 100) if total_revenue > 0 else 0
        
        # Despesas fixas
        fixed_expenses = expense_service.get_total_monthly_expenses()
        
        # Lucro líquido
        net_profit = contribution_margin - fixed_expenses
        
        return jsonify({
            'success': True,
            'data': {
                'total_revenue': float(total_revenue),
                'total_cogs': float(total_cogs),
                'total_variable_costs': float(total_variable_costs),
                'gross_profit': float(gross_profit),
                'gross_margin_pct': float(gross_margin_pct),
                'contribution_margin': float(contribution_margin),
                'contribution_margin_pct': float(contribution_margin_pct),
                'fixed_expenses': float(fixed_expenses),
                'net_profit': float(net_profit)
            }
        })
        
    except Exception as e:
        print(f"Error in financial summary: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/monthly-profit', methods=['GET'])
@login_required
def api_monthly_profit_updated():
    """Lucro líquido mensal (12 meses) - FIXED."""
    try:
        from collections import defaultdict
        from src.repositories.sale_repository import SaleRepository
        from src.repositories.sale_item_repository import SaleItemRepository
        from src.repositories.product_repository import ProductRepository
        from datetime import datetime, timedelta

        sale_repo = SaleRepository()
        item_repo = SaleItemRepository()
        product_repo = ProductRepository()

        # Pega todas as vendas
        sales = sale_repo.find_all(columns=['ID_VENDA', 'DATA', 'VALOR_TOTAL_VENDA'])
        
        if not sales:
            return jsonify({
                'success': True,
                'data': {
                    'months': [],
                    'net_profits': [],
                    'gross_margins': [],
                    'contribution_margins': []
                }
            })

        # Parse dates
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                try:
                    return datetime.strptime(date_str, '%d/%m/%Y')
                except ValueError:
                    return None

        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        # Filtra últimos 12 meses e agrupa por mês
        monthly_data = defaultdict(lambda: {
            'revenue': 0.0,
            'sale_ids': []
        })

        for sale in sales:
            sale_date = parse_date(sale.get('DATA'))
            if not sale_date or sale_date < start_date:
                continue
            
            month_key = sale_date.strftime('%Y-%m')
            monthly_data[month_key]['revenue'] += float(sale.get('VALOR_TOTAL_VENDA', 0))
            monthly_data[month_key]['sale_ids'].append(sale['ID_VENDA'])

        print(f"[ANALYTICS] monthly_profit: processing {len(monthly_data)} months")

        # Pega TODOS os itens de uma vez
        all_items = item_repo.find_all(columns=['ID_VENDA', 'CODIGO', 'QUANTIDADE'])
        
        # Pega TODOS os custos de produtos
        products = product_repo.find_all(columns=['CODIGO', 'CUSTO'])
        product_costs = {p['CODIGO']: float(p['CUSTO'] or 0) for p in products}

        # Calcula COGS e unidades por mês
        for month_key, data in monthly_data.items():
            sale_ids_set = set(data['sale_ids'])
            
            cogs = 0.0
            units = 0
            
            for item in all_items:
                if item['ID_VENDA'] in sale_ids_set:
                    codigo = item['CODIGO']
                    quantidade = int(item['QUANTIDADE'] or 0)
                    custo = product_costs.get(codigo, 0)
                    
                    cogs += custo * quantidade
                    units += quantidade
            
            data['cogs'] = cogs
            data['units'] = units

        # Despesas fixas
        fixed_expenses = expense_service.get_total_monthly_expenses()

        # Gera resultados para últimos 12 meses
        months = []
        net_profits = []
        gross_margins = []
        contribution_margins = []

        for i in range(11, -1, -1):
            month_date = end_date - timedelta(days=30 * i)
            month_key = month_date.strftime('%Y-%m')
            month_label = month_date.strftime('%b/%y')

            months.append(month_label)

            data = monthly_data.get(month_key, {'revenue': 0, 'cogs': 0, 'units': 0})

            revenue = data['revenue']
            cogs = data['cogs']
            units = data['units']

            # Custos variáveis
            payment_fee = revenue * 0.035
            packaging = units * 2.0
            cards = units * 1.0
            shipping = len(data.get('sale_ids', [])) * 1.50

            variable_costs = payment_fee + packaging + cards + shipping

            # Margens
            gross_profit = revenue - cogs
            gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0

            contribution = gross_profit - variable_costs
            contribution_margin = (contribution / revenue * 100) if revenue > 0 else 0

            net_profit = contribution - fixed_expenses

            net_profits.append(round(net_profit, 2))
            gross_margins.append(round(gross_margin, 2))
            contribution_margins.append(round(contribution_margin, 2))

        return jsonify({
            'success': True,
            'data': {
                'months': months,
                'net_profits': net_profits,
                'gross_margins': gross_margins,
                'contribution_margins': contribution_margins
            }
        })

    except Exception as e:
        print(f"Error in monthly profit: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/api/analytics/cost-breakdown', methods=['GET'])
@login_required
def api_cost_breakdown():
    """Breakdown de custos do mês atual - FIXED."""
    try:
        from src.repositories.sale_repository import SaleRepository
        from src.repositories.sale_item_repository import SaleItemRepository
        from src.repositories.product_repository import ProductRepository
        from datetime import datetime
        
        sale_repo = SaleRepository()
        item_repo = SaleItemRepository()
        product_repo = ProductRepository()
        
        # Mês atual
        current_month = datetime.now().strftime('%m/%Y')
        
        # Pegar vendas do mês
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                try:
                    return datetime.strptime(date_str, '%d/%m/%Y')
                except ValueError:
                    return None
        
        sales = sale_repo.find_all(columns=['ID_VENDA', 'DATA', 'VALOR_TOTAL_VENDA'])
        
        # Filtra mês atual
        month_sales = []
        for sale in sales:
            sale_date = parse_date(sale.get('DATA'))
            if sale_date and sale_date.strftime('%m/%Y') == current_month:
                month_sales.append(sale)
        
        print(f"[ANALYTICS] cost_breakdown: month_sales count={len(month_sales)}")
        
        if not month_sales:
            return jsonify({
                'success': True,
                'data': {
                    'total_cogs': 0,
                    'total_variable_costs': 0,
                    'total_fixed_expenses': expense_service.get_total_monthly_expenses()
                }
            })
        
        # COGS
        sale_ids = [s['ID_VENDA'] for s in month_sales]
        sale_ids_set = set(sale_ids)
        
        all_items = item_repo.find_all(columns=['ID_VENDA', 'CODIGO', 'QUANTIDADE'])
        products = product_repo.find_all(columns=['CODIGO', 'CUSTO'])
        product_costs = {p['CODIGO']: float(p['CUSTO'] or 0) for p in products}
        
        total_cogs = 0
        total_units = 0
        
        for item in all_items:
            if item['ID_VENDA'] in sale_ids_set:
                quantidade = int(item['QUANTIDADE'] or 0)
                custo = product_costs.get(item['CODIGO'], 0)
                total_cogs += custo * quantidade
                total_units += quantidade
        
        # Variable costs
        total_revenue = sum(float(s['VALOR_TOTAL_VENDA'] or 0) for s in month_sales)
        payment_fees = total_revenue * 0.035
        packaging = total_units * 3.0
        total_variable_costs = payment_fees + packaging
        
        # Fixed expenses
        total_fixed_expenses = expense_service.get_total_monthly_expenses()
        
        return jsonify({
            'success': True,
            'data': {
                'total_cogs': float(total_cogs),
                'total_variable_costs': float(total_variable_costs),
                'total_fixed_expenses': float(total_fixed_expenses)
            }
        })
        
    except Exception as e:
        print(f"Error in cost breakdown: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/breakeven-progress', methods=['GET'])
@login_required
def api_breakeven_progress():
    """Progresso de break-even - FIXED."""
    try:
        from src.repositories.sale_repository import SaleRepository
        from src.repositories.sale_item_repository import SaleItemRepository
        from src.repositories.product_repository import ProductRepository
        from datetime import datetime, timedelta
        
        sale_repo = SaleRepository()
        item_repo = SaleItemRepository()
        product_repo = ProductRepository()
        
        # Mês atual
        current_month = datetime.now().strftime('%m/%Y')
        
        # Pegar vendas do mês
        with sale_repo.get_conn() as conn:
            cur = sale_repo._get_cursor(conn)
            cur.execute('SELECT "ID_VENDA", "DATA", "VALOR_TOTAL_VENDA" FROM sales')
            all_sales = cur.fetchall()
        
        # Filtrar vendas do mês atual em Python
        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                try:
                    return datetime.strptime(date_str, '%d/%m/%Y')
                except ValueError:
                    return None
        
        month_sales = []
        for sale in all_sales:
            sale_date = parse_date(sale['DATA'])
            if sale_date and sale_date.strftime('%m/%Y') == current_month:
                month_sales.append(sale)
        
        # Despesas fixas
        fixed_expenses = expense_service.get_total_monthly_expenses()
        
        if not month_sales:
            return jsonify({
                'success': True,
                'data': {
                    'current_sales': 0,
                    'breakeven_sales': 0,
                    'progress_pct': 0,
                    'remaining_sales': 0,
                    'contribution_accumulated': 0,
                    'fixed_expenses': fixed_expenses
                }
            })
        
        # Calcular contribuição
        total_revenue = sum(float(s['VALOR_TOTAL_VENDA'] or 0) for s in month_sales)
        sale_ids = [s['ID_VENDA'] for s in month_sales]
        
        # Pegar itens + custos
        with item_repo.get_conn() as conn:
            cur = item_repo._get_cursor(conn)
            placeholders = ','.join(['%s' if item_repo.db_type == 'postgresql' else '?' for _ in sale_ids])
            
            cur.execute(f'''
                SELECT 
                    si."CODIGO",
                    si."QUANTIDADE",
                    COALESCE(p."CUSTO", 0) AS custo
                FROM sales_items si
                LEFT JOIN products p ON si."CODIGO" = p."CODIGO"
                WHERE si."ID_VENDA" IN ({placeholders})
            ''', sale_ids)
            
            month_items = cur.fetchall()
        
        total_cogs = 0
        total_units = 0
        
        for item in month_items:
            quantidade = int(item['QUANTIDADE'] or 0)
            custo = float(item['custo'] or 0)
            total_cogs += custo * quantidade
            total_units += quantidade
        
        # Custos variáveis
        payment_fees = total_revenue * 0.035
        packaging = total_units * 2.0
        cards = total_units * 1.0
        shipping = len(month_sales) * 1.50
        total_variable_costs = payment_fees + packaging + cards + shipping
        
        # Contribuição
        gross_profit = total_revenue - total_cogs
        contribution_total = gross_profit - total_variable_costs
        
        # Vendas atuais
        current_sales = len(month_sales)
        
        # Contribuição média por venda
        avg_contribution = contribution_total / current_sales if current_sales > 0 else 0
        
        # Break-even
        breakeven_sales = fixed_expenses / avg_contribution if avg_contribution > 0 else float('inf')
        
        # Progresso
        progress_pct = (current_sales / breakeven_sales * 100) if breakeven_sales > 0 and breakeven_sales != float('inf') else 0
        remaining_sales = max(0, breakeven_sales - current_sales)
        
        return jsonify({
            'success': True,
            'data': {
                'current_sales': int(current_sales),
                'breakeven_sales': round(breakeven_sales, 0) if breakeven_sales != float('inf') else 0,
                'progress_pct': round(progress_pct, 1),
                'remaining_sales': round(remaining_sales, 0),
                'contribution_accumulated': round(contribution_total, 2),
                'fixed_expenses': round(fixed_expenses, 2),
                'avg_contribution_per_sale': round(avg_contribution, 2)
            }
        })
        
    except Exception as e:
        print(f"Error in breakeven: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/analytics/products-performance', methods=['GET'])
@login_required
def api_products_performance():
    """Análise detalhada de produtos - OTIMIZADO."""
    try:
        # OTIMIZADO: Usa get_product_performance() que já faz JOIN
        performance = analytics_service.get_product_performance(top_n=20)
        
        return jsonify({
            'success': True,
            'data': performance['top_products']
        })
        
    except Exception as e:
        print(f"Error in products performance: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics/clients-performance', methods=['GET'])
@login_required
def api_clients_performance():
    """Análise detalhada de clientes."""
    try:
        from src.repositories.sale_repository import SaleRepository
        from collections import defaultdict
        
        sale_repo = SaleRepository()
        sales_df = sale_repo.get_all()
        
        if sales_df.empty:
            return jsonify({'success': True, 'data': []})
        
        # Converter colunas
        sales_df['VALOR_TOTAL_VENDA'] = pd.to_numeric(sales_df['VALOR_TOTAL_VENDA'], errors='coerce').fillna(0)
        
        # Agrupar por cliente
        client_stats = sales_df.groupby(['ID_CLIENTE', 'CLIENTE']).agg({
            'VALOR_TOTAL_VENDA': 'sum',
            'ID_VENDA': 'count'
        }).reset_index()
        
        client_stats.columns = ['ID_CLIENTE', 'CLIENTE', 'TOTAL_GASTO', 'NUM_COMPRAS']
        client_stats = client_stats.sort_values('TOTAL_GASTO', ascending=False).head(20)
        
        results = []
        for _, row in client_stats.iterrows():
            results.append({
                'id_cliente': row['ID_CLIENTE'],
                'cliente': row['CLIENTE'],
                'total_gasto': float(row['TOTAL_GASTO']),
                'num_compras': int(row['NUM_COMPRAS']),
                'ticket_medio': float(row['TOTAL_GASTO'] / row['NUM_COMPRAS']) if row['NUM_COMPRAS'] > 0 else 0
            })
        
        return jsonify({'success': True, 'data': results})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/analytics/sales-overview', methods=['GET'])
@login_required
def api_sales_overview():
    """Visão geral de vendas - FIXED."""
    try:
        from src.repositories.sale_repository import SaleRepository
        from src.repositories.sale_item_repository import SaleItemRepository
        
        sale_repo = SaleRepository()
        item_repo = SaleItemRepository()
        
        # Get summary (já otimizado)
        summary = sale_repo.get_sales_summary()
        
        print(f"[ANALYTICS] sales_overview: summary={summary}")
        
        # Total de transações únicas (vendas)
        total_vendas = summary['total_sales']
        total_receita = summary['total_revenue']
        total_itens = summary['total_items_sold']
        ticket_medio = summary['average_sale_value']
        
        # Por meio de pagamento
        by_payment = summary['by_payment_method']
        
        # Por categoria
        by_category = summary['by_category']
        
        return jsonify({
            'success': True,
            'data': {
                'total_vendas': total_vendas,
                'total_receita': total_receita,
                'total_itens': total_itens,
                'ticket_medio': ticket_medio,
                'by_payment': by_payment,
                'by_month': {}  # Opcional
            }
        })
        
    except Exception as e:
        print(f"Error in sales overview: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics/monthly-sales-count', methods=['GET'])
@login_required
def api_monthly_sales_count():
    """Quantidade de vendas por mês - FIXED."""
    try:
        from collections import defaultdict
        from src.repositories.sale_repository import SaleRepository
        
        sale_repo = SaleRepository()
        sales = sale_repo.find_all(columns=['DATA'])
        
        if not sales:
            return jsonify({'success': True, 'data': {'months': [], 'counts': []}})
        
        # Parse dates
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                try:
                    return datetime.strptime(date_str, '%d/%m/%Y')
                except ValueError:
                    return None
        
        # Get last 12 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        monthly_counts = defaultdict(int)
        
        for sale in sales:
            sale_date = parse_date(sale.get('DATA'))
            if not sale_date or sale_date < start_date:
                continue
            
            month_key = sale_date.strftime('%Y-%m')
            monthly_counts[month_key] += 1
        
        # Generate last 12 months
        months = []
        counts = []
        
        for i in range(11, -1, -1):
            month_date = end_date - timedelta(days=30*i)
            month_key = month_date.strftime('%Y-%m')
            month_label = month_date.strftime('%b/%y')
            
            months.append(month_label)
            counts.append(monthly_counts.get(month_key, 0))
        
        return jsonify({
            'success': True,
            'data': {
                'months': months,
                'counts': counts
            }
        })
        
    except Exception as e:
        print(f"Error in monthly sales count: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/monthly-margin', methods=['GET'])
@login_required
def api_monthly_margin():
    """Margem bruta e líquida por mês - FIXED."""
    try:
        from collections import defaultdict
        from src.repositories.sale_repository import SaleRepository
        from src.repositories.sale_item_repository import SaleItemRepository
        from src.repositories.product_repository import ProductRepository
        from datetime import datetime, timedelta
        
        sale_repo = SaleRepository()
        item_repo = SaleItemRepository()
        product_repo = ProductRepository()
        
        sales = sale_repo.find_all(columns=['ID_VENDA', 'DATA', 'VALOR_TOTAL_VENDA'])
        
        if not sales:
            return jsonify({
                'success': True,
                'data': {
                    'months': [],
                    'gross_margins': [],
                    'net_margins': []
                }
            })
        
        # Parse dates
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                try:
                    return datetime.strptime(date_str, '%d/%m/%Y')
                except ValueError:
                    return None
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # Agrupa vendas por mês
        monthly_data = defaultdict(lambda: {'revenue': 0, 'sale_ids': []})
        
        for sale in sales:
            sale_date = parse_date(sale.get('DATA'))
            if not sale_date or sale_date < start_date:
                continue
            
            month_key = sale_date.strftime('%Y-%m')
            monthly_data[month_key]['revenue'] += float(sale.get('VALOR_TOTAL_VENDA', 0))
            monthly_data[month_key]['sale_ids'].append(sale['ID_VENDA'])
        
        # Pega itens e custos
        all_items = item_repo.find_all(columns=['ID_VENDA', 'CODIGO', 'QUANTIDADE'])
        products = product_repo.find_all(columns=['CODIGO', 'CUSTO'])
        product_costs = {p['CODIGO']: float(p['CUSTO'] or 0) for p in products}
        
        # Calcula custos por mês
        for month_key, data in monthly_data.items():
            sale_ids_set = set(data['sale_ids'])
            
            cogs = 0.0
            for item in all_items:
                if item['ID_VENDA'] in sale_ids_set:
                    quantidade = int(item['QUANTIDADE'] or 0)
                    custo = product_costs.get(item['CODIGO'], 0)
                    cogs += custo * quantidade
            
            data['cogs'] = cogs
        
        # Despesas fixas mensais
        monthly_expenses = expense_service.get_total_monthly_expenses()
        
        # Gera resultados
        months = []
        gross_margins = []
        net_margins = []
        
        for i in range(11, -1, -1):
            month_date = end_date - timedelta(days=30*i)
            month_key = month_date.strftime('%Y-%m')
            month_label = month_date.strftime('%b/%y')
            
            months.append(month_label)
            
            data = monthly_data.get(month_key, {'revenue': 0, 'cogs': 0})
            
            revenue = data['revenue']
            cogs = data['cogs']
            
            gross_profit = revenue - cogs
            net_profit = gross_profit - monthly_expenses
            
            gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0
            net_margin = (net_profit / revenue * 100) if revenue > 0 else 0
            
            gross_margins.append(round(gross_margin, 2))
            net_margins.append(round(net_margin, 2))
        
        return jsonify({
            'success': True,
            'data': {
                'months': months,
                'gross_margins': gross_margins,
                'net_margins': net_margins
            }
        })
        
    except Exception as e:
        print(f"Error in monthly margin: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/products-with-margin', methods=['GET'])
@login_required
def api_products_with_margin():
    """Top produtos com nome + categoria, margem - FIXED."""
    try:
        # OTIMIZADO: Usa get_product_performance() que já faz JOIN
        performance = analytics_service.get_product_performance(top_n=20)
        
        results = []
        for product in performance['top_products']:
            # Calcula custos variáveis
            revenue = product['revenue']
            quantity = product['quantity_sold']
            
            payment_fee = revenue * 0.035
            packaging = quantity * 3.0
            variable_costs = payment_fee + packaging
            
            gross_profit = product['profit']
            contribution = gross_profit - variable_costs
            contribution_margin = (contribution / revenue * 100) if revenue > 0 else 0
            
            results.append({
                'codigo': product['codigo'],
                'produto': product['produto'],
                'categoria': product['categoria'],
                'label': f"{product['produto']} - {product['categoria']}",
                'quantity_sold': quantity,
                'revenue': revenue,
                'gross_margin': product['profit_margin'],
                'contribution_margin': round(contribution_margin, 2),
                'net_margin': round(contribution_margin, 2)
            })
        
        return jsonify({'success': True, 'data': results})
        
    except Exception as e:
        print(f"Error in products with margin: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    

@app.route('/api/analytics/category-margin', methods=['GET'])
@login_required
def api_category_margin():
    """Margem por categoria - FIXED."""
    try:
        from src.repositories.sale_item_repository import SaleItemRepository
        from src.repositories.product_repository import ProductRepository
        
        item_repo = SaleItemRepository()
        product_repo = ProductRepository()
        
        # JOIN SQL para pegar receita + custo por categoria
        with item_repo.get_conn() as conn:
            cur = item_repo._get_cursor(conn)
            
            cur.execute('''
                SELECT 
                    si."CATEGORIA",
                    SUM(COALESCE(si."PRECO_TOTAL", 0)) AS receita,
                    SUM(COALESCE(p."CUSTO", 0) * COALESCE(si."QUANTIDADE", 0)) AS custo
                FROM sales_items si
                LEFT JOIN products p ON si."CODIGO" = p."CODIGO"
                GROUP BY si."CATEGORIA"
                ORDER BY receita DESC
            ''')
            
            category_stats = cur.fetchall()
        
        results = []
        for row in category_stats:
            receita = float(row['receita'] or 0)
            custo = float(row['custo'] or 0)
            gross_profit = receita - custo
            gross_margin = (gross_profit / receita * 100) if receita > 0 else 0
            
            results.append({
                'category': row['CATEGORIA'],
                'revenue': receita,
                'cost': custo,
                'gross_profit': gross_profit,
                'gross_margin': round(gross_margin, 2)
            })
        
        return jsonify({'success': True, 'data': results})
        
    except Exception as e:
        print(f"Error in category margin: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/avg-ticket-trend', methods=['GET'])
@login_required
def api_avg_ticket_trend():
    """Ticket médio mensal."""
    try:
        from src.repositories.sale_repository import SaleRepository
        import pandas as pd
        
        sale_repo = SaleRepository()
        sales_df = sale_repo.get_all()
        
        if sales_df.empty:
            return jsonify({'success': True, 'data': {'months': [], 'tickets': []}})
        
        # Convert dates (flexible parsing)
        print(f"[ANALYTICS] avg_ticket_trend: sales rows={len(sales_df)}")
        sales_df['DATA_DT'] = pd.to_datetime(sales_df['DATA'], format='%d/%m/%Y', errors='coerce')
        mask = sales_df['DATA_DT'].isna()
        if mask.any():
            sales_df.loc[mask, 'DATA_DT'] = sales_df.loc[mask, 'DATA'].apply(lambda s: pd.to_datetime(s, format='%Y-%m-%d', errors='coerce'))
        sales_df = sales_df[sales_df['DATA_DT'].notna()]
        sales_df['MONTH_KEY'] = sales_df['DATA_DT'].dt.strftime('%Y-%m')
        sales_df['VALOR_TOTAL_VENDA'] = pd.to_numeric(sales_df['VALOR_TOTAL_VENDA'], errors='coerce').fillna(0)
        
        # Get last 12 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        sales_df = sales_df[sales_df['DATA_DT'] >= start_date]
        
        # Calculate avg ticket per month
        monthly_avg = sales_df.groupby('MONTH_KEY')['VALOR_TOTAL_VENDA'].mean().to_dict()
        
        # Generate results
        months = []
        tickets = []
        
        for i in range(11, -1, -1):
            month_date = end_date - timedelta(days=30*i)
            month_key = month_date.strftime('%Y-%m')
            month_label = month_date.strftime('%b/%y')
            
            months.append(month_label)
            tickets.append(round(monthly_avg.get(month_key, 0), 2))
        
        return jsonify({
            'success': True,
            'data': {
                'months': months,
                'tickets': tickets
            }
        })
        
    except Exception as e:
        print(f"Error in avg ticket trend: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    

    
@app.route('/api/expenses', methods=['GET'])
@login_required
def api_get_expenses():
    """Get all monthly expenses."""
    try:
        expenses = expense_service.get_expenses_breakdown()
        total = expense_service.get_total_monthly_expenses()
        
        return jsonify({
            'success': True,
            'data': {
                'expenses': expenses,
                'total': total
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/new-customers', methods=['GET'])
@login_required
def api_new_customers():
    """Get count of new customers in selected period - FIXED."""
    try:
        from src.repositories.sale_repository import SaleRepository
        
        days = int(request.args.get('days', 30))
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        sale_repo = SaleRepository()
        sales = sale_repo.get_all().to_dict('records')
        
        # Track first purchase date for each customer
        customer_first_purchase = {}
        
        import pandas as _pd
        for sale in sales:
            date_ts = _pd.to_datetime(sale.get('DATA'), dayfirst=True, errors='coerce')
            if pd.isna(date_ts):
                continue
            sale_date = date_ts.to_pydatetime()
            customer_id = str(sale.get('ID_CLIENTE'))

            if customer_id not in customer_first_purchase:
                customer_first_purchase[customer_id] = sale_date
            elif sale_date < customer_first_purchase[customer_id]:
                customer_first_purchase[customer_id] = sale_date
        
        # Count new customers in period
        new_customers = sum(
            1 for first_date in customer_first_purchase.values()
            if start_date <= first_date <= end_date
        )
        
        return jsonify({
            'success': True,
            'data': {'new_customers': new_customers}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/return-rate', methods=['GET'])
@login_required
def api_return_rate():
    """Calculate customer return rate - FIXED."""
    try:
        from collections import defaultdict
        from src.repositories.sale_repository import SaleRepository
        
        sale_repo = SaleRepository()
        sales = sale_repo.get_all().to_dict('records')
        customer_purchases = defaultdict(int)
        
        for sale in sales:
            customer_purchases[str(sale['ID_CLIENTE'])] += 1
        
        total_customers = len(customer_purchases)
        returning_customers = sum(1 for count in customer_purchases.values() if count > 1)
        
        return_rate = (returning_customers / total_customers * 100) if total_customers > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {'return_rate': round(return_rate, 1)}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/top-category', methods=['GET'])
@login_required
def api_top_category():
    """Get top selling category - FIXED."""
    try:
        # Usa get_category_analysis() que já faz agregação SQL
        category_data = analytics_service.get_category_analysis()
        
        if not category_data or not category_data.get('categories'):
            return jsonify({'success': True, 'data': {'category': '-'}})
        
        # Pega categoria com maior receita
        top_category = category_data['categories'][0]['category']
        
        return jsonify({
            'success': True,
            'data': {'category': top_category}
        })
        
    except Exception as e:
        print(f"Error in top category: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/gender-distribution', methods=['GET'])
@login_required
def api_gender_distribution():
    """Get gender distribution of customers."""
    try:
        from collections import defaultdict
        
        clients = client_service.list_all_clients()
        gender_count = defaultdict(int)
        
        for client in clients:
            tipo_lower = str(client.get('TIPO', '')).lower()
            gender = client.get('GENERO', '')
            
            if gender and tipo_lower == 'pessoa':
                gender_count[gender] += 1
        
        return jsonify({
            'success': True,
            'data': {
                'labels': list(gender_count.keys()),
                'values': list(gender_count.values())
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/seller-distribution', methods=['GET'])
@login_required
def api_seller_distribution():
    """Get distribution by seller - FIXED."""
    try:
        from collections import defaultdict
        from src.repositories.sale_repository import SaleRepository
        
        sale_repo = SaleRepository()
        sales = sale_repo.get_all().to_dict('records')
        clients = {str(c['ID_CLIENTE']): c for c in client_service.list_all_clients()}
        
        seller_revenue = defaultdict(float)
        
        for sale in sales:
            client = clients.get(str(sale['ID_CLIENTE']))
            if client:
                seller = client.get('VENDEDOR', 'Sem Vendedor')
                if not seller or not seller.strip():
                    seller = 'Sem Vendedor'
                seller_revenue[seller] += float(sale['VALOR_TOTAL_VENDA'])
        
        return jsonify({
            'success': True,
            'data': {
                'labels': list(seller_revenue.keys()),
                'values': list(seller_revenue.values())
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/top-products-full', methods=['GET'])
@login_required
def api_top_products_full():
    """Get top 10 products with product+category - FIXED."""
    try:
        limit = int(request.args.get('limit', 10))
        
        # OTIMIZADO: Usa analytics_service que já faz JOIN
        performance = analytics_service.get_product_performance(top_n=limit)
        
        result = []
        for product in performance['top_products']:
            result.append({
                'codigo': product['codigo'],
                'label': f"{product['produto']} - {product['categoria']}",
                'produto': product['produto'],
                'categoria': product['categoria'],
                'revenue': product['revenue'],
                'quantity': product['quantity_sold']
            })
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        print(f"Error in top products: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/top-clients-full', methods=['GET'])
@login_required
def api_top_clients_full():
    """Get top 10 clients - FIXED."""
    try:
        limit = int(request.args.get('limit', 10))
        
        # OTIMIZADO: Usa sale_repo.get_top_clients() que já faz GROUP BY
        from src.repositories.sale_repository import SaleRepository
        sale_repo = SaleRepository()
        
        top_clients = sale_repo.get_top_clients(limit=limit)
        
        result = []
        for client in top_clients:
            result.append({
                'id': client['ID_CLIENTE'],
                'name': client['CLIENTE'],
                'revenue': float(client['TOTAL_GASTO']),
                'purchases': int(client['NUM_COMPRAS'])
            })
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        print(f"Error in top clients: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== BUDGET ROUTES ==========

@app.route('/budgets')
@login_required
def budgets():
    """Budgets (Orçamentos) page."""
    clients = client_service.list_all_clients()
    products = product_service.list_all_products()
    return render_template('budgets.html', 
                         clients=clients, 
                         products=products,
                         user=session)


@app.route('/api/budgets/generate', methods=['POST'])
@login_required
def api_generate_budget():
    """
    Generate budget PDF with support for custom clients and products.
    Custom data is passed directly in the request, not saved to database.
    """
    try:
        data = request.get_json()
        
        # The data structure already contains all necessary info:
        # - For custom clients: data['client_data'] contains the info
        # - For custom products: data['items'] contains produto, categoria, valor_unit
        # The budget_service will handle both cases automatically
        
        # Generate PDF as bytes
        pdf_buffer = budget_service.generate_budget_pdf(data, return_bytes=True)
        
        # Return PDF file
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"orcamento_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        
    except Exception as e:
        print(f"Error generating budget: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/budgets/preview', methods=['POST'])
@login_required
def api_preview_budget():
    """Preview budget data with support for custom clients and products."""
    try:
        data = request.get_json()
        
        # Validate client data
        id_cliente = str(data.get('id_cliente', '')).strip().lower()
        
        if id_cliente == 'custom' or 'client_data' in data:
            client_data = data.get('client_data', {})
            client = {
                'CLIENTE': client_data.get('name') or client_data.get('CLIENTE') or 'Cliente Personalizado',
                'TELEFONE': client_data.get('phone') or client_data.get('TELEFONE') or '',
                'ENDERECO': client_data.get('address') or client_data.get('ENDERECO') or ''
            }
        else:
            client = budget_service.get_client_data(data['id_cliente'])
            if not client:
                client = {
                    'CLIENTE': 'Cliente Não Encontrado',
                    'TELEFONE': '',
                    'ENDERECO': ''
                }
        
        items = []
        total = 0.0
        
        for item in data['items']:
            codigo = str(item.get('codigo', '')).strip()
            
            # Check if it's a custom product
            if codigo.upper().startswith('CUSTOM') or ('produto' in item and 'categoria' in item):
                produto_nome = item.get('produto') or item.get('PRODUTO') or 'Produto Personalizado'
                categoria = item.get('categoria') or item.get('CATEGORIA') or 'Diversos'
                try:
                    valor_unit = float(item.get('valor_unit') or item.get('VALOR') or 0)
                except (ValueError, TypeError):
                    valor_unit = 0.0
            else:
                product = budget_service.get_product_data(item['codigo'])
                if not product:
                    produto_nome = f"Produto Não Encontrado ({item['codigo']})"
                    categoria = "-"
                    valor_unit = 0.0
                else:
                    produto_nome = product.get('PRODUTO', 'Produto')
                    categoria = product.get('CATEGORIA', '-')
                    valor_unit = float(product.get('VALOR', 0))
            
            quantidade = int(item['quantidade'])
            valor_total = quantidade * valor_unit
            total += valor_total
            
            items.append({
                'produto': produto_nome,
                'categoria': categoria,
                'quantidade': quantidade,
                'valor_unit': valor_unit,
                'valor_total': valor_total
            })
        
        return jsonify({
            'success': True,
            'data': {
                'client': {
                    'name': client['CLIENTE'],
                    'phone': client.get('TELEFONE', ''),
                    'address': client.get('ENDERECO', '')
                },
                'items': items,
                'total': total
            }
        })
        
    except Exception as e:
        print(f"Error previewing budget: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

    

@app.route('/notifications')
@login_required
def notifications():
    """Notifications page."""
    return render_template('notifications.html', user=session)


@app.route('/api/notifications', methods=['GET'])
@login_required
def api_get_notifications():
    """Get all notifications (with cache)."""
    try:
        notifications = get_cached_notifications()
        return jsonify({'success': True, 'data': notifications})
    except Exception as e:
        print(f"[API] Error getting notifications: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notifications/count', methods=['GET'])
@login_required
def api_get_notification_count():
    """Get notification count (with cache)."""
    try:
        notifications = get_cached_notifications()
        return jsonify({
            'success': True,
            'data': {
                'total_count': notifications['total_count'],
                'low_stock_count': len(notifications['low_stock']),
                'repurchase_pessoa_count': len(notifications['repurchase_pessoa']),
                'repurchase_empresa_count': len(notifications['repurchase_empresa'])
            }
        })
    except Exception as e:
        print(f"[API] Error getting notification count: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notifications/dismiss', methods=['POST'])
@login_required
def api_dismiss_notification():
    """Dismiss a notification."""
    try:
        data = request.get_json()
        notification_type = data.get('notification_type')
        notification_id = data.get('notification_id')
        
        if not notification_type or not notification_id:
            return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
        
        success = notification_service.dismiss_notification(notification_type, notification_id)
        
        if success:
            # Invalidate cache
            notification_cache['data'] = None
            return jsonify({'success': True, 'message': 'Notificação marcada como lida'})
        else:
            return jsonify({'success': False, 'error': 'Erro ao marcar notificação'}), 500
            
    except Exception as e:
        print(f"[API] Error dismissing notification: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notifications/undismiss', methods=['POST'])
@login_required
def api_undismiss_notification():
    """Restore a dismissed notification."""
    try:
        data = request.get_json()
        notification_type = data.get('notification_type')
        notification_id = data.get('notification_id')
        
        if not notification_type or not notification_id:
            return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
        
        success = notification_service.undismiss_notification(notification_type, notification_id)
        
        if success:
            # Invalidate cache
            notification_cache['data'] = None
            return jsonify({'success': True, 'message': 'Notificação restaurada'})
        else:
            return jsonify({'success': False, 'error': 'Erro ao restaurar notificação'}), 500
            
    except Exception as e:
        print(f"[API] Error undismissing notification: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/test-notifications')
@login_required
def test_notifications():
    """Test notifications (TEMPORARY)."""
    try:
        # Force refresh
        notification_cache['data'] = None
        
        notifications = notification_service.get_all_notifications()
        
        return jsonify({
            'success': True,
            'data': notifications,
            'debug': {
                'low_stock_count': len(notifications['low_stock']),
                'repurchase_pessoa_count': len(notifications['repurchase_pessoa']),
                'repurchase_empresa_count': len(notifications['repurchase_empresa']),
                'sample_low_stock': notifications['low_stock'][:3] if notifications['low_stock'] else [],
                'sample_repurchase': (notifications['repurchase_pessoa'][:1] if notifications['repurchase_pessoa'] else [])
            }
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        })


# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found(error):
    """404 error handler."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler."""
    return render_template('error.html', error='Erro interno do servidor'), 500


# ========== RUN APPLICATION ==========

if __name__ == '__main__':
    # Create templates and static directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)