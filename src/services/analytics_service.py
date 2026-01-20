"""
Analytics Service - OTIMIZADO PARA PERFORMANCE

Mudanças críticas:
1. Eliminado uso de Pandas onde possível
2. Agregações movidas para SQL (SUM, COUNT, GROUP BY, ORDER BY)
3. JOINs para reduzir número de queries
4. Processamento de datas otimizado
5. Queries com projeção de colunas específicas
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
from src.repositories.sale_repository import SaleRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.client_repository import ClientRepository
from src.repositories.sale_item_repository import SaleItemRepository


class AnalyticsService:
    """Service para analytics com performance otimizada."""
    
    def __init__(
        self,
        sale_repository: Optional[SaleRepository] = None,
        sale_item_repository: Optional[SaleItemRepository] = None,
        product_repository: Optional[ProductRepository] = None,
        client_repository: Optional[ClientRepository] = None
    ):
        self.sale_repo = sale_repository or SaleRepository()
        self.item_repo = sale_item_repository or SaleItemRepository()
        self.product_repo = product_repository or ProductRepository()
        self.client_repo = client_repository or ClientRepository()

    def _parse_date_str(self, s: str) -> Optional[datetime]:
        """Parse flexível de datas (dd/mm/YYYY ou ISO)."""
        if not s:
            return None
        
        s_str = str(s).strip()
        
        # Tenta formatos comuns
        for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
            try:
                return datetime.strptime(s_str, fmt)
            except ValueError:
                continue
        
        return None
    
    # ========== SALES ANALYTICS ==========
    
    def get_sales_trend(self, days: int = 30) -> Dict:
        """
        OTIMIZADO: Tendência de vendas com agregação SQL.
        
        Antes: 3-4 queries + processamento Pandas
        Depois: 2 queries SQL com GROUP BY
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Query 1: Vendas no período
        sales = self.sale_repo.get_by_date_range(
            start_date.strftime('%d/%m/%Y'),
            end_date.strftime('%d/%m/%Y')
        )
        
        # Agrupa por data em Python (otimizado com defaultdict)
        daily_sales = defaultdict(lambda: {'count': 0, 'revenue': 0.0, 'items': 0})
        
        sale_ids = []
        for sale in sales:
            date_obj = self._parse_date_str(sale.get('DATA'))
            if not date_obj:
                continue
            
            date_key = date_obj.strftime('%d/%m/%Y')
            daily_sales[date_key]['count'] += 1
            daily_sales[date_key]['revenue'] += float(sale.get('VALOR_TOTAL_VENDA', 0))
            sale_ids.append(sale['ID_VENDA'])
        
        # Query 2: Total de itens vendidos no período (agregação SQL)
        if sale_ids:
            with self.item_repo.get_conn() as conn:
                cur = self.item_repo._get_cursor(conn)
                
                # Monta placeholders dinamicamente
                placeholders = ','.join(['%s'] * len(sale_ids)) if self.item_repo.db_type == 'postgresql' else ','.join(['?'] * len(sale_ids))
                
                cur.execute(f'''
                    SELECT 
                        "ID_VENDA",
                        SUM(COALESCE("QUANTIDADE", 0)) as total_items
                    FROM sales_items
                    WHERE "ID_VENDA" IN ({placeholders})
                    GROUP BY "ID_VENDA"
                ''', sale_ids)
                
                items_by_sale = {row['ID_VENDA']: int(row['total_items']) for row in cur.fetchall()}
        else:
            items_by_sale = {}
        
        # Adiciona itens às vendas diárias
        for sale in sales:
            date_obj = self._parse_date_str(sale.get('DATA'))
            if not date_obj:
                continue
            
            date_key = date_obj.strftime('%d/%m/%Y')
            daily_sales[date_key]['items'] += items_by_sale.get(sale['ID_VENDA'], 0)
        
        # Converte para lista ordenada
        trend = []
        for date_str in sorted(daily_sales.keys(), key=lambda x: datetime.strptime(x, '%d/%m/%Y')):
            data = daily_sales[date_str]
            trend.append({
                'date': date_str,
                'sales_count': data['count'],
                'revenue': data['revenue'],
                'items_sold': data['items'],
                'avg_ticket': data['revenue'] / data['count'] if data['count'] > 0 else 0
            })
        
        return {
            'period': f"{days} dias",
            'start_date': start_date.strftime('%d/%m/%Y'),
            'end_date': end_date.strftime('%d/%m/%Y'),
            'daily_data': trend,
            'total_sales': sum(d['sales_count'] for d in trend),
            'total_revenue': sum(d['revenue'] for d in trend),
            'average_daily_revenue': sum(d['revenue'] for d in trend) / len(trend) if trend else 0
        }
    
    def get_period_comparison(self, period1_days: int, period2_days: int) -> Dict:
        """
        OTIMIZADO: Comparação de períodos com agregação SQL.
        """
        end_date = datetime.now()
        start_date1 = end_date - timedelta(days=period1_days)
        
        sales1 = self.sale_repo.get_by_date_range(
            start_date1.strftime('%d/%m/%Y'),
            end_date.strftime('%d/%m/%Y')
        )
        
        start_date2 = start_date1 - timedelta(days=period2_days)
        end_date2 = start_date1
        
        sales2 = self.sale_repo.get_by_date_range(
            start_date2.strftime('%d/%m/%Y'),
            end_date2.strftime('%d/%m/%Y')
        )
        
        # Calcula métricas
        revenue1 = sum(float(s['VALOR_TOTAL_VENDA']) for s in sales1)
        revenue2 = sum(float(s['VALOR_TOTAL_VENDA']) for s in sales2)
        
        # Total de itens (agregação SQL)
        sale_ids1 = [s['ID_VENDA'] for s in sales1]
        sale_ids2 = [s['ID_VENDA'] for s in sales2]
        
        def get_items_count(sale_ids):
            if not sale_ids:
                return 0
            
            with self.item_repo.get_conn() as conn:
                cur = self.item_repo._get_cursor(conn)
                placeholders = ','.join(['%s'] * len(sale_ids)) if self.item_repo.db_type == 'postgresql' else ','.join(['?'] * len(sale_ids))
                
                cur.execute(f'''
                    SELECT SUM(COALESCE("QUANTIDADE", 0)) as total
                    FROM sales_items
                    WHERE "ID_VENDA" IN ({placeholders})
                ''', sale_ids)
                
                result = cur.fetchone()
                return int(result['total'] or 0)
        
        items1 = get_items_count(sale_ids1)
        items2 = get_items_count(sale_ids2)
        
        # Calcula variações
        revenue_change = ((revenue1 - revenue2) / revenue2 * 100) if revenue2 > 0 else 0
        items_change = ((items1 - items2) / items2 * 100) if items2 > 0 else 0
        sales_change = ((len(sales1) - len(sales2)) / len(sales2) * 100) if len(sales2) > 0 else 0
        
        return {
            'period1': {
                'days': period1_days,
                'sales_count': len(sales1),
                'revenue': revenue1,
                'items_sold': items1,
                'avg_ticket': revenue1 / len(sales1) if sales1 else 0
            },
            'period2': {
                'days': period2_days,
                'sales_count': len(sales2),
                'revenue': revenue2,
                'items_sold': items2,
                'avg_ticket': revenue2 / len(sales2) if sales2 else 0
            },
            'changes': {
                'revenue_change_pct': revenue_change,
                'items_change_pct': items_change,
                'sales_change_pct': sales_change
            }
        }
    
    # ========== PRODUCT ANALYTICS ==========
    
    def get_product_performance(self, top_n: int = 10) -> Dict:
        """
        OTIMIZADO: Performance de produtos com JOIN SQL.
        
        Antes: 2 queries + loop + Pandas
        Depois: 1 query com JOIN
        """
        with self.item_repo.get_conn() as conn:
            cur = self.item_repo._get_cursor(conn)
            
            # JOIN para pegar stats + custo em 1 query
            cur.execute('''
                SELECT 
                    si."CODIGO",
                    si."PRODUTO",
                    si."CATEGORIA",
                    SUM(COALESCE(si."QUANTIDADE", 0)) AS qtd_vendida,
                    SUM(COALESCE(si."PRECO_TOTAL", 0)) AS receita,
                    COUNT(si."ID_VENDA") AS num_vendas,
                    COALESCE(p."CUSTO", 0) AS custo
                FROM sales_items si
                LEFT JOIN products p ON si."CODIGO" = p."CODIGO"
                GROUP BY si."CODIGO", si."PRODUTO", si."CATEGORIA", p."CUSTO"
                ORDER BY receita DESC
            ''')
            
            rows = cur.fetchall()
        
        results = []
        for row in rows:
            qtd_vendida = int(row['qtd_vendida'])
            receita = float(row['receita'])
            custo = float(row['custo'])
            
            profit = receita - (custo * qtd_vendida)
            profit_margin = (profit / receita * 100) if receita > 0 else 0
            
            results.append({
                'codigo': row['CODIGO'],
                'produto': row['PRODUTO'],
                'categoria': row['CATEGORIA'],
                'quantity_sold': qtd_vendida,
                'revenue': receita,
                'profit': profit,
                'profit_margin': profit_margin,
                'transactions': int(row['num_vendas'])
            })
        
        return {
            'top_products': results[:top_n],
            'all_products': results,
            'total_revenue': sum(r['revenue'] for r in results)
        }
    
    def get_category_analysis(self) -> Dict:
        """
        OTIMIZADO: Usa get_category_stats() que já retorna agregação SQL.
        """
        categories = self.item_repo.get_category_stats()
        
        if not categories:
            return {'categories': [], 'total_revenue': 0}
        
        total_revenue = sum(float(c['RECEITA']) for c in categories)
        
        results = []
        for cat in categories:
            receita = float(cat['RECEITA'])
            revenue_share = (receita / total_revenue * 100) if total_revenue > 0 else 0
            
            results.append({
                'category': cat['CATEGORIA'],
                'revenue': receita,
                'revenue_share': revenue_share,
                'items_sold': int(cat['QTD_VENDIDA']),
                'unique_products': int(cat['PRODUTOS_UNICOS'])
            })
        
        return {
            'categories': results,
            'total_revenue': total_revenue
        }
    
    def get_abc_analysis(self) -> Dict:
        """Análise ABC (Pareto) de produtos."""
        performance = self.get_product_performance(top_n=1000)
        products = performance['all_products']
        total_revenue = performance['total_revenue']
        
        if not products:
            return {'A': [], 'B': [], 'C': []}
        
        # Produtos já vêm ordenados por receita
        cumulative = 0
        a_products = []
        b_products = []
        c_products = []
        
        for product in products:
            cumulative += product['revenue']
            cumulative_pct = (cumulative / total_revenue * 100) if total_revenue > 0 else 0
            
            product['cumulative_revenue_pct'] = cumulative_pct
            
            if cumulative_pct <= 80:
                a_products.append(product)
            elif cumulative_pct <= 95:
                b_products.append(product)
            else:
                c_products.append(product)
        
        return {
            'A': a_products,
            'B': b_products,
            'C': c_products,
            'summary': {
                'A_count': len(a_products),
                'B_count': len(b_products),
                'C_count': len(c_products),
                'A_revenue_pct': 80.0,
                'B_revenue_pct': 15.0,
                'C_revenue_pct': 5.0
            }
        }
    
    # ========== CUSTOMER ANALYTICS ==========
    
    def get_customer_segmentation(self) -> Dict:
        """
        OTIMIZADO: Segmentação de clientes com agregação SQL.
        
        Antes: 3 queries + loops + Pandas
        Depois: 1 query com JOIN + GROUP BY
        """
        with self.sale_repo.get_conn() as conn:
            cur = self.sale_repo._get_cursor(conn)
            
            # Agrega métricas por cliente em SQL
            cur.execute('''
                SELECT 
                    s."ID_CLIENTE",
                    s."CLIENTE",
                    c."TIPO",
                    COUNT(s."ID_VENDA") AS purchases,
                    COALESCE(SUM(s."VALOR_TOTAL_VENDA"), 0) AS total_spent,
                    MAX(s."DATA") AS last_purchase_date,
                    MIN(s."DATA") AS first_purchase_date
                FROM sales s
                LEFT JOIN clients c ON s."ID_CLIENTE" = c."ID_CLIENTE"
                GROUP BY s."ID_CLIENTE", s."CLIENTE", c."TIPO"
            ''')
            
            customer_metrics = cur.fetchall()
        
        # Total de itens por cliente (agregação SQL)
        with self.item_repo.get_conn() as conn:
            cur = self.item_repo._get_cursor(conn)
            
            cur.execute('''
                SELECT 
                    s."ID_CLIENTE",
                    SUM(COALESCE(si."QUANTIDADE", 0)) AS items_bought
                FROM sales s
                JOIN sales_items si ON s."ID_VENDA" = si."ID_VENDA"
                GROUP BY s."ID_CLIENTE"
            ''')
            
            items_by_customer = {row['ID_CLIENTE']: int(row['items_bought']) for row in cur.fetchall()}
        
        # Segmenta clientes
        vip = []
        regular = []
        occasional = []
        inactive = []
        
        now = datetime.now()
        
        for row in customer_metrics:
            id_cliente = row['ID_CLIENTE']
            total_spent = float(row['total_spent'])
            purchases = int(row['purchases'])
            
            # Parse última compra
            last_purchase = self._parse_date_str(row['last_purchase_date'])
            recency = (now - last_purchase).days if last_purchase else 999
            
            customer_data = {
                'id_cliente': id_cliente,
                'cliente': row['CLIENTE'],
                'tipo': row['TIPO'] or 'Desconhecido',
                'total_spent': total_spent,
                'purchases': purchases,
                'items_bought': items_by_customer.get(id_cliente, 0),
                'avg_purchase': total_spent / purchases if purchases > 0 else 0,
                'recency_days': recency
            }
            
            # Lógica de segmentação
            if total_spent > 500 and purchases > 5:
                vip.append(customer_data)
            elif recency > 90:
                inactive.append(customer_data)
            elif purchases >= 3:
                regular.append(customer_data)
            else:
                occasional.append(customer_data)
        
        return {
            'VIP': sorted(vip, key=lambda x: x['total_spent'], reverse=True),
            'Regular': sorted(regular, key=lambda x: x['total_spent'], reverse=True),
            'Occasional': sorted(occasional, key=lambda x: x['total_spent'], reverse=True),
            'Inactive': sorted(inactive, key=lambda x: x['recency_days'], reverse=True),
            'summary': {
                'vip_count': len(vip),
                'regular_count': len(regular),
                'occasional_count': len(occasional),
                'inactive_count': len(inactive),
                'vip_revenue': sum(c['total_spent'] for c in vip),
                'regular_revenue': sum(c['total_spent'] for c in regular)
            }
        }
    
    # ========== FINANCIAL ANALYTICS ==========
    
    def get_profitability_report(self) -> Dict:
        """
        OTIMIZADO: Relatório de lucratividade com JOIN SQL.
        
        Antes: 2 queries + loop Pandas
        Depois: 1 query com JOIN
        """
        with self.item_repo.get_conn() as conn:
            cur = self.item_repo._get_cursor(conn)
            
            # JOIN para pegar receita + custo em 1 query
            cur.execute('''
                SELECT 
                    SUM(COALESCE(si."PRECO_TOTAL", 0)) AS total_revenue,
                    SUM(COALESCE(p."CUSTO", 0) * COALESCE(si."QUANTIDADE", 0)) AS total_cost
                FROM sales_items si
                LEFT JOIN products p ON si."CODIGO" = p."CODIGO"
            ''')
            
            row = cur.fetchone()
            total_revenue = float(row['total_revenue'] or 0)
            total_cost = float(row['total_cost'] or 0)
        
        gross_profit = total_revenue - total_cost
        profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Valor do inventário
        inventory = self.product_repo.get_inventory_value()
        
        return {
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'gross_profit': gross_profit,
            'profit_margin_pct': profit_margin,
            'inventory_cost_value': inventory['cost_value'],
            'inventory_retail_value': inventory['retail_value'],
            'potential_profit_from_inventory': inventory['retail_value'] - inventory['cost_value']
        }
    
    def get_payment_method_analysis(self) -> Dict:
        """
        OTIMIZADO: Usa get_sales_summary() que já agrega por meio de pagamento.
        """
        summary = self.sale_repo.get_sales_summary()
        payment_metrics = summary['by_payment_method']
        
        total_revenue = sum(payment_metrics.values())
        total_transactions = summary['total_sales']
        
        results = []
        for meio, revenue in payment_metrics.items():
            revenue_share = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            
            # Conta transações por meio
            with self.sale_repo.get_conn() as conn:
                cur = self.sale_repo._get_cursor(conn)
                placeholder = '%s' if self.sale_repo.db_type == 'postgresql' else '?'
                
                cur.execute(f'''
                    SELECT COUNT(*) AS count
                    FROM sales
                    WHERE "MEIO" = {placeholder}
                ''', (meio,))
                
                count = int(cur.fetchone()['count'])
            
            results.append({
                'payment_method': meio.title(),
                'transaction_count': count,
                'revenue': revenue,
                'revenue_share': revenue_share,
                'avg_ticket': revenue / count if count > 0 else 0
            })
        
        results.sort(key=lambda x: x['revenue'], reverse=True)
        
        return {
            'payment_methods': results,
            'total_revenue': total_revenue,
            'total_transactions': total_transactions
        }
    
    # ========== DEMAND FORECASTING ==========
    
    def forecast_demand(self, product_codigo: str, periods_ahead: int = 30) -> Dict:
        """Previsão de demanda (média móvel simplificada)."""
        items = self.item_repo.get_by_product(product_codigo)
        
        if not items:
            return {'error': 'No sales history for this product'}
        
        # Agrega vendas por data
        with self.sale_repo.get_conn() as conn:
            cur = self.sale_repo._get_cursor(conn)
            
            sale_ids = [item['ID_VENDA'] for item in items]
            placeholders = ','.join(['%s'] * len(sale_ids)) if self.sale_repo.db_type == 'postgresql' else ','.join(['?'] * len(sale_ids))
            
            cur.execute(f'''
                SELECT "DATA"
                FROM sales
                WHERE "ID_VENDA" IN ({placeholders})
                ORDER BY "DATA"
            ''', sale_ids)
            
            sale_dates = [row['DATA'] for row in cur.fetchall()]
        
        # Agrega quantidades por data
        daily_sales = defaultdict(int)
        for item in items:
            sale_id = item['ID_VENDA']
            sale_date = next((d for i, d in zip(sale_ids, sale_dates) if i == sale_id), None)
            
            if sale_date:
                date_obj = self._parse_date_str(sale_date)
                if date_obj:
                    daily_sales[date_obj.date()] += int(item['QUANTIDADE'])
        
        if not daily_sales:
            return {'error': 'No sales history for this product'}
        
        sorted_dates = sorted(daily_sales.keys())
        
        # Calcula média móvel
        if len(sorted_dates) < 7:
            avg_daily = sum(daily_sales.values()) / len(daily_sales)
            forecast = [avg_daily] * periods_ahead
        else:
            recent_sales = [daily_sales[date] for date in sorted_dates[-7:]]
            avg_daily = sum(recent_sales) / len(recent_sales)
            forecast = [avg_daily] * periods_ahead
        
        last_date = sorted_dates[-1]
        forecast_dates = [(last_date + timedelta(days=i+1)).strftime('%d/%m/%Y') for i in range(periods_ahead)]
        
        product = self.product_repo.get_by_codigo(product_codigo)
        
        return {
            'product_codigo': product_codigo,
            'product_name': product['PRODUTO'] if product else 'Unknown',
            'historical_avg_daily': avg_daily,
            'forecast_daily': forecast,
            'forecast_dates': forecast_dates,
            'forecast_total': sum(forecast),
            'periods_ahead': periods_ahead,
            'confidence': 'Low' if len(sorted_dates) < 30 else 'Medium' if len(sorted_dates) < 90 else 'High'
        }
    
    def get_seasonality_analysis(self) -> Dict:
        """Analyze seasonal patterns in sales."""
        sales = self.sale_repo.get_all().to_dict('records')
        
        if not sales:
            return {'error': 'No sales data available'}
        
        # Initialize metrics
        by_month = defaultdict(lambda: {'count': 0, 'revenue': 0.0})
        by_weekday = defaultdict(lambda: {'count': 0, 'revenue': 0.0})
        by_day_of_month = defaultdict(lambda: {'count': 0, 'revenue': 0.0})
        
        for sale in sales:
            date_obj = self._parse_date_str(sale.get('DATA'))
            if not date_obj:
                continue
            revenue = float(sale.get('VALOR_TOTAL_VENDA', 0))

            # By month
            month = date_obj.strftime('%B')
            by_month[month]['count'] += 1
            by_month[month]['revenue'] += revenue

            # By weekday
            weekday = date_obj.strftime('%A')
            by_weekday[weekday]['count'] += 1
            by_weekday[weekday]['revenue'] += revenue

            # By day of month period
            day = date_obj.day
            if day <= 10:
                period = 'Início (1-10)'
            elif day <= 20:
                period = 'Meio (11-20)'
            else:
                period = 'Fim (21-31)'

            by_day_of_month[period]['count'] += 1
            by_day_of_month[period]['revenue'] += revenue
        
        # Find patterns
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        by_month_sorted = [(m, by_month.get(m, {'count': 0, 'revenue': 0})) for m in month_order if m in by_month]
        by_weekday_sorted = [(w, by_weekday.get(w, {'count': 0, 'revenue': 0})) for w in weekday_order if w in by_weekday]
        
        if by_month_sorted:
            peak_month = max(by_month_sorted, key=lambda x: x[1]['revenue'])
        else:
            peak_month = ('N/A', {'count': 0, 'revenue': 0})
        
        if by_weekday_sorted:
            peak_weekday = max(by_weekday_sorted, key=lambda x: x[1]['revenue'])
        else:
            peak_weekday = ('N/A', {'count': 0, 'revenue': 0})
        
        return {
            'by_month': dict(by_month_sorted),
            'by_weekday': dict(by_weekday_sorted),
            'by_period_of_month': dict(by_day_of_month),
            'peak_month': peak_month[0],
            'peak_month_revenue': peak_month[1]['revenue'],
            'peak_weekday': peak_weekday[0],
            'peak_weekday_revenue': peak_weekday[1]['revenue']
        }