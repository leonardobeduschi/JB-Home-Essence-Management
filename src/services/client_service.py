"""
Client service for business logic.

This module orchestrates client operations, validation, and business rules.
"""

from typing import Optional, List, Dict
from src.models.client import Client, TipoCliente, FaixaIdade
from src.repositories.client_repository import ClientRepository
from src.validators.client_validator import ClientValidator
from src.utils.id_generator import IDGenerator


class ClientService:
    """
    Service layer for client business logic.
    
    Handles client registration, updates, and search operations
    while enforcing business rules and validation.
    """
    
    def __init__(self, repository: Optional[ClientRepository] = None):
        """
        Initialize the client service.
        
        Args:
            repository: ClientRepository instance (creates new if None)
        """
        self.repository = repository or ClientRepository()
        self.validator = ClientValidator()
    
    def register_client(
        self,
        cliente: str,
        vendedor: str,
        tipo: str,
        idade: str = "",
        genero: str = "",
        profissao: str = "",
        cpf_cnpj: str = "",
        telefone: str = "",
        endereco: str = ""
    ) -> Client:
        """
        Register a new client in the system.
        
        Validates all inputs and enforces tipo-specific business rules.
        Auto-generates unique ID_CLIENTE.
        
        Args:
            cliente: Client name
            vendedor: Salesperson name
            tipo: Client type ('pessoa' or 'empresa')
            idade: Age range (required for pessoa)
            genero: Gender (required for pessoa)
            profissao: Profession (optional)
            cpf_cnpj: CPF or CNPJ (required for empresa, optional for pessoa)
            telefone: Phone number (optional)
            endereco: Address (required for empresa, optional for pessoa)
            
        Returns:
            Client instance if successful
            
        Raises:
            ValueError: If validation fails or business rules are violated
        """
        try:
            # Generate unique ID
            existing_ids = [c['ID_CLIENTE'] for c in self.repository.find_all()]
            id_cliente = IDGenerator.generate_client_id(existing_ids)
            
            # Normalize tipo
            tipo = str(tipo).lower().strip()
            
            # Validate and format CPF/CNPJ if provided
            if cpf_cnpj and str(cpf_cnpj).strip():
                is_valid, error_msg = self.validator.validate_cpf_cnpj(cpf_cnpj, tipo)
                if not is_valid:
                    raise ValueError(error_msg)
                
                # Format for storage
                if tipo == 'pessoa':
                    cpf_cnpj = self.validator.format_cpf(cpf_cnpj)
                elif tipo == 'empresa':
                    cpf_cnpj = self.validator.format_cnpj(cpf_cnpj)
            
            # Validate and format phone if provided
            if telefone and telefone.strip():
                if not self.validator.validate_phone(telefone):
                    raise ValueError("Formato de telefone inválido. Use (00) 00000-0000 ou (00) 0000-0000")
                telefone = self.validator.format_phone(telefone)
            
            # Create Client instance (validates automatically)
            client = Client(
                id_cliente=id_cliente,
                cliente=cliente,
                vendedor=vendedor,
                tipo=tipo,
                idade=idade,
                genero=genero,
                profissao=profissao,
                cpf_cnpj=cpf_cnpj,
                telefone=telefone,
                endereco=endereco
            )
            
            # Save to repository
            self.repository.save(client)
            
            print(f"✓ Cliente '{client.cliente}' cadastrado com sucesso!")
            print(f"  ID: {client.id_cliente}")
            print(f"  Tipo: {client.tipo}")
            print(f"  Vendedor: {client.vendedor}")
            if client.cpf_cnpj:
                print(f"  CPF/CNPJ: {client.cpf_cnpj}")
            if client.telefone:
                print(f"  Telefone: {client.telefone}")
            
            return client
            
        except ValueError as e:
            # Re-raise validation errors with context
            raise ValueError(f"Erro ao cadastrar cliente: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro inesperado ao cadastrar cliente: {str(e)}")
    
    def update_client_info(
        self,
        id_cliente: str,
        **updates
    ) -> bool:
        """
        Update client information.
        
        Args:
            id_cliente: Client ID to update
            **updates: Fields to update
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If client not found or validation fails
        """
        try:
            # Verify client exists
            client = self.repository.get_by_id(id_cliente)
            if not client:
                raise ValueError(f"Cliente '{id_cliente}' não encontrado")
            
            # Prepare updates dictionary
            valid_updates = {}
            
            # Map lowercase parameter names to uppercase field names
            field_mapping = {
                'cliente': 'CLIENTE',
                'vendedor': 'VENDEDOR',
                'tipo': 'TIPO',
                'idade': 'IDADE',
                'genero': 'GENERO',
                'profissao': 'PROFISSAO',
                'cpf_cnpj': 'CPF_CNPJ',
                'telefone': 'TELEFONE',
                'endereco': 'ENDERECO'
            }
            
            for key, value in updates.items():
                if key.lower() in field_mapping:
                    field_name = field_mapping[key.lower()]
                    
                    # Special handling for CPF/CNPJ
                    if field_name == 'CPF_CNPJ' and value:
                        tipo = updates.get('tipo', client['TIPO'])
                        is_valid, error_msg = self.validator.validate_cpf_cnpj(value, tipo)
                        if not is_valid:
                            raise ValueError(error_msg)
                        
                        # Format
                        if tipo == 'pessoa':
                            value = self.validator.format_cpf(value)
                        elif tipo == 'empresa':
                            value = self.validator.format_cnpj(value)
                    
                    # Special handling for phone
                    if field_name == 'TELEFONE' and value:
                        if not self.validator.validate_phone(value):
                            raise ValueError("Formato de telefone inválido")
                        value = self.validator.format_phone(value)
                    
                    valid_updates[field_name] = value
            
            if not valid_updates:
                raise ValueError("Nenhum campo válido para atualizar")
            
            # Update via repository
            self.repository.update(id_cliente, valid_updates)
            
            print(f"✓ Cliente '{id_cliente}' atualizado com sucesso!")
            return True
            
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Erro ao atualizar cliente: {str(e)}")
    
    def get_client(self, id_cliente: str) -> Optional[Dict]:
        """
        Retrieve client information by ID.
        
        Args:
            id_cliente: Client ID
            
        Returns:
            Client data dictionary or None if not found
        """
        return self.repository.get_by_id(id_cliente)
    
    def search_clients_by_name(self, nome: str) -> List[Dict]:
        """
        Search clients by name (partial match).
        
        Args:
            nome: Name to search for
            
        Returns:
            List of matching clients
        """
        return self.repository.get_by_name(nome)
    
    def search_client_by_cpf_cnpj(self, cpf_cnpj: str) -> Optional[Dict]:
        """
        Search client by CPF/CNPJ.
        
        Args:
            cpf_cnpj: CPF or CNPJ to search for
            
        Returns:
            Client data if found
        """
        return self.repository.get_by_cpf_cnpj(cpf_cnpj)
    
    def list_all_clients(self) -> List[Dict]:
        """
        List all clients in the system.
        
        Returns:
            List of all clients
        """
        return self.repository.find_all()
    
    def list_by_vendedor(self, vendedor: str) -> List[Dict]:
        """
        List clients assigned to a specific salesperson.
        
        Args:
            vendedor: Salesperson name
            
        Returns:
            List of clients
        """
        return self.repository.get_by_vendedor(vendedor)
    
    def list_by_tipo(self, tipo: str) -> List[Dict]:
        """
        List clients by type (pessoa or empresa).
        
        Args:
            tipo: Client type
            
        Returns:
            List of clients
        """
        if tipo.lower() not in ['pessoa', 'empresa']:
            raise ValueError("Tipo deve ser 'pessoa' ou 'empresa'")
        
        return self.repository.get_by_tipo(tipo)
    
    def get_client_statistics(self) -> Dict:
        """
        Get comprehensive client statistics.
        
        Returns:
            Dictionary with statistics
        """
        stats = self.repository.get_statistics()
        
        print("\n" + "="*60)
        print("  ESTATÍSTICAS DE CLIENTES")
        print("="*60)
        print(f"Total de clientes: {stats['total']}")
        print(f"  Pessoas físicas: {stats['pessoas']}")
        print(f"  Empresas: {stats['empresas']}")
        
        if stats['por_vendedor']:
            print("\nClientes por vendedor:")
            for vendedor, count in stats['por_vendedor'].items():
                print(f"  - {vendedor}: {count} cliente(s)")
        
        print("="*60)
        
        return stats
    
    def client_exists(self, id_cliente: str) -> bool:
        """
        Check if a client exists in the system.
        
        Args:
            id_cliente: Client ID
            
        Returns:
            True if client exists
        """
        return self.repository.exists(id_cliente)
    
    def get_available_age_ranges(self) -> List[str]:
        """
        Get list of valid age ranges for pessoas.
        
        Returns:
            List of age range strings
        """
        return [e.value for e in FaixaIdade]
    

    def delete_client(self, id_cliente: str) -> bool:
        """
        Delete a client from the system.
        
        Args:
            id_cliente: Client ID to delete
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If client not found
        """
        client = self.repository.get_by_id(id_cliente)
        if not client:
            raise ValueError(f"Cliente '{id_cliente}' não encontrado")
        
        self.repository.delete(id_cliente)
        print(f"✓ Cliente {id_cliente} excluído com sucesso")
        return True