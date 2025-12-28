"""
Quick example of client module usage.

This demonstrates the basic operations for both pessoa and empresa types.
"""

from src.services.client_service import ClientService


def main():
    """Simple example workflow."""
    print("="*60)
    print("  Client Module - Quick Example")
    print("="*60)
    
    # Initialize service
    service = ClientService()
    
    # === PESSOA (Individual) Example ===
    print("\n" + "="*60)
    print("  EXEMPLO 1: Cadastro de Pessoa Física")
    print("="*60)
    
    print("\n1. Registering an individual client (pessoa)...")
    try:
        pessoa = service.register_client(
            cliente="Maria Oliveira",
            vendedor="Carlos Souza",
            tipo="pessoa",
            idade="25-34",           # Required for pessoa
            genero="Feminino",        # Required for pessoa
            profissao="Designer",
            cpf_cnpj="529.982.247-25",  # Optional for pessoa
            telefone="(48) 99876-5432",
            endereco="Rua das Acácias, 456"  # Optional for pessoa
        )
    except ValueError as e:
        print(f"Note: {e}")
    
    # === EMPRESA (Company) Example ===
    print("\n" + "="*60)
    print("  EXEMPLO 2: Cadastro de Empresa")
    print("="*60)
    
    print("\n2. Registering a company client (empresa)...")
    try:
        empresa = service.register_client(
            cliente="Spa Zen Relaxamento Ltda",
            vendedor="Carlos Souza",
            tipo="empresa",
            cpf_cnpj="34.274.233/0001-03",  # Required for empresa
            telefone="(48) 3333-4444",
            endereco="Av. Atlântica, 2000 - Centro"  # Required for empresa
            # Note: idade and genero are NOT provided (will be empty)
        )
    except ValueError as e:
        print(f"Note: {e}")
    
    # === Listing Clients ===
    print("\n" + "="*60)
    print("  EXEMPLO 3: Listagem de Clientes")
    print("="*60)
    
    print("\n3. Listing all clients:")
    all_clients = service.list_all_clients()
    print(f"   Total clients: {len(all_clients)}")
    
    for c in all_clients:
        print(f"\n   ID: {c['ID_CLIENTE']}")
        print(f"   Nome: {c['CLIENTE']}")
        print(f"   Tipo: {c['TIPO'].upper()}")
        print(f"   Vendedor: {c['VENDEDOR']}")
        
        if c['TIPO'] == 'pessoa':
            print(f"   Idade: {c['IDADE']}")
            print(f"   Gênero: {c['GENERO']}")
            if c['CPF_CNPJ']:
                print(f"   CPF: {c['CPF_CNPJ']}")
        else:  # empresa
            print(f"   CNPJ: {c['CPF_CNPJ']}")
            print(f"   Endereço: {c['ENDERECO']}")
        
        if c['TELEFONE']:
            print(f"   Telefone: {c['TELEFONE']}")
    
    # === Search Functionality ===
    print("\n" + "="*60)
    print("  EXEMPLO 4: Busca de Clientes")
    print("="*60)
    
    print("\n4. Searching by name (partial match)...")
    results = service.search_clients_by_name("Maria")
    if results:
        print(f"   Found {len(results)} client(s):")
        for r in results:
            print(f"   - {r['CLIENTE']} ({r['ID_CLIENTE']})")
    
    print("\n5. Getting client by ID...")
    client = service.get_client("CLI001")
    if client:
        print(f"   ✓ Found: {client['CLIENTE']}")
        print(f"     Type: {client['TIPO']}")
        print(f"     Salesperson: {client['VENDEDOR']}")
    
    # === Statistics ===
    print("\n" + "="*60)
    print("  EXEMPLO 5: Estatísticas")
    print("="*60)
    
    print("\n6. Client statistics:")
    stats = service.get_client_statistics()
    
    # === List by Type ===
    print("\n" + "="*60)
    print("  EXEMPLO 6: Filtros por Tipo")
    print("="*60)
    
    print("\n7. Listing only individual clients (pessoas):")
    pessoas = service.list_by_tipo("pessoa")
    for p in pessoas:
        print(f"   - {p['CLIENTE']} | Idade: {p['IDADE']} | Gênero: {p['GENERO']}")
    
    print("\n8. Listing only companies (empresas):")
    empresas = service.list_by_tipo("empresa")
    for e in empresas:
        print(f"   - {e['CLIENTE']} | CNPJ: {e['CPF_CNPJ']}")
    
    # === Update Example ===
    print("\n" + "="*60)
    print("  EXEMPLO 7: Atualização de Dados")
    print("="*60)
    
    print("\n9. Updating client information...")
    try:
        if all_clients:
            first_client_id = all_clients[0]['ID_CLIENTE']
            service.update_client_info(
                first_client_id,
                telefone="(48) 99999-0000",
                profissao="Gerente"
            )
            
            updated = service.get_client(first_client_id)
            print(f"   Updated client: {updated['CLIENTE']}")
            print(f"   New phone: {updated['TELEFONE']}")
            if updated['PROFISSAO']:
                print(f"   New profession: {updated['PROFISSAO']}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # === Available Age Ranges ===
    print("\n" + "="*60)
    print("  EXEMPLO 8: Faixas Etárias Disponíveis")
    print("="*60)
    
    print("\n10. Valid age ranges for pessoas:")
    age_ranges = service.get_available_age_ranges()
    for age in age_ranges:
        print(f"   - {age}")
    
    print("\n" + "="*60)
    print("✓ Examples completed successfully!")
    print("\nKey Concepts Demonstrated:")
    print("  1. Pessoa requires: IDADE + GENERO")
    print("  2. Empresa requires: CPF_CNPJ + ENDERECO")
    print("  3. Empresa cannot have IDADE or GENERO")
    print("  4. Auto-generated IDs (CLI001, CLI002, ...)")
    print("  5. CPF/CNPJ validation and formatting")
    print("  6. Phone number formatting")
    print("  7. Search and filter capabilities")
    print("\nCheck 'data/clients.csv' to see the persisted data.")
    print("="*60)


if __name__ == "__main__":
    main()