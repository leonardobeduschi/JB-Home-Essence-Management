"""
Script para normalizar o arquivo clients.csv existente.
Execute este script UMA VEZ para corrigir os dados existentes.

ATENÇÃO: Faça backup do seu clients.csv antes de executar!
"""

import pandas as pd
import os

def normalize_clients_csv():
    """Normaliza o arquivo clients.csv para o formato correto."""
    
    filepath = 'data/clients.csv'
    
    # Verifica se arquivo existe
    if not os.path.exists(filepath):
        print(f"❌ Arquivo {filepath} não encontrado!")
        return
    
    # Backup
    backup_path = filepath.replace('.csv', '_backup.csv')
    print(f"📦 Criando backup em: {backup_path}")
    
    # Lê o CSV
    try:
        df = pd.read_csv(filepath)
        
        # Salva backup
        df.to_csv(backup_path, index=False)
        print(f"✅ Backup criado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao ler CSV: {e}")
        return
    
    print(f"\n📊 Total de registros: {len(df)}")
    
    # Normalização
    corrections = {
        'tipo_normalized': 0,
        'idade_adjusted': 0,
        'empty_fields': 0
    }
    
    # 1. Normalizar TIPO (Pessoa/Empresa -> pessoa/empresa para consistência interna)
    # MAS salvar como Pessoa/Empresa no CSV para legibilidade
    if 'TIPO' in df.columns:
        # Converte para string e normaliza
        df['TIPO'] = df['TIPO'].astype(str).str.strip()
        
        # Normaliza para Pessoa ou Empresa (primeira letra maiúscula)
        df['TIPO'] = df['TIPO'].apply(lambda x: 'Pessoa' if x.lower() == 'pessoa' else 'Empresa')
        corrections['tipo_normalized'] = len(df)
        print(f"✅ Campo TIPO normalizado: {corrections['tipo_normalized']} registros")
    
    # 2. Normalizar campos vazios (NaN -> string vazia)
    for col in df.columns:
        null_count = df[col].isna().sum()
        if null_count > 0:
            df[col] = df[col].fillna('')
            corrections['empty_fields'] += null_count
    
    print(f"✅ Campos vazios corrigidos: {corrections['empty_fields']} campos")
    
    # 3. Verificar faixas etárias
    valid_ages = ['<18', '18-24', '25-34', '35-44', '45-54', '>55', '65+']
    if 'IDADE' in df.columns:
        invalid_ages = df[~df['IDADE'].isin(valid_ages + [''])]
        if len(invalid_ages) > 0:
            print(f"\n⚠️  Encontradas {len(invalid_ages)} faixas etárias não padronizadas:")
            print(invalid_ages[['ID_CLIENTE', 'CLIENTE', 'IDADE']].to_string())
    
    # 4. Garantir que ID_CLIENTE seja string
    df['ID_CLIENTE'] = df['ID_CLIENTE'].astype(str)
    
    # 5. Estatísticas
    print(f"\n📈 Estatísticas do arquivo normalizado:")
    print(f"   - Total de clientes: {len(df)}")
    print(f"   - Pessoas físicas: {len(df[df['TIPO'] == 'Pessoa'])}")
    print(f"   - Empresas: {len(df[df['TIPO'] == 'Empresa'])}")
    
    # Vendedores únicos
    vendedores = df['VENDEDOR'].value_counts()
    print(f"   - Vendedores únicos: {len(vendedores)}")
    for vendedor, count in vendedores.head(5).items():
        if vendedor:
            print(f"     • {vendedor}: {count} clientes")
    
    # Salvar arquivo normalizado
    try:
        df.to_csv(filepath, index=False)
        print(f"\n✅ Arquivo {filepath} normalizado com sucesso!")
        print(f"📁 Backup salvo em: {backup_path}")
        
    except Exception as e:
        print(f"\n❌ Erro ao salvar arquivo: {e}")
        print(f"   O backup está em: {backup_path}")

if __name__ == '__main__':
    print("="*60)
    print("  NORMALIZAÇÃO DO ARQUIVO CLIENTS.CSV")
    print("="*60)
    print("\n⚠️  ATENÇÃO: Este script irá modificar o arquivo clients.csv")
    print("   Um backup será criado automaticamente.")
    
    response = input("\nDeseja continuar? (s/N): ")
    
    if response.lower() == 's':
        normalize_clients_csv()
    else:
        print("\n❌ Operação cancelada pelo usuário.")
    
    print("\n" + "="*60)