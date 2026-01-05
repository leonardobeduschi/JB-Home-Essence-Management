"""
Script de Migração: Reestruturação do sistema de vendas.

ANTES: sales.csv com linhas duplicadas por ID_VENDA
DEPOIS: sales.csv (cabeçalhos) + sales_items.csv (itens)

Execute este script UMA VEZ para migrar seus dados.
"""

import pandas as pd
import os
from datetime import datetime


def migrate_sales_structure():
    """
    Migra o arquivo sales.csv antigo para o novo formato relacional.
    """
    
    # Configurações
    OLD_FILE = 'data/sales.csv'
    NEW_SALES_FILE = 'data/sales.csv'
    ITEMS_FILE = 'data/sales_items.csv'
    BACKUP_DIR = 'data/backup_migration'
    
    print("="*80)
    print("  MIGRAÇÃO DO SISTEMA DE VENDAS")
    print("  De: CSV único → Para: sales.csv + sales_items.csv")
    print("="*80)
    
    # ========== ETAPA 1: VALIDAÇÃO ==========
    print("\n[1/6] Validando arquivo de origem...")
    
    if not os.path.exists(OLD_FILE):
        print(f"❌ ERRO: Arquivo {OLD_FILE} não encontrado!")
        return False
    
    # Ler arquivo antigo
    try:
        df_old = pd.read_csv(OLD_FILE)
        print(f"✅ Arquivo lido com sucesso: {len(df_old)} linhas")
    except Exception as e:
        print(f"❌ ERRO ao ler arquivo: {e}")
        return False
    
    # Validar colunas obrigatórias
    required_cols = ['ID_VENDA', 'ID_CLIENTE', 'CLIENTE', 'MEIO', 'DATA', 
                     'PRODUTO', 'CATEGORIA', 'CODIGO', 'QUANTIDADE', 
                     'PRECO_UNIT', 'PRECO_TOTAL']
    
    missing_cols = [col for col in required_cols if col not in df_old.columns]
    if missing_cols:
        print(f"❌ ERRO: Colunas faltando: {missing_cols}")
        return False
    
    print(f"✅ Todas as colunas obrigatórias presentes")
    
    # ========== ETAPA 2: BACKUP ==========
    print("\n[2/6] Criando backup de segurança...")
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'sales_backup_{timestamp}.csv')
    
    try:
        df_old.to_csv(backup_file, index=False)
        print(f"✅ Backup criado: {backup_file}")
    except Exception as e:
        print(f"❌ ERRO ao criar backup: {e}")
        return False
    
    # ========== ETAPA 3: PROCESSAR DADOS ==========
    print("\n[3/6] Processando e agrupando dados...")
    
    # Converter tipos numéricos
    df_old['PRECO_TOTAL'] = pd.to_numeric(df_old['PRECO_TOTAL'], errors='coerce').fillna(0)
    df_old['PRECO_UNIT'] = pd.to_numeric(df_old['PRECO_UNIT'], errors='coerce').fillna(0)
    df_old['QUANTIDADE'] = pd.to_numeric(df_old['QUANTIDADE'], errors='coerce').fillna(0).astype(int)
    
    # Contar vendas únicas
    unique_sales = df_old['ID_VENDA'].nunique()
    total_lines = len(df_old)
    
    print(f"📊 Estatísticas:")
    print(f"   - Linhas totais (itens): {total_lines}")
    print(f"   - Vendas únicas: {unique_sales}")
    print(f"   - Média de itens por venda: {total_lines / unique_sales:.2f}")
    
    # ========== ETAPA 4: CRIAR SALES.CSV (CABEÇALHOS) ==========
    print("\n[4/6] Criando arquivo sales.csv (cabeçalhos)...")
    
    # Agrupar por ID_VENDA e pegar a primeira linha de cada grupo para info geral
    sales_grouped = df_old.groupby('ID_VENDA').agg({
        'ID_CLIENTE': 'first',
        'CLIENTE': 'first',
        'MEIO': 'first',
        'DATA': 'first',
        'PRECO_TOTAL': 'sum'  # Somar todos os itens da venda
    }).reset_index()
    
    # Renomear coluna para clareza
    sales_grouped.rename(columns={'PRECO_TOTAL': 'VALOR_TOTAL_VENDA'}, inplace=True)
    
    # Ordenar por ID_VENDA
    sales_grouped = sales_grouped.sort_values('ID_VENDA')
    
    # Definir ordem das colunas
    sales_columns = ['ID_VENDA', 'ID_CLIENTE', 'CLIENTE', 'MEIO', 'DATA', 'VALOR_TOTAL_VENDA']
    df_sales = sales_grouped[sales_columns]
    
    print(f"✅ Criado DataFrame sales com {len(df_sales)} vendas")
    print(f"   Colunas: {list(df_sales.columns)}")
    
    # ========== ETAPA 5: CRIAR SALES_ITEMS.CSV (ITENS) ==========
    print("\n[5/6] Criando arquivo sales_items.csv (itens)...")
    
    # Selecionar apenas colunas relevantes para itens
    items_columns = ['ID_VENDA', 'PRODUTO', 'CATEGORIA', 'CODIGO', 
                     'QUANTIDADE', 'PRECO_UNIT', 'PRECO_TOTAL']
    
    df_items = df_old[items_columns].copy()
    
    # Ordenar por ID_VENDA e depois por CODIGO
    df_items = df_items.sort_values(['ID_VENDA', 'CODIGO'])
    
    print(f"✅ Criado DataFrame sales_items com {len(df_items)} itens")
    print(f"   Colunas: {list(df_items.columns)}")
    
    # ========== ETAPA 6: SALVAR ARQUIVOS ==========
    print("\n[6/6] Salvando novos arquivos...")
    
    try:
        # Salvar sales.csv
        df_sales.to_csv(NEW_SALES_FILE, index=False)
        print(f"✅ Salvo: {NEW_SALES_FILE} ({len(df_sales)} linhas)")
        
        # Salvar sales_items.csv
        df_items.to_csv(ITEMS_FILE, index=False)
        print(f"✅ Salvo: {ITEMS_FILE} ({len(df_items)} linhas)")
        
    except Exception as e:
        print(f"❌ ERRO ao salvar arquivos: {e}")
        return False
    
    # ========== VALIDAÇÃO FINAL ==========
    print("\n" + "="*80)
    print("  VALIDAÇÃO FINAL")
    print("="*80)
    
    # Verificar integridade
    print("\n📊 Verificando integridade dos dados:")
    
    # 1. Número de itens deve ser igual
    if len(df_items) == total_lines:
        print(f"✅ Itens: {len(df_items)} = {total_lines} (OK)")
    else:
        print(f"⚠️  Itens: {len(df_items)} ≠ {total_lines} (VERIFICAR)")
    
    # 2. Número de vendas deve ser igual
    if len(df_sales) == unique_sales:
        print(f"✅ Vendas: {len(df_sales)} = {unique_sales} (OK)")
    else:
        print(f"⚠️  Vendas: {len(df_sales)} ≠ {unique_sales} (VERIFICAR)")
    
    # 3. Soma total deve ser igual
    original_total = df_old.groupby('ID_VENDA')['PRECO_TOTAL'].sum().sum()
    new_total = df_sales['VALOR_TOTAL_VENDA'].sum()
    
    if abs(original_total - new_total) < 0.01:  # Tolerância para arredondamento
        print(f"✅ Receita total: R$ {new_total:.2f} (OK)")
    else:
        print(f"⚠️  Receita: R$ {new_total:.2f} ≠ R$ {original_total:.2f} (VERIFICAR)")
    
    # 4. Verificar relacionamento (cada item tem venda correspondente)
    items_sale_ids = set(df_items['ID_VENDA'].unique())
    sales_ids = set(df_sales['ID_VENDA'].unique())
    
    if items_sale_ids == sales_ids:
        print(f"✅ Relacionamento: Todos os itens têm venda correspondente (OK)")
    else:
        orphans = items_sale_ids - sales_ids
        if orphans:
            print(f"⚠️  ATENÇÃO: {len(orphans)} ID_VENDA em itens sem cabeçalho: {orphans}")
    
    # ========== RESUMO FINAL ==========
    print("\n" + "="*80)
    print("  MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*80)
    print("\n📁 Arquivos criados:")
    print(f"   1. {NEW_SALES_FILE} - {len(df_sales)} vendas (cabeçalhos)")
    print(f"   2. {ITEMS_FILE} - {len(df_items)} itens")
    print(f"   3. {backup_file} - Backup do arquivo original")
    
    print("\n⚠️  PRÓXIMOS PASSOS:")
    print("   1. Verifique os novos arquivos CSV")
    print("   2. Atualize o código do sistema (repositories e services)")
    print("   3. Teste todas as funcionalidades")
    print("   4. Se tudo OK, pode deletar o backup")
    
    return True


def show_sample_data():
    """Mostra exemplos dos novos arquivos criados."""
    print("\n" + "="*80)
    print("  PREVIEW DOS DADOS")
    print("="*80)
    
    try:
        # Sales
        print("\n📄 sales.csv (primeiras 5 vendas):")
        df_sales = pd.read_csv('data/sales.csv')
        print(df_sales.head().to_string(index=False))
        
        # Items
        print("\n📄 sales_items.csv (primeiros 10 itens):")
        df_items = pd.read_csv('data/sales_items.csv')
        print(df_items.head(10).to_string(index=False))
        
        # Exemplo de relacionamento
        print("\n🔗 Exemplo de relacionamento (primeira venda):")
        first_sale_id = df_sales.iloc[0]['ID_VENDA']
        print(f"\nVenda: {first_sale_id}")
        print(df_sales[df_sales['ID_VENDA'] == first_sale_id].to_string(index=False))
        print(f"\nItens da venda {first_sale_id}:")
        print(df_items[df_items['ID_VENDA'] == first_sale_id].to_string(index=False))
        
    except Exception as e:
        print(f"❌ Erro ao mostrar preview: {e}")


if __name__ == '__main__':
    print("\n⚠️  ATENÇÃO: Este script irá REESTRUTURAR o arquivo sales.csv")
    print("   Um backup será criado automaticamente.")
    print("   Certifique-se de ter fechado o arquivo antes de continuar.")
    
    resposta = input("\n🤔 Deseja continuar? (digite 'SIM' para confirmar): ")
    
    if resposta.upper() == 'SIM':
        success = migrate_sales_structure()
        
        if success:
            print("\n✅ Tudo pronto! Agora você pode visualizar os dados:")
            show_sample_data()
        else:
            print("\n❌ Migração falhou. Verifique os erros acima.")
    else:
        print("\n❌ Operação cancelada pelo usuário.")