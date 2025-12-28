"""
Product model and validation.

This module defines the Product entity structure and validation rules.
"""

from dataclasses import dataclass
from typing import Optional


# CSV Schema for products
PRODUCT_SCHEMA = [
    'CODIGO',
    'PRODUTO',
    'CATEGORIA',
    'CUSTO',
    'VALOR',
    'ESTOQUE'
]


@dataclass
class Product:
    """
    Product entity representing an item in the inventory.
    
    Attributes:
        codigo: Unique product code (e.g., 'PROD001')
        produto: Product name
        categoria: Product category
        custo: Unit cost (must be positive)
        valor: Unit selling price (must be positive)
        estoque: Stock quantity (cannot be negative)
    """
    codigo: str
    produto: str
    categoria: str
    custo: float
    valor: float
    estoque: int
    
    def __post_init__(self):
        """Validate product data after initialization."""
        self._validate()
    
    def _validate(self) -> None:
        """
        Validate product attributes.
        
        Raises:
            ValueError: If any validation rule fails
        """
        # Validate CODIGO
        if not self.codigo or not isinstance(self.codigo, str):
            raise ValueError("CODIGO é obrigatório e deve ser texto")
        
        if not self.codigo.strip():
            raise ValueError("CODIGO não pode ser vazio")
        
        # Validate PRODUTO
        if not self.produto or not isinstance(self.produto, str):
            raise ValueError("PRODUTO é obrigatório e deve ser texto")
        
        if not self.produto.strip():
            raise ValueError("PRODUTO não pode ser vazio")
        
        # Validate CATEGORIA
        if not self.categoria or not isinstance(self.categoria, str):
            raise ValueError("CATEGORIA é obrigatória e deve ser texto")
        
        if not self.categoria.strip():
            raise ValueError("CATEGORIA não pode ser vazia")
        
        # Validate CUSTO
        try:
            self.custo = float(self.custo)
        except (ValueError, TypeError):
            raise ValueError("CUSTO deve ser um número válido")
        
        if self.custo <= 0:
            raise ValueError("CUSTO deve ser maior que zero")
        
        # Validate VALOR (selling price)
        try:
            self.valor = float(self.valor)
        except (ValueError, TypeError):
            raise ValueError("VALOR deve ser um número válido")
        
        if self.valor <= 0:
            raise ValueError("VALOR (preço de venda) deve ser maior que zero")
        
        # Validate ESTOQUE
        try:
            self.estoque = int(self.estoque)
        except (ValueError, TypeError):
            raise ValueError("ESTOQUE deve ser um número inteiro válido")
        
        if self.estoque < 0:
            raise ValueError("ESTOQUE não pode ser negativo")
    
    def calculate_margin(self) -> float:
        """
        Calculate profit margin percentage.
        
        Returns:
            Profit margin as percentage (e.g., 25.5 for 25.5%)
        """
        if self.custo == 0:
            return 0.0
        return ((self.valor - self.custo) / self.custo) * 100
    
    def calculate_markup(self) -> float:
        """
        Calculate markup percentage.
        
        Returns:
            Markup as percentage
        """
        if self.custo == 0:
            return 0.0
        return ((self.valor - self.custo) / self.custo) * 100
    
    def calculate_inventory_value(self) -> float:
        """
        Calculate total inventory value (cost-based).
        
        Returns:
            Total value of stock at cost price
        """
        return self.custo * self.estoque
    
    def calculate_retail_value(self) -> float:
        """
        Calculate total retail value of inventory.
        
        Returns:
            Total value of stock at selling price
        """
        return self.valor * self.estoque
    
    def to_dict(self) -> dict:
        """
        Convert Product to dictionary for CSV serialization.
        
        Returns:
            Dictionary with product data
        """
        return {
            'CODIGO': self.codigo.strip().upper(),
            'PRODUTO': self.produto.strip().title(),
            'CATEGORIA': self.categoria.strip().title(),
            'CUSTO': f"{self.custo:.2f}",
            'VALOR': f"{self.valor:.2f}",
            'ESTOQUE': str(self.estoque)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Product':
        """
        Create Product instance from dictionary.
        
        Args:
            data: Dictionary with product data
            
        Returns:
            Product instance
        """
        return cls(
            codigo=data.get('CODIGO', ''),
            produto=data.get('PRODUTO', ''),
            categoria=data.get('CATEGORIA', ''),
            custo=data.get('CUSTO', 0),
            valor=data.get('VALOR', 0),
            estoque=data.get('ESTOQUE', 0)
        )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"Product(codigo='{self.codigo}', produto='{self.produto}', "
                f"categoria='{self.categoria}', custo={self.custo:.2f}, "
                f"valor={self.valor:.2f}, estoque={self.estoque})")