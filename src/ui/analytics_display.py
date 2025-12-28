"""
Analytics display utilities.

Functions to visualize analytics data in the terminal with
ASCII charts, tables, and formatted reports.
"""

from typing import List, Dict
import math


def print_bar_chart(data: List[tuple], title: str, max_width: int = 50):
    """
    Print a horizontal bar chart.
    
    Args:
        data: List of (label, value) tuples
        title: Chart title
        max_width: Maximum bar width in characters
    """
    if not data:
        print("\nNenhum dado para exibir.")
        return
    
    print(f"\n{title}")
    print("="*70)
    
    # Find max value for scaling
    max_value = max(v for _, v in data)
    
    for label, value in data:
        # Calculate bar length
        if max_value > 0:
            bar_length = int((value / max_value) * max_width)
        else:
            bar_length = 0
        
        # Create bar
        bar = "█" * bar_length
        
        # Format value
        if isinstance(value, float):
            value_str = f"{value:.2f}"
        else:
            value_str = str(value)
        
        print(f"{label[:25]:<25} {bar} {value_str}")


def print_trend_chart(data: List[Dict], value_key: str, label_key: str = 'date', title: str = "Tendência"):
    """
    Print a simple ASCII trend chart.
    
    Args:
        data: List of dictionaries with trend data
        value_key: Key for values to plot
        label_key: Key for labels
        title: Chart title
    """
    if not data:
        print("\nNenhum dado para exibir.")
        return
    
    print(f"\n{title}")
    print("="*70)
    
    # Extract values
    values = [d[value_key] for d in data]
    labels = [d[label_key] for d in data]
    
    # Normalize values to 0-10 scale for chart
    max_val = max(values) if values else 1
    min_val = min(values) if values else 0
    
    if max_val == min_val:
        normalized = [5] * len(values)
    else:
        normalized = [int((v - min_val) / (max_val - min_val) * 10) for v in values]
    
    # Print chart (10 rows)
    for row in range(10, -1, -1):
        line = f"{row:2} |"
        for norm_val in normalized:
            if norm_val >= row:
                line += "█"
            else:
                line += " "
        print(line)
    
    # Print x-axis
    print("   " + "-" * len(values))
    
    # Print labels (show every nth label to avoid crowding)
    step = max(1, len(labels) // 10)
    label_line = "    "
    for i, label in enumerate(labels):
        if i % step == 0:
            # Shorten label
            short_label = label[-5:] if len(label) > 5 else label
            label_line += short_label[:5].ljust(step + 1)
    
    print(label_line)
    
    # Print legend
    print(f"\nMin: {min_val:.2f} | Max: {max_val:.2f}")


def print_comparison(period1: Dict, period2: Dict, changes: Dict):
    """
    Print period comparison.
    
    Args:
        period1: Recent period data
        period2: Previous period data
        changes: Change percentages
    """
    print("\n" + "="*70)
    print("  COMPARAÇÃO DE PERÍODOS")
    print("="*70)
    
    print(f"\nPeríodo Recente ({period1['days']} dias):")
    print(f"  Vendas: {period1['sales_count']}")
    print(f"  Receita: R$ {period1['revenue']:.2f}")
    print(f"  Itens: {period1['items_sold']}")
    print(f"  Ticket Médio: R$ {period1['avg_ticket']:.2f}")
    
    print(f"\nPeríodo Anterior ({period2['days']} dias):")
    print(f"  Vendas: {period2['sales_count']}")
    print(f"  Receita: R$ {period2['revenue']:.2f}")
    print(f"  Itens: {period2['items_sold']}")
    print(f"  Ticket Médio: R$ {period2['avg_ticket']:.2f}")
    
    print("\nVariação:")
    
    # Revenue change
    revenue_change = changes['revenue_change_pct']
    revenue_arrow = "📈" if revenue_change > 0 else "📉" if revenue_change < 0 else "→"
    print(f"  {revenue_arrow} Receita: {revenue_change:+.1f}%")
    
    # Sales change
    sales_change = changes['sales_change_pct']
    sales_arrow = "📈" if sales_change > 0 else "📉" if sales_change < 0 else "→"
    print(f"  {sales_arrow} Vendas: {sales_change:+.1f}%")
    
    # Items change
    items_change = changes['items_change_pct']
    items_arrow = "📈" if items_change > 0 else "📉" if items_change < 0 else "→"
    print(f"  {items_arrow} Itens: {items_change:+.1f}%")


def print_abc_analysis(abc_data: Dict):
    """
    Print ABC analysis results.
    
    Args:
        abc_data: ABC classification data
    """
    print("\n" + "="*70)
    print("  ANÁLISE ABC (Curva de Pareto)")
    print("="*70)
    
    summary = abc_data['summary']
    
    print("\nDistribuição:")
    print(f"  Classe A (80% receita): {summary['A_count']} produtos")
    print(f"  Classe B (15% receita): {summary['B_count']} produtos")
    print(f"  Classe C (5% receita): {summary['C_count']} produtos")
    
    print("\nClasse A - Produtos Estratégicos:")
    for i, product in enumerate(abc_data['A'][:5], 1):
        print(f"  {i}. {product['produto'][:30]}")
        print(f"     Receita: R$ {product['revenue']:.2f} | "
              f"Vendidos: {product['quantity_sold']} | "
              f"Margem: {product['profit_margin']:.1f}%")
    
    if len(abc_data['A']) > 5:
        print(f"  ... e mais {len(abc_data['A']) - 5} produtos")
    
    print("\n💡 Recomendação:")
    print("  Foque na gestão dos produtos Classe A - eles geram 80% da receita!")


def print_customer_segments(segments: Dict):
    """
    Print customer segmentation results.
    
    Args:
        segments: Customer segment data
    """
    print("\n" + "="*70)
    print("  SEGMENTAÇÃO DE CLIENTES")
    print("="*70)
    
    summary = segments['summary']
    
    print("\n📊 Resumo:")
    print(f"  🌟 VIP: {summary['vip_count']} clientes - R$ {summary['vip_revenue']:.2f}")
    print(f"  ✅ Regular: {summary['regular_count']} clientes - R$ {summary['regular_revenue']:.2f}")
    print(f"  ⭐ Ocasional: {summary['occasional_count']} clientes")
    print(f"  😴 Inativos: {summary['inactive_count']} clientes")
    
    print("\n🌟 Top 5 Clientes VIP:")
    for i, customer in enumerate(segments['VIP'][:5], 1):
        print(f"  {i}. {customer['cliente'][:25]}")
        print(f"     Total Gasto: R$ {customer['total_spent']:.2f} | "
              f"Compras: {customer['purchases']} | "
              f"Ticket Médio: R$ {customer['avg_purchase']:.2f}")
    
    if segments['Inactive']:
        print("\n💤 Clientes Inativos (há mais de 90 dias):")
        for i, customer in enumerate(segments['Inactive'][:3], 1):
            print(f"  {i}. {customer['cliente'][:25]} - "
                  f"Última compra: {customer['recency_days']} dias atrás")
        
        print("\n💡 Oportunidade: Crie uma campanha de reativação!")


def print_profitability_report(report: Dict):
    """
    Print profitability report.
    
    Args:
        report: Profitability data
    """
    print("\n" + "="*70)
    print("  RELATÓRIO DE LUCRATIVIDADE")
    print("="*70)
    
    print(f"\n💰 Receita Total: R$ {report['total_revenue']:.2f}")
    print(f"💸 Custo Total: R$ {report['total_cost']:.2f}")
    print(f"💵 Lucro Bruto: R$ {report['gross_profit']:.2f}")
    print(f"📊 Margem de Lucro: {report['profit_margin_pct']:.1f}%")
    
    print(f"\n📦 Inventário:")
    print(f"  Valor de Custo: R$ {report['inventory_cost_value']:.2f}")
    print(f"  Valor de Varejo: R$ {report['inventory_retail_value']:.2f}")
    print(f"  Lucro Potencial: R$ {report['potential_profit_from_inventory']:.2f}")
    
    # Visualize profit margin
    margin = report['profit_margin_pct']
    bar_length = int(margin / 2)  # Scale to 50 chars for 100%
    bar = "█" * bar_length
    
    print(f"\nMargem de Lucro Visual:")
    print(f"0%  {bar} {margin:.1f}%  100%")


def print_category_performance(category_data: Dict):
    """
    Print category performance.
    
    Args:
        category_data: Category analysis data
    """
    print("\n" + "="*70)
    print("  DESEMPENHO POR CATEGORIA")
    print("="*70)
    
    categories = category_data['categories']
    
    for i, cat in enumerate(categories, 1):
        print(f"\n{i}. {cat['category']}")
        print(f"   Vendas: {cat['sales_count']} | "
              f"Receita: R$ {cat['revenue']:.2f} ({cat['revenue_share']:.1f}%)")
        print(f"   Ticket Médio: R$ {cat['avg_sale_value']:.2f} | "
              f"Produtos: {cat['unique_products']}")
        
        # Bar for revenue share
        bar_length = int(cat['revenue_share'] / 2)
        bar = "█" * bar_length
        print(f"   {bar}")


def print_product_performance(products: List[Dict], top_n: int = 10):
    """
    Print detailed product performance.
    
    Args:
        products: Product performance data
        top_n: Number of products to show
    """
    print("\n" + "="*70)
    print(f"  TOP {top_n} PRODUTOS - ANÁLISE DETALHADA")
    print("="*70)
    
    for i, product in enumerate(products[:top_n], 1):
        print(f"\n{i}. {product['produto']} ({product['codigo']})")
        print(f"   Categoria: {product['categoria']}")
        print(f"   Quantidade Vendida: {product['quantity_sold']} unidades")
        print(f"   Receita: R$ {product['revenue']:.2f}")
        print(f"   Lucro: R$ {product['profit']:.2f} (Margem: {product['profit_margin']:.1f}%)")
        print(f"   Transações: {product['transactions']} | Clientes Únicos: {product['unique_customers']}")
        print(f"   Taxa de Giro: {product['turnover_rate']:.1f}% | Estoque Atual: {product['current_stock']}")


def print_clv_analysis(clv_data: List[Dict]):
    """
    Print customer lifetime value analysis.
    
    Args:
        clv_data: CLV data
    """
    print("\n" + "="*70)
    print("  LIFETIME VALUE (CLV) - TOP CLIENTES")
    print("="*70)
    
    print("\n💎 Clientes com Maior Valor Vitalício:")
    
    for i, customer in enumerate(clv_data, 1):
        print(f"\n{i}. {customer['cliente']} ({customer['tipo'].capitalize()})")
        print(f"   Total Gasto (histórico): R$ {customer['total_spent']:.2f}")
        print(f"   Ticket Médio: R$ {customer['avg_purchase']:.2f}")
        print(f"   Frequência: {customer['purchase_frequency_monthly']:.1f} compras/mês")
        print(f"   CLV Projetado (12 meses): R$ {customer['projected_clv_12mo']:.2f}")
        print(f"   💰 CLV Total Estimado: R$ {customer['total_clv']:.2f}")


def print_payment_analysis(payment_data: Dict):
    """
    Print payment method analysis.
    
    Args:
        payment_data: Payment method data
    """
    print("\n" + "="*70)
    print("  ANÁLISE POR MEIO DE PAGAMENTO")
    print("="*70)
    
    methods = payment_data['payment_methods']
    
    # Create bar chart data
    chart_data = [(m['payment_method'], m['revenue']) for m in methods]
    print_bar_chart(chart_data, "\nReceita por Meio de Pagamento", max_width=40)
    
    print(f"\n📊 Detalhes:")
    for method in methods:
        print(f"\n{method['payment_method']}:")
        print(f"  Transações: {method['transaction_count']} ({method['revenue_share']:.1f}%)")
        print(f"  Receita: R$ {method['revenue']:.2f}")
        print(f"  Ticket Médio: R$ {method['avg_ticket']:.2f}")