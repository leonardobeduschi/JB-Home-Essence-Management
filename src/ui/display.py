"""
Display utilities for formatting and presenting data.

This module provides functions to display products, clients, and sales
in a user-friendly table format.
"""

from typing import List, Dict


def print_table_header(columns: List[tuple[str, int]]):
    """
    Print table header with column alignment.
    
    Args:
        columns: List of (column_name, width) tuples
    """
    # Print header
    header = " | ".join(name.ljust(width) for name, width in columns)
    print("\n" + header)
    
    # Print separator
    separator = "-+-".join("-" * width for _, width in columns)
    print(separator)


def print_table_row(values: List[str], widths: List[int]):
    """
    Print table row with proper alignment.
    
    Args:
        values: List of values to display
        widths: List of column widths
    """
    row = " | ".join(str(val).ljust(width) for val, width in zip(values, widths))
    print(row)


def display_products(products: List[Dict], show_all: bool = True):
    """
    Display products in a formatted table.
    
    Args:
        products: List of product dictionaries
        show_all: Whether to show all products or limit to recent
    """
    if not products:
        print("\nNenhum produto cadastrado.")
        return
    
    # Limit if requested
    if not show_all and len(products) > 10:
        print(f"\nExibindo os {min(10, len(products))} produtos mais recentes:")
        products = products[-10:]
    else:
        print(f"\nTotal de produtos: {len(products)}")
    
    # Define columns
    columns = [
        ("Código", 12),
        ("Produto", 30),
        ("Categoria", 20),
        ("Custo", 10),
        ("Preço", 10),
        ("Estoque", 8)
    ]
    
    print_table_header(columns)
    
    # Print rows
    for p in products:
        custo = float(p.get('CUSTO', 0))
        valor = float(p.get('VALOR', 0))
        
        values = [
            p.get('CODIGO', ''),
            p.get('PRODUTO', '')[:28],  # Truncate long names
            p.get('CATEGORIA', '')[:18],
            f"R$ {custo:.2f}",
            f"R$ {valor:.2f}",
            p.get('ESTOQUE', '0')
        ]
        
        widths = [width for _, width in columns]
        print_table_row(values, widths)


def display_clients(clients: List[Dict], show_all: bool = True):
    """
    Display clients in a formatted table.
    
    Args:
        clients: List of client dictionaries
        show_all: Whether to show all clients or limit to recent
    """
    if not clients:
        print("\nNenhum cliente cadastrado.")
        return
    
    # Limit if requested
    if not show_all and len(clients) > 10:
        print(f"\nExibindo os {min(10, len(clients))} clientes mais recentes:")
        clients = clients[-10:]
    else:
        print(f"\nTotal de clientes: {len(clients)}")
    
    # Define columns
    columns = [
        ("ID", 8),
        ("Nome", 25),
        ("Tipo", 8),
        ("Vendedor", 20),
        ("Telefone", 17)
    ]
    
    print_table_header(columns)
    
    # Print rows
    for c in clients:
        tipo = c.get('TIPO', '').capitalize()
        
        values = [
            c.get('ID_CLIENTE', ''),
            c.get('CLIENTE', '')[:23],
            tipo,
            c.get('VENDEDOR', '')[:18],
            c.get('TELEFONE', '')
        ]
        
        widths = [width for _, width in columns]
        print_table_row(values, widths)


def display_sales(sales: List[Dict], show_all: bool = True):
    """
    Display sales in a formatted table.
    
    Args:
        sales: List of sale dictionaries
        show_all: Whether to show all sales or limit to recent
    """
    if not sales:
        print("\nNenhuma venda registrada.")
        return
    
    # Limit if requested
    if not show_all and len(sales) > 15:
        print(f"\nExibindo as {min(15, len(sales))} vendas mais recentes:")
        sales = sales[-15:]
    else:
        print(f"\nTotal de vendas: {len(sales)}")
    
    # Define columns
    columns = [
        ("ID", 8),
        ("Data", 12),
        ("Cliente", 20),
        ("Produto", 20),
        ("Qtd", 5),
        ("Total", 12),
        ("Pgto", 10)
    ]
    
    print_table_header(columns)
    
    # Print rows
    for s in sales:
        total = float(s.get('PRECO_TOTAL', 0))
        
        values = [
            s.get('ID_VENDA', ''),
            s.get('DATA', ''),
            s.get('CLIENTE', '')[:18],
            s.get('PRODUTO', '')[:18],
            s.get('QUANTIDADE', '0'),
            f"R$ {total:.2f}",
            s.get('MEIO', '').capitalize()[:8]
        ]
        
        widths = [width for _, width in columns]
        print_table_row(values, widths)


def display_product_detail(product: Dict):
    """
    Display detailed product information.
    
    Args:
        product: Product dictionary
    """
    print("\n" + "="*60)
    print("  DETALHES DO PRODUTO")
    print("="*60)
    
    custo = float(product.get('CUSTO', 0))
    valor = float(product.get('VALOR', 0))
    estoque = int(product.get('ESTOQUE', 0))
    
    # Calculate margin
    margin = ((valor - custo) / custo) * 100 if custo > 0 else 0
    
    print(f"\nCódigo: {product.get('CODIGO', '')}")
    print(f"Produto: {product.get('PRODUTO', '')}")
    print(f"Categoria: {product.get('CATEGORIA', '')}")
    print(f"\nCusto: R$ {custo:.2f}")
    print(f"Preço de Venda: R$ {valor:.2f}")
    print(f"Margem de Lucro: {margin:.1f}%")
    print(f"\nEstoque: {estoque} unidade(s)")
    print(f"Valor em Estoque (custo): R$ {custo * estoque:.2f}")
    print(f"Valor em Estoque (varejo): R$ {valor * estoque:.2f}")
    print("="*60)


def display_client_detail(client: Dict):
    """
    Display detailed client information.
    
    Args:
        client: Client dictionary
    """
    print("\n" + "="*60)
    print("  DETALHES DO CLIENTE")
    print("="*60)
    
    print(f"\nID: {client.get('ID_CLIENTE', '')}")
    print(f"Nome: {client.get('CLIENTE', '')}")
    print(f"Tipo: {client.get('TIPO', '').capitalize()}")
    print(f"Vendedor: {client.get('VENDEDOR', '')}")
    
    if client.get('TIPO', '').lower() == 'pessoa':
        print(f"\nIdade: {client.get('IDADE', '')}")
        print(f"Gênero: {client.get('GENERO', '')}")
        if client.get('PROFISSAO'):
            print(f"Profissão: {client.get('PROFISSAO', '')}")
    
    if client.get('CPF_CNPJ'):
        tipo_doc = "CNPJ" if client.get('TIPO', '').lower() == 'empresa' else "CPF"
        print(f"\n{tipo_doc}: {client.get('CPF_CNPJ', '')}")
    
    if client.get('TELEFONE'):
        print(f"Telefone: {client.get('TELEFONE', '')}")
    
    if client.get('ENDERECO'):
        print(f"Endereço: {client.get('ENDERECO', '')}")
    
    print("="*60)


def display_sale_detail(sale: Dict):
    """
    Display detailed sale information.
    
    Args:
        sale: Sale dictionary
    """
    print("\n" + "="*60)
    print("  DETALHES DA VENDA")
    print("="*60)
    
    quantidade = int(sale.get('QUANTIDADE', 0))
    preco_unit = float(sale.get('PRECO_UNIT', 0))
    preco_total = float(sale.get('PRECO_TOTAL', 0))
    
    print(f"\nID da Venda: {sale.get('ID_VENDA', '')}")
    print(f"Data: {sale.get('DATA', '')}")
    
    print(f"\nCliente: {sale.get('CLIENTE', '')} ({sale.get('ID_CLIENTE', '')})")
    
    print(f"\nProduto: {sale.get('PRODUTO', '')}")
    print(f"Código: {sale.get('CODIGO', '')}")
    print(f"Categoria: {sale.get('CATEGORIA', '')}")
    
    print(f"\nQuantidade: {quantidade} unidade(s)")
    print(f"Preço Unitário: R$ {preco_unit:.2f}")
    print(f"Preço Total: R$ {preco_total:.2f}")
    
    print(f"\nForma de Pagamento: {sale.get('MEIO', '').title()}")
    
    print("="*60)


def print_section_header(title: str):
    """
    Print a section header.
    
    Args:
        title: Section title
    """
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)