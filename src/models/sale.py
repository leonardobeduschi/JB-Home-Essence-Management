"""
Sale model with validation - UPDATED with new payment methods.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum
from datetime import datetime


class MeioPagamento(str, Enum):
    """Valid payment methods."""
    DINHEIRO = "dinheiro"
    PIX = "pix"
    CARTAO_CREDITO = "cartão de crédito"
    CARTAO_DEBITO = "cartão de débito"
    BOLETO = "boleto"
    TRANSFERENCIA = "transferência"
    CHEQUE = "cheque"
    CREDIARIO = "crediário"


@dataclass
class Sale:
    """
    Sale model - represents a sale header (NEW STRUCTURE).
    
    Each sale can have multiple items (stored in sale_items.csv).
    This header stores common info: client, date, payment method, total.
    """
    id_venda: str
    id_cliente: str
    cliente: str
    meio: str
    data: str
    valor_total_venda: float  # NEW: total value of the sale
    
    def __post_init__(self):
        """Validate sale data after initialization."""
        # Validate ID
        if not self.id_venda or not isinstance(self.id_venda, str):
            raise ValueError("ID da venda é obrigatório e deve ser string")
        
        # Validate client
        if not self.id_cliente or not isinstance(self.id_cliente, str):
            raise ValueError("ID do cliente é obrigatório")
        
        if not self.cliente or not isinstance(self.cliente, str):
            raise ValueError("Nome do cliente é obrigatório")
        
        # Validate payment method
        meio_lower = self.meio.lower().strip()
        valid_methods = [m.value for m in MeioPagamento]
        
        if meio_lower not in valid_methods:
            raise ValueError(
                f"Meio de pagamento inválido. "
                f"Opções: {', '.join(valid_methods)}"
            )
        
        # Normalize payment method
        self.meio = meio_lower
        
        # Validate date format (DD/MM/YYYY)
        if not self.data:
            raise ValueError("Data da venda é obrigatória")
        
        try:
            # Try to parse the date to validate format
            datetime.strptime(self.data, '%d/%m/%Y')
        except ValueError:
            raise ValueError("Data inválida. Use o formato DD/MM/YYYY")
        
        # Validate total value
        try:
            self.valor_total_venda = float(self.valor_total_venda)
            if self.valor_total_venda < 0:
                raise ValueError("Valor total da venda não pode ser negativo")
        except (TypeError, ValueError):
            raise ValueError("Valor total da venda deve ser um número válido")
    
    def to_dict(self) -> dict:
        """Convert sale to dictionary for CSV storage."""
        return {
            'ID_VENDA': self.id_venda,
            'DATA': self.data,
            'ID_CLIENTE': self.id_cliente,
            'CLIENTE': self.cliente,
            'MEIO': self.meio,
            'VALOR_TOTAL_VENDA': self.valor_total_venda
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Sale':
        """Create Sale instance from dictionary."""
        return cls(
            id_venda=data['ID_VENDA'],
            id_cliente=data['ID_CLIENTE'],
            cliente=data['CLIENTE'],
            meio=data['MEIO'],
            data=data['DATA'],
            valor_total_venda=float(data.get('VALOR_TOTAL_VENDA', 0))
        )


# CSV Schema for sales.csv (NEW STRUCTURE)
SALE_SCHEMA = {
    'ID_VENDA': str,
    'DATA': str,
    'ID_CLIENTE': str,
    'CLIENTE': str,
    'MEIO': str,
    'VALOR_TOTAL_VENDA': float
}