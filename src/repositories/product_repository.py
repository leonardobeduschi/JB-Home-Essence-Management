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
    Repository for product data persistence using SQLite via BaseRepository.

    Public methods preserved from the CSV implementation. Internally
    queries the `products` table and performs validations similar to the
    previous CSV-based implementation.
    """

    def __init__(self, filepath: str = 'data/products.csv'):
        super().__init__(filepath, PRODUCT_SCHEMA)

    def exists(self, codigo: str) -> bool:
        """Check if a product with given CODIGO exists (case-insensitive)."""
        if not codigo:
            return False
        with self.get_conn() as conn:
            cur = conn.execute('SELECT 1 FROM products WHERE CODIGO = ? COLLATE NOCASE LIMIT 1', (codigo,))
            return cur.fetchone() is not None

    def get_by_codigo(self, codigo: str) -> Optional[Dict]:
        """Retrieve a product by its code (case-insensitive)."""
        if not codigo:
            return None
        with self.get_conn() as conn:
            cur = conn.execute('SELECT * FROM products WHERE CODIGO = ? COLLATE NOCASE LIMIT 1', (codigo,))
            row = cur.fetchone()
            return dict(row) if row else None

    def save(self, product: Product) -> bool:
        """Save a new product to the database.

        Raises ValueError if product with same CODIGO already exists.
        """
        if self.exists(product.codigo):
            raise ValueError(f"Produto com código '{product.codigo}' já existe")
        try:
            data = {
                'CODIGO': product.codigo.strip().upper(),
                'PRODUTO': product.produto.strip().title(),
                'CATEGORIA': product.categoria.strip().title(),
                'CUSTO': float(f"{product.custo:.2f}"),
                'VALOR': float(f"{product.valor:.2f}"),
                'ESTOQUE': int(product.estoque)
            }
            self.insert(data)
            return True
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Erro ao salvar produto: {str(e)}")

    def update(self, codigo: str, updates: Dict) -> bool:
        """Update an existing product's information.

        Preserves the same validations and error messages as before.
        """
        if not self.exists(codigo):
            raise ValueError(f"Produto com código '{codigo}' não encontrado")

        # Validate and normalize updates
        allowed_fields = ['PRODUTO', 'CATEGORIA', 'CUSTO', 'VALOR', 'ESTOQUE']
        to_update = {}
        try:
            for field, value in updates.items():
                if field not in allowed_fields:
                    continue
                if field == 'CUSTO':
                    v = float(value)
                    if v <= 0:
                        raise ValueError("CUSTO deve ser maior que zero")
                    to_update['CUSTO'] = float(f"{v:.2f}")
                elif field == 'VALOR':
                    v = float(value)
                    if v <= 0:
                        raise ValueError("VALOR (preço de venda) deve ser maior que zero")
                    to_update['VALOR'] = float(f"{v:.2f}")
                elif field == 'ESTOQUE':
                    v = int(value)
                    if v < 0:
                        raise ValueError("ESTOQUE não pode ser negativo")
                    to_update['ESTOQUE'] = int(v)
                else:
                    if not value or not str(value).strip():
                        raise ValueError(f"{field} não pode ser vazio")
                    to_update[field] = str(value).strip()

            # Perform the update using BaseRepository.update
            return super().update(codigo, to_update)
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Erro ao atualizar produto: {str(e)}")

    def update_stock(self, codigo: str, quantity_change: int) -> bool:
        """Update product stock by adding or subtracting quantity."""
        product = self.get_by_codigo(codigo)
        if not product:
            raise ValueError(f"Produto com código '{codigo}' não encontrado")
        try:
            current_stock = int(product.get('ESTOQUE') or 0)
            new_stock = current_stock + int(quantity_change)
            if new_stock < 0:
                raise ValueError(f"Estoque insuficiente. Disponível: {current_stock} unidades")
            return self.update(codigo, {'ESTOQUE': new_stock})
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Erro ao atualizar estoque: {str(e)}")

    def get_by_category(self, categoria: str) -> List[Dict]:
        """Get all products in a specific category (case-insensitive)."""
        if not categoria:
            return []
        with self.get_conn() as conn:
            cur = conn.execute('SELECT * FROM products WHERE CATEGORIA = ? COLLATE NOCASE', (categoria,))
            rows = [dict(r) for r in cur.fetchall()]
            return rows

    def get_low_stock(self, threshold: int = 5) -> List[Dict]:
        """Get products with stock below or equal to a threshold."""
        with self.get_conn() as conn:
            cur = conn.execute('SELECT * FROM products WHERE COALESCE(ESTOQUE,0) <= ? ORDER BY CODIGO', (threshold,))
            return [dict(r) for r in cur.fetchall()]

    def get_inventory_value(self) -> Dict[str, float]:
        """Calculate total inventory value at cost and retail prices."""
        with self.get_conn() as conn:
            cur = conn.execute('SELECT SUM(COALESCE(CUSTO,0) * COALESCE(ESTOQUE,0)) AS cost_value, SUM(COALESCE(VALOR,0) * COALESCE(ESTOQUE,0)) AS retail_value FROM products')
            row = cur.fetchone()
            return {
                'cost_value': float(row['cost_value'] or 0),
                'retail_value': float(row['retail_value'] or 0)
            }

    def delete(self, codigo: str) -> bool:
        if not self.exists(codigo):
            raise ValueError(f"Produto com código '{codigo}' não encontrado")
        try:
            return super().delete(codigo)
        except Exception as e:
            raise Exception(f"Erro ao deletar produto: {str(e)}")