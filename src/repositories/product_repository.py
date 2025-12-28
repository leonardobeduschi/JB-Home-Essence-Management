"""
Product repository for CSV operations.

This module handles all CRUD operations for products in the CSV file.
"""

import pandas as pd
from typing import Optional, List, Dict
from src.repositories.base_repository import BaseRepository
from src.models.product import Product, PRODUCT_SCHEMA


class ProductRepository(BaseRepository):
    """
    Repository for product data persistence.
    
    Handles all CSV operations for products including create, read,
    update, and stock management.
    """
    
    def __init__(self, filepath: str = 'data/products.csv'):
        """
        Initialize the product repository.
        
        Args:
            filepath: Path to the products CSV file
        """
        super().__init__(filepath, PRODUCT_SCHEMA)
    
    def exists(self, codigo: str) -> bool:
        """
        Check if a product with given CODIGO exists.
        
        Args:
            codigo: Product code to check
            
        Returns:
            True if product exists, False otherwise
        """
        df = self._read_csv()
        return codigo.upper() in df['CODIGO'].str.upper().values
    
    def get_by_codigo(self, codigo: str) -> Optional[Dict]:
        """
        Retrieve a product by its code.
        
        Args:
            codigo: Product code to search for
            
        Returns:
            Dictionary with product data if found, None otherwise
        """
        df = self._read_csv()
        
        # Case-insensitive search
        mask = df['CODIGO'].str.upper() == codigo.upper()
        result = df[mask]
        
        if result.empty:
            return None
        
        return result.iloc[0].to_dict()
    
    def save(self, product: Product) -> bool:
        """
        Save a new product to the CSV.
        
        Args:
            product: Product instance to save
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If product with same CODIGO already exists
        """
        # Check for duplicate CODIGO
        if self.exists(product.codigo):
            raise ValueError(f"Produto com código '{product.codigo}' já existe")
        
        try:
            df = self._read_csv()
            
            # Convert product to dict and append
            new_row = pd.DataFrame([product.to_dict()])
            df = pd.concat([df, new_row], ignore_index=True)
            
            # Save to CSV
            self._write_csv(df)
            return True
            
        except Exception as e:
            raise Exception(f"Erro ao salvar produto: {str(e)}")
    
    def update(self, codigo: str, updates: Dict) -> bool:
        """
        Update an existing product's information.
        
        Args:
            codigo: Product code to update
            updates: Dictionary with fields to update
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If product not found or validation fails
        """
        if not self.exists(codigo):
            raise ValueError(f"Produto com código '{codigo}' não encontrado")
        
        try:
            df = self._read_csv()
            
            # Find the product row
            mask = df['CODIGO'].str.upper() == codigo.upper()
            idx = df[mask].index[0]
            
            # Apply updates (only allowed fields)
            allowed_fields = ['PRODUTO', 'CATEGORIA', 'CUSTO', 'VALOR', 'ESTOQUE']
            for field, value in updates.items():
                if field in allowed_fields:
                    # Validate based on field type
                    if field == 'CUSTO':
                        value = float(value)
                        if value <= 0:
                            raise ValueError("CUSTO deve ser maior que zero")
                        df.at[idx, field] = f"{value:.2f}"
                    elif field == 'VALOR':
                        value = float(value)
                        if value <= 0:
                            raise ValueError("VALOR (preço de venda) deve ser maior que zero")
                        df.at[idx, field] = f"{value:.2f}"
                    elif field == 'ESTOQUE':
                        value = int(value)
                        if value < 0:
                            raise ValueError("ESTOQUE não pode ser negativo")
                        df.at[idx, field] = str(value)
                    else:
                        if not value or not str(value).strip():
                            raise ValueError(f"{field} não pode ser vazio")
                        df.at[idx, field] = str(value).strip()
            
            # Save to CSV
            self._write_csv(df)
            return True
            
        except Exception as e:
            raise Exception(f"Erro ao atualizar produto: {str(e)}")
    
    def update_stock(self, codigo: str, quantity_change: int) -> bool:
        """
        Update product stock by adding or subtracting quantity.
        
        This is the method used when sales are registered.
        
        Args:
            codigo: Product code
            quantity_change: Amount to add (positive) or subtract (negative)
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If product not found or insufficient stock
        """
        product = self.get_by_codigo(codigo)
        if not product:
            raise ValueError(f"Produto com código '{codigo}' não encontrado")
        
        try:
            current_stock = int(product['ESTOQUE'])
            new_stock = current_stock + quantity_change
            
            if new_stock < 0:
                raise ValueError(
                    f"Estoque insuficiente. Disponível: {current_stock} unidades"
                )
            
            # Update the stock
            return self.update(codigo, {'ESTOQUE': new_stock})
            
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Erro ao atualizar estoque: {str(e)}")
    
    def get_by_category(self, categoria: str) -> List[Dict]:
        """
        Get all products in a specific category.
        
        Args:
            categoria: Category name
            
        Returns:
            List of product dictionaries
        """
        df = self._read_csv()
        
        # Case-insensitive search
        mask = df['CATEGORIA'].str.upper() == categoria.upper()
        result = df[mask]
        
        return result.to_dict('records')
    
    def get_low_stock(self, threshold: int = 5) -> List[Dict]:
        """
        Get products with stock below a threshold.
        
        Args:
            threshold: Stock level threshold
            
        Returns:
            List of products with low stock
        """
        df = self._read_csv()
        
        # Convert ESTOQUE to int for comparison
        df['ESTOQUE_INT'] = df['ESTOQUE'].astype(int)
        result = df[df['ESTOQUE_INT'] <= threshold]
        
        # Drop the temporary column
        result = result.drop('ESTOQUE_INT', axis=1)
        
        return result.to_dict('records')
    
    def get_inventory_value(self) -> Dict[str, float]:
        """
        Calculate total inventory value at cost and retail prices.
        
        Returns:
            Dictionary with 'cost_value' and 'retail_value'
        """
        df = self._read_csv()
        
        if df.empty:
            return {'cost_value': 0.0, 'retail_value': 0.0}
        
        # Convert to numeric
        df['CUSTO_NUM'] = pd.to_numeric(df['CUSTO'], errors='coerce').fillna(0)
        df['VALOR_NUM'] = pd.to_numeric(df['VALOR'], errors='coerce').fillna(0)
        df['ESTOQUE_NUM'] = pd.to_numeric(df['ESTOQUE'], errors='coerce').fillna(0)
        
        # Calculate values
        cost_value = (df['CUSTO_NUM'] * df['ESTOQUE_NUM']).sum()
        retail_value = (df['VALOR_NUM'] * df['ESTOQUE_NUM']).sum()
        
        return {
            'cost_value': float(cost_value),
            'retail_value': float(retail_value)
        }
    
    def delete(self, codigo: str) -> bool:
        """
        Delete a product from the CSV.
        
        Args:
            codigo: Product code to delete
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If product not found
        """
        if not self.exists(codigo):
            raise ValueError(f"Produto com código '{codigo}' não encontrado")
        
        try:
            df = self._read_csv()
            
            # Remove the product
            mask = df['CODIGO'].str.upper() != codigo.upper()
            df = df[mask]
            
            # Save to CSV
            self._write_csv(df)
            return True
            
        except Exception as e:
            raise Exception(f"Erro ao deletar produto: {str(e)}")