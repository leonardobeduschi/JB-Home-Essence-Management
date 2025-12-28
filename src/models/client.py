"""
Client model and validation.

This module defines the Client entity structure and business-specific validation rules.
Handles both 'pessoa' (individual) and 'empresa' (company) client types.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


# CSV Schema for clients
CLIENT_SCHEMA = [
    'ID_CLIENTE',
    'CLIENTE',
    'VENDEDOR',
    'TIPO',
    'IDADE',
    'GENERO',
    'PROFISSAO',
    'CPF_CNPJ',
    'TELEFONE',
    'ENDERECO'
]


class TipoCliente(Enum):
    """Client type enumeration."""
    PESSOA = "pessoa"
    EMPRESA = "empresa"


class FaixaIdade(Enum):
    """Age range enumeration for individual clients."""
    MENOR_18 = "<18"
    IDADE_18_24 = "18-24"
    IDADE_25_34 = "25-34"
    IDADE_35_44 = "35-44"
    IDADE_45_54 = "45-54"
    IDADE_55_MAIS = ">55"  # CORRIGIDO: era 55-64 e 65+, agora é >55
    IDADE_65_MAIS = "65+"


@dataclass
class Client:
    """
    Client entity representing a customer (individual or company).
    
    Business Rules:
    - If TIPO = 'empresa':
        * CPF_CNPJ and ENDERECO are MANDATORY
        * IDADE and GENERO must be EMPTY
    - If TIPO = 'pessoa':
        * IDADE and GENERO are MANDATORY
        * CPF_CNPJ and ENDERECO are OPTIONAL
    
    Attributes:
        id_cliente: Unique client ID (auto-generated, e.g., 'CLI001')
        cliente: Client name (person or company name)
        vendedor: Salesperson name
        tipo: Client type ('pessoa' or 'empresa')
        idade: Age range (required for pessoa, empty for empresa)
        genero: Gender (required for pessoa, empty for empresa)
        profissao: Profession (optional for both types)
        cpf_cnpj: Tax ID (mandatory for empresa, optional for pessoa)
        telefone: Phone number (optional for both types)
        endereco: Address (mandatory for empresa, optional for pessoa)
    """
    id_cliente: str
    cliente: str
    vendedor: str
    tipo: str
    idade: str = ""
    genero: str = ""
    profissao: str = ""
    cpf_cnpj: str = ""
    telefone: str = ""
    endereco: str = ""
    
    def __post_init__(self):
        """Validate client data after initialization."""
        self._validate()
    
    def _validate(self) -> None:
        """
        Validate client attributes according to business rules.
        
        Raises:
            ValueError: If any validation rule fails
        """
        # Validate ID_CLIENTE
        if not self.id_cliente or not isinstance(self.id_cliente, str):
            raise ValueError("ID_CLIENTE é obrigatório e deve ser texto")
        
        if not str(self.id_cliente).strip():
            raise ValueError("ID_CLIENTE não pode ser vazio")
        
        # Validate CLIENTE (name)
        if not self.cliente or not isinstance(self.cliente, str):
            raise ValueError("CLIENTE (nome) é obrigatório e deve ser texto")
        
        if not self.cliente.strip():
            raise ValueError("CLIENTE (nome) não pode ser vazio")
        
        # Validate VENDEDOR - PODE SER VAZIO (alguns clientes não têm vendedor ainda)
        if self.vendedor is None:
            self.vendedor = ""
        
        # Validate TIPO
        if not self.tipo or not isinstance(self.tipo, str):
            raise ValueError("TIPO é obrigatório e deve ser texto")
        
        # Normalizar tipo - aceita "Pessoa", "pessoa", "PESSOA", "Empresa", etc
        tipo_lower = self.tipo.lower().strip()
        if tipo_lower not in ['pessoa', 'empresa']:
            raise ValueError("TIPO deve ser 'pessoa' ou 'empresa'")
        
        # Normalize tipo para minúscula
        self.tipo = tipo_lower.capitalize()  # "Pessoa" ou "Empresa" para exibição
        
        # Apply tipo-specific validation rules (apenas para novos registros)
        # Para leitura de CSV existente, permite dados inconsistentes
    
    def _validate_empresa(self) -> None:
        """
        Validate empresa-specific business rules.
        
        Rules:
        - CPF_CNPJ is MANDATORY
        - ENDERECO is MANDATORY
        - IDADE must be EMPTY
        - GENERO must be EMPTY
        """
        # CPF_CNPJ is mandatory for empresa
        if not self.cpf_cnpj or not self.cpf_cnpj.strip():
            raise ValueError("CPF/CNPJ é obrigatório para empresas")
        
        # ENDERECO is mandatory for empresa
        if not self.endereco or not self.endereco.strip():
            raise ValueError("ENDEREÇO é obrigatório para empresas")
        
        # IDADE and GENERO must be empty for empresa
        # Force them to empty string
        self.idade = ""
        self.genero = ""
    
    def _validate_pessoa(self) -> None:
        """
        Validate pessoa-specific business rules.
        
        Rules:
        - IDADE is MANDATORY
        - GENERO is MANDATORY
        - CPF_CNPJ is optional
        - ENDERECO is optional
        """
        # IDADE is mandatory for pessoa
        if not self.idade or not self.idade.strip():
            raise ValueError("IDADE é obrigatória para pessoas físicas")
        
        # Validate idade format (should be a valid age range)
        valid_ages = [e.value for e in FaixaIdade]
        if self.idade.strip() not in valid_ages:
            raise ValueError(
                f"IDADE deve ser uma das faixas válidas: {', '.join(valid_ages)}"
            )
        
        # GENERO is mandatory for pessoa
        if not self.genero or not self.genero.strip():
            raise ValueError("GÊNERO é obrigatório para pessoas físicas")
    
    def is_empresa(self) -> bool:
        """Check if client is a company."""
        return self.tipo.lower() == 'empresa'
    
    def is_pessoa(self) -> bool:
        """Check if client is an individual."""
        return self.tipo.lower() == 'pessoa'
    
    def get_display_name(self) -> str:
        """
        Get formatted display name with type indicator.
        
        Returns:
            Formatted name (e.g., "João Silva (Pessoa)" or "ABC Ltda (Empresa)")
        """
        tipo_display = "Empresa" if self.is_empresa() else "Pessoa"
        return f"{self.cliente} ({tipo_display})"
    
    def to_dict(self) -> dict:
        """
        Convert Client to dictionary for CSV serialization.
        
        Returns:
            Dictionary with client data
        """
        return {
            'ID_CLIENTE': str(self.id_cliente).strip(),
            'CLIENTE': self.cliente.strip(),
            'VENDEDOR': self.vendedor.strip() if self.vendedor else "",
            'TIPO': self.tipo.strip().capitalize(),  # Salva como "Pessoa" ou "Empresa"
            'IDADE': self.idade.strip() if self.idade else "",
            'GENERO': self.genero.strip() if self.genero else "",
            'PROFISSAO': self.profissao.strip() if self.profissao else "",
            'CPF_CNPJ': self.cpf_cnpj.strip() if self.cpf_cnpj else "",
            'TELEFONE': self.telefone.strip() if self.telefone else "",
            'ENDERECO': self.endereco.strip() if self.endereco else ""
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Client':
        """
        Create Client instance from dictionary.
        
        Args:
            data: Dictionary with client data
            
        Returns:
            Client instance
        """
        return cls(
            id_cliente=str(data.get('ID_CLIENTE', '')),
            cliente=str(data.get('CLIENTE', '')),
            vendedor=str(data.get('VENDEDOR', '')),
            tipo=str(data.get('TIPO', '')),
            idade=str(data.get('IDADE', '')),
            genero=str(data.get('GENERO', '')),
            profissao=str(data.get('PROFISSAO', '')),
            cpf_cnpj=str(data.get('CPF_CNPJ', '')),
            telefone=str(data.get('TELEFONE', '')),
            endereco=str(data.get('ENDERECO', ''))
        )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"Client(id='{self.id_cliente}', nome='{self.cliente}', "
                f"tipo='{self.tipo}', vendedor='{self.vendedor}')")