"""
Sale repository for CSV operations - FIXED for new structure.
"""

import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime
from src.repositories.base_repository import BaseRepository
from src.models.sale import Sale, SALE_SCHEMA


class SaleRepository(BaseRepository):
    """Repository for sale data persistence."""
    
    def __init__(self, filepath: str = 'data/sales.csv'):
        super().__init__(filepath, SALE_SCHEMA)
    
    def exists(self, id_venda: str) -> bool:
        df = self._read_csv()
        return id_venda.upper() in df['ID_VENDA'].str.upper().values
    
    def get_by_id(self, id_venda: str) -> Optional[Dict]:
        df = self._read_csv()
        mask = df['ID_VENDA'].str.upper() == id_venda.upper()
        result = df[mask]
        
        if result.empty:
            return None
        
        return result.iloc[0].to_dict()
    
    def save(self, sale: Sale) -> bool:
        if self.exists(sale.id_venda):
            raise ValueError(f"Venda com ID '{sale.id_venda}' já existe")
        
        try:
            df = self._read_csv()
            new_row = pd.DataFrame([sale.to_dict()])
            df = pd.concat([df, new_row], ignore_index=True)
            self._write_csv(df)
            return True
        except Exception as e:
            raise Exception(f"Erro ao salvar venda: {str(e)}")
    
    def get_by_client(self, id_cliente: str) -> List[Dict]:
        df = self._read_csv()
        mask = df['ID_CLIENTE'].str.upper() == id_cliente.upper()
        result = df[mask]
        return result.to_dict('records')
    
    def get_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        df = self._read_csv()
        
        if df.empty:
            return []
        
        df['DATA_DT'] = pd.to_datetime(df['DATA'], format='%d/%m/%Y', errors='coerce')
        start_dt = datetime.strptime(start_date, '%d/%m/%Y')
        end_dt = datetime.strptime(end_date, '%d/%m/%Y')
        
        mask = (df['DATA_DT'] >= start_dt) & (df['DATA_DT'] <= end_dt)
        result = df[mask].drop('DATA_DT', axis=1)
        
        return result.to_dict('records')
    
    def get_by_payment_method(self, meio: str) -> List[Dict]:
        df = self._read_csv()
        mask = df['MEIO'].str.lower() == meio.lower()
        result = df[mask]
        return result.to_dict('records')
    
    def get_sales_summary(self) -> Dict:
        """Get comprehensive sales summary - FIXED for new structure."""
        from src.repositories.sale_item_repository import SaleItemRepository
        
        df = self._read_csv()
        
        if df.empty:
            return {
                'total_sales': 0,
                'total_revenue': 0.0,
                'total_items_sold': 0,
                'average_sale_value': 0.0,
                'by_payment_method': {},
                'by_category': {}
            }
        
        # Convert columns
        df['VALOR_TOTAL_VENDA'] = pd.to_numeric(df['VALOR_TOTAL_VENDA'], errors='coerce').fillna(0)
        df['MEIO_NORM'] = df['MEIO'].fillna('').astype(str).str.strip().str.title()
        
        # Get items data for total_items_sold and by_category
        item_repo = SaleItemRepository()
        items_df = item_repo._read_csv()
        
        total_items = 0
        if not items_df.empty:
            items_df['QUANTIDADE'] = pd.to_numeric(items_df['QUANTIDADE'], errors='coerce').fillna(0)
            total_items = int(items_df['QUANTIDADE'].sum())
        
        # Get category stats
        category_stats = item_repo.get_category_stats()
        by_category = {}
        if not category_stats.empty:
            by_category = category_stats.set_index('CATEGORIA')['RECEITA'].to_dict()
        
        summary = {
            'total_sales': len(df),
            'total_revenue': float(df['VALOR_TOTAL_VENDA'].sum()),
            'total_items_sold': total_items,
            'average_sale_value': float(df['VALOR_TOTAL_VENDA'].mean()),
            'by_payment_method': df.groupby('MEIO_NORM')['VALOR_TOTAL_VENDA'].sum().to_dict(),
            'by_category': by_category
        }
        
        return summary
    
    def get_top_clients(self, limit: int = 10) -> List[Dict]:
        df = self._read_csv()
        
        if df.empty:
            return []
        
        df['VALOR_TOTAL_VENDA'] = pd.to_numeric(df['VALOR_TOTAL_VENDA'], errors='coerce').fillna(0)
        
        top = df.groupby(['ID_CLIENTE', 'CLIENTE']).agg({
            'ID_VENDA': 'count',
            'VALOR_TOTAL_VENDA': 'sum'
        }).reset_index()
        
        top.columns = ['ID_CLIENTE', 'CLIENTE', 'NUM_COMPRAS', 'TOTAL_GASTO']
        top = top.sort_values('TOTAL_GASTO', ascending=False).head(limit)
        
        return top.to_dict('records')
    
    def delete(self, id_venda: str) -> bool:
        if not self.exists(id_venda):
            raise ValueError(f"Venda com ID '{id_venda}' não encontrada")
        
        try:
            df = self._read_csv()
            mask = df['ID_VENDA'].str.upper() != id_venda.upper()
            df = df[mask]
            self._write_csv(df)
            return True
        except Exception as e:
            raise Exception(f"Erro ao deletar venda: {str(e)}")
    
    def get_sale_with_items(self, id_venda: str) -> Dict:
        """Get sale header + items (JOIN between sales and sales_items)."""
        from src.repositories.sale_item_repository import SaleItemRepository
        
        header = self.get_by_id(id_venda)
        if not header:
            return None
        
        item_repo = SaleItemRepository()
        items = item_repo.get_by_sale_id(id_venda)
        
        return {
            'header': header,
            'items': items
        }
    
    def get_recent_sales(self, limit: int = 10) -> List[Dict]:
        """Get recent sales with proper data from new structure."""
        from src.repositories.sale_item_repository import SaleItemRepository
        
        df = self._read_csv()
        
        if df.empty:
            return []
        
        # Sort by ID_VENDA (descending) to get most recent
        df = df.sort_values('ID_VENDA', ascending=False).head(limit)
        
        # Convert to list of dicts
        sales = df.to_dict('records')
        
        # Add VALOR_TOTAL_VENDA as VALOR_TOTAL_VENDA for compatibility
        for sale in sales:
            sale['VALOR_TOTAL_VENDA'] = sale.get('VALOR_TOTAL_VENDA', 0)
        
        return sales