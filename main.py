"""
Main application entry point.

Perfumery Management System - Terminal Interface
"""

from src.ui.menu import Menu, create_submenu
from src.ui.display import *
from src.services.product_service import ProductService
from src.services.client_service import ClientService
from src.services.sale_service import SaleService
from src.services.analytics_service import AnalyticsService
from src.services.visualization_service import VisualizationService
from src.ui.analytics_display import *


class PerfumeryApp:
    """Main application class."""
    
    def __init__(self):
        """Initialize the application."""
        self.product_service = ProductService()
        self.client_service = ClientService()
        self.sale_service = SaleService()
        self.analytics_service = AnalyticsService()
        self.visualization_service = VisualizationService()
        
        self.main_menu = Menu("SISTEMA DE GESTÃO - PERFUMARIA")
        self._setup_main_menu()
    
    def _setup_main_menu(self):
        """Set up the main menu options."""
        self.main_menu.add_option('1', '📦 Gerenciar Produtos', self.products_menu)
        self.main_menu.add_option('2', '👥 Gerenciar Clientes', self.clients_menu)
        self.main_menu.add_option('3', '💰 Registrar Venda', self.register_sale)
        self.main_menu.add_option('4', ' Listar Dados', self.list_menu)
        self.main_menu.add_option('0', '🚪 Sair', self.main_menu.exit)
    
    # ========== PRODUCT MANAGEMENT ==========
    
    def products_menu(self):
        """Product management submenu."""
        menu = create_submenu("GERENCIAMENTO DE PRODUTOS", self.main_menu)
        menu.add_option('1', '➕ Cadastrar novo produto', self.create_product)
        menu.add_option('2', '📝 Atualizar produto', self.update_product)
        menu.add_option('3', '🔍 Buscar produto', self.search_product)
        menu.add_option('4', '📦 Ajustar estoque', self.adjust_stock)
        menu.add_option('5', '📋 Listar todos os produtos', self.list_all_products)
        menu.display()
    
    def create_product(self):
        """Register a new product."""
        print_section_header("CADASTRAR NOVO PRODUTO")
        
        try:
            codigo = self.main_menu.get_input("\nCódigo do produto: ")
            if not codigo:
                return
            
            # Check if product exists
            if self.product_service.product_exists(codigo):
                self.main_menu.show_error(f"Produto com código '{codigo}' já existe!")
                return
            
            produto = self.main_menu.get_input("Nome do produto: ")
            if not produto:
                return
            
            categoria = self.main_menu.get_input("Categoria: ")
            if not categoria:
                return
            
            custo = self.main_menu.get_number("Custo unitário (R$): ", min_value=0.01, is_float=True)
            if custo is None:
                return
            
            valor = self.main_menu.get_number("Preço de venda (R$): ", min_value=0.01, is_float=True)
            if valor is None:
                return
            
            estoque = self.main_menu.get_number("Estoque inicial: ", min_value=0)
            if estoque is None:
                return
            
            # Register product
            product = self.product_service.register_product(
                codigo=codigo,
                produto=produto,
                categoria=categoria,
                custo=custo,
                valor=valor,
                estoque=int(estoque)
            )
            
            self.main_menu.show_success("Produto cadastrado com sucesso!")
            
        except ValueError as e:
            self.main_menu.show_error(str(e))
        except Exception as e:
            self.main_menu.show_error(f"Erro inesperado: {str(e)}")
    
    def update_product(self):
        """Update product information."""
        print_section_header("ATUALIZAR PRODUTO")
        
        codigo = self.main_menu.get_input("\nCódigo do produto: ")
        if not codigo:
            return
        
        product = self.product_service.get_product(codigo)
        if not product:
            self.main_menu.show_error(f"Produto '{codigo}' não encontrado!")
            return
        
        # Show current info
        display_product_detail(product)
        
        print("\nDeixe em branco para manter o valor atual.")
        
        try:
            updates = {}
            
            produto = self.main_menu.get_input("Novo nome (Enter para manter): ", allow_empty=True)
            if produto:
                updates['produto'] = produto
            
            categoria = self.main_menu.get_input("Nova categoria (Enter para manter): ", allow_empty=True)
            if categoria:
                updates['categoria'] = categoria
            
            custo_str = self.main_menu.get_input("Novo custo (Enter para manter): ", allow_empty=True)
            if custo_str:
                try:
                    updates['custo'] = float(custo_str)
                except ValueError:
                    self.main_menu.show_warning("Custo inválido, mantendo valor atual")
            
            valor_str = self.main_menu.get_input("Novo preço de venda (Enter para manter): ", allow_empty=True)
            if valor_str:
                try:
                    updates['valor'] = float(valor_str)
                except ValueError:
                    self.main_menu.show_warning("Preço inválido, mantendo valor atual")
            
            if not updates:
                self.main_menu.show_info("Nenhuma alteração realizada.")
                return
            
            self.product_service.update_product_info(codigo, **updates)
            self.main_menu.show_success("Produto atualizado com sucesso!")
            
        except Exception as e:
            self.main_menu.show_error(str(e))
    
    def search_product(self):
        """Search for a product."""
        print_section_header("BUSCAR PRODUTO")
        
        codigo = self.main_menu.get_input("\nCódigo do produto: ")
        if not codigo:
            return
        
        product = self.product_service.get_product(codigo)
        if product:
            display_product_detail(product)
        else:
            self.main_menu.show_error(f"Produto '{codigo}' não encontrado!")
    
    def adjust_stock(self):
        """Adjust product stock."""
        print_section_header("AJUSTAR ESTOQUE")
        
        codigo = self.main_menu.get_input("\nCódigo do produto: ")
        if not codigo:
            return
        
        product = self.product_service.get_product(codigo)
        if not product:
            self.main_menu.show_error(f"Produto '{codigo}' não encontrado!")
            return
        
        print(f"\nProduto: {product['PRODUTO']}")
        print(f"Estoque atual: {product['ESTOQUE']} unidades")
        
        print("\nDigite:")
        print("  - Número positivo para ADICIONAR ao estoque")
        print("  - Número negativo para REMOVER do estoque")
        
        quantidade = self.main_menu.get_number("\nQuantidade: ", is_float=False)
        if quantidade is None or quantidade == 0:
            return
        
        motivo = self.main_menu.get_input("Motivo do ajuste: ", allow_empty=True)
        if not motivo:
            motivo = "ajuste manual"
        
        try:
            self.product_service.adjust_stock(codigo, int(quantidade), motivo)
            self.main_menu.show_success("Estoque ajustado com sucesso!")
        except Exception as e:
            self.main_menu.show_error(str(e))
    
    def list_all_products(self):
        """List all products."""
        print_section_header("TODOS OS PRODUTOS")
        
        products = self.product_service.list_all_products()
        display_products(products)
    
    # ========== CLIENT MANAGEMENT ==========
    
    def clients_menu(self):
        """Client management submenu."""
        menu = create_submenu("GERENCIAMENTO DE CLIENTES", self.main_menu)
        menu.add_option('1', '➕ Cadastrar novo cliente', self.create_client)
        menu.add_option('2', '📝 Atualizar cliente', self.update_client)
        menu.add_option('3', '🔍 Buscar cliente', self.search_client)
        menu.add_option('4', '📋 Listar todos os clientes', self.list_all_clients)
        menu.display()
    
    def create_client(self):
        """Register a new client."""
        print_section_header("CADASTRAR NOVO CLIENTE")
        
        try:
            cliente = self.main_menu.get_input("\nNome do cliente: ")
            if not cliente:
                return
            
            vendedor = self.main_menu.get_input("Nome do vendedor: ")
            if not vendedor:
                return
            
            # Choose type
            print("\nTipo de cliente:")
            print("  [1] Pessoa Física")
            print("  [2] Empresa")
            
            tipo_choice = self.main_menu.get_input("Escolha: ")
            if tipo_choice == '1':
                tipo = 'pessoa'
            elif tipo_choice == '2':
                tipo = 'empresa'
            else:
                self.main_menu.show_error("Opção inválida!")
                return
            
            # Type-specific fields
            idade = ""
            genero = ""
            cpf_cnpj = ""
            endereco = ""
            
            if tipo == 'pessoa':
                print("\nFaixas etárias disponíveis:")
                age_ranges = self.client_service.get_available_age_ranges()
                for i, age in enumerate(age_ranges, 1):
                    print(f"  [{i}] {age}")
                
                age_choice = self.main_menu.get_input("Escolha a faixa etária: ")
                try:
                    idade = age_ranges[int(age_choice) - 1]
                except (ValueError, IndexError):
                    self.main_menu.show_error("Faixa etária inválida!")
                    return
                
                genero = self.main_menu.get_input("Gênero: ")
                if not genero:
                    return
                
                cpf_cnpj = self.main_menu.get_input("CPF (opcional, Enter para pular): ", allow_empty=True)
                endereco = self.main_menu.get_input("Endereço (opcional, Enter para pular): ", allow_empty=True)
            
            else:  # empresa
                cpf_cnpj = self.main_menu.get_input("CNPJ: ")
                if not cpf_cnpj:
                    return
                
                endereco = self.main_menu.get_input("Endereço: ")
                if not endereco:
                    return
            
            # Optional fields
            profissao = self.main_menu.get_input("Profissão (opcional, Enter para pular): ", allow_empty=True)
            telefone = self.main_menu.get_input("Telefone (opcional, Enter para pular): ", allow_empty=True)
            
            # Register client
            client = self.client_service.register_client(
                cliente=cliente,
                vendedor=vendedor,
                tipo=tipo,
                idade=idade,
                genero=genero,
                profissao=profissao,
                cpf_cnpj=cpf_cnpj,
                telefone=telefone,
                endereco=endereco
            )
            
            self.main_menu.show_success("Cliente cadastrado com sucesso!")
            
        except ValueError as e:
            self.main_menu.show_error(str(e))
        except Exception as e:
            self.main_menu.show_error(f"Erro inesperado: {str(e)}")
    
    def update_client(self):
        """Update client information."""
        print_section_header("ATUALIZAR CLIENTE")
        
        id_cliente = self.main_menu.get_input("\nID do cliente: ")
        if not id_cliente:
            return
        
        client = self.client_service.get_client(id_cliente)
        if not client:
            self.main_menu.show_error(f"Cliente '{id_cliente}' não encontrado!")
            return
        
        display_client_detail(client)
        
        print("\nDeixe em branco para manter o valor atual.")
        
        try:
            updates = {}
            
            telefone = self.main_menu.get_input("Novo telefone (Enter para manter): ", allow_empty=True)
            if telefone:
                updates['telefone'] = telefone
            
            profissao = self.main_menu.get_input("Nova profissão (Enter para manter): ", allow_empty=True)
            if profissao:
                updates['profissao'] = profissao
            
            if not updates:
                self.main_menu.show_info("Nenhuma alteração realizada.")
                return
            
            self.client_service.update_client_info(id_cliente, **updates)
            self.main_menu.show_success("Cliente atualizado com sucesso!")
            
        except Exception as e:
            self.main_menu.show_error(str(e))
    
    def search_client(self):
        """Search for a client."""
        print_section_header("BUSCAR CLIENTE")
        
        id_cliente = self.main_menu.get_input("\nID do cliente: ")
        if not id_cliente:
            return
        
        client = self.client_service.get_client(id_cliente)
        if client:
            display_client_detail(client)
        else:
            self.main_menu.show_error(f"Cliente '{id_cliente}' não encontrado!")
    
    def list_all_clients(self):
        """List all clients."""
        print_section_header("TODOS OS CLIENTES")
        
        clients = self.client_service.list_all_clients()
        display_clients(clients)
    
    # ========== SALES ==========
    
    def register_sale(self):
        """Register a new sale."""
        print_section_header("REGISTRAR VENDA")
        
        try:
            # Step 1: Select client
            id_cliente = self.main_menu.get_input("\nID do cliente: ")
            if not id_cliente:
                return
            
            client = self.client_service.get_client(id_cliente)
            if not client:
                self.main_menu.show_error(f"Cliente '{id_cliente}' não encontrado!")
                return
            
            print(f"✓ Cliente: {client['CLIENTE']}")
            
            # Step 2: Select product
            codigo = self.main_menu.get_input("\nCódigo do produto: ")
            if not codigo:
                return
            
            product = self.product_service.get_product(codigo)
            if not product:
                self.main_menu.show_error(f"Produto '{codigo}' não encontrado!")
                return
            
            print(f"✓ Produto: {product['PRODUTO']}")
            print(f"  Preço: R$ {float(product['VALOR']):.2f}")
            print(f"  Estoque disponível: {product['ESTOQUE']} unidades")
            
            # Step 3: Quantity
            quantidade = self.main_menu.get_number("\nQuantidade: ", min_value=1)
            if quantidade is None:
                return
            
            # Step 4: Calculate and confirm
            calculation = self.sale_service.calculate_sale_total(codigo, int(quantidade))
            
            print("\n" + "-"*60)
            print("RESUMO DA VENDA:")
            print(f"  Cliente: {client['CLIENTE']}")
            print(f"  Produto: {calculation['produto']}")
            print(f"  Quantidade: {calculation['quantidade']}")
            print(f"  Preço unitário: R$ {calculation['preco_unit']:.2f}")
            print(f"  TOTAL: R$ {calculation['preco_total']:.2f}")
            print("-"*60)
            
            if not calculation['estoque_suficiente']:
                self.main_menu.show_error("Estoque insuficiente!")
                return
            
            if not self.main_menu.confirm("\nConfirmar venda?", default=False):
                self.main_menu.show_info("Venda cancelada.")
                return
            
            # Step 5: Payment method
            print("\nMeios de pagamento disponíveis:")
            payment_methods = self.sale_service.get_available_payment_methods()
            for i, method in enumerate(payment_methods, 1):
                print(f"  [{i}] {method.title()}")
            
            payment_choice = self.main_menu.get_input("Escolha o meio de pagamento: ")
            try:
                meio = payment_methods[int(payment_choice) - 1]
            except (ValueError, IndexError):
                self.main_menu.show_error("Meio de pagamento inválido!")
                return
            
            # Step 6: Register sale
            sale = self.sale_service.register_sale(
                id_cliente=id_cliente,
                codigo=codigo,
                quantidade=int(quantidade),
                meio=meio
            )
            
            self.main_menu.show_success("Venda registrada com sucesso!")
            
            # Show sale details
            display_sale_detail(sale.to_dict())
            
        except ValueError as e:
            self.main_menu.show_error(str(e))
        except Exception as e:
            self.main_menu.show_error(f"Erro inesperado: {str(e)}")
    
    # ========== REPORTS ==========
    
    def reports_menu(self):
        """Reports and statistics submenu."""
        menu = create_submenu("RELATÓRIOS E ESTATÍSTICAS", self.main_menu)
        menu.add_option('1', '📊 Resumo de vendas', self.sales_summary)
        menu.add_option('2', '🏆 Top produtos', self.top_products)
        menu.add_option('3', '🏆 Top clientes', self.top_clients)
        menu.add_option('4', '👥 Estatísticas de clientes', self.client_stats)
        menu.add_option('5', '📦 Produtos com estoque baixo', self.low_stock)
        menu.add_option('6', '💰 Resumo do inventário', self.inventory_summary)
        menu.add_option('7', '📈 Analytics Avançado', self.advanced_analytics_menu)
        menu.display()
    
    def sales_summary(self):
        """Display sales summary."""
        print_section_header("RESUMO DE VENDAS")
        self.sale_service.get_sales_summary()
    
    def top_products(self):
        """Display top products."""
        print_section_header("TOP PRODUTOS")
        self.sale_service.get_top_products(limit=10)
    
    def top_clients(self):
        """Display top clients."""
        print_section_header("TOP CLIENTES")
        self.sale_service.get_top_clients(limit=10)
    
    def client_stats(self):
        """Display client statistics."""
        print_section_header("ESTATÍSTICAS DE CLIENTES")
        self.client_service.get_client_statistics()
    
    def low_stock(self):
        """Display products with low stock."""
        print_section_header("PRODUTOS COM ESTOQUE BAIXO")
        threshold = self.main_menu.get_number("\nLimite de estoque (padrão: 5): ", min_value=1)
        if threshold is None:
            threshold = 5
        self.product_service.check_low_stock(int(threshold))
    
    def inventory_summary(self):
        """Display inventory summary."""
        print_section_header("RESUMO DO INVENTÁRIO")
        self.product_service.get_inventory_summary()
    
    # ========== ADVANCED ANALYTICS ==========
    
    def advanced_analytics_menu(self):
        """Advanced analytics submenu."""
        menu = create_submenu("ANALYTICS AVANÇADO", self.main_menu)
        menu.add_option('1', '📈 Tendência de Vendas', self.sales_trend)
        menu.add_option('2', '⚖️  Comparação de Períodos', self.period_comparison)
        menu.add_option('3', '🎯 Análise ABC (Pareto)', self.abc_analysis)
        menu.add_option('4', '👥 Segmentação de Clientes', self.customer_segmentation)
        menu.add_option('5', '💎 Customer Lifetime Value', self.clv_analysis)
        menu.add_option('6', '📊 Desempenho por Categoria', self.category_performance)
        menu.add_option('7', '🔍 Análise Detalhada de Produtos', self.detailed_product_analysis)
        menu.add_option('8', '💰 Relatório de Lucratividade', self.profitability_report)
        menu.add_option('9', '💳 Análise de Pagamentos', self.payment_analysis)
        menu.add_option('A', '🔮 Previsão de Demanda', self.demand_forecast)
        menu.add_option('B', '📅 Análise de Sazonalidade', self.seasonality_analysis)
        menu.add_option('C', '📊 Gerar Gráficos', self.generate_charts_menu)
        menu.display()
    
    def sales_trend(self):
        """Display sales trend."""
        print_section_header("TENDÊNCIA DE VENDAS")
        
        print("\nPeríodo de análise:")
        print("  [1] Últimos 7 dias")
        print("  [2] Últimos 30 dias")
        print("  [3] Últimos 90 dias")
        
        choice = self.main_menu.get_input("Escolha: ")
        
        days_map = {'1': 7, '2': 30, '3': 90}
        days = days_map.get(choice, 30)
        
        try:
            trend = self.analytics_service.get_sales_trend(days)
            
            print(f"\n📊 Tendência de Vendas - {trend['period']}")
            print(f"Período: {trend['start_date']} até {trend['end_date']}")
            print(f"\nTotal de vendas: {trend['total_sales']}")
            print(f"Receita total: R$ {trend['total_revenue']:.2f}")
            print(f"Receita média diária: R$ {trend['average_daily_revenue']:.2f}")
            
            if trend['daily_data']:
                print_trend_chart(
                    trend['daily_data'],
                    value_key='revenue',
                    label_key='date',
                    title="\nGráfico de Receita Diária"
                )
                
                # Show top 5 days
                sorted_days = sorted(trend['daily_data'], key=lambda x: x['revenue'], reverse=True)
                print("\n🏆 Top 5 Dias com Maior Receita:")
                for i, day in enumerate(sorted_days[:5], 1):
                    print(f"  {i}. {day['date']}: R$ {day['revenue']:.2f} "
                          f"({day['sales_count']} vendas)")
        
        except Exception as e:
            self.main_menu.show_error(f"Erro ao gerar tendência: {str(e)}")
    
    def period_comparison(self):
        """Display period comparison."""
        print_section_header("COMPARAÇÃO DE PERÍODOS")
        
        print("\nComparar:")
        print("  [1] Últimos 7 dias vs. 7 dias anteriores")
        print("  [2] Últimos 30 dias vs. 30 dias anteriores")
        print("  [3] Personalizado")
        
        choice = self.main_menu.get_input("Escolha: ")
        
        if choice == '1':
            period1, period2 = 7, 7
        elif choice == '2':
            period1, period2 = 30, 30
        elif choice == '3':
            period1 = self.main_menu.get_number("Período recente (dias): ", min_value=1)
            period2 = self.main_menu.get_number("Período anterior (dias): ", min_value=1)
            if period1 is None or period2 is None:
                return
        else:
            self.main_menu.show_error("Opção inválida")
            return
        
        try:
            comparison = self.analytics_service.get_period_comparison(int(period1), int(period2))
            print_comparison(
                comparison['period1'],
                comparison['period2'],
                comparison['changes']
            )
        except Exception as e:
            self.main_menu.show_error(f"Erro ao comparar períodos: {str(e)}")
    
    def abc_analysis(self):
        """Display ABC analysis."""
        print_section_header("ANÁLISE ABC (CURVA DE PARETO)")
        
        try:
            abc_data = self.analytics_service.get_abc_analysis()
            print_abc_analysis(abc_data)
        except Exception as e:
            self.main_menu.show_error(f"Erro ao gerar análise ABC: {str(e)}")
    
    def customer_segmentation(self):
        """Display customer segmentation."""
        print_section_header("SEGMENTAÇÃO DE CLIENTES")
        
        try:
            segments = self.analytics_service.get_customer_segmentation()
            print_customer_segments(segments)
        except Exception as e:
            self.main_menu.show_error(f"Erro ao segmentar clientes: {str(e)}")
    
    def clv_analysis(self):
        """Display customer lifetime value analysis."""
        print_section_header("CUSTOMER LIFETIME VALUE (CLV)")
        
        top_n = self.main_menu.get_number("Quantos clientes exibir? (padrão: 10): ", min_value=1)
        if top_n is None:
            top_n = 10
        
        try:
            clv_data = self.analytics_service.get_customer_lifetime_value(int(top_n))
            print_clv_analysis(clv_data)
        except Exception as e:
            self.main_menu.show_error(f"Erro ao calcular CLV: {str(e)}")
    
    def category_performance(self):
        """Display category performance."""
        print_section_header("DESEMPENHO POR CATEGORIA")
        
        try:
            category_data = self.analytics_service.get_category_analysis()
            print_category_performance(category_data)
        except Exception as e:
            self.main_menu.show_error(f"Erro ao analisar categorias: {str(e)}")
    
    def detailed_product_analysis(self):
        """Display detailed product analysis."""
        print_section_header("ANÁLISE DETALHADA DE PRODUTOS")
        
        top_n = self.main_menu.get_number("Quantos produtos exibir? (padrão: 10): ", min_value=1)
        if top_n is None:
            top_n = 10
        
        try:
            performance = self.analytics_service.get_product_performance(int(top_n))
            print_product_performance(performance['top_products'], int(top_n))
            
            print(f"\n📊 Resumo Geral:")
            print(f"  Total de produtos vendidos: {performance['total_products_sold']}")
            print(f"  Receita total: R$ {performance['total_revenue']:.2f}")
            print(f"  Lucro total: R$ {performance['total_profit']:.2f}")
            
        except Exception as e:
            self.main_menu.show_error(f"Erro ao analisar produtos: {str(e)}")
    
    def profitability_report(self):
        """Display profitability report."""
        print_section_header("RELATÓRIO DE LUCRATIVIDADE")
        
        try:
            report = self.analytics_service.get_profitability_report()
            print_profitability_report(report)
        except Exception as e:
            self.main_menu.show_error(f"Erro ao gerar relatório: {str(e)}")
    
    def payment_analysis(self):
        """Display payment method analysis."""
        print_section_header("ANÁLISE DE MEIOS DE PAGAMENTO")
        
        try:
            payment_data = self.analytics_service.get_payment_method_analysis()
            print_payment_analysis(payment_data)
        except Exception as e:
            self.main_menu.show_error(f"Erro ao analisar pagamentos: {str(e)}")
    
    def demand_forecast(self):
        """Display demand forecasting."""
        print_section_header("PREVISÃO DE DEMANDA")
        
        codigo = self.main_menu.get_input("\nCódigo do produto: ")
        if not codigo:
            return
        
        periods = self.main_menu.get_number("Dias para prever (padrão: 30): ", min_value=1)
        if periods is None:
            periods = 30
        
        try:
            forecast = self.analytics_service.forecast_demand(codigo, int(periods))
            
            if 'error' in forecast:
                self.main_menu.show_error(forecast['error'])
                return
            
            print(f"\n📊 Previsão de Demanda - {forecast['product_name']} ({forecast['product_codigo']})")
            print(f"\nPeríodo de Previsão: {forecast['periods_ahead']} dias")
            print(f"Média Histórica Diária: {forecast['historical_avg_daily']:.1f} unidades/dia")
            print(f"Previsão Diária: {forecast['forecast_daily'][0]:.1f} unidades/dia")
            print(f"Previsão Total: {forecast['forecast_total']:.0f} unidades")
            print(f"Confiança: {forecast['confidence']}")
            
            print("\n💡 Recomendação de Estoque:")
            product = self.product_service.get_product(codigo)
            if product:
                current_stock = int(product['ESTOQUE'])
                forecasted_demand = forecast['forecast_total']
                
                print(f"  Estoque Atual: {current_stock} unidades")
                print(f"  Demanda Prevista: {forecasted_demand:.0f} unidades")
                
                if current_stock < forecasted_demand:
                    shortage = forecasted_demand - current_stock
                    print(f"  ⚠️  ATENÇÃO: Possível falta de {shortage:.0f} unidades!")
                    print(f"  Sugestão: Reabastecer com pelo menos {shortage:.0f} unidades")
                else:
                    print(f"  ✓ Estoque suficiente para o período")
        
        except Exception as e:
            self.main_menu.show_error(f"Erro ao gerar previsão: {str(e)}")
    
    def seasonality_analysis(self):
        """Display seasonality analysis."""
        print_section_header("ANÁLISE DE SAZONALIDADE")
        
        try:
            seasonality = self.analytics_service.get_seasonality_analysis()
            
            if 'error' in seasonality:
                self.main_menu.show_error(seasonality['error'])
                return
            
            print("\n📅 Padrões Sazonais Identificados:")
            
            # By month
            if seasonality['by_month']:
                print("\n🗓️  Por Mês:")
                months_pt = {
                    'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
                    'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
                    'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
                    'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
                }
                for month, data in seasonality['by_month'].items():
                    month_pt = months_pt.get(month, month)
                    print(f"  {month_pt}: {data['count']} vendas | R$ {data['revenue']:.2f}")
                
                peak_month_pt = months_pt.get(seasonality['peak_month'], seasonality['peak_month'])
                print(f"\n  🏆 Mês com Maior Receita: {peak_month_pt} "
                      f"(R$ {seasonality['peak_month_revenue']:.2f})")
            
            # By weekday
            if seasonality['by_weekday']:
                print("\n📆 Por Dia da Semana:")
                weekdays_pt = {
                    'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
                    'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
                }
                for weekday, data in seasonality['by_weekday'].items():
                    weekday_pt = weekdays_pt.get(weekday, weekday)
                    print(f"  {weekday_pt}: {data['count']} vendas | R$ {data['revenue']:.2f}")
                
                peak_weekday_pt = weekdays_pt.get(seasonality['peak_weekday'], seasonality['peak_weekday'])
                print(f"\n  🏆 Dia com Maior Receita: {peak_weekday_pt} "
                      f"(R$ {seasonality['peak_weekday_revenue']:.2f})")
            
            # By period of month
            if seasonality['by_period_of_month']:
                print("\n📊 Por Período do Mês:")
                for period, data in seasonality['by_period_of_month'].items():
                    print(f"  {period}: {data['count']} vendas | R$ {data['revenue']:.2f}")
        
        except Exception as e:
            self.main_menu.show_error(f"Erro ao analisar sazonalidade: {str(e)}")
    
    def generate_charts_menu(self):
        """Charts generation submenu."""
        menu = create_submenu("GERAR GRÁFICOS", self.main_menu)
        menu.add_option('1', '📈 Gráfico de Tendência de Vendas', self.chart_sales_trend)
        menu.add_option('2', '📊 Gráfico de Categorias', self.chart_categories)
        menu.add_option('3', '🏆 Gráfico Top Produtos', self.chart_top_products)
        menu.add_option('4', '👥 Gráfico de Segmentação', self.chart_customer_segments)
        menu.add_option('5', '💳 Gráfico de Pagamentos', self.chart_payment_methods)
        menu.add_option('6', '🎯 Gráfico ABC (Pareto)', self.chart_abc_analysis)
        menu.add_option('7', '💰 Gráfico de Lucratividade', self.chart_profitability)
        menu.display()
    
    def chart_sales_trend(self):
        """Generate sales trend chart."""
        print_section_header("GRÁFICO DE TENDÊNCIA")
        
        days = self.main_menu.get_number("Período (dias, padrão: 30): ", min_value=1)
        if days is None:
            days = 30
        
        try:
            trend = self.analytics_service.get_sales_trend(int(days))
            filepath = self.visualization_service.plot_sales_trend(trend)
            self.main_menu.show_success(f"Gráfico salvo em: {filepath}")
        except Exception as e:
            self.main_menu.show_error(f"Erro ao gerar gráfico: {str(e)}")
    
    def chart_categories(self):
        """Generate category distribution chart."""
        print_section_header("GRÁFICO DE CATEGORIAS")
        
        try:
            category_data = self.analytics_service.get_category_analysis()
            filepath = self.visualization_service.plot_category_distribution(category_data)
            self.main_menu.show_success(f"Gráfico salvo em: {filepath}")
        except Exception as e:
            self.main_menu.show_error(f"Erro ao gerar gráfico: {str(e)}")
    
    def chart_top_products(self):
        """Generate top products chart."""
        print_section_header("GRÁFICO TOP PRODUTOS")
        
        top_n = self.main_menu.get_number("Quantos produtos (padrão: 10): ", min_value=1)
        if top_n is None:
            top_n = 10
        
        try:
            performance = self.analytics_service.get_product_performance(int(top_n))
            filepath = self.visualization_service.plot_top_products(
                performance['all_products'], int(top_n)
            )
            self.main_menu.show_success(f"Gráfico salvo em: {filepath}")
        except Exception as e:
            self.main_menu.show_error(f"Erro ao gerar gráfico: {str(e)}")
    
    def chart_customer_segments(self):
        """Generate customer segmentation chart."""
        print_section_header("GRÁFICO DE SEGMENTAÇÃO")
        
        try:
            segments = self.analytics_service.get_customer_segmentation()
            filepath = self.visualization_service.plot_customer_segments(segments)
            self.main_menu.show_success(f"Gráfico salvo em: {filepath}")
        except Exception as e:
            self.main_menu.show_error(f"Erro ao gerar gráfico: {str(e)}")
    
    def chart_payment_methods(self):
        """Generate payment methods chart."""
        print_section_header("GRÁFICO DE PAGAMENTOS")
        
        try:
            payment_data = self.analytics_service.get_payment_method_analysis()
            filepath = self.visualization_service.plot_payment_methods(payment_data)
            self.main_menu.show_success(f"Gráfico salvo em: {filepath}")
        except Exception as e:
            self.main_menu.show_error(f"Erro ao gerar gráfico: {str(e)}")
    
    def chart_abc_analysis(self):
        """Generate ABC analysis chart."""
        print_section_header("GRÁFICO ABC")
        
        try:
            abc_data = self.analytics_service.get_abc_analysis()
            filepath = self.visualization_service.plot_abc_analysis(abc_data)
            self.main_menu.show_success(f"Gráfico salvo em: {filepath}")
        except Exception as e:
            self.main_menu.show_error(f"Erro ao gerar gráfico: {str(e)}")
    
    def chart_profitability(self):
        """Generate profitability chart."""
        print_section_header("GRÁFICO DE LUCRATIVIDADE")
        
        try:
            profitability = self.analytics_service.get_profitability_report()
            filepath = self.visualization_service.plot_profitability_overview(profitability)
            self.main_menu.show_success(f"Gráfico salvo em: {filepath}")
        except Exception as e:
            self.main_menu.show_error(f"Erro ao gerar gráfico: {str(e)}")
    

    
    # ========== LIST MENU ==========
    
    def list_menu(self):
        """List data submenu."""
        menu = create_submenu("LISTAR DADOS", self.main_menu)
        menu.add_option('1', '📦 Listar produtos', self.list_all_products)
        menu.add_option('2', '👥 Listar clientes', self.list_all_clients)
        menu.add_option('3', '💰 Listar vendas', self.list_all_sales)
        menu.display()
    
    def list_all_sales(self):
        """List all sales."""
        print_section_header("TODAS AS VENDAS")
        
        sales = self.sale_service.list_all_sales()
        display_sales(sales)
    
    # ========== RUN ==========
    
    def run(self):
        """Run the application."""
        try:
            self.main_menu.display()
        except KeyboardInterrupt:
            print("\n\nEncerrando o sistema...")
        finally:
            print("\nObrigado por usar o Sistema de Gestão de Perfumaria!")
            print("Até logo! 👋\n")


def main():
    """Application entry point."""
    app = PerfumeryApp()
    app.run()


if __name__ == "__main__":
    main()