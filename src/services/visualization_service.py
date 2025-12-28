"""
Visualization service for generating charts and graphs.

This module provides functions to create visual charts using matplotlib
for sales trends, product performance, and other analytics.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from typing import List, Dict, Optional
import os


class VisualizationService:
    """Service for creating visual charts and graphs."""
    
    def __init__(self, output_dir: str = 'reports'):
        """
        Initialize visualization service.
        
        Args:
            output_dir: Directory to save generated charts
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Configure matplotlib for better-looking charts
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.rcParams['figure.figsize'] = (12, 6)
        plt.rcParams['font.size'] = 10
    
    def plot_sales_trend(self, trend_data: Dict, save: bool = True) -> str:
        """
        Create sales trend line chart.
        
        Args:
            trend_data: Sales trend data from analytics service
            save: Whether to save the chart
            
        Returns:
            Path to saved chart file
        """
        daily_data = trend_data['daily_data']
        
        if not daily_data:
            return None
        
        # Prepare data
        dates = [datetime.strptime(d['date'], '%d/%m/%Y') for d in daily_data]
        revenues = [d['revenue'] for d in daily_data]
        sales_counts = [d['sales_count'] for d in daily_data]
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Plot 1: Revenue trend
        ax1.plot(dates, revenues, marker='o', linewidth=2, color='#2ecc71', label='Receita')
        ax1.fill_between(dates, revenues, alpha=0.3, color='#2ecc71')
        ax1.set_title(f'Tendência de Receita - {trend_data["period"]}', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Data', fontsize=12)
        ax1.set_ylabel('Receita (R$)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=10)
        
        # Format y-axis as currency
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x:,.0f}'))
        
        # Format x-axis dates
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Plot 2: Sales count
        ax2.bar(dates, sales_counts, color='#3498db', alpha=0.7, label='Número de Vendas')
        ax2.set_title('Número de Vendas por Dia', fontsize=16, fontweight='bold')
        ax2.set_xlabel('Data', fontsize=12)
        ax2.set_ylabel('Quantidade de Vendas', fontsize=12)
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.legend(fontsize=10)
        
        # Format x-axis dates
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        ax2.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Save or show
        if save:
            filename = f'tendencia_vendas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            return filepath
        else:
            plt.show()
            return None
    
    def plot_category_distribution(self, category_data: Dict, save: bool = True) -> str:
        """
        Create category distribution pie chart.
        
        Args:
            category_data: Category analysis data
            save: Whether to save the chart
            
        Returns:
            Path to saved chart file
        """
        categories = category_data['categories']
        
        if not categories:
            return None
        
        # Prepare data
        labels = [c['category'] for c in categories]
        revenues = [c['revenue'] for c in categories]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create pie chart
        colors = plt.cm.Set3(range(len(labels)))
        wedges, texts, autotexts = ax.pie(
            revenues,
            labels=labels,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            textprops={'fontsize': 11}
        )
        
        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(12)
        
        ax.set_title('Distribuição de Receita por Categoria', fontsize=16, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        # Save or show
        if save:
            filename = f'distribuicao_categorias_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            return filepath
        else:
            plt.show()
            return None
    
    def plot_top_products(self, products: List[Dict], top_n: int = 10, save: bool = True) -> str:
        """
        Create top products bar chart.
        
        Args:
            products: Product performance data
            top_n: Number of products to show
            save: Whether to save the chart
            
        Returns:
            Path to saved chart file
        """
        if not products:
            return None
        
        # Get top N products
        top_products = products[:top_n]
        
        # Prepare data
        product_names = [p['produto'][:20] for p in top_products]  # Truncate long names
        revenues = [p['revenue'] for p in top_products]
        profits = [p['profit'] for p in top_products]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Create horizontal bar chart
        y_pos = range(len(product_names))
        
        bars1 = ax.barh([i - 0.2 for i in y_pos], revenues, 0.4, 
                        label='Receita', color='#3498db', alpha=0.8)
        bars2 = ax.barh([i + 0.2 for i in y_pos], profits, 0.4,
                        label='Lucro', color='#2ecc71', alpha=0.8)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(product_names)
        ax.invert_yaxis()  # Top product at top
        ax.set_xlabel('Valor (R$)', fontsize=12)
        ax.set_title(f'Top {top_n} Produtos - Receita e Lucro', fontsize=16, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3, axis='x')
        
        # Format x-axis as currency
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x:,.0f}'))
        
        plt.tight_layout()
        
        # Save or show
        if save:
            filename = f'top_produtos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            return filepath
        else:
            plt.show()
            return None
    
    def plot_customer_segments(self, segments: Dict, save: bool = True) -> str:
        """
        Create customer segmentation visualization.
        
        Args:
            segments: Customer segmentation data
            save: Whether to save the chart
            
        Returns:
            Path to saved chart file
        """
        summary = segments['summary']
        
        # Prepare data
        segment_names = ['VIP', 'Regular', 'Ocasional', 'Inativo']
        counts = [
            summary['vip_count'],
            summary['regular_count'],
            summary['occasional_count'],
            summary['inactive_count']
        ]
        revenues = [
            summary.get('vip_revenue', 0),
            summary.get('regular_revenue', 0),
            0,  # Occasional doesn't have revenue in summary
            0   # Inactive doesn't have revenue in summary
        ]
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Plot 1: Customer count by segment
        colors = ['#f39c12', '#2ecc71', '#3498db', '#95a5a6']
        bars = ax1.bar(segment_names, counts, color=colors, alpha=0.8)
        ax1.set_title('Distribuição de Clientes por Segmento', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Número de Clientes', fontsize=12)
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # Plot 2: Revenue by segment (only VIP and Regular)
        segment_names_rev = ['VIP', 'Regular']
        revenues_filtered = [revenues[0], revenues[1]]
        
        bars2 = ax2.bar(segment_names_rev, revenues_filtered, 
                       color=[colors[0], colors[1]], alpha=0.8)
        ax2.set_title('Receita por Segmento', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Receita (R$)', fontsize=12)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x:,.0f}'))
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'R$ {height:,.0f}',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        plt.tight_layout()
        
        # Save or show
        if save:
            filename = f'segmentacao_clientes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            return filepath
        else:
            plt.show()
            return None
    
    def plot_payment_methods(self, payment_data: Dict, save: bool = True) -> str:
        """
        Create payment methods analysis chart.
        
        Args:
            payment_data: Payment method data
            save: Whether to save the chart
            
        Returns:
            Path to saved chart file
        """
        methods = payment_data['payment_methods']
        
        if not methods:
            return None
        
        # Prepare data
        method_names = [m['payment_method'] for m in methods]
        revenues = [m['revenue'] for m in methods]
        counts = [m['transaction_count'] for m in methods]
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Plot 1: Revenue by payment method (pie chart)
        colors = plt.cm.Pastel1(range(len(method_names)))
        wedges, texts, autotexts = ax1.pie(
            revenues,
            labels=method_names,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            textprops={'fontsize': 11}
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax1.set_title('Distribuição de Receita por Meio de Pagamento', 
                     fontsize=14, fontweight='bold')
        
        # Plot 2: Transaction count (bar chart)
        bars = ax2.bar(method_names, counts, color=colors, alpha=0.8)
        ax2.set_title('Número de Transações por Meio de Pagamento',
                     fontsize=14, fontweight='bold')
        ax2.set_ylabel('Número de Transações', fontsize=12)
        ax2.grid(True, alpha=0.3, axis='y')
        
        # Rotate x-axis labels if needed
        if len(method_names) > 3:
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        plt.tight_layout()
        
        # Save or show
        if save:
            filename = f'meios_pagamento_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            return filepath
        else:
            plt.show()
            return None
    
    def plot_abc_analysis(self, abc_data: Dict, save: bool = True) -> str:
        """
        Create ABC analysis Pareto chart.
        
        Args:
            abc_data: ABC analysis data
            save: Whether to save the chart
            
        Returns:
            Path to saved chart file
        """
        all_products = abc_data['all_products']
        
        if not all_products:
            return None
        
        # Prepare data (already sorted by revenue)
        product_names = [p['produto'][:15] for p in all_products[:20]]  # Top 20
        revenues = [p['revenue'] for p in all_products[:20]]
        
        # Calculate cumulative percentage
        total_revenue = sum([p['revenue'] for p in all_products])
        cumulative_pct = []
        cumsum = 0
        for revenue in revenues:
            cumsum += revenue
            cumulative_pct.append((cumsum / total_revenue) * 100)
        
        # Create figure
        fig, ax1 = plt.subplots(figsize=(16, 8))
        
        # Bar chart for revenue
        color = '#3498db'
        ax1.bar(range(len(product_names)), revenues, color=color, alpha=0.7, label='Receita')
        ax1.set_xlabel('Produtos', fontsize=12)
        ax1.set_ylabel('Receita (R$)', fontsize=12, color=color)
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.set_xticks(range(len(product_names)))
        ax1.set_xticklabels(product_names, rotation=45, ha='right')
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x:,.0f}'))
        
        # Line chart for cumulative percentage
        ax2 = ax1.twinx()
        color = '#e74c3c'
        ax2.plot(range(len(product_names)), cumulative_pct, color=color, marker='o', 
                linewidth=2, markersize=6, label='% Acumulado')
        ax2.set_ylabel('Porcentagem Acumulada (%)', fontsize=12, color=color)
        ax2.tick_params(axis='y', labelcolor=color)
        ax2.set_ylim([0, 105])
        
        # Add 80% reference line
        ax2.axhline(y=80, color='green', linestyle='--', linewidth=2, alpha=0.7, label='80% (Classe A)')
        ax2.axhline(y=95, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='95% (Classe B)')
        
        # Title and legends
        ax1.set_title('Análise ABC - Curva de Pareto', fontsize=16, fontweight='bold', pad=20)
        
        # Combine legends
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
        
        ax1.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        # Save or show
        if save:
            filename = f'analise_abc_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            return filepath
        else:
            plt.show()
            return None
    
    def plot_profitability_overview(self, profitability: Dict, save: bool = True) -> str:
        """
        Create profitability overview chart.
        
        Args:
            profitability: Profitability report data
            save: Whether to save the chart
            
        Returns:
            Path to saved chart file
        """
        # Prepare data
        categories = ['Receita\nTotal', 'Custo\nTotal', 'Lucro\nBruto']
        values = [
            profitability['total_revenue'],
            profitability['total_cost'],
            profitability['gross_profit']
        ]
        colors = ['#3498db', '#e74c3c', '#2ecc71']
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Plot 1: Revenue, Cost, Profit bars
        bars = ax1.bar(categories, values, color=colors, alpha=0.8, width=0.6)
        ax1.set_title('Visão Geral de Lucratividade', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Valor (R$)', fontsize=12)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'R$ {x:,.0f}'))
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'R$ {height:,.0f}',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # Plot 2: Margin pie chart
        margin_data = [
            profitability['gross_profit'],
            profitability['total_cost']
        ]
        margin_labels = [
            f"Lucro\n({profitability['profit_margin_pct']:.1f}%)",
            f"Custo\n({100-profitability['profit_margin_pct']:.1f}%)"
        ]
        
        colors2 = ['#2ecc71', '#e74c3c']
        wedges, texts, autotexts = ax2.pie(
            margin_data,
            labels=margin_labels,
            autopct='R$ %1.0f',
            startangle=90,
            colors=colors2,
            textprops={'fontsize': 11}
        )
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax2.set_title('Composição da Receita', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # Save or show
        if save:
            filename = f'lucratividade_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            return filepath
        else:
            plt.show()
            return None