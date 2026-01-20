"""
Sale Item Repository - Optimized

Principais otimizações:
1. get_product_stats() e get_category_stats() retornam dicts em vez de Pandas
2. Agregações complexas feitas em SQL puro
3. Batch inserts otimizados
"""

from typing import List, Dict
from src.repositories.base_repository import BaseRepository
from src.models.sale_item import SaleItem, SALE_ITEM_SCHEMA


class SaleItemRepository(BaseRepository):
    """Repository otimizado para itens de venda."""

    def __init__(self, filepath: str = 'data/sales_items.csv'):
        super().__init__(filepath, SALE_ITEM_SCHEMA, table_name='sales_items')

    def save(self, item: SaleItem) -> bool:
        """Salva um item."""
        try:
            data = item.to_dict()
            if data.get('QUANTIDADE') is not None:
                data['QUANTIDADE'] = int(data['QUANTIDADE'])
            if data.get('PRECO_UNIT') is not None:
                data['PRECO_UNIT'] = float(data['PRECO_UNIT'])
            if data.get('PRECO_TOTAL') is not None:
                data['PRECO_TOTAL'] = float(data['PRECO_TOTAL'])
            self.insert(data)
            return True
        except Exception as e:
            raise Exception(f"Erro ao salvar item: {str(e)}")

    def save_many(self, items: List[SaleItem]) -> bool:
        """
        OTIMIZADO: Batch insert em 1 query com executemany.
        """
        try:
            rows = []
            for item in items:
                d = item.to_dict()
                rows.append((
                    d.get('ID_VENDA'), 
                    d.get('PRODUTO'), 
                    d.get('CATEGORIA'),
                    d.get('CODIGO'), 
                    int(d.get('QUANTIDADE') or 0),
                    float(d.get('PRECO_UNIT') or 0), 
                    float(d.get('PRECO_TOTAL') or 0)
                ))
            
            with self.get_conn() as conn:
                cur = self._get_cursor(conn)
                
                if self.db_type == 'postgresql':
                    sql = '''
                        INSERT INTO sales_items 
                        ("ID_VENDA", "PRODUTO", "CATEGORIA", "CODIGO", "QUANTIDADE", "PRECO_UNIT", "PRECO_TOTAL") 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    '''
                else:
                    sql = '''
                        INSERT INTO sales_items 
                        ("ID_VENDA", "PRODUTO", "CATEGORIA", "CODIGO", "QUANTIDADE", "PRECO_UNIT", "PRECO_TOTAL") 
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    '''
                
                cur.executemany(sql, rows)
            return True
        except Exception as e:
            raise Exception(f"Erro ao salvar itens: {str(e)}")

    def get_by_sale_id(self, id_venda: str) -> List[Dict]:
        """Retorna itens de uma venda."""
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            cur.execute(f'SELECT * FROM sales_items WHERE "ID_VENDA" = {placeholder}', (id_venda,))
            return [dict(r) for r in cur.fetchall()]

    def get_by_product(self, codigo: str) -> List[Dict]:
        """Retorna itens de um produto."""
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            cur.execute(f'SELECT * FROM sales_items WHERE "CODIGO" = {placeholder}', (codigo,))
            return [dict(r) for r in cur.fetchall()]

    def get_by_category(self, categoria: str) -> List[Dict]:
        """Retorna itens de uma categoria."""
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            cur.execute(f'SELECT * FROM sales_items WHERE "CATEGORIA" = {placeholder}', (categoria,))
            return [dict(r) for r in cur.fetchall()]

    def delete_by_sale_id(self, id_venda: str) -> bool:
        """Deleta itens de uma venda."""
        try:
            with self.get_conn() as conn:
                cur = self._get_cursor(conn)
                placeholder = '%s' if self.db_type == 'postgresql' else '?'
                cur.execute(f'DELETE FROM sales_items WHERE "ID_VENDA" = {placeholder}', (id_venda,))
                return cur.rowcount >= 0
        except Exception as e:
            raise Exception(f"Erro ao deletar itens: {str(e)}")

    def get_product_stats(self) -> List[Dict]:
        """
        OTIMIZADO: Retorna lista de dicts em vez de Pandas DataFrame.
        
        Agregação feita 100% em SQL.
        """
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            cur.execute('''
                SELECT 
                    "CODIGO", 
                    "PRODUTO", 
                    "CATEGORIA",
                    SUM(COALESCE("QUANTIDADE", 0)) AS "QTD_VENDIDA",
                    SUM(COALESCE("PRECO_TOTAL", 0)) AS "RECEITA",
                    COUNT("ID_VENDA") AS "NUM_VENDAS"
                FROM sales_items
                GROUP BY "CODIGO", "PRODUTO", "CATEGORIA"
                ORDER BY "RECEITA" DESC
            ''')
            
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def get_category_stats(self) -> List[Dict]:
        """
        OTIMIZADO: Retorna lista de dicts em vez de Pandas DataFrame.
        
        Agregação feita 100% em SQL.
        """
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            cur.execute('''
                SELECT 
                    "CATEGORIA",
                    SUM(COALESCE("QUANTIDADE", 0)) AS "QTD_VENDIDA",
                    SUM(COALESCE("PRECO_TOTAL", 0)) AS "RECEITA",
                    COUNT(DISTINCT "CODIGO") AS "PRODUTOS_UNICOS"
                FROM sales_items
                GROUP BY "CATEGORIA"
                ORDER BY "RECEITA" DESC
            ''')
            
            rows = cur.fetchall()
            return [dict(r) for r in rows]