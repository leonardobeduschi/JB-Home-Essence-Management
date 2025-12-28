"""
Sale model and validation.

This module defines the Sale entity structure and business rules.
Sales are transactions that link clients and products, automatically
calculating totals and updating inventory.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


# CSV Schema for sales
SALE_SCHEMA = [
    'ID_VENDA',
    'ID_CLIENTE',
    'CLIENTE',
    'MEIO',
    'DATA',
    'PRODUTO',
    'CATEGORIA',
    'CODIGO',
    'QUANTIDADE',
    'PRECO_UNIT',
    'PRECO_TOTAL'
]


class MeioPagamento(Enum):
    """Payment method enumeration."""
    PIX = "pix"
    CARTAO = "cartão"
    CARTAO_CREDITO = "cartão de crédito"
    CARTAO_DEBITO = "cartão de débito"
    DINHEIRO = "dinheiro"
    TRANSFERENCIA = "transferência"
    BOLETO = "boleto"


@dataclass
class Sale:
    """
    Sale entity representing a transaction.
    
    Attributes:
        id_venda: Unique sale ID (auto-generated, e.g., 'VND001')
        id_cliente: Client ID reference
        cliente: Client name (auto-filled from client)
        meio: Payment method
        data: Sale date (DD/MM/YYYY)
        produto: Product name (auto-filled from product)
        categoria: Product category (auto-filled from product)
        codigo: Product code reference
        quantidade: Quantity sold
        preco_unit: Unit price at time of sale
        preco_total: Total price (auto-calculated)
    """
    id_venda: str
    id_cliente: str
    cliente: str
    meio: str
    data: str
    produto: str
    categoria: str
    codigo: str
    quantidade: int
    preco_unit: float
    preco_total: float = 0.0
    
    def __post_init__(self):
        """Validate sale data and calculate total."""
        self._validate()
        self._calculate_total()
    
    def _validate(self) -> None:
        """
        Validate sale attributes.
        
        Raises:
            ValueError: If any validation rule fails
        """
        # Validate ID_VENDA
        if not self.id_venda or not isinstance(self.id_venda, str):
            raise ValueError("ID_VENDA é obrigatório e deve ser texto")
        
        if not self.id_venda.strip():
            raise ValueError("ID_VENDA não pode ser vazio")
        
        # Validate ID_CLIENTE
        if not self.id_cliente or not isinstance(self.id_cliente, str):
            raise ValueError("ID_CLIENTE é obrigatório e deve ser texto")
        
        if not self.id_cliente.strip():
            raise ValueError("ID_CLIENTE não pode ser vazio")
        
        # Validate CLIENTE (name)
        if not self.cliente or not isinstance(self.cliente, str):
            raise ValueError("CLIENTE (nome) é obrigatório e deve ser texto")
        
        if not self.cliente.strip():
            raise ValueError("CLIENTE (nome) não pode ser vazio")
        
        # Validate MEIO (payment method)
        if not self.meio or not isinstance(self.meio, str):
            raise ValueError("MEIO (forma de pagamento) é obrigatório")
        
        meio_lower = self.meio.lower().strip()
        valid_meios = [e.value for e in MeioPagamento]
        if meio_lower not in valid_meios:
            raise ValueError(
                f"MEIO deve ser um dos seguintes: {', '.join(valid_meios)}"
            )
        
        # Normalize meio
        self.meio = meio_lower
        
        # Validate DATA
        if not self.data or not isinstance(self.data, str):
            raise ValueError("DATA é obrigatória")
        
        # Validate date format (DD/MM/YYYY)
        try:
            datetime.strptime(self.data.strip(), '%d/%m/%Y')
        except ValueError:
            raise ValueError("DATA deve estar no formato DD/MM/YYYY")
        
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
        
        # Validate CODIGO
        if not self.codigo or not isinstance(self.codigo, str):
            raise ValueError("CODIGO (do produto) é obrigatório")
        
        if not self.codigo.strip():
            raise ValueError("CODIGO não pode ser vazio")
        
        # Validate QUANTIDADE
        try:
            self.quantidade = int(self.quantidade)
        except (ValueError, TypeError):
            raise ValueError("QUANTIDADE deve ser um número inteiro válido")
        
        if self.quantidade <= 0:
            raise ValueError("QUANTIDADE deve ser maior que zero")
        
        # Validate PRECO_UNIT
        try:
            self.preco_unit = float(self.preco_unit)
        except (ValueError, TypeError):
            raise ValueError("PREÇO UNITÁRIO deve ser um número válido")
        
        if self.preco_unit <= 0:
            raise ValueError("PREÇO UNITÁRIO deve ser maior que zero")
    
    def _calculate_total(self) -> None:
        """Calculate total price (QUANTIDADE × PRECO_UNIT)."""
        self.preco_total = self.quantidade * self.preco_unit
    
    def get_display_date(self) -> str:
        """
        Get formatted display date.
        
        Returns:
            Date in DD/MM/YYYY format
        """
        return self.data
    
    def get_payment_method_display(self) -> str:
        """
        Get formatted payment method for display.
        
        Returns:
            Capitalized payment method
        """
        return self.meio.title()
    
    def to_dict(self) -> dict:
        """
        Convert Sale to dictionary for CSV serialization.
        
        Returns:
            Dictionary with sale data
        """
        return {
            'ID_VENDA': self.id_venda.strip().upper(),
            'ID_CLIENTE': self.id_cliente.strip().upper(),
            'CLIENTE': self.cliente.strip(),
            'MEIO': self.meio.strip().lower(),
            'DATA': self.data.strip(),
            'PRODUTO': self.produto.strip(),
            'CATEGORIA': self.categoria.strip(),
            'CODIGO': self.codigo.strip().upper(),
            'QUANTIDADE': str(self.quantidade),
            'PRECO_UNIT': f"{self.preco_unit:.2f}",
            'PRECO_TOTAL': f"{self.preco_total:.2f}"
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Sale':
        """
        Create Sale instance from dictionary.
        
        Args:
            data: Dictionary with sale data
            
        Returns:
            Sale instance
        """
        return cls(
            id_venda=data.get('ID_VENDA', ''),
            id_cliente=data.get('ID_CLIENTE', ''),
            cliente=data.get('CLIENTE', ''),
            meio=data.get('MEIO', ''),
            data=data.get('DATA', ''),
            produto=data.get('PRODUTO', ''),
            categoria=data.get('CATEGORIA', ''),
            codigo=data.get('CODIGO', ''),
            quantidade=data.get('QUANTIDADE', 0),
            preco_unit=data.get('PRECO_UNIT', 0),
            preco_total=data.get('PRECO_TOTAL', 0)
        )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"Sale(id='{self.id_venda}', cliente='{self.cliente}', "
                f"produto='{self.produto}', quantidade={self.quantidade}, "
                f"total=R${self.preco_total:.2f})")