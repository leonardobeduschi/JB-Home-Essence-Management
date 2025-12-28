"""
Sale repository for CSV operations.

This module handles all CRUD operations for sales in the CSV file.
"""

import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime
from src.repositories.base_repository import BaseRepository
from src.models.sale import Sale, SALE_SCHEMA


class SaleRepository(BaseRepository):
    """
    Repository for sale data persistence.
    
    Handles all CSV operations for sales including create, read,
    and various query operations.
    """
    
    def __init__(self, filepath: str = 'data/sales.csv'):
        """
        Initialize the sale repository.
        
        Args:
            filepath: Path to the sales CSV file
        """
        super().__init__(filepath, SALE_SCHEMA)
    
    def exists(self, id_venda: str) -> bool:
        """
        Check if a sale with given ID_VENDA exists.
        
        Args:
            id_venda: Sale ID to check
            
        Returns:
            True if sale exists, False otherwise
        """
        df = self._read_csv()
        return id_venda.upper() in df['ID_VENDA'].str.upper().values
    
    def get_by_id(self, id_venda: str) -> Optional[Dict]:
        """
        Retrieve a sale by its ID.
        
        Args:
            id_venda: Sale ID to search for
            
        Returns:
            Dictionary with sale data if found, None otherwise
        """
        df = self._read_csv()
        
        # Case-insensitive search
        mask = df['ID_VENDA'].str.upper() == id_venda.upper()
        result = df[mask]
        
        if result.empty:
            return None
        
        return result.iloc[0].to_dict()
    
    def save(self, sale: Sale) -> bool:
        """
        Save a new sale to the CSV.
        
        Args:
            sale: Sale instance to save
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If sale with same ID_VENDA already exists
        """
        # Check for duplicate ID_VENDA
        if self.exists(sale.id_venda):
            raise ValueError(f"Venda com ID '{sale.id_venda}' já existe")
        
        try:
            df = self._read_csv()
            
            # Convert sale to dict and append
            new_row = pd.DataFrame([sale.to_dict()])
            df = pd.concat([df, new_row], ignore_index=True)
            
            # Save to CSV
            self._write_csv(df)
            return True
            
        except Exception as e:
            raise Exception(f"Erro ao salvar venda: {str(e)}")
    
    def get_by_client(self, id_cliente: str) -> List[Dict]:
        """
        Get all sales for a specific client.
        
        Args:
            id_cliente: Client ID
            
        Returns:
            List of sales
        """
        df = self._read_csv()
        
        # Case-insensitive search
        mask = df['ID_CLIENTE'].str.upper() == id_cliente.upper()
        result = df[mask]
        
        return result.to_dict('records')
    
    def get_by_product(self, codigo: str) -> List[Dict]:
        """
        Get all sales for a specific product.
        
        Args:
            codigo: Product code
            
        Returns:
            List of sales
        """
        df = self._read_csv()
        
        # Case-insensitive search
        mask = df['CODIGO'].str.upper() == codigo.upper()
        result = df[mask]
        
        return result.to_dict('records')
    
    def get_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Get sales within a date range.
        
        Args:
            start_date: Start date (DD/MM/YYYY)
            end_date: End date (DD/MM/YYYY)
            
        Returns:
            List of sales in date range
        """
        df = self._read_csv()
        
        if df.empty:
            return []
        
        # Convert DATA column to datetime
        df['DATA_DT'] = pd.to_datetime(df['DATA'], format='%d/%m/%Y', errors='coerce')
        start_dt = datetime.strptime(start_date, '%d/%m/%Y')
        end_dt = datetime.strptime(end_date, '%d/%m/%Y')
        
        # Filter by date range
        mask = (df['DATA_DT'] >= start_dt) & (df['DATA_DT'] <= end_dt)
        result = df[mask].drop('DATA_DT', axis=1)
        
        return result.to_dict('records')
    
    def get_by_payment_method(self, meio: str) -> List[Dict]:
        """
        Get all sales by payment method.
        
        Args:
            meio: Payment method
            
        Returns:
            List of sales
        """
        df = self._read_csv()
        
        # Case-insensitive search
        mask = df['MEIO'].str.lower() == meio.lower()
        result = df[mask]
        
        return result.to_dict('records')
    
    def get_sales_summary(self) -> Dict:
        """
        Get comprehensive sales summary.
        
        Returns:
            Dictionary with sales statistics
        """
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
        
        # Convert numeric columns
        df['PRECO_TOTAL_NUM'] = pd.to_numeric(df['PRECO_TOTAL'], errors='coerce').fillna(0)
        df['QUANTIDADE_NUM'] = pd.to_numeric(df['QUANTIDADE'], errors='coerce').fillna(0)

        # Normalize text columns to avoid case differences (e.g., 'garbo' vs 'GARBO')
        df['CATEGORIA_NORM'] = df['CATEGORIA'].fillna('').astype(str).str.strip().str.title()
        df['MEIO_NORM'] = df['MEIO'].fillna('').astype(str).str.strip().str.title()
        df['PRODUTO_NORM'] = df['PRODUTO'].fillna('').astype(str).str.strip().str.title()
        
        summary = {
            'total_sales': len(df),
            'total_revenue': float(df['PRECO_TOTAL_NUM'].sum()),
            'total_items_sold': int(df['QUANTIDADE_NUM'].sum()),
            'average_sale_value': float(df['PRECO_TOTAL_NUM'].mean()),
            'by_payment_method': df.groupby('MEIO_NORM')['PRECO_TOTAL_NUM'].sum().to_dict(),
            'by_category': df.groupby('CATEGORIA_NORM')['PRECO_TOTAL_NUM'].sum().to_dict()
        }
        
        return summary
    
    def get_top_products(self, limit: int = 10) -> List[Dict]:
        """
        Get top-selling products by quantity.
        
        Args:
            limit: Maximum number of products to return
            
        Returns:
            List of products with total quantity sold
        """
        df = self._read_csv()
        
        if df.empty:
            return []
        
        # Convert quantity to numeric
        df['QUANTIDADE_NUM'] = pd.to_numeric(df['QUANTIDADE'], errors='coerce').fillna(0)

        # Normalize product names to avoid case differences
        df['PRODUTO_NORM'] = df['PRODUTO'].fillna('').astype(str).str.strip().str.title()

        # Group by product and sum quantities
        top = df.groupby(['CODIGO', 'PRODUTO_NORM']).agg({
            'QUANTIDADE_NUM': 'sum',
            'PRECO_TOTAL': lambda x: pd.to_numeric(x, errors='coerce').sum()
        }).reset_index()

        top.columns = ['CODIGO', 'PRODUTO', 'QUANTIDADE_TOTAL', 'RECEITA_TOTAL']
        top = top.sort_values('QUANTIDADE_TOTAL', ascending=False).head(limit)

        return top.to_dict('records')
    
    def get_top_clients(self, limit: int = 10) -> List[Dict]:
        """
        Get top clients by revenue.
        
        Args:
            limit: Maximum number of clients to return
            
        Returns:
            List of clients with total purchases
        """
        df = self._read_csv()
        
        if df.empty:
            return []
        
        # Convert to numeric
        df['PRECO_TOTAL_NUM'] = pd.to_numeric(df['PRECO_TOTAL'], errors='coerce').fillna(0)
        
        # Group by client
        top = df.groupby(['ID_CLIENTE', 'CLIENTE']).agg({
            'ID_VENDA': 'count',
            'PRECO_TOTAL_NUM': 'sum'
        }).reset_index()
        
        top.columns = ['ID_CLIENTE', 'CLIENTE', 'NUM_COMPRAS', 'TOTAL_GASTO']
        top = top.sort_values('TOTAL_GASTO', ascending=False).head(limit)
        
        return top.to_dict('records')
    
    def delete(self, id_venda: str) -> bool:
        """
        Delete a sale from the CSV.
        
        Note: This does NOT restore inventory. Use with caution.
        
        Args:
            id_venda: Sale ID to delete
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If sale not found
        """
        if not self.exists(id_venda):
            raise ValueError(f"Venda com ID '{id_venda}' não encontrada")
        
        try:
            df = self._read_csv()
            
            # Remove the sale
            mask = df['ID_VENDA'].str.upper() != id_venda.upper()
            df = df[mask]
            
            # Save to CSV
            self._write_csv(df)
            return True
            
        except Exception as e:
            raise Exception(f"Erro ao deletar venda: {str(e)}")
        
    # Adicione estes métodos ao final da classe SaleRepository em sale_repository.py:

    def get_by_sale_id(self, id_venda: str) -> List[Dict]:
        """
        Get ALL items from a sale (for multi-item sales).
        
        Args:
            id_venda: Sale ID
            
        Returns:
            List of all items with this ID_VENDA
        """
        df = self._read_csv()
        
        # Case-insensitive search
        mask = df['ID_VENDA'].str.upper() == id_venda.upper()
        result = df[mask]
        
        return result.to_dict('records')

    def delete_by_sale_id(self, id_venda: str) -> bool:
        """
        Delete ALL items from a sale (for multi-item sales).
        
        Args:
            id_venda: Sale ID to delete
            
        Returns:
            True if successful
            
        Raises:
                ValueError: If sale not found
        """
        if not self.exists(id_venda):
            raise ValueError(f"Venda com ID '{id_venda}' não encontrada")
        
        try:
            df = self._read_csv()
            
            # Remove ALL rows with this ID_VENDA
            mask = df['ID_VENDA'].str.upper() != id_venda.upper()
            df = df[mask]
            
            # Save to CSV
            self._write_csv(df)
            return True
            
        except Exception as e:
            raise Exception(f"Erro ao deletar venda: {str(e)}")