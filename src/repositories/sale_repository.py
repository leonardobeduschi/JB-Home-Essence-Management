"""
Sale repository for CSV operations - FIXED for new structure.
"""

import pandas as pd
from typing import Optional, List, Dict
from datetime import datetime
from src.repositories.base_repository import BaseRepository
from src.models.sale import Sale, SALE_SCHEMA


class SaleRepository(BaseRepository):
    """Repository for sale data persistence using SQLite via BaseRepository."""

    def __init__(self, filepath: str = 'data/sales.csv'):
        super().__init__(filepath, SALE_SCHEMA)

    def exists(self, id_venda: str) -> bool:
        if not id_venda:
            return False
        with self.get_conn() as conn:
            cur = conn.execute('SELECT 1 FROM sales WHERE ID_VENDA = ? COLLATE NOCASE LIMIT 1', (id_venda,))
            return cur.fetchone() is not None

    def get_by_id(self, id_venda: str) -> Optional[Dict]:
        if not id_venda:
            return None
        with self.get_conn() as conn:
            cur = conn.execute('SELECT * FROM sales WHERE ID_VENDA = ? COLLATE NOCASE LIMIT 1', (id_venda,))
            row = cur.fetchone()
            return dict(row) if row else None

    def save(self, sale: Sale) -> bool:
        if self.exists(sale.id_venda):
            raise ValueError(f"Venda com ID '{sale.id_venda}' já existe")
        try:
            data = sale.to_dict()
            # Normalize date to ISO if possible, prefer YYYY-MM-DD in DB
            def to_iso_str(s):
                if not s:
                    return None
                s_str = str(s).strip()
                from datetime import datetime
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
        with self.get_conn() as conn:
            cur = conn.execute('SELECT * FROM sales WHERE ID_CLIENTE = ? COLLATE NOCASE', (id_cliente,))
            return [dict(r) for r in cur.fetchall()]

    def get_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        # Accept dates in dd/mm/YYYY or ISO YYYY-MM-DD and convert to ISO
        def to_iso(s):
            if not s:
                return None
            s_str = str(s).strip()
            for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
                try:
                    from datetime import datetime
                    return datetime.strptime(s_str, fmt).date().isoformat()
                except Exception:
                    continue
            return None

        s_iso = to_iso(start_date)
        e_iso = to_iso(end_date)
        if not s_iso or not e_iso:
            return []
        with self.get_conn() as conn:
            cur = conn.execute('SELECT * FROM sales WHERE DATA >= ? AND DATA <= ? ORDER BY DATA', (s_iso, e_iso))
            return [dict(r) for r in cur.fetchall()]

    def get_by_payment_method(self, meio: str) -> List[Dict]:
        with self.get_conn() as conn:
            cur = conn.execute('SELECT * FROM sales WHERE LOWER(MEIO) = LOWER(?)', (meio,))
            return [dict(r) for r in cur.fetchall()]

    def get_sales_summary(self) -> Dict:
        from src.repositories.sale_item_repository import SaleItemRepository
        with self.get_conn() as conn:
            cur = conn.execute('SELECT COUNT(*) as total, SUM(COALESCE(VALOR_TOTAL_VENDA,0)) as total_revenue, AVG(COALESCE(VALOR_TOTAL_VENDA,0)) as avg_sale FROM sales')
            row = cur.fetchone()
            total_sales = int(row['total'] or 0)
            total_revenue = float(row['total_revenue'] or 0)
            average_sale_value = float(row['avg_sale'] or 0)

        # Total items
        item_repo = SaleItemRepository()
        with item_repo.get_conn() as conn:
            cur = conn.execute('SELECT SUM(COALESCE(QUANTIDADE,0)) as total_items FROM sales_items')
            total_items = int(cur.fetchone()['total_items'] or 0)

        # By payment method
        with self.get_conn() as conn:
            cur = conn.execute("SELECT MEIO, SUM(COALESCE(VALOR_TOTAL_VENDA,0)) as total FROM sales GROUP BY MEIO")
            by_payment = {row['MEIO']: row['total'] for row in cur.fetchall()}

        # By category
        category_stats = item_repo.get_category_stats()
        by_category = {}
        if not category_stats.empty:
            by_category = category_stats.set_index('CATEGORIA')['RECEITA'].to_dict()

        return {
            'total_sales': total_sales,
            'total_revenue': total_revenue,
            'total_items_sold': total_items,
            'average_sale_value': average_sale_value,
            'by_payment_method': by_payment,
            'by_category': by_category
        }

    def get_top_clients(self, limit: int = 10) -> List[Dict]:
        with self.get_conn() as conn:
            cur = conn.execute('SELECT ID_CLIENTE, CLIENTE, COUNT(ID_VENDA) as NUM_COMPRAS, SUM(COALESCE(VALOR_TOTAL_VENDA,0)) as TOTAL_GASTO FROM sales GROUP BY ID_CLIENTE, CLIENTE ORDER BY TOTAL_GASTO DESC LIMIT ?', (limit,))
            return [dict(r) for r in cur.fetchall()]

    def delete(self, id_venda: str) -> bool:
        if not self.exists(id_venda):
            raise ValueError(f"Venda com ID '{id_venda}' não encontrada")
        try:
            return super().delete(id_venda)
        except Exception as e:
            raise Exception(f"Erro ao deletar venda: {str(e)}")

    def get_sale_with_items(self, id_venda: str) -> Dict:
        from src.repositories.sale_item_repository import SaleItemRepository
        header = self.get_by_id(id_venda)
        if not header:
            return None
        item_repo = SaleItemRepository()
        items = item_repo.get_by_sale_id(id_venda)
        return {
            'header': header,
            'items': items
        }

    def get_recent_sales(self, limit: int = 10) -> List[Dict]:
        with self.get_conn() as conn:
            cur = conn.execute('SELECT * FROM sales ORDER BY ID_VENDA DESC LIMIT ?', (limit,))
            sales = [dict(r) for r in cur.fetchall()]
            for s in sales:
                s['VALOR_TOTAL_VENDA'] = s.get('VALOR_TOTAL_VENDA', 0)
            return sales