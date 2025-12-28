"""
Quick example of product module usage.

This demonstrates the basic operations in a simple, clear way.
"""

from src.services.product_service import ProductService


def main():
    """Simple example workflow."""
    print("="*60)
    print("  Product Module - Quick Example")
    print("="*60)
    
    # Initialize service
    service = ProductService()
    
    # 1. Register a product
    print("\n1. Registering a new product...")
    try:
        product = service.register_product(
            codigo="EXAMPLE01",
            produto="Lavender Dream",
            categoria="Essential Oils",
            custo=28.90,
            valor=45.00,  # Selling price
            estoque=75
        )
    except ValueError as e:
        print(f"Note: {e} (product may already exist)")
    
    # 2. Check if product exists
    print("\n2. Checking product existence...")
    exists = service.product_exists("EXAMPLE01")
    print(f"   Product EXAMPLE01 exists: {exists}")
    
    # 3. Get product details
    print("\n3. Retrieving product details...")
    product = service.get_product("EXAMPLE01")
    if product:
        print(f"   Name: {product['PRODUTO']}")
        print(f"   Category: {product['CATEGORIA']}")
        print(f"   Cost: R$ {float(product['CUSTO']):.2f}")
        print(f"   Selling Price: R$ {float(product['VALOR']):.2f}")
        print(f"   Stock: {product['ESTOQUE']} units")
        
        # Calculate margin
        custo = float(product['CUSTO'])
        valor = float(product['VALOR'])
        margin = ((valor - custo) / custo) * 100
        print(f"   Profit Margin: {margin:.1f}%")
    
    # 4. Update stock (simulate a sale)
    print("\n4. Simulating a sale (removing 10 units)...")
    try:
        service.adjust_stock("EXAMPLE01", -10, "venda simulada")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 5. Check updated stock
    print("\n5. Checking updated stock...")
    current_stock = service.get_stock_quantity("EXAMPLE01")
    print(f"   Current stock: {current_stock} units")
    
    # 6. Update product pricing
    print("\n6. Updating product price...")
    try:
        service.update_product_info(
            "EXAMPLE01",
            valor=47.50  # New selling price
        )
        updated = service.get_product("EXAMPLE01")
        print(f"   New selling price: R$ {float(updated['VALOR']):.2f}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 7. List all products
    print("\n7. Listing all products in system:")
    all_products = service.list_all_products()
    print(f"   Total products: {len(all_products)}")
    for p in all_products:
        print(f"   - {p['CODIGO']}: {p['PRODUTO']}")
        print(f"     Cost: R$ {float(p['CUSTO']):.2f} | "
              f"Price: R$ {float(p['VALOR']):.2f} | "
              f"Stock: {p['ESTOQUE']}")
    
    # 8. Get inventory summary
    print("\n8. Inventory summary:")
    service.get_inventory_summary()
    
    print("\n" + "="*60)
    print("✓ Example completed successfully!")
    print("\nCheck 'data/products.csv' to see the persisted data.")
    print("="*60)


if __name__ == "__main__":
    main()