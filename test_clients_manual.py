"""
Manual testing script for Client module.

Run this script to test client registration with tipo-specific validation,
CPF/CNPJ validation, and all business rules.

Usage:
    python test_clients_manual.py
"""

from src.services.client_service import ClientService


def print_separator(title: str = ""):
    """Print a visual separator."""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print('='*60)
    else:
        print("-" * 60)


def test_pessoa_registration():
    """Test pessoa (individual) client registration."""
    print_separator("TEST 1: Pessoa Registration")
    
    service = ClientService()
    
    # Test 1: Valid pessoa
    print("\n1. Registering valid pessoa...")
    try:
        service.register_client(
            cliente="João Silva",
            vendedor="Maria Santos",
            tipo="pessoa",
            idade="25-34",
            genero="Masculino",
            profissao="Engenheiro",
            cpf_cnpj="123.456.789-09",  # Valid CPF format
            telefone="(11) 98765-4321",
            endereco="Rua das Flores, 123"
        )
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Pessoa without mandatory IDADE
    print("\n2. Testing pessoa without IDADE (should fail)...")
    try:
        service.register_client(
            cliente="Ana Costa",
            vendedor="Maria Santos",
            tipo="pessoa",
            idade="",  # Missing required field
            genero="Feminino"
        )
        print("✗ ERROR: Accepted pessoa without IDADE")
    except ValueError as e:
        print(f"✓ Correctly rejected: {e}")
    
    # Test 3: Pessoa without mandatory GENERO
    print("\n3. Testing pessoa without GENERO (should fail)...")
    try:
        service.register_client(
            cliente="Carlos Mendes",
            vendedor="Maria Santos",
            tipo="pessoa",
            idade="35-44",
            genero=""  # Missing required field
        )
        print("✗ ERROR: Accepted pessoa without GENERO")
    except ValueError as e:
        print(f"✓ Correctly rejected: {e}")
    
    # Test 4: Invalid age range
    print("\n4. Testing invalid age range...")
    try:
        service.register_client(
            cliente="Pedro Alves",
            vendedor="Maria Santos",
            tipo="pessoa",
            idade="20-30",  # Invalid format
            genero="Masculino"
        )
        print("✗ ERROR: Accepted invalid age range")
    except ValueError as e:
        print(f"✓ Correctly rejected: {e}")


def test_empresa_registration():
    """Test empresa (company) client registration."""
    print_separator("TEST 2: Empresa Registration")
    
    service = ClientService()
    
    # Test 1: Valid empresa
    print("\n1. Registering valid empresa...")
    try:
        service.register_client(
            cliente="Tech Solutions Ltda",
            vendedor="João Pereira",
            tipo="empresa",
            cpf_cnpj="12.345.678/0001-90",  # Valid CNPJ format
            telefone="(11) 3456-7890",
            endereco="Av. Paulista, 1000"
        )
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Empresa without CPF_CNPJ
    print("\n2. Testing empresa without CPF/CNPJ (should fail)...")
    try:
        service.register_client(
            cliente="Commerce Inc",
            vendedor="João Pereira",
            tipo="empresa",
            cpf_cnpj="",  # Missing required field
            endereco="Rua do Comércio, 500"
        )
        print("✗ ERROR: Accepted empresa without CPF/CNPJ")
    except ValueError as e:
        print(f"✓ Correctly rejected: {e}")
    
    # Test 3: Empresa without ENDERECO
    print("\n3. Testing empresa without ENDERECO (should fail)...")
    try:
        service.register_client(
            cliente="Business Corp",
            vendedor="João Pereira",
            tipo="empresa",
            cpf_cnpj="98.765.432/0001-10",
            endereco=""  # Missing required field
        )
        print("✗ ERROR: Accepted empresa without ENDERECO")
    except ValueError as e:
        print(f"✓ Correctly rejected: {e}")
    
    # Test 4: Empresa with IDADE/GENERO (should be cleared)
    print("\n4. Testing empresa with IDADE/GENERO (should be auto-cleared)...")
    try:
        client = service.register_client(
            cliente="Clean Data Ltda",
            vendedor="João Pereira",
            tipo="empresa",
            idade="25-34",  # Will be cleared
            genero="N/A",    # Will be cleared
            cpf_cnpj="11.222.333/0001-44",
            endereco="Rua Limpa, 100"
        )
        
        # Verify they were cleared
        saved = service.get_client(client.id_cliente)
        if saved['IDADE'] == "" and saved['GENERO'] == "":
            print("✓ IDADE and GENERO correctly cleared for empresa")
        else:
            print("✗ ERROR: IDADE/GENERO not cleared")
    except Exception as e:
        print(f"✗ Error: {e}")


def test_cpf_cnpj_validation():
    """Test CPF/CNPJ validation."""
    print_separator("TEST 3: CPF/CNPJ Validation")
    
    service = ClientService()
    
    # Test 1: Invalid CPF
    print("\n1. Testing invalid CPF...")
    try:
        service.register_client(
            cliente="Invalid CPF",
            vendedor="Test",
            tipo="pessoa",
            idade="25-34",
            genero="Masculino",
            cpf_cnpj="111.111.111-11"  # Invalid CPF (all same digits)
        )
        print("✗ ERROR: Accepted invalid CPF")
    except ValueError as e:
        print(f"✓ Correctly rejected: {e}")
    
    # Test 2: Invalid CNPJ
    print("\n2. Testing invalid CNPJ...")
    try:
        service.register_client(
            cliente="Invalid CNPJ",
            vendedor="Test",
            tipo="empresa",
            cpf_cnpj="00.000.000/0000-00",  # Invalid CNPJ
            endereco="Test Street"
        )
        print("✗ ERROR: Accepted invalid CNPJ")
    except ValueError as e:
        print(f"✓ Correctly rejected: {e}")
    
    # Test 3: CPF with wrong length
    print("\n3. Testing CPF with wrong length...")
    try:
        service.register_client(
            cliente="Wrong Length",
            vendedor="Test",
            tipo="pessoa",
            idade="25-34",
            genero="Masculino",
            cpf_cnpj="123.456.78"  # Too short
        )
        print("✗ ERROR: Accepted CPF with wrong length")
    except ValueError as e:
        print(f"✓ Correctly rejected: {e}")


def test_duplicate_detection():
    """Test duplicate client detection."""
    print_separator("TEST 4: Duplicate Detection")
    
    service = ClientService()
    
    # Register a client first
    print("\n1. Registering initial client...")
    try:
        service.register_client(
            cliente="Unique Client",
            vendedor="Test",
            tipo="pessoa",
            idade="25-34",
            genero="Masculino",
            cpf_cnpj="529.982.247-25"  # Valid CPF
        )
    except Exception as e:
        print(f"Note: {e}")
    
    # Try to register with same CPF
    print("\n2. Testing duplicate CPF detection...")
    try:
        service.register_client(
            cliente="Another Name",
            vendedor="Test",
            tipo="pessoa",
            idade="35-44",
            genero="Feminino",
            cpf_cnpj="529.982.247-25"  # Same CPF
        )
        print("✗ ERROR: Accepted duplicate CPF")
    except ValueError as e:
        print(f"✓ Correctly rejected duplicate: {e}")


def test_client_listing():
    """Test client listing functionality."""
    print_separator("TEST 5: Client Listing")
    
    service = ClientService()
    
    print("\n1. Listing all clients:")
    clients = service.list_all_clients()
    
    if clients:
        print(f"\nTotal clients: {len(clients)}\n")
        for c in clients:
            print(f"ID: {c['ID_CLIENTE']}")
            print(f"Nome: {c['CLIENTE']}")
            print(f"Tipo: {c['TIPO']}")
            print(f"Vendedor: {c['VENDEDOR']}")
            
            if c['TIPO'] == 'pessoa':
                print(f"Idade: {c['IDADE']}")
                print(f"Gênero: {c['GENERO']}")
            else:
                print(f"CPF/CNPJ: {c['CPF_CNPJ']}")
                print(f"Endereço: {c['ENDERECO']}")
            
            print_separator()
    else:
        print("No clients found")
    
    # List by tipo
    print("\n2. Listing only pessoas:")
    pessoas = service.list_by_tipo("pessoa")
    print(f"Total pessoas: {len(pessoas)}")
    for p in pessoas:
        print(f"  - {p['CLIENTE']} (Idade: {p['IDADE']}, Gênero: {p['GENERO']})")
    
    print("\n3. Listing only empresas:")
    empresas = service.list_by_tipo("empresa")
    print(f"Total empresas: {len(empresas)}")
    for e in empresas:
        print(f"  - {e['CLIENTE']} (CNPJ: {e['CPF_CNPJ']})")


def test_client_search():
    """Test client search functionality."""
    print_separator("TEST 6: Client Search")
    
    service = ClientService()
    
    # Search by name
    print("\n1. Searching clients by name (partial match)...")
    results = service.search_clients_by_name("Silva")
    print(f"Found {len(results)} client(s) with 'Silva' in name:")
    for r in results:
        print(f"  - {r['CLIENTE']} ({r['ID_CLIENTE']})")
    
    # Search by ID
    print("\n2. Getting client by ID...")
    client = service.get_client("CLI001")
    if client:
        print(f"✓ Found: {client['CLIENTE']}")
    else:
        print("Client CLI001 not found")
    
    # Search by CPF/CNPJ
    print("\n3. Searching by CPF/CNPJ...")
    client = service.search_client_by_cpf_cnpj("529.982.247-25")
    if client:
        print(f"✓ Found: {client['CLIENTE']} ({client['ID_CLIENTE']})")
    else:
        print("No client found with that CPF")


def test_client_updates():
    """Test client update functionality."""
    print_separator("TEST 7: Client Updates")
    
    service = ClientService()
    
    print("\n1. Updating client information...")
    try:
        # Update a pessoa
        service.update_client_info(
            "CLI001",
            telefone="(11) 99999-8888",
            profissao="Arquiteto"
        )
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n2. Verifying update...")
    client = service.get_client("CLI001")
    if client:
        print(f"  Nome: {client['CLIENTE']}")
        print(f"  Telefone: {client['TELEFONE']}")
        print(f"  Profissão: {client['PROFISSAO']}")


def test_client_statistics():
    """Test client statistics."""
    print_separator("TEST 8: Client Statistics")
    
    service = ClientService()
    
    print("\n1. Getting comprehensive statistics:")
    stats = service.get_client_statistics()


def test_age_ranges():
    """Test age range validation."""
    print_separator("TEST 9: Age Range Validation")
    
    service = ClientService()
    
    print("\n1. Available age ranges:")
    ranges = service.get_available_age_ranges()
    for r in ranges:
        print(f"  - {r}")
    
    print("\n2. Testing each valid age range...")
    for i, age_range in enumerate(ranges[:3], 1):  # Test first 3
        try:
            service.register_client(
                cliente=f"Test Age {i}",
                vendedor="Test",
                tipo="pessoa",
                idade=age_range,
                genero="Masculino"
            )
            print(f"  ✓ Age range '{age_range}' accepted")
        except Exception as e:
            print(f"  ✗ Error with '{age_range}': {e}")


def test_phone_formatting():
    """Test phone number formatting."""
    print_separator("TEST 10: Phone Formatting")
    
    service = ClientService()
    
    print("\n1. Testing phone number formatting...")
    test_phones = [
        ("11987654321", "Mobile"),
        ("1134567890", "Landline"),
        ("(11) 98765-4321", "Pre-formatted mobile"),
        ("(11) 3456-7890", "Pre-formatted landline")
    ]
    
    for phone, desc in test_phones:
        try:
            client = service.register_client(
                cliente=f"Phone Test {desc}",
                vendedor="Test",
                tipo="pessoa",
                idade="25-34",
                genero="Masculino",
                telefone=phone
            )
            saved = service.get_client(client.id_cliente)
            print(f"  ✓ {desc}: {phone} → {saved['TELEFONE']}")
        except Exception as e:
            print(f"  ✗ {desc} failed: {e}")


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "="*60)
    print("  CLIENT MODULE - MANUAL TEST SUITE")
    print("="*60)
    print("\nThis will test all client functionality including")
    print("tipo-specific validation (pessoa vs empresa).")
    
    input("\nPress ENTER to start tests...")
    
    try:
        test_pessoa_registration()
        test_empresa_registration()
        test_cpf_cnpj_validation()
        test_duplicate_detection()
        test_client_listing()
        test_client_search()
        test_client_updates()
        test_client_statistics()
        test_age_ranges()
        test_phone_formatting()
        
        print_separator("TEST SUITE COMPLETED")
        print("\n✓ All tests completed!")
        print("\nNext steps:")
        print("1. Check data/clients.csv to verify data persistence")
        print("2. Run this script again to verify data was saved correctly")
        print("3. Review the console output above for any errors")
        print("\nExpected CSV schema:")
        print("ID_CLIENTE,CLIENTE,VENDEDOR,TIPO,IDADE,GENERO,PROFISSAO,CPF_CNPJ,TELEFONE,ENDERECO")
        
    except Exception as e:
        print(f"\n✗ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()