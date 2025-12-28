"""
Client repository for CSV operations.

This module handles all CRUD operations for clients in the CSV file.
"""

import pandas as pd
from typing import Optional, List, Dict
from src.repositories.base_repository import BaseRepository
from src.models.client import Client, CLIENT_SCHEMA


class ClientRepository(BaseRepository):
    """
    Repository for client data persistence.
    
    Handles all CSV operations for clients including create, read,
    update, and search operations.
    """
    
    def __init__(self, filepath: str = 'data/clients.csv'):
        """
        Initialize the client repository.
        
        Args:
            filepath: Path to the clients CSV file
        """
        super().__init__(filepath, CLIENT_SCHEMA)
    
    def exists(self, id_cliente: str) -> bool:
        """
        Check if a client with given ID_CLIENTE exists.
        
        Args:
            id_cliente: Client ID to check
            
        Returns:
            True if client exists, False otherwise
        """
        df = self._read_csv()
        # Converte ID_CLIENTE para string antes de comparar
        return str(id_cliente) in df['ID_CLIENTE'].astype(str).values
    
    def get_by_id(self, id_cliente: str) -> Optional[Dict]:
        """
        Retrieve a client by their ID.
        
        Args:
            id_cliente: Client ID to search for
            
        Returns:
            Dictionary with client data if found, None otherwise
        """
        df = self._read_csv()
        
        # Busca por ID exato (não case-sensitive por ser número)
        mask = df['ID_CLIENTE'].astype(str) == str(id_cliente)
        result = df[mask]
        
        if result.empty:
            return None
        
        return result.iloc[0].to_dict()
    
    def get_by_name(self, nome: str) -> List[Dict]:
        """
        Search clients by name (partial match).
        
        Args:
            nome: Client name to search for (case-insensitive)
            
        Returns:
            List of matching clients
        """
        df = self._read_csv()
        
        # Case-insensitive partial match
        mask = df['CLIENTE'].str.upper().str.contains(nome.upper(), na=False)
        result = df[mask]
        
        return result.to_dict('records')
    
    def get_by_cpf_cnpj(self, cpf_cnpj: str) -> Optional[Dict]:
        """
        Retrieve a client by CPF/CNPJ.
        
        Args:
            cpf_cnpj: CPF or CNPJ to search for
            
        Returns:
            Dictionary with client data if found, None otherwise
        """
        df = self._read_csv()
        
        # Remove formatting for comparison
        import re
        search_value = re.sub(r'[^0-9]', '', cpf_cnpj)
        
        # Search in CPF_CNPJ column
        for idx, row in df.iterrows():
            db_value = re.sub(r'[^0-9]', '', str(row['CPF_CNPJ']))
            if db_value == search_value:
                return row.to_dict()
        
        return None
    
    def save(self, client: Client) -> bool:
        """
        Save a new client to the CSV.
        
        Args:
            client: Client instance to save
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If client with same ID_CLIENTE already exists
        """
        # Check for duplicate ID_CLIENTE
        if self.exists(client.id_cliente):
            raise ValueError(f"Cliente com ID '{client.id_cliente}' já existe")
        
        # Check for duplicate CPF/CNPJ if provided
        if client.cpf_cnpj and client.cpf_cnpj.strip():
            existing = self.get_by_cpf_cnpj(client.cpf_cnpj)
            if existing:
                raise ValueError(
                    f"CPF/CNPJ '{client.cpf_cnpj}' já cadastrado para "
                    f"cliente '{existing['CLIENTE']}' (ID: {existing['ID_CLIENTE']})"
                )
        
        try:
            df = self._read_csv()
            
            # Convert client to dict and append
            new_row = pd.DataFrame([client.to_dict()])
            df = pd.concat([df, new_row], ignore_index=True)
            
            # Save to CSV
            self._write_csv(df)
            return True
            
        except Exception as e:
            raise Exception(f"Erro ao salvar cliente: {str(e)}")
    
    def update(self, id_cliente: str, updates: Dict) -> bool:
        """
        Update an existing client's information.
        
        Args:
            id_cliente: Client ID to update
            updates: Dictionary with fields to update
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If client not found or validation fails
        """
        if not self.exists(id_cliente):
            raise ValueError(f"Cliente com ID '{id_cliente}' não encontrado")
        
        try:
            df = self._read_csv()
            
            # Find the client row
            mask = df['ID_CLIENTE'].astype(str) == str(id_cliente)
            idx = df[mask].index[0]
            
            # Get current tipo to validate updates
            current_tipo = str(df.at[idx, 'TIPO']).lower()
            
            # Apply updates (only allowed fields, excluding ID_CLIENTE)
            allowed_fields = [
                'CLIENTE', 'VENDEDOR', 'TIPO', 'IDADE', 'GENERO',
                'PROFISSAO', 'CPF_CNPJ', 'TELEFONE', 'ENDERECO'
            ]
            
            for field, value in updates.items():
                if field in allowed_fields:
                    df.at[idx, field] = str(value).strip() if value else ""
            
            # Re-validate tipo-specific rules after update
            updated_tipo = str(df.at[idx, 'TIPO']).lower()
            
            if updated_tipo == 'empresa':
                # Ensure CPF_CNPJ and ENDERECO are not empty
                if not str(df.at[idx, 'CPF_CNPJ']).strip():
                    raise ValueError("CPF/CNPJ é obrigatório para empresas")
                if not str(df.at[idx, 'ENDERECO']).strip():
                    raise ValueError("ENDEREÇO é obrigatório para empresas")
                # Clear IDADE and GENERO
                df.at[idx, 'IDADE'] = ""
                df.at[idx, 'GENERO'] = ""
            
            elif updated_tipo == 'pessoa':
                # Ensure IDADE and GENERO are not empty
                if not str(df.at[idx, 'IDADE']).strip():
                    raise ValueError("IDADE é obrigatória para pessoas físicas")
                if not str(df.at[idx, 'GENERO']).strip():
                    raise ValueError("GÊNERO é obrigatório para pessoas físicas")
            
            # Save to CSV
            self._write_csv(df)
            return True
            
        except Exception as e:
            raise Exception(f"Erro ao atualizar cliente: {str(e)}")
    
    def get_by_vendedor(self, vendedor: str) -> List[Dict]:
        """
        Get all clients assigned to a specific salesperson.
        
        Args:
            vendedor: Salesperson name
            
        Returns:
            List of clients
        """
        df = self._read_csv()
        
        # Case-insensitive search
        mask = df['VENDEDOR'].str.upper() == vendedor.upper()
        result = df[mask]
        
        return result.to_dict('records')
    
    def get_by_tipo(self, tipo: str) -> List[Dict]:
        """
        Get all clients of a specific type.
        
        Args:
            tipo: Client type ('pessoa' or 'empresa')
            
        Returns:
            List of clients
        """
        df = self._read_csv()
        
        # Case-insensitive search
        mask = df['TIPO'].str.upper() == tipo.upper()
        result = df[mask]
        
        return result.to_dict('records')
    
    def get_statistics(self) -> Dict:
        """
        Get client statistics.
        
        Returns:
            Dictionary with statistics (total, by tipo, by vendedor)
        """
        df = self._read_csv()
        
        if df.empty:
            return {
                'total': 0,
                'pessoas': 0,
                'empresas': 0,
                'por_vendedor': {}
            }
        
        stats = {
            'total': len(df),
            'pessoas': len(df[df['TIPO'].str.lower() == 'pessoa']),
            'empresas': len(df[df['TIPO'].str.lower() == 'empresa']),
            'por_vendedor': df['VENDEDOR'].value_counts().to_dict()
        }
        
        return stats
    
    def delete(self, id_cliente: str) -> bool:
        """
        Delete a client from the CSV.
        
        Args:
            id_cliente: Client ID to delete
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If client not found
        """
        if not self.exists(id_cliente):
            raise ValueError(f"Cliente com ID '{id_cliente}' não encontrado")
        
        try:
            df = self._read_csv()
            
            # Remove the client
            mask = df['ID_CLIENTE'].astype(str) != str(id_cliente)
            df = df[mask]
            
            # Save to CSV
            self._write_csv(df)
            return True
            
        except Exception as e:
            raise Exception(f"Erro ao deletar cliente: {str(e)}")