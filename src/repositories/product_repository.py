"""
Product Repository - Optimized

Principais otimizações:
1. get_inventory_value() com agregação SQL
2. Queries com projeção de colunas
3. Eliminação de Pandas onde possível
"""

from typing import Optional, List, Dict
from src.repositories.base_repository import BaseRepository
from src.models.product import Product, PRODUCT_SCHEMA


class ProductRepository(BaseRepository):
    """Repository otimizado para produtos."""

    def __init__(self, filepath: str = 'data/products.csv'):
        super().__init__(filepath, PRODUCT_SCHEMA, table_name='products')

    def exists(self, codigo: str) -> bool:
        if not codigo:
            return False
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            
            if self.db_type == 'postgresql':
                cur.execute(f'SELECT 1 FROM products WHERE UPPER("CODIGO") = UPPER({placeholder}) LIMIT 1', (codigo,))
            else:
                cur.execute('SELECT 1 FROM products WHERE "CODIGO" = ? COLLATE NOCASE LIMIT 1', (codigo,))
            
            return cur.fetchone() is not None

    def get_by_codigo(self, codigo: str) -> Optional[Dict]:
        if not codigo:
            return None
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            
            if self.db_type == 'postgresql':
                cur.execute(f'SELECT * FROM products WHERE UPPER("CODIGO") = UPPER({placeholder}) LIMIT 1', (codigo,))
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
        """
        OTIMIZADO: Atualiza estoque com 1 query SQL.
        
        Antes: SELECT + UPDATE (2 queries)
        Depois: UPDATE direto com validação
        """
        try:
            with self.get_conn() as conn:
                cur = self._get_cursor(conn)
                placeholder = '%s' if self.db_type == 'postgresql' else '?'
                
                # 1 query: UPDATE com validação inline
                if self.db_type == 'postgresql':
                    cur.execute(f'''
                        UPDATE products 
                        SET "ESTOQUE" = "ESTOQUE" + {placeholder}
                        WHERE "CODIGO" = {placeholder}
                        AND ("ESTOQUE" + {placeholder}) >= 0
                        RETURNING "ESTOQUE"
                    ''', (quantity_change, codigo, quantity_change))
                    
                    result = cur.fetchone()
                    if not result:
                        # Verifica se produto existe ou se estoque ficaria negativo
                        cur.execute(f'SELECT "ESTOQUE" FROM products WHERE "CODIGO" = {placeholder}', (codigo,))
                        product = cur.fetchone()
                        if not product:
                            raise ValueError(f"Produto com código '{codigo}' não encontrado")
                        else:
                            current_stock = int(product['ESTOQUE'] or 0)
                            raise ValueError(f"Estoque insuficiente. Disponível: {current_stock} unidades")
                    
                    return True
                else:
                    # SQLite não tem RETURNING, usa abordagem tradicional
                    cur.execute('SELECT "ESTOQUE" FROM products WHERE "CODIGO" = ? COLLATE NOCASE', (codigo,))
                    product = cur.fetchone()
                    
                    if not product:
                        raise ValueError(f"Produto com código '{codigo}' não encontrado")
                    
                    current_stock = int(product['ESTOQUE'] or 0)
                    new_stock = current_stock + int(quantity_change)
                    
                    if new_stock < 0:
                        raise ValueError(f"Estoque insuficiente. Disponível: {current_stock} unidades")
                    
                    cur.execute('''
                        UPDATE products 
                        SET "ESTOQUE" = ?
                        WHERE "CODIGO" = ? COLLATE NOCASE
                    ''', (new_stock, codigo))
                    
                    return True
                    
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Erro ao atualizar estoque: {str(e)}")

    def get_by_category(self, categoria: str) -> List[Dict]:
        if not categoria:
            return []
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            cur.execute(f'SELECT * FROM products WHERE "CATEGORIA" = {placeholder}', (categoria,))
            return [dict(r) for r in cur.fetchall()]

    def get_low_stock(self, threshold: int = 5) -> List[Dict]:
        """
        OTIMIZADO: Retorna produtos com estoque baixo.
        """
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            
            cur.execute(f'''
                SELECT * FROM products 
                WHERE COALESCE("ESTOQUE", 0) <= {placeholder}
                ORDER BY "CODIGO"
            ''', (threshold,))
            
            return [dict(r) for r in cur.fetchall()]

    def get_inventory_value(self) -> Dict[str, float]:
        """
        OTIMIZADO: Calcula valor do inventário com agregação SQL.
        
        Antes: SELECT * + loop Python
        Depois: 1 query com SUM
        """
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            
            cur.execute('''
                SELECT 
                    COALESCE(SUM("CUSTO" * "ESTOQUE"), 0) AS cost_value,
                    COALESCE(SUM("VALOR" * "ESTOQUE"), 0) AS retail_value
                FROM products
            ''')
            
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