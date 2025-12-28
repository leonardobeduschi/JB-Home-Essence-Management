# src/__init__.py
"""
Perfumery Management System
A comprehensive system for sales, inventory, and client management.
"""

__version__ = "1.0.0"
__author__ = "Your Name"


# src/models/__init__.py
"""
Data models for the perfumery system.

Product Schema: CODIGO, PRODUTO, CATEGORIA, CUSTO, VALOR, ESTOQUE
Client Schema: ID_CLIENTE, CLIENTE, VENDEDOR, TIPO, IDADE, GENERO, PROFISSAO, CPF_CNPJ, TELEFONE, ENDERECO
"""

from src.models.product import Product, PRODUCT_SCHEMA
from src.models.client import Client, CLIENT_SCHEMA, TipoCliente, FaixaIdade

__all__ = ['Product', 'PRODUCT_SCHEMA', 'Client', 'CLIENT_SCHEMA', 'TipoCliente', 'FaixaIdade']


# src/repositories/__init__.py
"""Data access layer for CSV operations."""

from src.repositories.base_repository import BaseRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.client_repository import ClientRepository

__all__ = ['BaseRepository', 'ProductRepository', 'ClientRepository']


# src/services/__init__.py
"""Business logic layer."""

from src.services.product_service import ProductService
from src.services.client_service import ClientService

__all__ = ['ProductService', 'ClientService']