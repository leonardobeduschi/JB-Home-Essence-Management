# src/ui/__init__.py
"""User interface components."""

from src.ui.menu import Menu, create_submenu
from src.ui.display import (
    display_products,
    display_clients,
    display_sales,
    display_product_detail,
    display_client_detail,
    display_sale_detail
)
from src.ui.analytics_display import (
    print_bar_chart,
    print_trend_chart,
    print_comparison,
    print_abc_analysis,
    print_customer_segments,
    print_profitability_report
)

__all__ = [
    'Menu', 'create_submenu',
    'display_products', 'display_clients', 'display_sales',
    'display_product_detail', 'display_client_detail', 'display_sale_detail',
    'print_bar_chart', 'print_trend_chart', 'print_comparison',
    'print_abc_analysis', 'print_customer_segments', 'print_profitability_report'
]
# src/validators/__init__.py
"""Input validation utilities."""

from src.validators.client_validator import ClientValidator

__all__ = ['ClientValidator']


# src/utils/__init__.py
"""Utility functions and helpers."""

from src.utils.id_generator import IDGenerator

__all__ = ['IDGenerator']# src/__init__.py
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
Sale Schema: ID_VENDA, ID_CLIENTE, CLIENTE, MEIO, DATA, PRODUTO, CATEGORIA, CODIGO, QUANTIDADE, PRECO_UNIT, PRECO_TOTAL
"""

from src.models.product import Product, PRODUCT_SCHEMA
from src.models.client import Client, CLIENT_SCHEMA, TipoCliente, FaixaIdade
from src.models.sale import Sale, SALE_SCHEMA, MeioPagamento

__all__ = [
    'Product', 'PRODUCT_SCHEMA',
    'Client', 'CLIENT_SCHEMA', 'TipoCliente', 'FaixaIdade',
    'Sale', 'SALE_SCHEMA', 'MeioPagamento'
]


# src/repositories/__init__.py
"""Data access layer for CSV operations."""

from src.repositories.base_repository import BaseRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.client_repository import ClientRepository
from src.repositories.sale_repository import SaleRepository

__all__ = ['BaseRepository', 'ProductRepository', 'ClientRepository', 'SaleRepository']


# src/services/__init__.py
"""Business logic layer."""

from src.services.product_service import ProductService
from src.services.client_service import ClientService
from src.services.sale_service import SaleService
from src.services.analytics_service import AnalyticsService
from src.services.visualization_service import VisualizationService
from src.services.export_service import ExportService

__all__ = [
    'ProductService', 'ClientService', 'SaleService', 
    'AnalyticsService', 'VisualizationService', 'ExportService'
]