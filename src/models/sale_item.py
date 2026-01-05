"""
Sale Item model - NOVO ARQUIVO.

Crie este arquivo em: src/models/sale_item.py
"""

from dataclasses import dataclass


# CSV Schema for sale items
SALE_ITEM_SCHEMA = [
    'ID_VENDA',
    'PRODUTO',
    'CATEGORIA',
    'CODIGO',
    'QUANTIDADE',
    'PRECO_UNIT',
    'PRECO_TOTAL'
]


@dataclass
class SaleItem:
    """
    Sale Item entity - representa um produto em uma venda.
    
    Relacionamento: N itens pertencem a 1 venda (via ID_VENDA).
    
    Attributes:
        id_venda: ID da venda (FK para sales.csv)
        produto: Nome do produto
        categoria: Categoria do produto
        codigo: Código do produto
        quantidade: Quantidade vendida
        preco_unit: Preço unitário no momento da venda
        preco_total: Total do item (quantidade × preco_unit)
    """
    id_venda: str
    produto: str
    categoria: str
    codigo: str
    quantidade: int
    preco_unit: float
    preco_total: float = 0.0
    
    def __post_init__(self):
        """Validate and calculate total."""
        self._validate()
        self._calculate_total()
    
    def _validate(self) -> None:
        """Validate item attributes."""
        if not self.id_venda or not str(self.id_venda).strip():
            raise ValueError("ID_VENDA é obrigatório")
        
        if not self.produto or not str(self.produto).strip():
            raise ValueError("PRODUTO é obrigatório")
        
        if not self.categoria or not str(self.categoria).strip():
            raise ValueError("CATEGORIA é obrigatória")
        
        if not self.codigo or not str(self.codigo).strip():
            raise ValueError("CODIGO é obrigatório")
        
        try:
            self.quantidade = int(self.quantidade)
        except (ValueError, TypeError):
            raise ValueError("QUANTIDADE deve ser um número inteiro")
        
        if self.quantidade <= 0:
            raise ValueError("QUANTIDADE deve ser maior que zero")
        
        try:
            self.preco_unit = float(self.preco_unit)
        except (ValueError, TypeError):
            raise ValueError("PRECO_UNIT deve ser um número válido")
        
        if self.preco_unit < 0:
            raise ValueError("PRECO_UNIT não pode ser negativo")
    
    def _calculate_total(self) -> None:
        """Calculate total price."""
        self.preco_total = self.quantidade * self.preco_unit
    
    def to_dict(self) -> dict:
        """Convert to dictionary for CSV."""
        return {
            'ID_VENDA': str(self.id_venda).strip().upper(),
            'PRODUTO': str(self.produto).strip(),
            'CATEGORIA': str(self.categoria).strip(),
            'CODIGO': str(self.codigo).strip().upper(),
            'QUANTIDADE': str(self.quantidade),
            'PRECO_UNIT': f"{self.preco_unit:.2f}",
            'PRECO_TOTAL': f"{self.preco_total:.2f}"
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SaleItem':
        """Create from dictionary."""
        return cls(
            id_venda=data.get('ID_VENDA', ''),
            produto=data.get('PRODUTO', ''),
            categoria=data.get('CATEGORIA', ''),
            codigo=data.get('CODIGO', ''),
            quantidade=data.get('QUANTIDADE', 0),
            preco_unit=data.get('PRECO_UNIT', 0),
            preco_total=data.get('PRECO_TOTAL', 0)
        )
    
    def __repr__(self) -> str:
        return (f"SaleItem(id_venda='{self.id_venda}', produto='{self.produto}', "
                f"quantidade={self.quantidade}, total=R${self.preco_total:.2f})")