"""
Flask web application for Perfumery Management System.

This module provides the web interface and REST API endpoints.
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from functools import wraps
from datetime import datetime, timedelta
import secrets
import os

from src.services.product_service import ProductService
from src.services.client_service import ClientService
from src.services.sale_service import SaleService
from src.services.analytics_service import AnalyticsService
from src.services.visualization_service import VisualizationService
from src.services.export_service import ExportService


# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)

# Initialize services
product_service = ProductService()
client_service = ClientService()
sale_service = SaleService()
analytics_service = AnalyticsService()
visualization_service = VisualizationService()
export_service = ExportService()

# Simple user database (in production, use a real database)
# Password: In production, use proper hashing (bcrypt, argon2)
USERS = {
    'admin': {
        'password': 'admin123',  # Change in production!
        'name': 'Administrator',
        'role': 'admin'
    },
    'vendedor': {
        'password': 'vend123',
        'name': 'Vendedor',
        'role': 'seller'
    }
}


# Authentication decorator
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


# ========== AUTHENTICATION ROUTES ==========

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
        
        user = USERS.get(username)
        if user and user['password'] == password:
            session.permanent = True
            session['username'] = username
            session['name'] = user['name']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Usuário ou senha inválidos')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout handler."""
    session.clear()
    return redirect(url_for('login'))


# ========== DASHBOARD ROUTES ==========

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard."""
    try:
        # Get summary data
        summary = sale_service.get_sales_summary()
        
        # Get recent sales
        all_sales = sale_service.list_all_sales()
        recent_sales = all_sales[-10:] if all_sales else []
        
        # Get CRITICAL low stock products (estoque <= 1)
        low_stock = product_service.check_low_stock(threshold=1)
        
        # Get top products
        top_products_data = analytics_service.get_product_performance(top_n=5)
        top_products = top_products_data['top_products']
        
        return render_template('dashboard.html',
                             summary=summary,
                             recent_sales=recent_sales,
                             low_stock=low_stock,
                             top_products=top_products,
                             user=session)
    except Exception as e:
        return render_template('error.html', error=str(e))


# ========== PRODUCT ROUTES ==========

@app.route('/products')
@login_required
def products():
    """Products management page."""
    products = product_service.list_all_products()
    return render_template('products.html', products=products, user=session)


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
    """Add sale page and handler - WITH MULTI-ITEM SUPPORT."""
    if request.method == 'POST':
        try:
            import json
            
            # Check if it's multi-item sale (new system)
            cart_data_str = request.form.get('cart_data')
            
            if cart_data_str:
                # NEW: Multi-item sale
                cart_data = json.loads(cart_data_str)
                
                sales = sale_service.register_sale_multi_item(
                    id_cliente=cart_data['id_cliente'],
                    meio=cart_data['meio'],
                    items=cart_data['items']
                )
                
                return redirect(url_for('sales'))
            else:
                # LEGACY: Single item sale (for compatibility)
                sale = sale_service.register_sale(
                    id_cliente=request.form['id_cliente'],
                    codigo=request.form['codigo'],
                    quantidade=int(request.form['quantidade']),
                    meio=request.form['meio'],
                    preco_unit=float(request.form.get('preco_unit')) if request.form.get('preco_unit') else None
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
                         user=session)

# ========== ANALYTICS ROUTES ==========

@app.route('/analytics')
@login_required
def analytics():
    """Analytics dashboard."""
    return render_template('analytics.html', user=session)


@app.route('/reports')
@login_required
def reports():
    """Reports page."""
    return render_template('reports.html', user=session)


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
    """Get product by code."""
    try:
        product = product_service.get_product(codigo)
        if product:
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


@app.route('/api/analytics/top-products', methods=['GET'])
@login_required
def api_top_products():
    """Get top products."""
    try:
        limit = int(request.args.get('limit', 10))
        performance = analytics_service.get_product_performance(limit)
        return jsonify({'success': True, 'data': performance['top_products']})
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
    """Get category analysis."""
    try:
        categories = analytics_service.get_category_analysis()
        return jsonify({'success': True, 'data': categories})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/payment-methods', methods=['GET'])
@login_required
def api_payment_methods():
    """Get payment methods analysis."""
    try:
        payment_data = analytics_service.get_payment_method_analysis()
        return jsonify({'success': True, 'data': payment_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== NEW API ENDPOINTS FOR DASHBOARD/ANALYTICS ==========

@app.route('/api/analytics/monthly-revenue', methods=['GET'])
@login_required
def api_monthly_revenue():
    """Get monthly revenue for last 12 months."""
    try:
        from collections import defaultdict
        
        # Get all sales
        sales = sale_service.list_all_sales()
        
        # Get last 12 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        # Group by month
        monthly_data = defaultdict(float)
        
        for sale in sales:
            try:
                # SaleRecord is a namedtuple (access attributes, not dict-index)
                sale_date = datetime.strptime(sale.DATA, '%d/%m/%Y')
                if sale_date >= start_date:
                    month_key = sale_date.strftime('%Y-%m')
                    monthly_data[month_key] += float(sale.PRECO_TOTAL)
            except Exception as e:
                print(f"Error processing sale date: {e}")
                continue
        
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


@app.route('/api/analytics/new-customers', methods=['GET'])
@login_required
def api_new_customers():
    """Get count of new customers in selected period."""
    try:
        days = int(request.args.get('days', 30))
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        sales = sale_service.list_all_sales()
        
        # Track first purchase date for each customer
        customer_first_purchase = {}
        
        for sale in sales:
            try:
                # SaleRecord is a namedtuple - use attribute access
                sale_date = datetime.strptime(sale.DATA, '%d/%m/%Y')
                customer_id = str(sale.ID_CLIENTE)
                
                if customer_id not in customer_first_purchase:
                    customer_first_purchase[customer_id] = sale_date
                elif sale_date < customer_first_purchase[customer_id]:
                    customer_first_purchase[customer_id] = sale_date
            except:
                continue
        
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
    """Calculate customer return rate."""
    try:
        from collections import defaultdict
        
        sales = sale_service.list_all_sales()
        customer_purchases = defaultdict(int)
        
        for sale in sales:
            customer_purchases[str(sale.ID_CLIENTE)] += 1
        
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
    """Get top selling category."""
    try:
        from collections import defaultdict
        
        sales = sale_service.list_all_sales()
        category_revenue = defaultdict(float)
        
        for sale in sales:
            # sale is a SaleRecord (fields normalized in SaleService.list_all_sales)
            category_revenue[sale.CATEGORIA] += float(sale.PRECO_TOTAL)
        
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
    """Get distribution by seller."""
    try:
        from collections import defaultdict
        
        sales = sale_service.list_all_sales()
        clients = {str(c['ID_CLIENTE']): c for c in client_service.list_all_clients()}
        
        seller_revenue = defaultdict(float)
        
        for sale in sales:
            client = clients.get(str(sale.ID_CLIENTE))
            if client:
                seller = client.get('VENDEDOR', 'Sem Vendedor')
                if not seller or not seller.strip():
                    seller = 'Sem Vendedor'
                seller_revenue[seller] += float(sale.PRECO_TOTAL)
        
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
    """Get top 10 products with product+category."""
    try:
        limit = int(request.args.get('limit', 10))
        from collections import defaultdict
        
        sales = sale_service.list_all_sales()
        
        # Group by CODIGO (unique product)
        product_data = defaultdict(lambda: {
            'produto': '',
            'categoria': '',
            'revenue': 0,
            'quantity': 0
        })
        
        for sale in sales:
            codigo = sale.CODIGO
            product_data[codigo]['produto'] = sale.PRODUTO
            product_data[codigo]['categoria'] = sale.CATEGORIA
            product_data[codigo]['revenue'] += float(sale.PRECO_TOTAL)
            product_data[codigo]['quantity'] += int(sale.QUANTIDADE)
        
        # Sort by revenue
        sorted_products = sorted(
            product_data.items(),
            key=lambda x: x[1]['revenue'],
            reverse=True
        )[:limit]
        
        result = []
        for codigo, data in sorted_products:
            result.append({
                'codigo': codigo,
                'label': f"{data['produto']} - {data['categoria']}",
                'produto': data['produto'],
                'categoria': data['categoria'],
                'revenue': data['revenue'],
                'quantity': data['quantity']
            })
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/top-clients-full', methods=['GET'])
@login_required
def api_top_clients_full():
    """Get top 10 clients."""
    try:
        limit = int(request.args.get('limit', 10))
        from collections import defaultdict
        
        sales = sale_service.list_all_sales()
        
        client_revenue = defaultdict(lambda: {
            'name': '',
            'revenue': 0,
            'purchases': 0
        })
        
        for sale in sales:
            client_id = str(sale.ID_CLIENTE)
            client_revenue[client_id]['name'] = sale.CLIENTE
            client_revenue[client_id]['revenue'] += float(sale.PRECO_TOTAL)
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


@app.route('/api/export/sales', methods=['GET'])
@login_required
@admin_required
def api_export_sales():
    """Export sales to Excel."""
    try:
        sales = sale_service.list_all_sales()
        filepath = export_service.export_sales_to_excel(sales)
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/chart/trend', methods=['GET'])
@login_required
def api_chart_trend():
    """Generate trend chart."""
    try:
        days = int(request.args.get('days', 30))
        trend = analytics_service.get_sales_trend(days)
        filepath = visualization_service.plot_sales_trend(trend)
        return send_file(filepath, mimetype='image/png')
    except Exception as e:
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
    app.run(debug=True, host='0.0.0.0', port=5000)