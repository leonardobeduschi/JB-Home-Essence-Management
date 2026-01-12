# ==================== product_repository.py ====================
"""
Product repository - PostgreSQL Compatible
"""

import pandas as pd
from typing import Optional, List, Dict
from src.repositories.base_repository import BaseRepository
from src.models.product import Product, PRODUCT_SCHEMA


class ProductRepository(BaseRepository):
    """Repository for product data persistence."""

    def __init__(self, filepath: str = 'data/products.csv'):
        super().__init__(filepath, PRODUCT_SCHEMA, table_name='products')

    def exists(self, codigo: str) -> bool:
        if not codigo:
            return False
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            if self.db_type == 'postgresql':
                cur.execute('SELECT 1 FROM products WHERE UPPER("CODIGO") = UPPER(%s) LIMIT 1', (codigo,))
            else:
                cur.execute('SELECT 1 FROM products WHERE "CODIGO" = ? COLLATE NOCASE LIMIT 1', (codigo,))
            return cur.fetchone() is not None

    def get_by_codigo(self, codigo: str) -> Optional[Dict]:
        if not codigo:
            return None
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            if self.db_type == 'postgresql':
                cur.execute('SELECT * FROM products WHERE UPPER("CODIGO") = UPPER(%s) LIMIT 1', (codigo,))
            else:
                cur.execute('SELECT * FROM products WHERE "CODIGO" = ? COLLATE NOCASE LIMIT 1', (codigo,))
            row = cur.fetchone()
            return dict(row) if row else None

    def save(self, product: Product) -> bool:
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
        if not self.exists(codigo):
            raise ValueError(f"Produto com código '{codigo}' não encontrado")
        
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
            
            return super().update(codigo, to_update)
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Erro ao atualizar produto: {str(e)}")

    def update_stock(self, codigo: str, quantity_change: int) -> bool:
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
        if not categoria:
            return []
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            if self.db_type == 'postgresql':
                cur.execute('SELECT * FROM products WHERE "CATEGORIA" = %s', (categoria,))
            else:
                cur.execute('SELECT * FROM products WHERE "CATEGORIA" = ? COLLATE NOCASE', (categoria,))
            return [dict(r) for r in cur.fetchall()]

    def get_low_stock(self, threshold: int = 5) -> List[Dict]:
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            if self.db_type == 'postgresql':
                cur.execute('SELECT * FROM products WHERE COALESCE("ESTOQUE",0) <= %s ORDER BY "CODIGO"', (threshold,))
            else:
                cur.execute('SELECT * FROM products WHERE COALESCE("ESTOQUE",0) <= ? ORDER BY "CODIGO"', (threshold,))
            return [dict(r) for r in cur.fetchall()]

    def get_inventory_value(self) -> Dict[str, float]:
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            cur.execute('SELECT SUM(COALESCE("CUSTO",0) * COALESCE("ESTOQUE",0)) AS cost_value, SUM(COALESCE("VALOR",0) * COALESCE("ESTOQUE",0)) AS retail_value FROM products')
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