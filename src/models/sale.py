"""
Sale model and validation - FIXED for new structure.

Substitua COMPLETAMENTE o arquivo src/models/sale.py por este:
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


# CSV Schema for sales (ONLY header fields)
SALE_SCHEMA = [
    'ID_VENDA',
    'ID_CLIENTE',
    'CLIENTE',
    'MEIO',
    'DATA',
    'VALOR_TOTAL_VENDA'
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
    Sale entity - APENAS o cabeçalho da venda.
    Itens estão em SaleItem (sales_items.csv).
    
    Attributes:
        id_venda: Unique sale ID
        id_cliente: Client ID (FK)
        cliente: Client name
        meio: Payment method
        data: Sale date (DD/MM/YYYY)
        valor_total_venda: Total sale value (sum of all items)
    """
    id_venda: str
    id_cliente: str
    cliente: str
    meio: str
    data: str
    valor_total_venda: float = 0.0
    
    def __post_init__(self):
        """Validate sale data."""
        self._validate()
    
    def _validate(self) -> None:
        """Validate sale attributes."""
        # Validate ID_VENDA
        if not self.id_venda or not str(self.id_venda).strip():
            raise ValueError("ID_VENDA é obrigatório")
        
        # Validate ID_CLIENTE
        if not self.id_cliente or not str(self.id_cliente).strip():
            raise ValueError("ID_CLIENTE é obrigatório")
        
        # Validate CLIENTE
        if not self.cliente or not str(self.cliente).strip():
            raise ValueError("CLIENTE é obrigatório")
        
        # Validate MEIO
        if not self.meio or not str(self.meio).strip():
            raise ValueError("MEIO de pagamento é obrigatório")
        
        valid_payment_methods = [e.value for e in MeioPagamento]
        if self.meio.lower() not in valid_payment_methods:
            print(f"⚠️ Aviso: Meio de pagamento '{self.meio}' não está na lista padrão")
        
        # Validate DATA
        if not self.data or not str(self.data).strip():
            raise ValueError("DATA é obrigatória")
        
        try:
            datetime.strptime(str(self.data).strip(), '%d/%m/%Y')
        except ValueError:
            raise ValueError("DATA deve estar no formato DD/MM/YYYY")
        
        # Validate VALOR_TOTAL_VENDA
        try:
            self.valor_total_venda = float(self.valor_total_venda)
        except (ValueError, TypeError):
            raise ValueError("VALOR_TOTAL_VENDA deve ser numérico")
        
        if self.valor_total_venda < 0:
            raise ValueError("VALOR_TOTAL_VENDA não pode ser negativo")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for CSV."""
        return {
            'ID_VENDA': str(self.id_venda).strip().upper(),
            'ID_CLIENTE': str(self.id_cliente).strip().upper(),
            'CLIENTE': str(self.cliente).strip(),
            'MEIO': str(self.meio).strip().lower(),
            'DATA': str(self.data).strip(),
            'VALOR_TOTAL_VENDA': f"{self.valor_total_venda:.2f}"
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Sale':
        """Create from dictionary."""
        return cls(
            id_venda=data.get('ID_VENDA', ''),
            id_cliente=data.get('ID_CLIENTE', ''),
            cliente=data.get('CLIENTE', ''),
            meio=data.get('MEIO', ''),
            data=data.get('DATA', ''),
            valor_total_venda=float(data.get('VALOR_TOTAL_VENDA', 0))
        )
    
    def get_payment_method_display(self) -> str:
        """Get formatted payment method for display."""
        payment_display = {
            'pix': 'PIX',
            'cartão': 'Cartão',
            'cartão de crédito': 'Cartão de Crédito',
            'cartão de débito': 'Cartão de Débito',
            'dinheiro': 'Dinheiro',
            'transferência': 'Transferência',
            'boleto': 'Boleto'
        }
        return payment_display.get(self.meio.lower(), self.meio.title())
    
    def __repr__(self) -> str:
        """String representation."""
        return (f"Sale(id_venda='{self.id_venda}', cliente='{self.cliente}', "
                f"valor_total=R${self.valor_total_venda:.2f}, meio='{self.meio}')")