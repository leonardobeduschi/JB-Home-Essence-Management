"""
Analytics service for advanced reporting and insights.

This module provides comprehensive analytics capabilities including:
- Sales trends and forecasting
- Customer behavior analysis
- Product performance metrics
- Financial reporting
- Period comparisons
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from src.repositories.sale_repository import SaleRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.client_repository import ClientRepository


class AnalyticsService:
    """
    Service for advanced analytics and business intelligence.
    """
    
    def __init__(
        self,
        sale_repository: Optional[SaleRepository] = None,
        product_repository: Optional[ProductRepository] = None,
        client_repository: Optional[ClientRepository] = None
    ):
        """Initialize analytics service."""
        self.sale_repo = sale_repository or SaleRepository()
        self.product_repo = product_repository or ProductRepository()
        self.client_repo = client_repository or ClientRepository()
    
    # ========== SALES ANALYTICS ==========
    
    def get_sales_trend(self, days: int = 30) -> Dict:
        """
        Get sales trend for the last N days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with daily sales data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        sales = self.sale_repo.get_by_date_range(
            start_date.strftime('%d/%m/%Y'),
            end_date.strftime('%d/%m/%Y')
        )
        
        # Group by date
        daily_sales = defaultdict(lambda: {'count': 0, 'revenue': 0.0, 'items': 0})
        
        for sale in sales:
            date = sale['DATA']
            daily_sales[date]['count'] += 1
            daily_sales[date]['revenue'] += float(sale['PRECO_TOTAL'])
            daily_sales[date]['items'] += int(sale['QUANTIDADE'])
        
        # Convert to sorted list
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
        Compare two time periods.
        
        Args:
            period1_days: Days for recent period
            period2_days: Days for comparison period
            
        Returns:
            Comparison metrics
        """
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
        revenue1 = sum(float(s['PRECO_TOTAL']) for s in sales1)
        revenue2 = sum(float(s['PRECO_TOTAL']) for s in sales2)
        
        items1 = sum(int(s['QUANTIDADE']) for s in sales1)
        items2 = sum(int(s['QUANTIDADE']) for s in sales2)
        
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
        """
        Analyze sales patterns by hour (if time data available).
        
        Note: Currently uses day of week as we don't have hour data.
        
        Returns:
            Sales pattern by day of week
        """
        sales = self.sale_repo.get_all().to_dict('records')
        
        # Group by day of week
        dow_sales = defaultdict(lambda: {'count': 0, 'revenue': 0.0})
        
        for sale in sales:
            try:
                date_obj = datetime.strptime(sale['DATA'], '%d/%m/%Y')
                dow = date_obj.strftime('%A')  # Day name
                
                dow_sales[dow]['count'] += 1
                dow_sales[dow]['revenue'] += float(sale['PRECO_TOTAL'])
            except:
                continue
        
        return dict(dow_sales)
    
    # ========== PRODUCT ANALYTICS ==========
    
    def get_product_performance(self, top_n: int = 10) -> Dict:
        """
        Comprehensive product performance analysis.
        
        Args:
            top_n: Number of top products to return
            
        Returns:
            Product performance metrics
        """
        sales = self.sale_repo.get_all().to_dict('records')
        products = self.product_repo.get_all().to_dict('records')
        
        # Aggregate by product
        product_metrics = defaultdict(lambda: {
            'quantity_sold': 0,
            'revenue': 0.0,
            'transactions': 0,
            'customers': set()
        })
        
        for sale in sales:
            codigo = sale['CODIGO']
            product_metrics[codigo]['quantity_sold'] += int(sale['QUANTIDADE'])
            product_metrics[codigo]['revenue'] += float(sale['PRECO_TOTAL'])
            product_metrics[codigo]['transactions'] += 1
            product_metrics[codigo]['customers'].add(sale['ID_CLIENTE'])
        
        # Calculate additional metrics
        results = []
        for codigo, metrics in product_metrics.items():
            # Get product info
            product = next((p for p in products if p['CODIGO'] == codigo), None)
            if not product:
                continue
            
            custo = float(product['CUSTO'])
            valor = float(product['VALOR'])
            estoque = int(product['ESTOQUE'])
            
            # Calculate profit
            profit = metrics['revenue'] - (custo * metrics['quantity_sold'])
            profit_margin = (profit / metrics['revenue'] * 100) if metrics['revenue'] > 0 else 0
            
            # Calculate turnover rate
            turnover_rate = metrics['quantity_sold'] / (metrics['quantity_sold'] + estoque) * 100 if (metrics['quantity_sold'] + estoque) > 0 else 0
            
            results.append({
                'codigo': codigo,
                'produto': product['PRODUTO'],
                'categoria': product['CATEGORIA'],
                'quantity_sold': metrics['quantity_sold'],
                'revenue': metrics['revenue'],
                'profit': profit,
                'profit_margin': profit_margin,
                'transactions': metrics['transactions'],
                'unique_customers': len(metrics['customers']),
                'avg_quantity_per_sale': metrics['quantity_sold'] / metrics['transactions'],
                'current_stock': estoque,
                'turnover_rate': turnover_rate
            })
        
        # Sort by revenue
        results.sort(key=lambda x: x['revenue'], reverse=True)
        
        return {
            'top_products': results[:top_n],
            'all_products': results,
            'total_products_sold': len(results),
            'total_revenue': sum(r['revenue'] for r in results),
            'total_profit': sum(r['profit'] for r in results)
        }
    
    def get_category_analysis(self) -> Dict:
        """
        Analyze sales by product category.
        
        Returns:
            Category performance metrics
        """
        sales = self.sale_repo.get_all().to_dict('records')
        
        category_metrics = defaultdict(lambda: {
            'sales_count': 0,
            'revenue': 0.0,
            'items_sold': 0,
            'unique_products': set()
        })
        
        for sale in sales:
            # Normalize category to title case to avoid duplicates due to casing
            cat = str(sale.get('CATEGORIA', '')).strip().title()
            category_metrics[cat]['sales_count'] += 1
            category_metrics[cat]['revenue'] += float(sale.get('PRECO_TOTAL', 0))
            category_metrics[cat]['items_sold'] += int(sale.get('QUANTIDADE', 0))
            category_metrics[cat]['unique_products'].add(sale.get('CODIGO'))
        
        # Convert to list
        results = []
        total_revenue = sum(m['revenue'] for m in category_metrics.values())
        
        for category, metrics in category_metrics.items():
            revenue_share = (metrics['revenue'] / total_revenue * 100) if total_revenue > 0 else 0
            
            results.append({
                'category': category,
                'sales_count': metrics['sales_count'],
                'revenue': metrics['revenue'],
                'revenue_share': revenue_share,
                'items_sold': metrics['items_sold'],
                'unique_products': len(metrics['unique_products']),
                'avg_sale_value': metrics['revenue'] / metrics['sales_count']
            })
        
        results.sort(key=lambda x: x['revenue'], reverse=True)
        
        return {
            'categories': results,
            'total_categories': len(results),
            'total_revenue': total_revenue
        }
    
    def get_abc_analysis(self) -> Dict:
        """
        ABC analysis of products (Pareto principle).
        
        A = 80% of revenue (top products)
        B = 15% of revenue (medium products)
        C = 5% of revenue (low products)
        
        Returns:
            Products classified by ABC
        """
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
            'A': a_products,  # Top performers
            'B': b_products,  # Medium performers
            'C': c_products,  # Low performers
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
        Segment customers by purchase behavior (RFM-like).
        
        Returns:
            Customer segments
        """
        sales = self.sale_repo.get_all().to_dict('records')
        clients = self.client_repo.get_all().to_dict('records')
        
        # Aggregate customer data
        customer_metrics = defaultdict(lambda: {
            'total_spent': 0.0,
            'purchases': 0,
            'items_bought': 0,
            'last_purchase_date': None,
            'first_purchase_date': None
        })
        
        for sale in sales:
            id_cliente = sale['ID_CLIENTE']
            date = datetime.strptime(sale['DATA'], '%d/%m/%Y')
            
            customer_metrics[id_cliente]['total_spent'] += float(sale['PRECO_TOTAL'])
            customer_metrics[id_cliente]['purchases'] += 1
            customer_metrics[id_cliente]['items_bought'] += int(sale['QUANTIDADE'])
            
            if customer_metrics[id_cliente]['last_purchase_date'] is None or date > customer_metrics[id_cliente]['last_purchase_date']:
                customer_metrics[id_cliente]['last_purchase_date'] = date
            
            if customer_metrics[id_cliente]['first_purchase_date'] is None or date < customer_metrics[id_cliente]['first_purchase_date']:
                customer_metrics[id_cliente]['first_purchase_date'] = date
        
        # Segment customers
        vip = []  # High value
        regular = []  # Regular customers
        occasional = []  # Low frequency
        inactive = []  # No recent purchases
        
        now = datetime.now()
        
        for id_cliente, metrics in customer_metrics.items():
            client = next((c for c in clients if c['ID_CLIENTE'] == id_cliente), None)
            if not client:
                continue
            
            # Calculate recency (days since last purchase)
            recency = (now - metrics['last_purchase_date']).days if metrics['last_purchase_date'] else 999
            
            customer_data = {
                'id_cliente': id_cliente,
                'cliente': client['CLIENTE'],
                'tipo': client['TIPO'],
                'total_spent': metrics['total_spent'],
                'purchases': metrics['purchases'],
                'items_bought': metrics['items_bought'],
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
        """
        Calculate customer lifetime value (CLV).
        
        Args:
            top_n: Number of top customers to return
            
        Returns:
            Customers with CLV metrics
        """
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
            date = datetime.strptime(sale['DATA'], '%d/%m/%Y')
            
            customer_clv[id_cliente]['total_spent'] += float(sale['PRECO_TOTAL'])
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
            
            # Customer lifetime in days
            lifetime_days = (metrics['last_purchase'] - metrics['first_purchase']).days + 1
            
            # Predicted lifetime value (simple projection)
            avg_purchase = metrics['total_spent'] / metrics['purchases']
            purchase_frequency = metrics['purchases'] / (lifetime_days / 30)  # Per month
            
            # Project for next 12 months
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
        """
        Comprehensive profitability analysis.
        
        Returns:
            Profit metrics
        """
        sales = self.sale_repo.get_all().to_dict('records')
        products = self.product_repo.get_all().to_dict('records')
        
        total_revenue = 0.0
        total_cost = 0.0
        
        for sale in sales:
            codigo = sale['CODIGO']
            quantidade = int(sale['QUANTIDADE'])
            preco_total = float(sale['PRECO_TOTAL'])
            
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
        """
        Analyze sales by payment method.
        
        Returns:
            Payment method metrics
        """
        sales = self.sale_repo.get_all().to_dict('records')
        
        payment_metrics = defaultdict(lambda: {
            'count': 0,
            'revenue': 0.0,
            'avg_ticket': 0.0
        })
        
        for sale in sales:
            meio = sale['MEIO']
            payment_metrics[meio]['count'] += 1
            payment_metrics[meio]['revenue'] += float(sale['PRECO_TOTAL'])
        
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
        """
        Simple demand forecasting using moving average.
        
        Args:
            product_codigo: Product code to forecast
            periods_ahead: Number of days to forecast
            
        Returns:
            Forecast data
        """
        sales = self.sale_repo.get_by_product(product_codigo)
        
        if not sales:
            return {'error': 'No sales history for this product'}
        
        # Group by date
        daily_sales = defaultdict(int)
        for sale in sales:
            date = sale['DATA']
            daily_sales[date] += int(sale['QUANTIDADE'])
        
        # Calculate moving average (7-day)
        sorted_dates = sorted(daily_sales.keys(), key=lambda x: datetime.strptime(x, '%d/%m/%Y'))
        
        if len(sorted_dates) < 7:
            # Not enough data, use simple average
            avg_daily = sum(daily_sales.values()) / len(daily_sales)
            forecast = [avg_daily] * periods_ahead
        else:
            # Use 7-day moving average
            recent_sales = [daily_sales[date] for date in sorted_dates[-7:]]
            avg_daily = sum(recent_sales) / len(recent_sales)
            forecast = [avg_daily] * periods_ahead
        
        # Calculate forecast dates
        last_date = datetime.strptime(sorted_dates[-1], '%d/%m/%Y')
        forecast_dates = [(last_date + timedelta(days=i+1)).strftime('%d/%m/%Y') 
                         for i in range(periods_ahead)]
        
        # Get product info
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
        """
        Analyze seasonal patterns in sales.
        
        Returns:
            Seasonality metrics by month, weekday, etc.
        """
        sales = self.sale_repo.get_all().to_dict('records')
        
        if not sales:
            return {'error': 'No sales data available'}
        
        # Initialize metrics
        by_month = defaultdict(lambda: {'count': 0, 'revenue': 0.0})
        by_weekday = defaultdict(lambda: {'count': 0, 'revenue': 0.0})
        by_day_of_month = defaultdict(lambda: {'count': 0, 'revenue': 0.0})
        
        for sale in sales:
            try:
                date_obj = datetime.strptime(sale['DATA'], '%d/%m/%Y')
                revenue = float(sale['PRECO_TOTAL'])
                
                # By month
                month = date_obj.strftime('%B')  # Full month name
                by_month[month]['count'] += 1
                by_month[month]['revenue'] += revenue
                
                # By weekday
                weekday = date_obj.strftime('%A')  # Full day name
                by_weekday[weekday]['count'] += 1
                by_weekday[weekday]['revenue'] += revenue
                
                # By day of month (1-31)
                day = date_obj.day
                if day <= 10:
                    period = 'Início (1-10)'
                elif day <= 20:
                    period = 'Meio (11-20)'
                else:
                    period = 'Fim (21-31)'
                
                by_day_of_month[period]['count'] += 1
                by_day_of_month[period]['revenue'] += revenue
                
            except:
                continue
        
        # Find patterns
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Sort by defined order
        by_month_sorted = [(m, by_month.get(m, {'count': 0, 'revenue': 0})) for m in month_order if m in by_month]
        by_weekday_sorted = [(w, by_weekday.get(w, {'count': 0, 'revenue': 0})) for w in weekday_order if w in by_weekday]
        
        # Find peak patterns
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
    
