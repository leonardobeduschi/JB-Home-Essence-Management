# ==================== client_repository.py ====================
"""
Client repository - PostgreSQL Compatible
"""

import pandas as pd
from typing import Optional, List, Dict
from src.repositories.base_repository import BaseRepository
from src.models.client import Client, CLIENT_SCHEMA


class ClientRepository(BaseRepository):
    """Repository for client data persistence."""

    def __init__(self, filepath: str = 'data/clients.csv'):
        super().__init__(filepath, CLIENT_SCHEMA, table_name='clients')

    def exists(self, id_cliente: str) -> bool:
        if not id_cliente:
            return False
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            if self.db_type == 'postgresql':
                cur.execute('SELECT 1 FROM clients WHERE "ID_CLIENTE" = %s LIMIT 1', (str(id_cliente),))
            else:
                cur.execute('SELECT 1 FROM clients WHERE "ID_CLIENTE" = ? LIMIT 1', (str(id_cliente),))
            return cur.fetchone() is not None

    def get_by_id(self, id_cliente: str) -> Optional[Dict]:
        if not id_cliente:
            return None
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            if self.db_type == 'postgresql':
                cur.execute('SELECT * FROM clients WHERE "ID_CLIENTE" = %s LIMIT 1', (str(id_cliente),))
            else:
                cur.execute('SELECT * FROM clients WHERE "ID_CLIENTE" = ? LIMIT 1', (str(id_cliente),))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_by_name(self, nome: str) -> List[Dict]:
        if not nome:
            return []
        pattern = f"%{nome}%"
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            if self.db_type == 'postgresql':
                cur.execute('SELECT * FROM clients WHERE UPPER("CLIENTE") LIKE UPPER(%s)', (pattern,))
            else:
                cur.execute('SELECT * FROM clients WHERE UPPER("CLIENTE") LIKE UPPER(?)', (pattern,))
            return [dict(r) for r in cur.fetchall()]

    def get_by_cpf_cnpj(self, cpf_cnpj: str) -> Optional[Dict]:
        if not cpf_cnpj:
            return None
        import re
        search_value = re.sub(r'[^0-9]', '', cpf_cnpj)
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            cur.execute('SELECT * FROM clients WHERE "CPF_CNPJ" IS NOT NULL')
            for row in cur.fetchall():
                db_value = re.sub(r'[^0-9]', '', str(row.get('CPF_CNPJ', '') or ''))
                if db_value == search_value:
                    return dict(row)
        return None

    def save(self, client: Client) -> bool:
        if self.exists(client.id_cliente):
            raise ValueError(f"Cliente com ID '{client.id_cliente}' já existe")
        if client.cpf_cnpj and client.cpf_cnpj.strip():
            existing = self.get_by_cpf_cnpj(client.cpf_cnpj)
            if existing:
                raise ValueError(
                    f"CPF/CNPJ '{client.cpf_cnpj}' já cadastrado para "
                    f"cliente '{existing['CLIENTE']}' (ID: {existing['ID_CLIENTE']})"
                )
        try:
            data = client.to_dict()
            self.insert(data)
            return True
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Erro ao salvar cliente: {str(e)}")

    def update(self, id_cliente: str, updates: Dict) -> bool:
        if not self.exists(id_cliente):
            raise ValueError(f"Cliente com ID '{id_cliente}' não encontrado")
        
        allowed_fields = ['CLIENTE', 'VENDEDOR', 'TIPO', 'IDADE', 'GENERO', 'PROFISSAO', 'CPF_CNPJ', 'TELEFONE', 'ENDERECO']
        to_update = {}
        
        try:
            current = self.get_by_id(id_cliente)
            if not current:
                raise ValueError(f"Cliente com ID '{id_cliente}' não encontrado")
            
            for field, value in updates.items():
                if field in allowed_fields:
                    to_update[field] = str(value).strip() if value else ""
            
            updated = {**current, **to_update}
            updated_tipo = str(updated.get('TIPO', '')).lower()
            
            if updated_tipo == 'empresa':
                if not str(updated.get('CPF_CNPJ', '')).strip():
                    raise ValueError("CPF/CNPJ é obrigatório para empresas")
                if not str(updated.get('ENDERECO', '')).strip():
                    raise ValueError("ENDEREÇO é obrigatório para empresas")
                updated['IDADE'] = ''
                updated['GENERO'] = ''
            elif updated_tipo == 'pessoa':
                if not str(updated.get('IDADE', '')).strip():
                    raise ValueError("IDADE é obrigatória para pessoas físicas")
                if not str(updated.get('GENERO', '')).strip():
                    raise ValueError("GÊNERO é obrigatório para pessoas físicas")
            
            return super().update(id_cliente, to_update)
        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"Erro ao atualizar cliente: {str(e)}")

    def get_by_vendedor(self, vendedor: str) -> List[Dict]:
        if not vendedor:
            return []
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            if self.db_type == 'postgresql':
                cur.execute('SELECT * FROM clients WHERE "VENDEDOR" = %s', (vendedor,))
            else:
                cur.execute('SELECT * FROM clients WHERE "VENDEDOR" = ? COLLATE NOCASE', (vendedor,))
            return [dict(r) for r in cur.fetchall()]

    def get_by_tipo(self, tipo: str) -> List[Dict]:
        if not tipo:
            return []
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            if self.db_type == 'postgresql':
                cur.execute('SELECT * FROM clients WHERE LOWER("TIPO") = LOWER(%s)', (tipo,))
            else:
                cur.execute('SELECT * FROM clients WHERE "TIPO" = ? COLLATE NOCASE', (tipo,))
            return [dict(r) for r in cur.fetchall()]

    def get_statistics(self) -> Dict:
        with self.get_conn() as conn:
            cur = self._get_cursor(conn)
            cur.execute('SELECT COUNT(*) as total FROM clients')
            total = cur.fetchone()['total']
            
            cur = self._get_cursor(conn)
            cur.execute("SELECT COUNT(*) as c FROM clients WHERE LOWER(\"TIPO\") = 'pessoa'")
            pessoas = cur.fetchone()['c']
            
            cur = self._get_cursor(conn)
            cur.execute("SELECT COUNT(*) as c FROM clients WHERE LOWER(\"TIPO\") = 'empresa'")
            empresas = cur.fetchone()['c']
            
            cur = self._get_cursor(conn)
            cur.execute('SELECT "VENDEDOR", COUNT(*) as cnt FROM clients GROUP BY "VENDEDOR"')
            por_vendedor = {row['VENDEDOR']: row['cnt'] for row in cur.fetchall()}
            
            return {
                'total': int(total),
                'pessoas': int(pessoas),
                'empresas': int(empresas),
                'por_vendedor': por_vendedor
            }

    def delete(self, id_cliente: str) -> bool:
        if not self.exists(id_cliente):
            raise ValueError(f"Cliente com ID '{id_cliente}' não encontrado")
        try:
            return super().delete(id_cliente)
        except Exception as e:
            raise Exception(f"Erro ao deletar cliente: {str(e)}")