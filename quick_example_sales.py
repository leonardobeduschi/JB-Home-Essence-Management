"""
Quick example of sale module usage.

This demonstrates the complete sales workflow including
product and client integration.
"""

from src.services.sale_service import SaleService
from src.services.product_service import ProductService
from src.services.client_service import ClientService


def main():
    """Simple sales workflow example."""
    print("="*60)
    print("  Sale Module - Quick Example")
    print("="*60)
    
    # Initialize services
    sale_service = SaleService()
    product_service = ProductService()
    client_service = ClientService()
    
    # === STEP 1: Show Available Products ===
    print("\n" + "="*60)
    print("  STEP 1: Available Products")
    print("="*60)
    
    products = product_service.list_all_products()
    print(f"\nTotal products available: {len(products)}")
    
    if products:
        print("\nProducts in stock:")
        for p in products[:5]:  # Show first 5
            print(f"  - {p['CODIGO']}: {p['PRODUTO']}")
            print(f"    Price: R$ {float(p['VALOR']):.2f} | Stock: {p['ESTOQUE']} units")
    
    # === STEP 2: Show Available Clients ===
    print("\n" + "="*60)
    print("  STEP 2: Available Clients")
    print("="*60)
    
    clients = client_service.list_all_clients()
    print(f"\nTotal clients: {len(clients)}")
    
    if clients:
        print("\nClients:")
        for c in clients[:3]:  # Show first 3
            print(f"  - {c['ID_CLIENTE']}: {c['CLIENTE']} ({c['TIPO']})")
    
    # === STEP 3: Calculate Sale Before Confirming ===
    print("\n" + "="*60)
    print("  STEP 3: Calculate Sale (Preview)")
    print("="*60)
    
    if products and clients:
        first_product = products[0]['CODIGO']
        first_client = clients[0]['ID_CLIENTE']
        
        print(f"\nCalculating sale: 3 units of {first_product}...")
        
        try:
            calculation = sale_service.calculate_sale_total(first_product, 3)
            
            print(f"  Product: {calculation['produto']}")
            print(f"  Unit price: R$ {calculation['preco_unit']:.2f}")
            print(f"  Quantity: {calculation['quantidade']}")
            print(f"  Total: R$ {calculation['preco_total']:.2f}")
            print(f"  Stock available: {calculation['estoque_disponivel']}")
            print(f"  Sufficient stock: {'Yes' if calculation['estoque_suficiente'] else 'No'}")
            
            # === STEP 4: Register the Sale ===
            print("\n" + "="*60)
            print("  STEP 4: Register Sale")
            print("="*60)
            
            print(f"\nRegistering sale...")
            
            sale = sale_service.register_sale(
                id_cliente=first_client,
                codigo=first_product,
                quantidade=3,
                meio="pix"
            )
            
        except Exception as e:
            print(f"\nNote: {e}")
            print("This may mean the sale was already registered or insufficient stock.")
    
    # === STEP 5: List Recent Sales ===
    print("\n" + "="*60)
    print("  STEP 5: Recent Sales")
    print("="*60)
    
    all_sales = sale_service.list_all_sales()
    print(f"\nTotal sales: {len(all_sales)}")
    
    if all_sales:
        print("\nLast 5 sales:")
        for sale in all_sales[-5:]:
            print(f"\n  {sale['ID_VENDA']} - {sale['DATA']}")
            print(f"  Client: {sale['CLIENTE']}")
            print(f"  Product: {sale['PRODUTO']}")
            print(f"  Quantity: {sale['QUANTIDADE']} × R$ {float(sale['PRECO_UNIT']):.2f}")
            print(f"  Total: R$ {float(sale['PRECO_TOTAL']):.2f}")
            print(f"  Payment: {sale['MEIO'].title()}")
    
    # === STEP 6: Sales by Client ===
    print("\n" + "="*60)
    print("  STEP 6: Sales by Client")
    print("="*60)
    
    if clients:
        client_id = clients[0]['ID_CLIENTE']
        print(f"\nSales for client {client_id}:")
        
        client_sales = sale_service.list_sales_by_client(client_id)
        
        if client_sales:
            total_spent = sum(float(s['PRECO_TOTAL']) for s in client_sales)
            print(f"  Total purchases: {len(client_sales)}")
            print(f"  Total spent: R$ {total_spent:.2f}")
            
            for s in client_sales:
                print(f"  - {s['DATA']}: {s['PRODUTO']} (R$ {float(s['PRECO_TOTAL']):.2f})")
        else:
            print("  No sales yet for this client")
    
    # === STEP 7: Sales Summary ===
    print("\n" + "="*60)
    print("  STEP 7: Sales Summary")
    print("="*60)
    
    summary = sale_service.get_sales_summary()
    
    # === STEP 8: Top Products and Clients ===
    print("\n" + "="*60)
    print("  STEP 8: Top Performers")
    print("="*60)
    
    print("\n" + "-"*60)
    sale_service.get_top_products(limit=3)
    
    print("\n" + "-"*60)
    sale_service.get_top_clients(limit=3)
    
    # === STEP 9: Payment Methods ===
    print("\n" + "="*60)
    print("  STEP 9: Available Payment Methods")
    print("="*60)
    
    methods = sale_service.get_available_payment_methods()
    print("\nAccepted payment methods:")
    for method in methods:
        print(f"  - {method.title()}")
    
    # === FINAL SUMMARY ===
    print("\n" + "="*60)
    print("✓ Example completed successfully!")
    print("="*60)
    
    print("\nKey Features Demonstrated:")
    print("  1. ✅ Product and client integration")
    print("  2. ✅ Automatic price lookup")
    print("  3. ✅ Stock availability checking")
    print("  4. ✅ Automatic total calculation")
    print("  5. ✅ Inventory update on sale")
    print("  6. ✅ Sales listing and filtering")
    print("  7. ✅ Statistics and summaries")
    print("  8. ✅ Top products and clients")
    
    print("\nCheck these files:")
    print("  - data/sales.csv (sale records)")
    print("  - data/products.csv (updated stock)")
    print("  - data/clients.csv (client info)")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()