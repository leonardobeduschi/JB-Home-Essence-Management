"""
Script de diagnóstico para identificar problemas com PRECO_TOTAL.
Execute: python diagnostic.py
"""

import pandas as pd
import traceback

print("="*60)
print("DIAGNÓSTICO DO SISTEMA")
print("="*60)

# Test 1: Check sales.csv structure
print("\n1. Verificando estrutura de sales.csv...")
try:
    sales_df = pd.read_csv('data/sales.csv')
    print(f"✅ Arquivo lido com sucesso!")
    print(f"   Colunas: {list(sales_df.columns)}")
    print(f"   Total de linhas: {len(sales_df)}")
    
    # Check if PRECO_TOTAL exists
    if 'PRECO_TOTAL' in sales_df.columns:
        print("⚠️  PROBLEMA: Coluna PRECO_TOTAL ainda existe em sales.csv!")
        print("   Deveria ter apenas: ID_VENDA, ID_CLIENTE, CLIENTE, MEIO, DATA, VALOR_TOTAL_VENDA")
    else:
        print("✅ Estrutura correta!")
        
    # Check if VALOR_TOTAL_VENDA exists
    if 'VALOR_TOTAL_VENDA' in sales_df.columns:
        print("✅ Coluna VALOR_TOTAL_VENDA encontrada!")
    else:
        print("❌ PROBLEMA: Coluna VALOR_TOTAL_VENDA não encontrada!")
        
except Exception as e:
    print(f"❌ Erro ao ler sales.csv: {e}")
    traceback.print_exc()

# Test 2: Check sales_items.csv structure
print("\n2. Verificando estrutura de sales_items.csv...")
try:
    items_df = pd.read_csv('data/sales_items.csv')
    print(f"✅ Arquivo lido com sucesso!")
    print(f"   Colunas: {list(items_df.columns)}")
    print(f"   Total de linhas: {len(items_df)}")
    
    expected_cols = ['ID_VENDA', 'PRODUTO', 'CATEGORIA', 'CODIGO', 'QUANTIDADE', 'PRECO_UNIT', 'PRECO_TOTAL']
    missing = [col for col in expected_cols if col not in items_df.columns]
    
    if missing:
        print(f"⚠️  Colunas faltando: {missing}")
    else:
        print("✅ Todas as colunas esperadas estão presentes!")
        
except Exception as e:
    print(f"❌ Erro ao ler sales_items.csv: {e}")
    traceback.print_exc()

# Test 3: Try to load summary
print("\n3. Testando get_sales_summary()...")
try:
    from src.services.sale_service import SaleService
    
    service = SaleService()
    summary = service.get_sales_summary()
    
    print("✅ Summary carregado com sucesso!")
    print(f"   Total de vendas: {summary['total_sales']}")
    print(f"   Receita total: R$ {summary['total_revenue']:.2f}")
    print(f"   Ticket médio: R$ {summary['average_sale_value']:.2f}")
    
except Exception as e:
    print(f"❌ Erro ao carregar summary: {e}")
    traceback.print_exc()

# Test 4: Try to load recent sales
print("\n4. Testando get_recent_sales()...")
try:
    from src.repositories.sale_repository import SaleRepository
    
    repo = SaleRepository()
    recent = repo.get_recent_sales(limit=5)
    
    print(f"✅ Recent sales carregado com sucesso!")
    print(f"   Total encontrado: {len(recent)}")
    
    if recent:
        print("\n   Primeira venda:")
        for key, value in recent[0].items():
            print(f"   - {key}: {value}")
    
except Exception as e:
    print(f"❌ Erro ao carregar recent sales: {e}")
    traceback.print_exc()

# Test 5: Check for PRECO_TOTAL references in code
print("\n5. Procurando referências a PRECO_TOTAL no código...")
import os
import glob

preco_total_files = []
for filepath in glob.glob('src/**/*.py', recursive=True):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'PRECO_TOTAL' in content and 'sales.csv' in content.lower():
                preco_total_files.append(filepath)
    except:
        pass

if preco_total_files:
    print("⚠️  Arquivos que ainda referenciam PRECO_TOTAL:")
    for f in preco_total_files:
        print(f"   - {f}")
else:
    print("✅ Nenhuma referência problemática encontrada!")

print("\n" + "="*60)
print("DIAGNÓSTICO CONCLUÍDO")
print("="*60)