"""
Analytics service for advanced reporting and insights - FIXED for new structure.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from src.repositories.sale_repository import SaleRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.client_repository import ClientRepository
from src.repositories.sale_item_repository import SaleItemRepository


class AnalyticsService:
    """Service for advanced analytics and business intelligence."""
    
    def __init__(
        self,
        sale_repository: Optional[SaleRepository] = None,
        sale_item_repository: Optional[SaleItemRepository] = None,
        product_repository: Optional[ProductRepository] = None,
        client_repository: Optional[ClientRepository] = None
    ):
        """Initialize analytics service."""
        self.sale_repo = sale_repository or SaleRepository()
        self.item_repo = sale_item_repository or SaleItemRepository()
        self.product_repo = product_repository or ProductRepository()
        self.client_repo = client_repository or ClientRepository()

    def _parse_date_str(self, s: str):
        """Parse a date string flexibly, supporting dd/mm/YYYY and ISO.
        Returns a datetime.datetime or None if it cannot be parsed."""
        try:
            ts = pd.to_datetime(s, dayfirst=True, errors='coerce')
            if pd.isna(ts):
                return None
            return ts.to_pydatetime()
        except Exception:
            return None    
    # ========== SALES ANALYTICS ==========
    
    def get_sales_trend(self, days: int = 30) -> Dict:
        """Get sales trend for the last N days."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get sales headers
        sales = self.sale_repo.get_by_date_range(
            start_date.strftime('%d/%m/%Y'),
            end_date.strftime('%d/%m/%Y')
        )
        
        # Group by date (flexible parsing)
        daily_sales = defaultdict(lambda: {'count': 0, 'revenue': 0.0})
        print(f"[ANALYTICS] get_sales_trend: sales rows={len(sales)}")
        for sale in sales:
            date_obj = self._parse_date_str(sale.get('DATA'))
            if not date_obj:
                continue
            date_key = date_obj.strftime('%d/%m/%Y')
            daily_sales[date_key]['count'] += 1
            daily_sales[date_key]['revenue'] += float(sale.get('VALOR_TOTAL_VENDA', 0))
        
        # Get total items from sale_items
        items_df = self.item_repo._read_csv()
        sale_ids = [s['ID_VENDA'] for s in sales]
        items_in_period = items_df[items_df['ID_VENDA'].isin(sale_ids)]
        
        for _, item in items_in_period.iterrows():
            # Find corresponding sale date (parsed)
            sale = next((s for s in sales if s['ID_VENDA'] == item['ID_VENDA']), None)
            if sale:
                date_obj = self._parse_date_str(sale.get('DATA'))
                if not date_obj:
                    continue
                date_key = date_obj.strftime('%d/%m/%Y')
                daily_sales[date_key]['items'] = daily_sales[date_key].get('items', 0) + int(item['QUANTIDADE'])
        
        # Convert to sorted list
        trend = []
        for date_str in sorted(daily_sales.keys(), key=lambda x: datetime.strptime(x, '%d/%m/%Y')):
            data = daily_sales[date_str]
            trend.append({
                'date': date_str,
                'sales_count': data['count'],
                'revenue': data['revenue'],
                'items_sold': data.get('items', 0),
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
        """Compare two time periods."""
        # Recent period
        end_date = datetime.now()
        start_date1 = end_date - timedelta(days=period1_days)
        
        sales1 = self.sale_repo.get_by_date_range(
            start_date1.strftime('%d/%m/%Y'),
            end_date.strftime('%d/%m/%Y')
        )
        
        # Previous period
        start_date2 = start_date1 - timedelta(days=period2_days)
        end_date2 = start_date1
        
        sales2 = self.sale_repo.get_by_date_range(
            start_date2.strftime('%d/%m/%Y'),
            end_date2.strftime('%d/%m/%Y')
        )
        
        # Calculate metrics
        revenue1 = sum(float(s['VALOR_TOTAL_VENDA']) for s in sales1)
        revenue2 = sum(float(s['VALOR_TOTAL_VENDA']) for s in sales2)
        
        # Get items for periods
        items_df = self.item_repo._read_csv()
        sale_ids1 = [s['ID_VENDA'] for s in sales1]
        sale_ids2 = [s['ID_VENDA'] for s in sales2]
        
        items1 = int(items_df[items_df['ID_VENDA'].isin(sale_ids1)]['QUANTIDADE'].sum())
        items2 = int(items_df[items_df['ID_VENDA'].isin(sale_ids2)]['QUANTIDADE'].sum())
        
        # Calculate changes
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
    
    def get_hourly_sales_pattern(self) -> Dict:
        """Analyze sales patterns by day of week."""
        sales = self.sale_repo.get_all().to_dict('records')
        
        # Group by day of week
        dow_sales = defaultdict(lambda: {'count': 0, 'revenue': 0.0})
        
        for sale in sales:
            date_obj = self._parse_date_str(sale.get('DATA'))
            if not date_obj:
                continue
            dow = date_obj.strftime('%A')
            dow_sales[dow]['count'] += 1
            dow_sales[dow]['revenue'] += float(sale.get('VALOR_TOTAL_VENDA', 0))
        
        return dict(dow_sales)
    
    # ========== PRODUCT ANALYTICS ==========
    
    def get_product_performance(self, top_n: int = 10) -> Dict:
        """Get product performance using sales_items."""
        item_stats = self.item_repo.get_product_stats()
        print(f"[ANALYTICS] get_product_performance: item_stats rows={0 if item_stats is None else (0 if getattr(item_stats, 'empty', False) else len(item_stats))}")
        
        if item_stats.empty:
            return {'top_products': [], 'all_products': [], 'total_revenue': 0}
        
        # Enrich with cost data
        products_df = self.product_repo.get_all()
        print(f"[ANALYTICS] get_product_performance: products rows={len(products_df)}")
        
        results = []
        for _, row in item_stats.iterrows():
            codigo = row['CODIGO']
            
            # Get cost
            product = products_df[products_df['CODIGO'] == codigo]
            custo = float(product['CUSTO'].iloc[0]) if not product.empty else 0
            
            # Calculate profit
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
        
        results.sort(key=lambda x: x['revenue'], reverse=True)
        
        return {
            'top_products': results[:top_n],
            'all_products': results,
            'total_revenue': sum(r['revenue'] for r in results)
        }
    
    def get_category_analysis(self) -> Dict:
        """Category analysis using sales_items."""
        category_stats = self.item_repo.get_category_stats()
        
        if category_stats.empty:
            return {'categories': [], 'total_revenue': 0}
        
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
        
        return {
            'categories': results,
            'total_revenue': float(total_revenue)
        }
    
    def get_abc_analysis(self) -> Dict:
        """ABC analysis of products (Pareto principle)."""
        performance = self.get_product_performance(top_n=1000)
        products = performance['all_products']
        total_revenue = performance['total_revenue']
        
        if not products:
            return {'A': [], 'B': [], 'C': []}
        
        # Sort by revenue
        products.sort(key=lambda x: x['revenue'], reverse=True)
        
        # Calculate cumulative revenue
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
        """Segment customers by purchase behavior."""
        sales = self.sale_repo.get_all().to_dict('records')
        clients = self.client_repo.get_all().to_dict('records')
        
        # Aggregate customer data
        customer_metrics = defaultdict(lambda: {
            'total_spent': 0.0,
            'purchases': 0,
            'last_purchase_date': None,
            'first_purchase_date': None
        })
        
        for sale in sales:
            id_cliente = sale['ID_CLIENTE']
            date = self._parse_date_str(sale.get('DATA'))
            if not date:
                continue
            
            customer_metrics[id_cliente]['total_spent'] += float(sale.get('VALOR_TOTAL_VENDA', 0))
            customer_metrics[id_cliente]['purchases'] += 1
            
            if customer_metrics[id_cliente]['last_purchase_date'] is None or date > customer_metrics[id_cliente]['last_purchase_date']:
                customer_metrics[id_cliente]['last_purchase_date'] = date
            
            if customer_metrics[id_cliente]['first_purchase_date'] is None or date < customer_metrics[id_cliente]['first_purchase_date']:
                customer_metrics[id_cliente]['first_purchase_date'] = date
        
        # Get total items per customer
        items_df = self.item_repo._read_csv()
        customer_items = items_df.groupby('ID_VENDA')['QUANTIDADE'].sum().to_dict()
        
        # Map to customer
        for sale in sales:
            id_cliente = sale['ID_CLIENTE']
            id_venda = sale['ID_VENDA']
            if id_venda in customer_items:
                if 'items_bought' not in customer_metrics[id_cliente]:
                    customer_metrics[id_cliente]['items_bought'] = 0
                customer_metrics[id_cliente]['items_bought'] += customer_items[id_venda]
        
        # Segment customers
        vip = []
        regular = []
        occasional = []
        inactive = []
        
        now = datetime.now()
        
        for id_cliente, metrics in customer_metrics.items():
            client = next((c for c in clients if c['ID_CLIENTE'] == id_cliente), None)
            if not client:
                continue
            
            recency = (now - metrics['last_purchase_date']).days if metrics['last_purchase_date'] else 999
            
            customer_data = {
                'id_cliente': id_cliente,
                'cliente': client['CLIENTE'],
                'tipo': client['TIPO'],
                'total_spent': metrics['total_spent'],
                'purchases': metrics['purchases'],
                'items_bought': metrics.get('items_bought', 0),
                'avg_purchase': metrics['total_spent'] / metrics['purchases'],
                'recency_days': recency
            }
            
            # Segment logic
            if metrics['total_spent'] > 500 and metrics['purchases'] > 5:
                vip.append(customer_data)
            elif recency > 90:
                inactive.append(customer_data)
            elif metrics['purchases'] >= 3:
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
    
    def get_customer_lifetime_value(self, top_n: int = 10) -> List[Dict]:
        """Calculate customer lifetime value (CLV)."""
        sales = self.sale_repo.get_all().to_dict('records')
        clients = self.client_repo.get_all().to_dict('records')
        
        customer_clv = defaultdict(lambda: {
            'total_spent': 0.0,
            'purchases': 0,
            'first_purchase': None,
            'last_purchase': None
        })
        
        for sale in sales:
            id_cliente = sale['ID_CLIENTE']
            date = self._parse_date_str(sale.get('DATA'))
            if not date:
                continue
            
            customer_clv[id_cliente]['total_spent'] += float(sale.get('VALOR_TOTAL_VENDA', 0))
            customer_clv[id_cliente]['purchases'] += 1
            
            if customer_clv[id_cliente]['first_purchase'] is None or date < customer_clv[id_cliente]['first_purchase']:
                customer_clv[id_cliente]['first_purchase'] = date
            
            if customer_clv[id_cliente]['last_purchase'] is None or date > customer_clv[id_cliente]['last_purchase']:
                customer_clv[id_cliente]['last_purchase'] = date
        
        # Calculate CLV metrics
        results = []
        for id_cliente, metrics in customer_clv.items():
            client = next((c for c in clients if c['ID_CLIENTE'] == id_cliente), None)
            if not client:
                continue
            
            lifetime_days = (metrics['last_purchase'] - metrics['first_purchase']).days + 1
            avg_purchase = metrics['total_spent'] / metrics['purchases']
            purchase_frequency = metrics['purchases'] / (lifetime_days / 30)
            projected_clv = avg_purchase * purchase_frequency * 12
            
            results.append({
                'id_cliente': id_cliente,
                'cliente': client['CLIENTE'],
                'tipo': client['TIPO'],
                'total_spent': metrics['total_spent'],
                'purchases': metrics['purchases'],
                'avg_purchase': avg_purchase,
                'lifetime_days': lifetime_days,
                'purchase_frequency_monthly': purchase_frequency,
                'projected_clv_12mo': projected_clv,
                'total_clv': metrics['total_spent'] + projected_clv
            })
        
        results.sort(key=lambda x: x['total_clv'], reverse=True)
        return results[:top_n]
    
    # ========== FINANCIAL ANALYTICS ==========
    
    def get_profitability_report(self) -> Dict:
        """Comprehensive profitability analysis."""
        items_df = self.item_repo._read_csv()
        print(f"[ANALYTICS] get_profitability_report: items rows={len(items_df)}")
        products = self.product_repo.get_all().to_dict('records')
        print(f"[ANALYTICS] get_profitability_report: products rows={len(products)}")
        
        total_revenue = 0.0
        total_cost = 0.0
        
        for _, item in items_df.iterrows():
            codigo = item['CODIGO']
            quantidade = int(item['QUANTIDADE'])
            preco_total = float(item['PRECO_TOTAL'])
            
            # Find product cost
            product = next((p for p in products if p['CODIGO'] == codigo), None)
            if product:
                custo = float(product['CUSTO'])
                total_cost += custo * quantidade
            
            total_revenue += preco_total
        
        gross_profit = total_revenue - total_cost
        profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Get inventory value
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
        """Analyze sales by payment method."""
        sales = self.sale_repo.get_all().to_dict('records')
        print(f"[ANALYTICS] get_payment_method_analysis: sales rows={len(sales)}")
        
        payment_metrics = defaultdict(lambda: {
            'count': 0,
            'revenue': 0.0,
            'avg_ticket': 0.0
        })
        
        for sale in sales:
            meio = sale['MEIO']
            payment_metrics[meio]['count'] += 1
            payment_metrics[meio]['revenue'] += float(sale['VALOR_TOTAL_VENDA'])
        
        # Calculate averages
        total_revenue = sum(m['revenue'] for m in payment_metrics.values())
        
        results = []
        for meio, metrics in payment_metrics.items():
            metrics['avg_ticket'] = metrics['revenue'] / metrics['count']
            revenue_share = (metrics['revenue'] / total_revenue * 100) if total_revenue > 0 else 0
            
            results.append({
                'payment_method': meio.title(),
                'transaction_count': metrics['count'],
                'revenue': metrics['revenue'],
                'revenue_share': revenue_share,
                'avg_ticket': metrics['avg_ticket']
            })
        
        results.sort(key=lambda x: x['revenue'], reverse=True)
        
        return {
            'payment_methods': results,
            'total_revenue': total_revenue,
            'total_transactions': sum(m['count'] for m in payment_metrics.values())
        }
    
    # ========== DEMAND FORECASTING ==========
    
    def forecast_demand(self, product_codigo: str, periods_ahead: int = 30) -> Dict:
        """Simple demand forecasting using moving average."""
        items = self.item_repo.get_by_product(product_codigo)
        
        if not items:
            return {'error': 'No sales history for this product'}
        
# Get sales dates and aggregate by actual date objects (robust to formats)
        sales_df = self.sale_repo.get_all()

        # Group by date (date objects)
        daily_sales = defaultdict(int)
        for item in items:
            sale = sales_df[sales_df['ID_VENDA'] == item['ID_VENDA']]
            if not sale.empty:
                date_raw = sale.iloc[0]['DATA']
                date_obj = self._parse_date_str(date_raw)
                if not date_obj:
                    continue
                date_key = date_obj.date()
                daily_sales[date_key] += int(item['QUANTIDADE'])

        if not daily_sales:
            return {'error': 'No sales history for this product'}

        sorted_dates = sorted(daily_sales.keys())

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