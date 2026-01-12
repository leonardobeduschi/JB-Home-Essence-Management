"""
Limpeza final antes do commit.
Remove arquivos desnecessários e verifica segurança.
"""

import os
from pathlib import Path

def main():
    print("🧹 Limpeza Final do Projeto")
    print("="*60)
    
    # Files to delete
    files_to_delete = [
        # CSVs migrados
        'data/clients.csv',
        'data/clients_backup.csv',
        'data/products.csv',
        'data/sales.csv',
        'data/sales_items.csv',
        
        # SQLite antigo
        'data/database.sqlite3',
        'data/database.sqlite3.backup',
        
        # Scripts temporários
        'cleanup.py',
        'quick_migrate.py',
    ]
    
    deleted = 0
    for file in files_to_delete:
        if Path(file).exists():
            try:
                os.remove(file)
                print(f"  ✅ Deletado: {file}")
                deleted += 1
            except Exception as e:
                print(f"  ❌ Erro: {file} - {e}")
    
    print(f"\n✅ {deleted} arquivos removidos")
    
    # Security checks
    print("\n🔒 Verificações de Segurança:")
    
    checks = [
        ('.env', '❌ .env NÃO deve estar no Git!'),
        ('data/expenses_config.json', '❌ expenses_config.json NÃO deve estar no Git!'),
        ('.gitignore', '✅ .gitignore deve existir'),
        ('data/expenses_config.template.json', '✅ Template deve existir'),
    ]
    
    for file, message in checks:
        exists = Path(file).exists()
        if exists and file in ['.env', 'data/expenses_config.json']:
            print(f"  ⚠️  {file} existe - VERIFIQUE .gitignore!")
        elif exists:
            print(f"  ✅ {file} OK")
        else:
            print(f"  ⚠️  {file} não encontrado")
    
    print("\n📋 Próximos passos:")
    print("  1. Verifique se .gitignore está correto")
    print("  2. Teste: git status (não deve mostrar .env ou expenses_config.json)")
    print("  3. Se OK: git add . && git commit && git push")
    
if __name__ == '__main__':
    main()