"""
Sale Item repository - NOVO ARQUIVO.

Crie este arquivo em: src/repositories/sale_item_repository.py
"""

import pandas as pd
from typing import List, Dict
from src.repositories.base_repository import BaseRepository
from src.models.sale_item import SaleItem, SALE_ITEM_SCHEMA


class SaleItemRepository(BaseRepository):
    """
    Repository for sale items (produtos vendidos).
    
    Gerencia o arquivo sales_items.csv.
    """
    
    def __init__(self, filepath: str = 'data/sales_items.csv'):
        """Initialize repository."""
        super().__init__(filepath, SALE_ITEM_SCHEMA)
    
    def exists(self, item_id: str) -> bool:
        """
        Check if an item exists (não usado para items, mas necessário pela classe base).
        
        Args:
            item_id: Não relevante para items
            
        Returns:
            False (items não têm ID único, apenas ID_VENDA)
        """
        return False
    
    def save(self, item: SaleItem) -> bool:
        """
        Save a sale item.
        
        Args:
            item: SaleItem instance
            
        Returns:
            True if successful
        """
        try:
            df = self._read_csv()
            new_row = pd.DataFrame([item.to_dict()])
            df = pd.concat([df, new_row], ignore_index=True)
            self._write_csv(df)
            return True
        except Exception as e:
            raise Exception(f"Erro ao salvar item: {str(e)}")
    
    def save_many(self, items: List[SaleItem]) -> bool:
        """
        Save multiple items at once (mais eficiente).
        
        Args:
            items: List of SaleItem instances
            
        Returns:
            True if successful
        """
        try:
            df = self._read_csv()
            new_rows = pd.DataFrame([item.to_dict() for item in items])
            df = pd.concat([df, new_rows], ignore_index=True)
            self._write_csv(df)
            return True
        except Exception as e:
            raise Exception(f"Erro ao salvar itens: {str(e)}")
    
    def get_by_sale_id(self, id_venda: str) -> List[Dict]:
        """
        Get all items from a specific sale.
        
        Args:
            id_venda: Sale ID
            
        Returns:
            List of items
        """
        df = self._read_csv()
        mask = df['ID_VENDA'].str.upper() == str(id_venda).upper()
        result = df[mask]
        return result.to_dict('records')
    
    def get_by_product(self, codigo: str) -> List[Dict]:
        """
        Get all sales of a specific product.
        
        Args:
            codigo: Product code
            
        Returns:
            List of items
        """
        df = self._read_csv()
        mask = df['CODIGO'].str.upper() == str(codigo).upper()
        result = df[mask]
        return result.to_dict('records')
    
    def get_by_category(self, categoria: str) -> List[Dict]:
        """
        Get all items from a category.
        
        Args:
            categoria: Category name
            
        Returns:
            List of items
        """
        df = self._read_csv()
        mask = df['CATEGORIA'].str.upper() == str(categoria).upper()
        result = df[mask]
        return result.to_dict('records')
    
    def delete_by_sale_id(self, id_venda: str) -> bool:
        """
        Delete all items from a sale.
        
        Args:
            id_venda: Sale ID
            
        Returns:
            True if successful
        """
        try:
            df = self._read_csv()
            mask = df['ID_VENDA'].str.upper() != str(id_venda).upper()
            df = df[mask]
            self._write_csv(df)
            return True
        except Exception as e:
            raise Exception(f"Erro ao deletar itens: {str(e)}")
    
    def get_product_stats(self) -> pd.DataFrame:
        """
        Get statistics by product (para análises).
        
        Returns:
            DataFrame with product statistics
        """
        df = self._read_csv()
        
        if df.empty:
            return pd.DataFrame()
        
        # Convert to numeric
        df['QUANTIDADE'] = pd.to_numeric(df['QUANTIDADE'], errors='coerce').fillna(0)
        df['PRECO_TOTAL'] = pd.to_numeric(df['PRECO_TOTAL'], errors='coerce').fillna(0)
        
        # Group by product
        stats = df.groupby(['CODIGO', 'PRODUTO', 'CATEGORIA']).agg({
            'QUANTIDADE': 'sum',
            'PRECO_TOTAL': 'sum',
            'ID_VENDA': 'count'  # Número de vendas
        }).reset_index()
        
        stats.columns = ['CODIGO', 'PRODUTO', 'CATEGORIA', 'QTD_VENDIDA', 'RECEITA', 'NUM_VENDAS']
        stats = stats.sort_values('RECEITA', ascending=False)
        
        return stats
    
    def get_category_stats(self) -> pd.DataFrame:
        """
        Get statistics by category.
        
        Returns:
            DataFrame with category statistics
        """
        df = self._read_csv()
        
        if df.empty:
            return pd.DataFrame()
        
        df['QUANTIDADE'] = pd.to_numeric(df['QUANTIDADE'], errors='coerce').fillna(0)
        df['PRECO_TOTAL'] = pd.to_numeric(df['PRECO_TOTAL'], errors='coerce').fillna(0)
        
        stats = df.groupby('CATEGORIA').agg({
            'QUANTIDADE': 'sum',
            'PRECO_TOTAL': 'sum',
            'CODIGO': 'nunique'  # Produtos diferentes
        }).reset_index()
        
        stats.columns = ['CATEGORIA', 'QTD_VENDIDA', 'RECEITA', 'PRODUTOS_UNICOS']
        stats = stats.sort_values('RECEITA', ascending=False)
        
        return stats