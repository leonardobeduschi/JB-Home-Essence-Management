# JB Home Essence - Sistema de Gestão

**JB Home Essence Management** é uma aplicação web (Flask) para gestão completa de uma perfumaria/loja: clientes, produtos, vendas, despesas, análises e dashboards administrativos.

---

## 🚀 Visão Geral

O sistema fornece funcionalidade para: registro e gestão de produtos, clientes, cadastro e visualização de vendas, cálculo de margens (com distinção entre custos variáveis e despesas fixas), relatórios analíticos, e um painel administrativo com controles de estoque e desempenho.

Principais pontos:
- Separação clara entre **custos variáveis** (por venda) e **despesas fixas** (mensais)
- Cálculo correto de margem de contribuição por produto
- UI com templates Jinja2 e recursos estáticos (CSS/JS)
- Suporta **SQLite** (padrão) e **PostgreSQL** (via configuração `DB_TYPE`)

---

## ✅ Funcionalidades

- Gestão de Produtos (cadastro, listagem, margens)
- Gestão de Clientes
- Registro de Vendas e Itens por Venda
- Cálculo de margens e custos variáveis (taxas, embalagens, materiais)
- Controle de despesas fixas mensais e análise P&L
- Dashboard com resumos, top produtos e baixo estoque
- Exportação/relatórios (Excel/Pandas)
- Gerenciamento de manuais e documentação interna
- Autenticação de usuários com senhas hasheadas

---

## 🧩 Stack & Arquitetura

- **Linguagem:** Python 3.11 (ver `runtime.txt`)
- **Framework:** Flask
- **Data:** SQLite (padrão) / PostgreSQL (opcional)
- **Dependências:** veja `requirements.txt`
- **Estrutura:** `src/services` (business logic), `src/repositories` (acesso a dados), `templates`, `static`.

---

## 🔧 Instalação e Execução Local

Requisitos: Python 3.11 e pip.

1. Clone o repositório

```bash
git clone <repo-url>
cd JB-Home-Essence-Management
```

2. Crie e ative um virtualenv

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

3. Instale dependências

```bash
pip install -r requirements.txt
```

4. Crie um arquivo `.env` na raiz com variáveis básicas (exemplo):

```
FLASK_ENV=development
FLASK_SECRET_KEY=<uma_chave_secreta>
DB_TYPE=sqlite
SQLITE_DB=instance/db.sqlite
```

5. Configure `data/expenses_config.json` (arquivo é ignorado pelo git):
- Copie `data/expenses_config.template.json` → `data/expenses_config.json` e preencha com seus valores locais
- Ou defina a variável de ambiente `EXPENSES_CONFIG_JSON` com o JSON (útil para Docker/CI/hosts onde o arquivo não é commitado)

6. Execute a aplicação (desenvolvimento):

```bash
python app.py
# ou
python main.py
```
Acesse em http://localhost:5000

---

## 📦 Execução em Produção

- Use Gunicorn ou um WSGI server: `gunicorn --bind 0.0.0.0:8000 app:app`
- Configure `FLASK_ENV=production` e defina `FLASK_SECRET_KEY` com um valor forte
- Configure `SESSION_COOKIE_SECURE=true` em ambiente HTTPS

### Docker
- Montar arquivo de configuração:

```bash
docker run -p 5000:5000 \
  -v /host/secrets/expenses_config.json:/app/data/expenses_config.json \
  your-image:tag
```

- Passar via variável de ambiente:

```bash
docker run -p 5000:5000 -e "EXPENSES_CONFIG_JSON=$(cat /path/expenses_config.json)" your-image:tag
```

### Kubernetes (dica)
- Crie um Secret com o conteúdo do `expenses_config.json` e monte-o em `/app/data/expenses_config.json`.

---

## 🔐 Configurações Sensíveis & `expenses_config.json`

- O arquivo `data/expenses_config.json` é mantido no `.gitignore` por conter valores de negócio sensíveis.
- O código atual segue a ordem de prioridade ao inicializar a configuração:
  1. `data/expenses_config.json` (se existir)
  2. Conteúdo da variável de ambiente `EXPENSES_CONFIG_JSON` (se definido)
  3. `data/expenses_config.template.json` (copiado somente se não houver o arquivo real)
  4. Esqueleto vazio criado como último recurso

**Se o host estiver usando o template**, significa que o arquivo real não está presente no ambiente. Para garantir que o host use os dados reais:
- Monte `data/expenses_config.json` como volume/secret no host ou
- Configure `EXPENSES_CONFIG_JSON` com o JSON do arquivo (preferível em secret managers)

---

## 🧪 Testes

- Testes unitários estão em `tests/`.
- Para executar:

```bash
pip install pytest
pytest -q
```

---

## 🛠️ Boas Práticas

- Nunca comite dados sensíveis (`data/expenses_config.json`, senhas, chaves)
- Use secret managers ou volumes para injetar configurações em produção
- Configure variables de ambiente para senhas/hashe
- Monitore o uso do banco e faça backups regulares

---

## 🤝 Contribuição

- Abra uma issue para discutir alterações maiores
- Envie PRs com descrição clara e testes quando aplicável

---

## ❓ Suporte

Se quiser, posso:
- Adicionar instruções de deploy (Dockerfile/Helm/Procfile) completas
- Implementar leitura automática de `EXPENSES_CONFIG` via `/run/secrets` (Docker Secrets)
- Atualizar os exemplos `.env` e `data/expenses_config.template.json`

---

**Observação:** o repositório não contém um arquivo `LICENSE`. Adicione uma licença antes de publicar.

---

Obrigado por usar o JB Home Essence! ✨

2. Ajuste estoque se necessário: `[1] → [4] Ajustar estoque`

### CSV Corrompido
**Causa:** Edição manual incorreta

**Solução:**
1. Restaure do backup: `data/*.csv.backup_*`
2. Ou delete e deixe o sistema recriar:
```bash
rm data/products.csv
python main.py  # Recria automaticamente
```

---

## 📝 Boas Práticas de Uso

### Backup Regular
```bash
# Crie backup manual
cp data/products.csv data/products.csv.backup
cp data/clients.csv data/clients.csv.backup
cp data/sales.csv data/sales.csv.backup
```

### Verificação de Integridade
```bash
# Verifique schemas
python verify_schema.py
```

### Nunca Edite CSV Manualmente
- Use sempre a interface do sistema
- Se precisar editar, faça backup primeiro
- Respeite o schema exato (nomes de colunas)

---

## 🎓 Arquitetura

### Padrões Utilizados
- **Repository Pattern:** Isolamento de dados
- **Service Layer:** Lógica de negócio
- **Data Transfer Objects:** Entidades tipadas
- **Transaction Pattern:** Operações atômicas

### Fluxo de Dados
```
Interface (UI)
      ↓
Service Layer (Business Logic)
      ↓
Repository Layer (Data Access)
      ↓
CSV Files (Storage)
```

### Transações de Venda
```
1. Validate Client → ✓
2. Validate Product → ✓
3. Check Stock → ✓
4. Save Sale → ✓ (Commit Point 1)
5. Update Inventory → ✓ (Commit Point 2)
   ↓ (if fails)
   Rollback: Delete Sale
```

---

## 🚀 Próximos Passos (Roadmap)

### Fase 2: Analytics Avançado
- [ ] Gráficos de vendas
- [ ] Previsão de demanda
- [ ] Análise de sazonalidade
- [ ] Relatórios exportáveis (PDF/Excel)

### Fase 3: Interface Web
- [ ] Dashboard web com Flask/FastAPI
- [ ] API REST para integrações
- [ ] Multi-usuário com autenticação

### Fase 4: Database
- [ ] Migração para SQLite/PostgreSQL
- [ ] Backup automático
- [ ] Histórico de alterações

---

## 📄 Licença

Este projeto foi desenvolvido para uso em produção em perfumaria.

---

## 👨‍💻 Desenvolvimento

**Arquitetura:** Clean Architecture  
**Linguagem:** Python 3.8+  
**Paradigma:** Orientado a Objetos + Funcional  
**Qualidade:** Type hints, docstrings, testes abrangentes  

---

## 📞 Suporte

Para problemas ou dúvidas:
1. Consulte `TROUBLESHOOTING.md`
2. Execute os testes relevantes
3. Verifique os logs de erro
4. Restaure de backup se necessário

---

**Sistema pronto para produção! 🎉**

Execute `python main.py` e comece a gerenciar sua perfumaria de forma profissional.