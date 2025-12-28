"""
Export service for generating reports in various formats.

This module provides functions to export analytics and reports
to PDF, Excel, and CSV formats.
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List
import os


class ExportService:
    """Service for exporting reports to various formats."""
    
    def __init__(self, output_dir: str = 'reports'):
        """
        Initialize export service.
        
        Args:
            output_dir: Directory to save exported files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def export_sales_to_excel(self, sales_data: List[Dict], filename: str = None) -> str:
        """
        Export sales data to Excel file.
        
        Args:
            sales_data: List of sales dictionaries
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to exported file
        """
        if not filename:
            filename = f'vendas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Create DataFrame
        df = pd.DataFrame(sales_data)
        
        # Create Excel writer
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Write sales data
            df.to_excel(writer, sheet_name='Vendas', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Vendas']
            for column in df:
                column_length = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = column_length + 2
        
        return filepath
    
    def export_products_to_excel(self, products_data: List[Dict], filename: str = None) -> str:
        """
        Export products data to Excel file.
        
        Args:
            products_data: List of product dictionaries
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to exported file
        """
        if not filename:
            filename = f'produtos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Create DataFrame
        df = pd.DataFrame(products_data)
        
        # Convert numeric columns
        if 'CUSTO' in df.columns:
            df['CUSTO'] = pd.to_numeric(df['CUSTO'], errors='coerce')
        if 'VALOR' in df.columns:
            df['VALOR'] = pd.to_numeric(df['VALOR'], errors='coerce')
        if 'ESTOQUE' in df.columns:
            df['ESTOQUE'] = pd.to_numeric(df['ESTOQUE'], errors='coerce')
        
        # Calculate additional columns
        if 'CUSTO' in df.columns and 'VALOR' in df.columns:
            df['MARGEM'] = ((df['VALOR'] - df['CUSTO']) / df['CUSTO'] * 100).round(2)
            df['VALOR_ESTOQUE_CUSTO'] = (df['CUSTO'] * df['ESTOQUE']).round(2)
            df['VALOR_ESTOQUE_VENDA'] = (df['VALOR'] * df['ESTOQUE']).round(2)
        
        # Export to Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Produtos', index=False)
            
            worksheet = writer.sheets['Produtos']
            for column in df:
                column_length = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_length + 2, 50)
        
        return filepath
    
    def export_analytics_to_excel(self, analytics_data: Dict, filename: str = None) -> str:
        """
        Export comprehensive analytics report to Excel.
        
        Args:
            analytics_data: Dictionary with various analytics
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to exported file
        """
        if not filename:
            filename = f'relatorio_analytics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        filepath = os.path.join(self.output_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            
            # Sheet 1: Summary
            if 'summary' in analytics_data:
                summary_df = pd.DataFrame([analytics_data['summary']])
                summary_df.to_excel(writer, sheet_name='Resumo', index=False)
            
            # Sheet 2: Top Products
            if 'top_products' in analytics_data:
                products_df = pd.DataFrame(analytics_data['top_products'])
                products_df.to_excel(writer, sheet_name='Top Produtos', index=False)
            
            # Sheet 3: Top Clients
            if 'top_clients' in analytics_data:
                clients_df = pd.DataFrame(analytics_data['top_clients'])
                clients_df.to_excel(writer, sheet_name='Top Clientes', index=False)
            
            # Sheet 4: Category Performance
            if 'categories' in analytics_data:
                category_df = pd.DataFrame(analytics_data['categories'])
                category_df.to_excel(writer, sheet_name='Categorias', index=False)
            
            # Sheet 5: Payment Methods
            if 'payment_methods' in analytics_data:
                payment_df = pd.DataFrame(analytics_data['payment_methods'])
                payment_df.to_excel(writer, sheet_name='Meios Pagamento', index=False)
            
            # Auto-adjust all worksheets
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return filepath
    
    def export_to_csv(self, data: List[Dict], filename: str, sheet_name: str = None) -> str:
        """
        Export data to CSV file.
        
        Args:
            data: List of dictionaries
            filename: Output filename
            sheet_name: Not used for CSV (for compatibility)
            
        Returns:
            Path to exported file
        """
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Create DataFrame and export
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        return filepath
    
    def export_profitability_report(self, profitability: Dict, 
                                   product_performance: Dict,
                                   filename: str = None) -> str:
        """
        Export detailed profitability report to Excel.
        
        Args:
            profitability: Profitability data
            product_performance: Product performance data
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        if not filename:
            filename = f'relatorio_lucratividade_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        filepath = os.path.join(self.output_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            
            # Sheet 1: Overall Profitability
            summary_data = {
                'Métrica': [
                    'Receita Total',
                    'Custo Total',
                    'Lucro Bruto',
                    'Margem de Lucro (%)',
                    'Valor Estoque (Custo)',
                    'Valor Estoque (Varejo)',
                    'Lucro Potencial Estoque'
                ],
                'Valor': [
                    profitability['total_revenue'],
                    profitability['total_cost'],
                    profitability['gross_profit'],
                    profitability['profit_margin_pct'],
                    profitability['inventory_cost_value'],
                    profitability['inventory_retail_value'],
                    profitability['potential_profit_from_inventory']
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Resumo Geral', index=False)
            
            # Sheet 2: Product-level profitability
            if 'all_products' in product_performance:
                products_df = pd.DataFrame(product_performance['all_products'])
                products_df = products_df[[
                    'produto', 'codigo', 'categoria', 'revenue', 'profit',
                    'profit_margin', 'quantity_sold', 'current_stock'
                ]]
                products_df.columns = [
                    'Produto', 'Código', 'Categoria', 'Receita', 'Lucro',
                    'Margem (%)', 'Qtd Vendida', 'Estoque Atual'
                ]
                products_df.to_excel(writer, sheet_name='Lucro por Produto', index=False)
            
            # Auto-adjust columns
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return filepath
    
    def export_customer_report(self, segments: Dict, clv_data: List[Dict],
                              filename: str = None) -> str:
        """
        Export customer analysis report to Excel.
        
        Args:
            segments: Customer segmentation data
            clv_data: Customer lifetime value data
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        if not filename:
            filename = f'relatorio_clientes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        filepath = os.path.join(self.output_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            
            # Sheet 1: Segment Summary
            summary_data = {
                'Segmento': ['VIP', 'Regular', 'Ocasional', 'Inativo'],
                'Quantidade': [
                    segments['summary']['vip_count'],
                    segments['summary']['regular_count'],
                    segments['summary']['occasional_count'],
                    segments['summary']['inactive_count']
                ],
                'Receita': [
                    segments['summary'].get('vip_revenue', 0),
                    segments['summary'].get('regular_revenue', 0),
                    0,
                    0
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Resumo Segmentos', index=False)
            
            # Sheet 2: VIP Customers
            if segments['VIP']:
                vip_df = pd.DataFrame(segments['VIP'])
                vip_df.to_excel(writer, sheet_name='Clientes VIP', index=False)
            
            # Sheet 3: Customer Lifetime Value
            if clv_data:
                clv_df = pd.DataFrame(clv_data)
                clv_df.to_excel(writer, sheet_name='Lifetime Value', index=False)
            
            # Sheet 4: Inactive Customers
            if segments['Inactive']:
                inactive_df = pd.DataFrame(segments['Inactive'])
                inactive_df.to_excel(writer, sheet_name='Clientes Inativos', index=False)
            
            # Auto-adjust columns
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return filepath