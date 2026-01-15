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

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard route - FIXED for new structure."""
    try:
        import pandas as pd
        print("[DASHBOARD] Starting dashboard load...")
        
        # Initialize services
        sale_service = SaleService()
        product_service = ProductService()
        print("[DASHBOARD] Services initialized")
        
        # Get sales summary
        print("[DASHBOARD] Getting sales summary...")
        summary = sale_service.get_sales_summary()
        print(f"[DASHBOARD] Summary: {summary}")
        
        # Get recent sales
        print("[DASHBOARD] Getting recent sales...")
        from src.repositories.sale_repository import SaleRepository
        sale_repo = SaleRepository()
        recent_sales = sale_repo.get_recent_sales(limit=10)
        print(f"[DASHBOARD] Recent sales: {len(recent_sales)}")
        
        # Get top products
        print("[DASHBOARD] Getting top products...")
        from src.repositories.sale_item_repository import SaleItemRepository
        from src.repositories.product_repository import ProductRepository
        
        item_repo = SaleItemRepository()
        product_repo = ProductRepository()
        
        product_stats = item_repo.get_product_stats()
        print(f"[DASHBOARD] Product stats shape: {product_stats.shape if not product_stats.empty else 'empty'}")
        
        top_products = []
        if not product_stats.empty:
            # Get top 5 products
            top_5 = product_stats.head(5)
            
            for idx, row in top_5.iterrows():
                print(f"[DASHBOARD] Processing product {idx}: {row.get('PRODUTO', 'unknown')}")
                # Get product details for profit margin
                product = product_repo.get_by_codigo(row['CODIGO'])
                
                profit_margin = 0
                if product:
                    custo = float(product.get('CUSTO', 0))
                    valor = float(product.get('VALOR', 0))
                    if valor > 0:
                        profit_margin = ((valor - custo) / valor) * 100
                
                top_products.append({
                    'produto': row['PRODUTO'],
                    'categoria': row['CATEGORIA'],
                    'quantity_sold': int(row['QTD_VENDIDA']),
                    'revenue': float(row['RECEITA']),
                    'profit_margin': profit_margin
                })
        
        print(f"[DASHBOARD] Top products: {len(top_products)}")
        
        # Get low stock products
        print("[DASHBOARD] Getting low stock products...")
        try:
            products_df = product_repo.get_all()
            if not products_df.empty:
                products_df['ESTOQUE'] = pd.to_numeric(products_df['ESTOQUE'], errors='coerce').fillna(0)
                low_stock_df = products_df[products_df['ESTOQUE'] <= 1]
                low_stock = low_stock_df.to_dict('records')
            else:
                low_stock = []
            print(f"[DASHBOARD] Low stock: {len(low_stock)}")
        except Exception as e:
            print(f"[DASHBOARD] Error getting low stock: {e}")
            low_stock = []

        # Convert Decimal to float for template compatibility
        if 'by_category' in summary:
            summary['by_category'] = {k: float(v) for k, v in summary['by_category'].items()}
        
        print("[DASHBOARD] Rendering template...")
        return render_template(
            'dashboard.html',
            summary=summary,
            recent_sales=recent_sales,
            top_products=top_products,
            low_stock=low_stock
        )
        
    except Exception as e:
        print(f"[DASHBOARD] ❌ ERROR: {str(e)}")
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
        items_df = item_repo._read_csv()
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
        items_df = item_repo._read_csv()
        
        if items_df.empty:
            return jsonify({
                'success': True,
                'data': [],
                'has_more': False,
                'total': 0
            })
        
        # Sort by ID_VENDA descending (most recent first)
        items_df = items_df.sort_values('ID_VENDA', ascending=False)
        
        # Get paginated slice
        total = len(items_df)
        paginated_items = items_df.iloc[offset:offset + limit]
        
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
    """Get category analysis - FIXED com normalização."""
    try:
        from src.repositories.sale_item_repository import SaleItemRepository
        import pandas as pd
        
        item_repo = SaleItemRepository()
        items_df = item_repo._read_csv()
        
        if items_df.empty:
            return jsonify({'success': True, 'data': {'categories': []}})
        
        # NORMALIZAR categorias (Title Case)
        items_df['CATEGORIA'] = items_df['CATEGORIA'].str.strip().str.title()
        items_df['PRECO_TOTAL'] = pd.to_numeric(items_df['PRECO_TOTAL'], errors='coerce').fillna(0)
        items_df['QUANTIDADE'] = pd.to_numeric(items_df['QUANTIDADE'], errors='coerce').fillna(0)
        
        # Agrupar por categoria normalizada
        category_stats = items_df.groupby('CATEGORIA').agg({
            'PRECO_TOTAL': 'sum',
            'QUANTIDADE': 'sum',
            'CODIGO': 'nunique'
        }).reset_index()
        
        category_stats.columns = ['CATEGORIA', 'RECEITA', 'QTD_VENDIDA', 'PRODUTOS_UNICOS']
        category_stats = category_stats.sort_values('RECEITA', ascending=False)
        
        total_revenue = category_stats['RECEITA'].sum()
        
        results = []
        for _, row in category_stats.iterrows():
            receita = float(row['RECEITA'])
            revenue_share = (receita / total_revenue * 100) if total_revenue > 0 else 0
            
            results.append({
                'category': row['CATEGORIA'],
                'revenue': receita,
                'revenue_share': revenue_share,
                'items_sold': int(row['QTD_VENDIDA']),
                'unique_products': int(row['PRODUTOS_UNICOS'])
            })
        
        return jsonify({
            'success': True,
            'data': {
                'categories': results,
                'total_revenue': float(total_revenue)
            }
        })
        
    except Exception as e:
        print(f"Error in categories: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/payment-methods', methods=['GET'])
@login_required
def api_payment_methods():
    """Get payment methods analysis."""
    try:
        # Log current counts to ensure fresh data
        from src.repositories.sale_repository import SaleRepository
        sale_repo = SaleRepository()
        sales_df = sale_repo.get_all()
        print(f"[ANALYTICS] payment_methods: sales rows={len(sales_df)}")

        payment_data = analytics_service.get_payment_method_analysis()
        return jsonify({'success': True, 'data': payment_data})
    except Exception as e:
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
        sales_df = sale_repo.get_all()
        print(f"[ANALYTICS] monthly_revenue: sales rows={len(sales_df)}")
        import pandas as _pd
        # Flexible date parsing (accept dd/mm/YYYY and ISO YYYY-MM-DD)
        sales_df['DATA_DT'] = _pd.to_datetime(sales_df['DATA'], dayfirst=True, errors='coerce')
        # Fallback: parse dd/mm/YYYY explicitly for rows not parsed by the vectorized call
        mask = sales_df['DATA_DT'].isna()
        if mask.any():
            sales_df.loc[mask, 'DATA_DT'] = sales_df.loc[mask, 'DATA'].apply(lambda s: _pd.to_datetime(s, format='%d/%m/%Y', errors='coerce'))
        sales_df = sales_df[sales_df['DATA_DT'].notna()]
        sales_df['MONTH_KEY'] = sales_df['DATA_DT'].dt.strftime('%Y-%m')
        sales_df['VALOR_TOTAL_VENDA'] = _pd.to_numeric(sales_df['VALOR_TOTAL_VENDA'], errors='coerce').fillna(0)
        
        # Get last 12 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        monthly_data = defaultdict(float)
        recent = sales_df[sales_df['DATA_DT'] >= _pd.Timestamp(start_date)]
        print(f"[ANALYTICS] monthly_revenue: recent rows={len(recent)}")
        for _, sale in recent.iterrows():
            month_key = sale['MONTH_KEY']
            monthly_data[month_key] += float(sale['VALOR_TOTAL_VENDA'])
        
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
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/analytics/monthly-financial-summary', methods=['GET'])
@login_required
def api_monthly_financial_summary():
    """Resumo financeiro do mês atual."""
    try:
        from src.repositories.sale_repository import SaleRepository
        from src.repositories.sale_item_repository import SaleItemRepository
        from src.repositories.product_repository import ProductRepository
        import pandas as pd
        from datetime import datetime
        
        sale_repo = SaleRepository()
        item_repo = SaleItemRepository()
        product_repo = ProductRepository()
        
        # Pegar vendas do mês atual
        current_month = datetime.now().strftime('%m/%Y')
        sales_df = sale_repo.get_all()
        print(f"[ANALYTICS] monthly_financial_summary: sales rows={len(sales_df)}")
        sales_df['DATA_DT'] = pd.to_datetime(sales_df['DATA'], dayfirst=True, errors='coerce')
        mask = sales_df['DATA_DT'].isna()
        if mask.any():
            sales_df.loc[mask, 'DATA_DT'] = sales_df.loc[mask, 'DATA'].apply(lambda s: pd.to_datetime(s, format='%d/%m/%Y', errors='coerce'))
        sales_df = sales_df[sales_df['DATA_DT'].notna()]
        sales_df['MONTH'] = sales_df['DATA_DT'].dt.strftime('%m/%Y')
        month_sales = sales_df[sales_df['MONTH'] == current_month]
        print(f"[ANALYTICS] monthly_financial_summary: month_sales rows={len(month_sales)}")
        
        if month_sales.empty:
            return jsonify({
                'success': True,
                'data': {
                    'gross_margin_pct': 0,
                    'contribution_margin_pct': 0,
                    'fixed_expenses': expense_service.get_total_monthly_expenses(),
                    'net_profit': 0
                }
            })
        
        # Calcular métricas do mês
        total_revenue = month_sales['VALOR_TOTAL_VENDA'].astype(float).sum()
        
        # Pegar itens do mês
        sale_ids = month_sales['ID_VENDA'].tolist()
        items_df = item_repo._read_csv()
        print(f"[ANALYTICS] monthly_financial_summary: items rows={len(items_df)}")
        month_items = items_df[items_df['ID_VENDA'].isin(sale_ids)]
        print(f"[ANALYTICS] monthly_financial_summary: month_items rows={len(month_items)}")
        
        # Calcular COGS
        products_df = product_repo.get_all()
        product_costs = products_df.set_index('CODIGO')['CUSTO'].to_dict()
        
        total_cogs = 0
        for _, item in month_items.iterrows():
            codigo = str(item['CODIGO'])
            quantidade = int(item.get('QUANTIDADE', 0))
            custo = float(product_costs.get(codigo, 0))
            total_cogs += custo * quantidade
        
        # Calcular custos variáveis (estimativa: 3.5% taxa + R$ 3/unidade embalagem)
        total_units = month_items['QUANTIDADE'].astype(int).sum()
        payment_fees = total_revenue * 0.035  # 3.5% taxa média
        packaging_costs = total_units * 3.0   # R$ 3 por unidade (embalagem + materiais)
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
    """Lucro líquido mensal (12 meses) - MODELO FINANCEIRO CORRETO"""
    try:
        from collections import defaultdict
        from src.repositories.sale_repository import SaleRepository
        from src.repositories.sale_item_repository import SaleItemRepository
        from src.repositories.product_repository import ProductRepository
        import pandas as pd
        from datetime import datetime, timedelta

        sale_repo = SaleRepository()
        item_repo = SaleItemRepository()
        product_repo = ProductRepository()

        sales_df = sale_repo.get_all()
        items_df = item_repo._read_csv()
        products_df = product_repo.get_all()

        if sales_df.empty:
            return jsonify({
                'success': True,
                'data': {
                    'months': [],
                    'net_profits': [],
                    'gross_margins': [],
                    'contribution_margins': []
                }
            })

        # === Datas ===
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        sales_df['DATA_DT'] = pd.to_datetime(
            sales_df['DATA'],
            dayfirst=True,
            errors='coerce'
        )
        # Fallback for mixed formats
        mask = sales_df['DATA_DT'].isna()
        if mask.any():
            sales_df.loc[mask, 'DATA_DT'] = sales_df.loc[mask, 'DATA'].apply(lambda s: pd.to_datetime(s, format='%d/%m/%Y', errors='coerce'))

        print(f"[ANALYTICS] monthly_profit: sales rows={len(sales_df)}")

        sales_df = sales_df[
            (sales_df['DATA_DT'] >= start_date) &
            (sales_df['DATA_DT'].notna())
        ]
        print(f"[ANALYTICS] monthly_profit: recent rows={len(sales_df)}")

        sales_df['MONTH_KEY'] = sales_df['DATA_DT'].dt.strftime('%Y-%m')
        sales_df['VALOR_TOTAL_VENDA'] = pd.to_numeric(
            sales_df['VALOR_TOTAL_VENDA'],
            errors='coerce'
        ).fillna(0)

        # === Custo dos produtos (COGS) ===
        product_costs = (
            products_df
            .assign(CODIGO=products_df['CODIGO'].astype(str))
            .set_index('CODIGO')['CUSTO']
            .to_dict()
        )

        # === Estrutura mensal ===
        monthly_data = defaultdict(lambda: {
            'revenue': 0.0,
            'cogs': 0.0,
            'units': 0,
            'sales_count': 0
        })

        # Receita por mês
        for _, sale in sales_df.iterrows():
            month_key = sale['MONTH_KEY']
            monthly_data[month_key]['revenue'] += float(sale['VALOR_TOTAL_VENDA'])
            monthly_data[month_key]['sales_count'] += 1

        # Itens vendidos → COGS
        if not items_df.empty:
            items_df['CODIGO'] = items_df['CODIGO'].astype(str)
            items_df['QUANTIDADE'] = pd.to_numeric(
                items_df['QUANTIDADE'],
                errors='coerce'
            ).fillna(0)

            sales_month_map = (
                sales_df[['ID_VENDA', 'MONTH_KEY']]
                .set_index('ID_VENDA')['MONTH_KEY']
                .to_dict()
            )

            for _, item in items_df.iterrows():
                sale_id = item['ID_VENDA']
                month_key = sales_month_map.get(sale_id)

                if not month_key:
                    continue

                quantidade = int(item['QUANTIDADE'])
                custo_unit = float(product_costs.get(item['CODIGO'], 0))

                monthly_data[month_key]['cogs'] += custo_unit * quantidade
                monthly_data[month_key]['units'] += quantidade

        # === DESPESAS FIXAS REAIS (SEM ESTOQUE) ===
        fixed_expenses = (
            76.90 +   # Impostos
            200.00 +  # Transportadora
            100.00 +  # Marketing
            65.00 +   # Telefonia
            50.00     # Energia
        )

        months = []
        net_profits = []
        gross_margins = []
        contribution_margins = []

        for i in range(11, -1, -1):
            month_date = end_date - timedelta(days=30 * i)
            month_key = month_date.strftime('%Y-%m')
            month_label = month_date.strftime('%b/%y')

            months.append(month_label)

            data = monthly_data.get(month_key, {
                'revenue': 0,
                'cogs': 0,
                'units': 0,
                'sales_count': 0
            })

            revenue = data['revenue']
            cogs = data['cogs']
            units = data['units']
            sales_count = data['sales_count']

            # === Custos variáveis CORRETOS ===
            payment_fee = revenue * 0.035          # 3,5%
            packaging = units * 2.00               # embalagem por unidade
            cards = units * 1.00                   # cartões por unidade
            shipping_materials = sales_count * 1.50  # por venda

            variable_costs = (
                payment_fee +
                packaging +
                cards +
                shipping_materials
            )

            # === Margens ===
            gross_profit = revenue - cogs
            gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0

            contribution = gross_profit - variable_costs
            contribution_margin = (
                contribution / revenue * 100
            ) if revenue > 0 else 0

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
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/api/analytics/cost-breakdown', methods=['GET'])
@login_required
def api_cost_breakdown():
    """Breakdown de custos do mês atual."""
    try:
        from src.repositories.sale_repository import SaleRepository
        from src.repositories.sale_item_repository import SaleItemRepository
        from src.repositories.product_repository import ProductRepository
        import pandas as pd
        from datetime import datetime
        
        sale_repo = SaleRepository()
        item_repo = SaleItemRepository()
        product_repo = ProductRepository()
        
        # Mês atual
        current_month = datetime.now().strftime('%m/%Y')
        sales_df = sale_repo.get_all()
        print(f"[ANALYTICS] cost_breakdown: sales rows={len(sales_df)}")
        sales_df['DATA_DT'] = pd.to_datetime(sales_df['DATA'], dayfirst=True, errors='coerce')
        mask = sales_df['DATA_DT'].isna()
        if mask.any():
            sales_df.loc[mask, 'DATA_DT'] = sales_df.loc[mask, 'DATA'].apply(lambda s: pd.to_datetime(s, format='%d/%m/%Y', errors='coerce'))
        sales_df = sales_df[sales_df['DATA_DT'].notna()]
        sales_df['MONTH'] = sales_df['DATA_DT'].dt.strftime('%m/%Y')
        month_sales = sales_df[sales_df['MONTH'] == current_month]
        print(f"[ANALYTICS] cost_breakdown: month_sales rows={len(month_sales)}")
        
        if month_sales.empty:
            return jsonify({
                'success': True,
                'data': {
                    'total_cogs': 0,
                    'total_variable_costs': 0,
                    'total_fixed_expenses': expense_service.get_total_monthly_expenses()
                }
            })
        
        # COGS
        sale_ids = month_sales['ID_VENDA'].tolist()
        items_df = item_repo._read_csv()
        month_items = items_df[items_df['ID_VENDA'].isin(sale_ids)]
        
        products_df = product_repo.get_all()
        product_costs = products_df.set_index('CODIGO')['CUSTO'].to_dict()
        
        total_cogs = 0
        total_units = 0
        for _, item in month_items.iterrows():
            codigo = str(item['CODIGO'])
            quantidade = int(item.get('QUANTIDADE', 0))
            custo = float(product_costs.get(codigo, 0))
            total_cogs += custo * quantidade
            total_units += quantidade
        
        # Variable costs
        total_revenue = month_sales['VALOR_TOTAL_VENDA'].astype(float).sum()
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
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/breakeven-progress', methods=['GET'])
@login_required
def api_breakeven_progress():
    """Progresso de break-even do mês atual."""
    try:
        from src.repositories.sale_repository import SaleRepository
        from src.repositories.sale_item_repository import SaleItemRepository
        from src.repositories.product_repository import ProductRepository
        import pandas as pd
        from datetime import datetime
        
        sale_repo = SaleRepository()
        item_repo = SaleItemRepository()
        product_repo = ProductRepository()
        
        # Mês atual
        current_month = datetime.now().strftime('%m/%Y')
        sales_df = sale_repo.get_all()
        sales_df['DATA_DT'] = pd.to_datetime(sales_df['DATA'], dayfirst=True, errors='coerce')
        mask = sales_df['DATA_DT'].isna()
        if mask.any():
            sales_df.loc[mask, 'DATA_DT'] = sales_df.loc[mask, 'DATA'].apply(lambda s: pd.to_datetime(s, format='%d/%m/%Y', errors='coerce'))
        sales_df = sales_df[sales_df['DATA_DT'].notna()]
        sales_df['MONTH'] = sales_df['DATA_DT'].dt.strftime('%m/%Y')
        month_sales = sales_df[sales_df['MONTH'] == current_month]
        
        # Despesas fixas
        fixed_expenses = expense_service.get_total_monthly_expenses()
        
        if month_sales.empty:
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
        
        # Calcular contribuição total
        sale_ids = month_sales['ID_VENDA'].tolist()
        items_df = item_repo._read_csv()
        month_items = items_df[items_df['ID_VENDA'].isin(sale_ids)]
        
        products_df = product_repo.get_all()
        product_costs = products_df.set_index('CODIGO')['CUSTO'].to_dict()
        
        total_revenue = month_sales['VALOR_TOTAL_VENDA'].astype(float).sum()
        total_cogs = 0
        total_units = 0
        
        for _, item in month_items.iterrows():
            codigo = str(item['CODIGO'])
            quantidade = int(item.get('QUANTIDADE', 0))
            custo = float(product_costs.get(codigo, 0))
            total_cogs += custo * quantidade
            total_units += quantidade
        
        # Variable costs
        payment_fees = total_revenue * 0.035
        packaging = total_units * 3.0
        total_variable_costs = payment_fees + packaging
        
        # Contribution margin
        gross_profit = total_revenue - total_cogs
        contribution_total = gross_profit - total_variable_costs
        
        # Current sales count
        current_sales = len(month_sales)
        
        # Average contribution per sale
        avg_contribution = contribution_total / current_sales if current_sales > 0 else 0
        
        # Break-even sales
        breakeven_sales = fixed_expenses / avg_contribution if avg_contribution > 0 else float('inf')
        
        # Progress
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
        print(f"Error in breakeven progress: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/analytics/products-performance', methods=['GET'])
@login_required
def api_products_performance():
    """Análise detalhada de produtos."""
    try:
        from src.repositories.sale_item_repository import SaleItemRepository
        from src.repositories.product_repository import ProductRepository
        import pandas as pd
        
        item_repo = SaleItemRepository()
        product_repo = ProductRepository()
        
        # Estatísticas de produtos
        product_stats = item_repo.get_product_stats()
        
        if product_stats.empty:
            return jsonify({'success': True, 'data': []})
        
        # Enriquecer com dados de custo
        products_df = product_repo.get_all()
        
        results = []
        for _, row in product_stats.head(20).iterrows():  # Top 20
            codigo = row['CODIGO']
            product = products_df[products_df['CODIGO'] == codigo]
            
            custo = float(product['CUSTO'].iloc[0]) if not product.empty else 0
            receita = float(row['RECEITA'])
            qtd_vendida = int(row['QTD_VENDIDA'])
            
            profit = receita - (custo * qtd_vendida)
            profit_margin = (profit / receita * 100) if receita > 0 else 0
            
            results.append({
                'codigo': codigo,
                'produto': row['PRODUTO'],
                'categoria': row['CATEGORIA'],
                'quantity_sold': qtd_vendida,
                'revenue': receita,
                'profit': profit,
                'profit_margin': profit_margin,
                'transactions': int(row['NUM_VENDAS'])
            })
        
        return jsonify({'success': True, 'data': results})
        
    except Exception as e:
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
    """Visão geral de vendas."""
    try:
        from src.repositories.sale_repository import SaleRepository
        from src.repositories.sale_item_repository import SaleItemRepository
        import pandas as pd
        
        sale_repo = SaleRepository()
        item_repo = SaleItemRepository()
        
        sales_df = sale_repo.get_all()
        items_df = item_repo._read_csv()
        
        if sales_df.empty:
            return jsonify({'success': True, 'data': {
                'total_vendas': 0,
                'total_receita': 0,
                'total_itens': 0,
                'ticket_medio': 0,
                'by_payment': {},
                'by_month': {}
            }})
        
        # Converter colunas
        sales_df['VALOR_TOTAL_VENDA'] = pd.to_numeric(sales_df['VALOR_TOTAL_VENDA'], errors='coerce').fillna(0)
        print(f"[ANALYTICS] sales_overview: sales rows={len(sales_df)}, items rows={len(items_df)}")
        sales_df['DATA_DT'] = pd.to_datetime(sales_df['DATA'], dayfirst=True, errors='coerce')
        mask = sales_df['DATA_DT'].isna()
        if mask.any():
            sales_df.loc[mask, 'DATA_DT'] = sales_df.loc[mask, 'DATA'].apply(lambda s: pd.to_datetime(s, format='%d/%m/%Y', errors='coerce'))
        mask = sales_df['DATA_DT'].isna()
        if mask.any():
            sales_df.loc[mask, 'DATA_DT'] = sales_df.loc[mask, 'DATA'].apply(lambda s: pd.to_datetime(s, format='%d/%m/%Y', errors='coerce'))
        sales_df = sales_df[sales_df['DATA_DT'].notna()]
        sales_df['MONTH'] = sales_df['DATA_DT'].dt.strftime('%Y-%m')
        
        items_df['QUANTIDADE'] = pd.to_numeric(items_df['QUANTIDADE'], errors='coerce').fillna(0)
        
        # Métricas gerais
        total_vendas = len(sales_df)
        total_receita = float(sales_df['VALOR_TOTAL_VENDA'].sum())
        total_itens = int(items_df['QUANTIDADE'].sum())
        ticket_medio = total_receita / total_vendas if total_vendas > 0 else 0
        
        # Por meio de pagamento
        by_payment = sales_df.groupby('MEIO')['VALOR_TOTAL_VENDA'].sum().to_dict()
        by_payment = {k.title(): float(v) for k, v in by_payment.items()}
        
        # Por mês (últimos 6 meses)
        by_month = sales_df.groupby('MONTH')['VALOR_TOTAL_VENDA'].sum().sort_index().tail(6).to_dict()
        
        return jsonify({
            'success': True,
            'data': {
                'total_vendas': total_vendas,
                'total_receita': total_receita,
                'total_itens': total_itens,
                'ticket_medio': ticket_medio,
                'by_payment': by_payment,
                'by_month': {k: float(v) for k, v in by_month.items()}
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
# Adicione estes endpoints no seu app.py

@app.route('/api/analytics/monthly-sales-count', methods=['GET'])
@login_required
def api_monthly_sales_count():
    """Quantidade de vendas por mês (últimos 12 meses)."""
    try:
        from collections import defaultdict
        from src.repositories.sale_repository import SaleRepository
        import pandas as pd
        
        sale_repo = SaleRepository()
        sales_df = sale_repo.get_all()
        
        if sales_df.empty:
            return jsonify({'success': True, 'data': {'months': [], 'counts': []}})
        
        # Convert dates (flexible parsing)
        sales_df['DATA_DT'] = pd.to_datetime(sales_df['DATA'], dayfirst=True, errors='coerce')
        mask = sales_df['DATA_DT'].isna()
        if mask.any():
            sales_df.loc[mask, 'DATA_DT'] = sales_df.loc[mask, 'DATA'].apply(lambda s: pd.to_datetime(s, format='%d/%m/%Y', errors='coerce'))
        sales_df = sales_df[sales_df['DATA_DT'].notna()]
        sales_df['MONTH_KEY'] = sales_df['DATA_DT'].dt.strftime('%Y-%m')
        
        # Get last 12 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        sales_df = sales_df[sales_df['DATA_DT'] >= pd.Timestamp(start_date)]
        
        # Count sales per month
        monthly_counts = sales_df.groupby('MONTH_KEY').size().to_dict()
        
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
    """Margem bruta e líquida por mês."""
    try:
        from collections import defaultdict
        from src.repositories.sale_repository import SaleRepository
        from src.repositories.sale_item_repository import SaleItemRepository
        from src.repositories.product_repository import ProductRepository
        import pandas as pd
        
        sale_repo = SaleRepository()
        item_repo = SaleItemRepository()
        product_repo = ProductRepository()
        
        sales_df = sale_repo.get_all()
        items_df = item_repo._read_csv()
        products_df = product_repo.get_all()
        
        if sales_df.empty or items_df.empty:
            return jsonify({
                'success': True,
                'data': {
                    'months': [],
                    'gross_margins': [],
                    'net_margins': []
                }
            })
        
        # Get last 12 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # Convert dates (flexible parsing)
        sales_df['DATA_DT'] = pd.to_datetime(sales_df['DATA'], dayfirst=True, errors='coerce')
        mask = sales_df['DATA_DT'].isna()
        if mask.any():
            sales_df.loc[mask, 'DATA_DT'] = sales_df.loc[mask, 'DATA'].apply(lambda s: pd.to_datetime(s, format='%d/%m/%Y', errors='coerce'))
        sales_df = sales_df[sales_df['DATA_DT'].notna()]
        sales_df['MONTH_KEY'] = sales_df['DATA_DT'].dt.strftime('%Y-%m')
        sales_df = sales_df[sales_df['DATA_DT'] >= pd.Timestamp(start_date)]
        
        # Get product costs
        product_costs = products_df.set_index('CODIGO')['CUSTO'].to_dict()
        
        # Calculate monthly margins
        monthly_data = defaultdict(lambda: {
            'revenue': 0,
            'cost': 0,
            'sales_count': 0
        })
        
        # Revenue and sales count from sales
        print(f"[ANALYTICS] monthly_margin: sales rows={len(sales_df)}, items rows={len(items_df)}")
        for _, sale in sales_df.iterrows():
            month_key = sale['MONTH_KEY']
            monthly_data[month_key]['revenue'] += float(sale['VALOR_TOTAL_VENDA'])
            monthly_data[month_key]['sales_count'] += 1
        
        # Costs from items
        items_df['CODIGO'] = items_df['CODIGO'].astype(str)
        items_df['QUANTIDADE'] = pd.to_numeric(items_df['QUANTIDADE'], errors='coerce').fillna(0)
        
        for _, item in items_df.iterrows():
            sale_id = item['ID_VENDA']
            sale_month = sales_df[sales_df['ID_VENDA'] == sale_id]
            
            if not sale_month.empty:
                month_key = sale_month.iloc[0]['MONTH_KEY']
                codigo = str(item['CODIGO'])
                quantidade = int(item['QUANTIDADE'])
                custo = float(product_costs.get(codigo, 0))
                
                monthly_data[month_key]['cost'] += custo * quantidade
        
        # Get monthly expenses
        monthly_expenses = expense_service.get_total_monthly_expenses()
        
        # Generate results
        months = []
        gross_margins = []
        net_margins = []
        
        for i in range(11, -1, -1):
            month_date = end_date - timedelta(days=30*i)
            month_key = month_date.strftime('%Y-%m')
            month_label = month_date.strftime('%b/%y')
            
            months.append(month_label)
            
            data = monthly_data.get(month_key, {'revenue': 0, 'cost': 0, 'sales_count': 0})
            
            # Calculate margins
            revenue = data['revenue']
            cost = data['cost']
            gross_profit = revenue - cost
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
    """Top produtos com nome + categoria, margem bruta e de contribuição."""
    try:
        from src.repositories.sale_item_repository import SaleItemRepository
        from src.repositories.product_repository import ProductRepository
        import pandas as pd
        
        item_repo = SaleItemRepository()
        product_repo = ProductRepository()
        
        items_df = item_repo._read_csv()
        products_df = product_repo.get_all()
        
        if items_df.empty:
            return jsonify({'success': True, 'data': []})
        
        # Convert numeric columns
        items_df['PRECO_TOTAL'] = pd.to_numeric(items_df['PRECO_TOTAL'], errors='coerce').fillna(0)
        items_df['QUANTIDADE'] = pd.to_numeric(items_df['QUANTIDADE'], errors='coerce').fillna(0)
        
        # Group by product + category
        product_stats = items_df.groupby(['CODIGO', 'PRODUTO', 'CATEGORIA']).agg({
            'PRECO_TOTAL': 'sum',
            'QUANTIDADE': 'sum'
        }).reset_index()
        
        product_stats.columns = ['CODIGO', 'PRODUTO', 'CATEGORIA', 'RECEITA', 'QTD_VENDIDA']
        
        # Get costs
        product_costs = products_df.set_index('CODIGO')[['CUSTO', 'VALOR']].to_dict('index')
        
        results = []
        for _, row in product_stats.iterrows():
            codigo = row['CODIGO']
            receita = float(row['RECEITA'])
            qtd = int(row['QTD_VENDIDA'])
            
            # Get cost and price
            product_data = product_costs.get(codigo, {'CUSTO': 0, 'VALOR': 0})
            custo = float(product_data['CUSTO'])
            
            # Gross margin
            cost_total = custo * qtd
            gross_profit = receita - cost_total
            gross_margin = (gross_profit / receita * 100) if receita > 0 else 0
            
            # Variable costs (taxa 3.5% + embalagem R$ 3/un)
            payment_fee = receita * 0.035
            packaging = qtd * 3.0
            variable_costs = payment_fee + packaging
            
            # Contribution margin
            contribution = gross_profit - variable_costs
            contribution_margin = (contribution / receita * 100) if receita > 0 else 0
            
            results.append({
                'codigo': codigo,
                'produto': row['PRODUTO'],
                'categoria': row['CATEGORIA'],
                'label': f"{row['PRODUTO']} - {row['CATEGORIA']}",
                'quantity_sold': qtd,
                'revenue': receita,
                'gross_margin': round(gross_margin, 2),
                'contribution_margin': round(contribution_margin, 2),
                'net_margin': round(contribution_margin, 2)  # Compatibilidade
            })
        
        # Sort by revenue
        results.sort(key=lambda x: x['revenue'], reverse=True)
        
        return jsonify({'success': True, 'data': results[:20]})
        
    except Exception as e:
        print(f"Error in products with margin: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    



@app.route('/api/analytics/category-margin', methods=['GET'])
@login_required
def api_category_margin():
    """Margem por categoria."""
    try:
        from src.repositories.sale_item_repository import SaleItemRepository
        from src.repositories.product_repository import ProductRepository
        import pandas as pd
        
        item_repo = SaleItemRepository()
        product_repo = ProductRepository()
        
        items_df = item_repo._read_csv()
        products_df = product_repo.get_all()
        
        if items_df.empty:
            return jsonify({'success': True, 'data': []})
        
        # Normalize categories
        items_df['CATEGORIA'] = items_df['CATEGORIA'].str.strip().str.title()
        items_df['PRECO_TOTAL'] = pd.to_numeric(items_df['PRECO_TOTAL'], errors='coerce').fillna(0)
        items_df['QUANTIDADE'] = pd.to_numeric(items_df['QUANTIDADE'], errors='coerce').fillna(0)
        
        # Get costs
        product_costs = products_df.set_index('CODIGO')['CUSTO'].to_dict()
        
        # Calculate cost for each item
        items_df['CUSTO_TOTAL'] = items_df.apply(
            lambda row: float(product_costs.get(row['CODIGO'], 0)) * int(row['QUANTIDADE']),
            axis=1
        )
        
        # Group by category
        category_stats = items_df.groupby('CATEGORIA').agg({
            'PRECO_TOTAL': 'sum',
            'CUSTO_TOTAL': 'sum'
        }).reset_index()
        
        results = []
        for _, row in category_stats.iterrows():
            receita = float(row['PRECO_TOTAL'])
            custo = float(row['CUSTO_TOTAL'])
            gross_profit = receita - custo
            gross_margin = (gross_profit / receita * 100) if receita > 0 else 0
            
            results.append({
                'category': row['CATEGORIA'],
                'revenue': receita,
                'cost': custo,
                'gross_profit': gross_profit,
                'gross_margin': round(gross_margin, 2)
            })
        
        results.sort(key=lambda x: x['revenue'], reverse=True)
        
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
        sales_df['DATA_DT'] = pd.to_datetime(sales_df['DATA'], dayfirst=True, errors='coerce')
        mask = sales_df['DATA_DT'].isna()
        if mask.any():
            sales_df.loc[mask, 'DATA_DT'] = sales_df.loc[mask, 'DATA'].apply(lambda s: pd.to_datetime(s, format='%d/%m/%Y', errors='coerce'))
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
        from collections import defaultdict
        from src.repositories.sale_item_repository import SaleItemRepository
        
        item_repo = SaleItemRepository()
        items_df = item_repo._read_csv()
        
        if items_df.empty:
            return jsonify({'success': True, 'data': {'category': '-'}})
        
        # Convert numeric columns
        items_df['PRECO_TOTAL'] = pd.to_numeric(items_df['PRECO_TOTAL'], errors='coerce').fillna(0)
        
        # Group by category
        category_revenue = items_df.groupby('CATEGORIA')['PRECO_TOTAL'].sum().to_dict()
        
        if category_revenue:
            top_category = max(category_revenue.items(), key=lambda x: x[1])
            return jsonify({
                'success': True,
                'data': {'category': top_category[0]}
            })
        
        return jsonify({
            'success': True,
            'data': {'category': '-'}
        })
    except Exception as e:
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
        from collections import defaultdict
        from src.repositories.sale_item_repository import SaleItemRepository
        
        item_repo = SaleItemRepository()
        items_df = item_repo._read_csv()
        
        if items_df.empty:
            return jsonify({'success': True, 'data': []})
        
        # Convert numeric columns
        items_df['PRECO_TOTAL'] = pd.to_numeric(items_df['PRECO_TOTAL'], errors='coerce').fillna(0)
        items_df['QUANTIDADE'] = pd.to_numeric(items_df['QUANTIDADE'], errors='coerce').fillna(0)
        
        # Group by product
        product_data = items_df.groupby(['CODIGO', 'PRODUTO', 'CATEGORIA']).agg({
            'PRECO_TOTAL': 'sum',
            'QUANTIDADE': 'sum'
        }).reset_index()
        
        # Sort by revenue
        product_data = product_data.sort_values('PRECO_TOTAL', ascending=False).head(limit)
        
        result = []
        for _, row in product_data.iterrows():
            result.append({
                'codigo': row['CODIGO'],
                'label': f"{row['PRODUTO']} - {row['CATEGORIA']}",
                'produto': row['PRODUTO'],
                'categoria': row['CATEGORIA'],
                'revenue': float(row['PRECO_TOTAL']),
                'quantity': int(row['QUANTIDADE'])
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
        from collections import defaultdict
        from src.repositories.sale_repository import SaleRepository
        
        sale_repo = SaleRepository()
        sales = sale_repo.get_all().to_dict('records')
        
        client_revenue = defaultdict(lambda: {
            'name': '',
            'revenue': 0,
            'purchases': 0
        })
        
        for sale in sales:
            client_id = str(sale['ID_CLIENTE'])
            client_revenue[client_id]['name'] = sale['CLIENTE']
            client_revenue[client_id]['revenue'] += float(sale['VALOR_TOTAL_VENDA'])
            client_revenue[client_id]['purchases'] += 1
        
        # Sort by revenue
        sorted_clients = sorted(
            client_revenue.items(),
            key=lambda x: x[1]['revenue'],
            reverse=True
        )[:limit]
        
        result = []
        for client_id, data in sorted_clients:
            result.append({
                'id': client_id,
                'name': data['name'],
                'revenue': data['revenue'],
                'purchases': data['purchases']
            })
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
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
    """Generate budget PDF."""
    try:
        data = request.get_json()
        
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
    """Preview budget data."""
    try:
        data = request.get_json()
        
        # Validate data
        client = budget_service.get_client_data(data['id_cliente'])
        if not client:
            return jsonify({'success': False, 'error': 'Cliente não encontrado'}), 404
        
        items = []
        total = 0.0
        
        for item in data['items']:
            product = budget_service.get_product_data(item['codigo'])
            if not product:
                return jsonify({'success': False, 'error': f"Produto não encontrado: {item['codigo']}"}), 404
            
            quantidade = int(item['quantidade'])
            valor_unit = float(product['VALOR'])
            valor_total = quantidade * valor_unit
            total += valor_total
            
            items.append({
                'produto': product['PRODUTO'],
                'categoria': product['CATEGORIA'],
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