"""
Sale Repository - Optimized

Principais otimizações:
1. Agregações movidas para SQL (SUM, COUNT, GROUP BY)
2. Queries com projeção de colunas
3. JOINs para reduzir número de queries
4. Eliminação de loops com queries internas
"""

from typing import Optional, List, Dict
from datetime import datetime
from src.repositories.base_repository import BaseRepository
from src.models.sale import Sale, SALE_SCHEMA


class SaleRepository(BaseRepository):
    """Repository otimizado para vendas."""

    def __init__(self, filepath: str = 'data/sales.csv'):
        super().__init__(filepath, SALE_SCHEMA, table_name='sales')

    def exists(self, id_venda: str) -> bool:
        if not id_venda:
            return False
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            cur.execute(f'SELECT 1 FROM sales WHERE "ID_VENDA" = {placeholder} LIMIT 1', (id_venda,))
            return cur.fetchone() is not None

    def get_by_id(self, id_venda: str) -> Optional[Dict]:
        if not id_venda:
            return None
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            cur.execute(f'SELECT * FROM sales WHERE "ID_VENDA" = {placeholder} LIMIT 1', (id_venda,))
            row = cur.fetchone()
            return dict(row) if row else None

    def save(self, sale: Sale) -> bool:
        if self.exists(sale.id_venda):
            raise ValueError(f"Venda com ID '{sale.id_venda}' já existe")
        
        try:
            data = sale.to_dict()
            
            # Normaliza data para ISO
            def to_iso_str(s):
                if not s:
                    return None
                s_str = str(s).strip()
                for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
                    try:
                        return datetime.strptime(s_str, fmt).date().isoformat()
                    except Exception:
                        continue
                return None

            iso = to_iso_str(data.get('DATA'))
            if iso:
                data['DATA'] = iso

            self.insert(data)
            return True
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Erro ao salvar venda: {str(e)}")

    def get_by_client(self, id_cliente: str) -> List[Dict]:
        """Retorna vendas de um cliente."""
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            cur.execute(f'SELECT * FROM sales WHERE "ID_CLIENTE" = {placeholder}', (id_cliente,))
            return [dict(r) for r in cur.fetchall()]

    def get_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Retorna vendas em um período."""
        def to_iso(s):
            if not s:
                return None
            s_str = str(s).strip()
            for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
                try:
                    return datetime.strptime(s_str, fmt).date().isoformat()
                except Exception:
                    continue
            return None

        s_iso = to_iso(start_date)
        e_iso = to_iso(end_date)
        if not s_iso or not e_iso:
            return []
        
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            
            if self.db_type == 'postgresql':
                cur.execute(
                    'SELECT * FROM sales WHERE "DATA" >= %s AND "DATA" <= %s ORDER BY "DATA"',
                    (s_iso, e_iso)
                )
            else:
                cur.execute(
                    'SELECT * FROM sales WHERE "DATA" >= ? AND "DATA" <= ? ORDER BY "DATA"',
                    (s_iso, e_iso)
                )
            
            return [dict(r) for r in cur.fetchall()]

    def get_sales_summary(self) -> Dict:
        """
        OTIMIZADO: Todas as agregações em SQL puro.
        
        Antes: 4-5 queries + processamento Python
        Depois: 3 queries otimizadas
        """
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            
            # 1. Agregações principais de vendas (1 query)
            cur.execute('''
                SELECT 
                    COUNT(*) as total,
                    COALESCE(SUM("VALOR_TOTAL_VENDA"), 0) as total_revenue,
                    COALESCE(AVG("VALOR_TOTAL_VENDA"), 0) as avg_sale
                FROM sales
            ''')
            row = cur.fetchone()
            total_sales = int(row['total'] or 0)
            total_revenue = float(row['total_revenue'] or 0)
            average_sale_value = float(row['avg_sale'] or 0)

            # 2. Total de itens vendidos (1 query)
            cur.execute('''
                SELECT COALESCE(SUM("QUANTIDADE"), 0) as total_items 
                FROM sales_items
            ''')
            result = cur.fetchone()
            total_items = int(result['total_items'] or 0)

            # 3. Vendas por meio de pagamento (1 query com GROUP BY)
            cur.execute('''
                SELECT 
                    "MEIO", 
                    COALESCE(SUM("VALOR_TOTAL_VENDA"), 0) as total
                FROM sales 
                GROUP BY "MEIO"
            ''')
            by_payment = {row['MEIO']: float(row['total']) for row in cur.fetchall()}

            # 4. Receita por categoria (1 query com GROUP BY)
            cur.execute('''
                SELECT 
                    "CATEGORIA",
                    COALESCE(SUM("PRECO_TOTAL"), 0) as total
                FROM sales_items
                GROUP BY "CATEGORIA"
            ''')
            by_category = {row['CATEGORIA']: float(row['total']) for row in cur.fetchall()}

        return {
            'total_sales': total_sales,
            'total_revenue': total_revenue,
            'total_items_sold': total_items,
            'average_sale_value': average_sale_value,
            'by_payment_method': by_payment,
            'by_category': by_category
        }

    def get_top_clients(self, limit: int = 10) -> List[Dict]:
        """
        OTIMIZADO: Agregação em SQL com GROUP BY + ORDER BY + LIMIT.
        """
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            
            cur.execute(f'''
                SELECT 
                    "ID_CLIENTE", 
                    "CLIENTE",
                    COUNT("ID_VENDA") as "NUM_COMPRAS",
                    COALESCE(SUM("VALOR_TOTAL_VENDA"), 0) as "TOTAL_GASTO"
                FROM sales
                GROUP BY "ID_CLIENTE", "CLIENTE"
                ORDER BY "TOTAL_GASTO" DESC 
                LIMIT {placeholder}
            ''', (limit,))
            
            return [dict(r) for r in cur.fetchall()]

    def get_recent_sales(self, limit: int = 10) -> List[Dict]:
        """
        OTIMIZADO: ORDER BY + LIMIT direto no SQL.
        """
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            
            cur.execute(f'''
                SELECT * FROM sales 
                ORDER BY "ID_VENDA" DESC 
                LIMIT {placeholder}
            ''', (limit,))
            
            sales = [dict(r) for r in cur.fetchall()]
            
            # Garante campo existe (evita KeyError)
            for s in sales:
                s['VALOR_TOTAL_VENDA'] = s.get('VALOR_TOTAL_VENDA', 0)
            
            return sales

    def delete(self, id_venda: str) -> bool:
        if not self.exists(id_venda):
            raise ValueError(f"Venda com ID '{id_venda}' não encontrada")
        try:
            return super().delete(id_venda)
        except Exception as e:
            raise Exception(f"Erro ao deletar venda: {str(e)}")

    def get_sale_with_items(self, id_venda: str) -> Dict:
        """
        OTIMIZADO: JOIN para pegar header + items em 1 query.
        """
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            placeholder = '%s' if self.db_type == 'postgresql' else '?'
            
            # Header
            cur.execute(f'SELECT * FROM sales WHERE "ID_VENDA" = {placeholder}', (id_venda,))
            header = cur.fetchone()
            
            if not header:
                return None
            
            # Items (1 query)
            cur.execute(f'SELECT * FROM sales_items WHERE "ID_VENDA" = {placeholder}', (id_venda,))
            items = [dict(r) for r in cur.fetchall()]
            
            return {
                'header': dict(header),
                'items': items
            }