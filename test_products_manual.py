"""
Manual testing script for Product module.

Run this script to test product registration, updates, and stock management.
This demonstrates all functionality before building the UI.

Usage:
    python test_products_manual.py
"""

from src.services.product_service import ProductService


def print_separator(title: str = ""):
    """Print a visual separator."""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print('='*60)
    else:
        print("-" * 60)


def test_product_registration():
    """Test product registration functionality."""
    print_separator("TEST 1: Product Registration")
    
    service = ProductService()
    
    # Test 1: Register valid products
    print("\n1. Registering valid products...")
    try:
        service.register_product(
            codigo="AROMA001",
            produto="Lavanda Premium",
            categoria="Aromas Florais",
            custo=25.50,
            valor=42.00,  # Selling price
            estoque=100
        )
        
        service.register_product(
            codigo="AROMA002",
            produto="Vanilla Essence",
            categoria="Aromas Doces",
            custo=30.00,
            valor=49.90,
            estoque=50
        )
        
        service.register_product(
            codigo="DIFUSOR01",
            produto="Difusor Elétrico Branco",
            categoria="Difusores",
            custo=85.00,
            valor=149.90,
            estoque=20
        )
        
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: Try to register duplicate CODIGO
    print("\n2. Testing duplicate CODIGO validation...")
    try:
        service.register_product(
            codigo="AROMA001",  # Duplicate
            produto="Another Product",
            categoria="Test",
            custo=10.00,
            valor=20.00,
            estoque=5
        )
        print("✗ ERROR: Duplicate was accepted (should have failed)")
    except ValueError as e:
        print(f"✓ Correctly rejected duplicate: {e}")
    
    # Test 3: Test invalid cost
    print("\n3. Testing negative cost validation...")
    try:
        service.register_product(
            codigo="TEST001",
            produto="Invalid Product",
            categoria="Test",
            custo=-10.00,  # Invalid
            valor=20.00,
            estoque=5
        )
        print("✗ ERROR: Negative cost was accepted (should have failed)")
    except ValueError as e:
        print(f"✓ Correctly rejected negative cost: {e}")
    
    # Test 4: Test invalid selling price
    print("\n4. Testing negative selling price validation...")
    try:
        service.register_product(
            codigo="TEST002",
            produto="Invalid Price",
            categoria="Test",
            custo=10.00,
            valor=-20.00,  # Invalid
            estoque=5
        )
        print("✗ ERROR: Negative price was accepted (should have failed)")
    except ValueError as e:
        print(f"✓ Correctly rejected negative price: {e}")
    
    # Test 5: Test invalid stock
    print("\n5. Testing negative stock validation...")
    try:
        service.register_product(
            codigo="TEST003",
            produto="Invalid Stock",
            categoria="Test",
            custo=10.00,
            valor=20.00,
            estoque=-5  # Invalid
        )
        print("✗ ERROR: Negative stock was accepted (should have failed)")
    except ValueError as e:
        print(f"✓ Correctly rejected negative stock: {e}")


def test_product_listing():
    """Test product listing functionality."""
    print_separator("TEST 2: Product Listing")
    
    service = ProductService()
    
    print("\n1. Listing all products:")
    products = service.list_all_products()
    
    if products:
        print(f"\nTotal products: {len(products)}\n")
        for p in products:
            custo = float(p['CUSTO'])
            valor = float(p['VALOR'])
            margin = ((valor - custo) / custo) * 100 if custo > 0 else 0
            
            print(f"Código: {p['CODIGO']}")
            print(f"Produto: {p['PRODUTO']}")
            print(f"Categoria: {p['CATEGORIA']}")
            print(f"Custo: R$ {custo:.2f}")
            print(f"Preço de Venda: R$ {valor:.2f}")
            print(f"Margem: {margin:.1f}%")
            print(f"Estoque: {p['ESTOQUE']} unidades")
            print_separator()
    else:
        print("No products found")
    
    # List by category
    print("\n2. Listing products in 'Aromas Florais' category:")
    florais = service.list_by_category("Aromas Florais")
    for p in florais:
        print(f"  - {p['PRODUTO']} ({p['CODIGO']})")


def test_product_retrieval():
    """Test individual product retrieval."""
    print_separator("TEST 3: Product Retrieval")
    
    service = ProductService()
    
    print("\n1. Getting product AROMA001:")
    product = service.get_product("AROMA001")
    
    if product:
        print(f"✓ Product found:")
        print(f"  Nome: {product['PRODUTO']}")
        print(f"  Categoria: {product['CATEGORIA']}")
        print(f"  Custo: R$ {float(product['CUSTO']):.2f}")
        print(f"  Preço de Venda: R$ {float(product['VALOR']):.2f}")
        print(f"  Estoque: {product['ESTOQUE']} unidades")
    else:
        print("✗ Product not found")
    
    print("\n2. Checking if product exists:")
    exists = service.product_exists("AROMA001")
    print(f"  AROMA001 exists: {exists}")
    
    exists = service.product_exists("NOTFOUND")
    print(f"  NOTFOUND exists: {exists}")
    
    print("\n3. Getting specific product attributes:")
    stock = service.get_stock_quantity("AROMA001")
    price = service.get_product_price("AROMA001")
    print(f"  Stock quantity: {stock} units")
    print(f"  Selling price: R$ {price:.2f}")


def test_stock_updates():
    """Test stock update functionality."""
    print_separator("TEST 4: Stock Management")
    
    service = ProductService()
    
    # Get initial stock
    print("\n1. Initial stock for AROMA001:")
    initial = service.get_stock_quantity("AROMA001")
    print(f"  Current stock: {initial} unidades")
    
    # Test stock addition
    print("\n2. Adding 50 units to stock:")
    try:
        service.adjust_stock("AROMA001", 50, "entrada de mercadoria")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test stock subtraction
    print("\n3. Removing 30 units from stock:")
    try:
        service.adjust_stock("AROMA001", -30, "ajuste de inventário")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test insufficient stock
    print("\n4. Testing insufficient stock protection:")
    try:
        current = service.get_stock_quantity("AROMA001")
        service.adjust_stock("AROMA001", -(current + 10), "teste")
        print("✗ ERROR: Negative stock was allowed (should have failed)")
    except ValueError as e:
        print(f"✓ Correctly rejected insufficient stock: {e}")


def test_product_updates():
    """Test product information updates."""
    print_separator("TEST 5: Product Updates")
    
    service = ProductService()
    
    print("\n1. Updating product information for AROMA002:")
    try:
        service.update_product_info(
            "AROMA002",
            produto="Vanilla Essence Premium",
            custo=32.50,
            valor=54.90
        )
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n2. Verifying update:")
    product = service.get_product("AROMA002")
    if product:
        print(f"  Updated name: {product['PRODUTO']}")
        print(f"  Updated cost: R$ {float(product['CUSTO']):.2f}")
        print(f"  Updated price: R$ {float(product['VALOR']):.2f}")


def test_low_stock_alert():
    """Test low stock detection."""
    print_separator("TEST 6: Low Stock Alert")
    
    service = ProductService()
    
    # Adjust some products to low stock
    print("\n1. Setting DIFUSOR01 to low stock (3 units):")
    try:
        current = service.get_stock_quantity("DIFUSOR01")
        service.adjust_stock("DIFUSOR01", -(current - 3), "teste de estoque baixo")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n2. Checking for low stock products (threshold: 5):")
    service.check_low_stock(threshold=5)


def test_inventory_summary():
    """Test inventory summary functionality."""
    print_separator("TEST 7: Inventory Summary")
    
    service = ProductService()
    
    print("\n1. Getting comprehensive inventory summary:")
    summary = service.get_inventory_summary()
    
    print("\n2. Summary details:")
    print(f"  Products: {summary['total_products']}")
    print(f"  Total items: {summary['total_items']}")
    print(f"  Cost value: R$ {summary['inventory_cost_value']:.2f}")
    print(f"  Retail value: R$ {summary['inventory_retail_value']:.2f}")
    print(f"  Potential profit: R$ {summary['potential_profit']:.2f}")


def test_edge_cases():
    """Test edge cases and error handling."""
    print_separator("TEST 8: Edge Cases")
    
    service = ProductService()
    
    print("\n1. Testing empty product name:")
    try:
        service.register_product(
            codigo="EMPTY001",
            produto="   ",  # Empty after strip
            categoria="Test",
            custo=10.00,
            valor=20.00,
            estoque=5
        )
        print("✗ ERROR: Empty name was accepted")
    except ValueError as e:
        print(f"✓ Correctly rejected empty name: {e}")
    
    print("\n2. Testing case-insensitive CODIGO lookup:")
    product = service.get_product("aroma001")  # lowercase
    if product:
        print(f"✓ Found product with lowercase code: {product['PRODUTO']}")
    
    print("\n3. Testing non-existent product update:")
    try:
        service.update_product_info("NOTFOUND", produto="Test")
        print("✗ ERROR: Update on non-existent product succeeded")
    except ValueError as e:
        print(f"✓ Correctly rejected: {e}")
    
    print("\n4. Testing price lower than cost (warning scenario):")
    try:
        service.register_product(
            codigo="LOWPRICE01",
            produto="Below Cost Product",
            categoria="Test",
            custo=50.00,
            valor=40.00,  # Price < Cost
            estoque=10
        )
        print("⚠️  WARNING: Product registered with price lower than cost")
        print("   This is allowed but generates negative margin")
    except Exception as e:
        print(f"Result: {e}")


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "="*60)
    print("  PRODUCT MODULE - MANUAL TEST SUITE")
    print("="*60)
    print("\nThis will test all product functionality step by step.")
    print("Check the console output and verify the CSV file after.")
    
    input("\nPress ENTER to start tests...")
    
    try:
        test_product_registration()
        test_product_listing()
        test_product_retrieval()
        test_stock_updates()
        test_product_updates()
        test_low_stock_alert()
        test_inventory_summary()
        test_edge_cases()
        
        print_separator("TEST SUITE COMPLETED")
        print("\n✓ All tests completed!")
        print("\nNext steps:")
        print("1. Check data/products.csv to verify data persistence")
        print("2. Run this script again to verify data was saved correctly")
        print("3. Review the console output above for any errors")
        print("\nExpected CSV schema:")
        print("CODIGO,PRODUTO,CATEGORIA,CUSTO,VALOR,ESTOQUE")
        
    except Exception as e:
        print(f"\n✗ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()