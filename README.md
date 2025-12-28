# Sistema de Gestão para Perfumaria

Sistema completo de gerenciamento de vendas, estoque e clientes desenvolvido em Python com arquitetura limpa e profissional.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)

---

## 📋 Índice

- [Características](#-características)
- [Instalação](#-instalação)
- [Como Usar](#-como-usar)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Schemas dos Dados](#-schemas-dos-dados)
- [Funcionalidades Detalhadas](#-funcionalidades-detalhadas)
- [Testes](#-testes)
- [Solução de Problemas](#-solução-de-problemas)

---

## ✨ Características

### Gestão de Produtos
- ✅ Cadastro com código único
- ✅ Controle de custo e preço de venda
- ✅ Gestão automática de estoque
- ✅ Cálculo de margem de lucro
- ✅ Alertas de estoque baixo
- ✅ Relatório de valor de inventário

### Gestão de Clientes
- ✅ Cadastro de pessoas físicas e empresas
- ✅ Validação de CPF/CNPJ com algoritmo brasileiro
- ✅ Campos obrigatórios por tipo (pessoa vs empresa)
- ✅ Formatação automática de telefone
- ✅ Busca por ID, nome ou CPF/CNPJ

### Gestão de Vendas
- ✅ Registro transacional (tudo ou nada)
- ✅ Cálculo automático de totais
- ✅ Atualização automática de estoque
- ✅ Validação de disponibilidade
- ✅ Múltiplas formas de pagamento
- ✅ Histórico completo de vendas

### Relatórios e Estatísticas
- ✅ Resumo de vendas por período
- ✅ Top produtos mais vendidos
- ✅ Top clientes por faturamento
- ✅ Análise por categoria
- ✅ Análise por meio de pagamento
- ✅ Estatísticas de clientes

---

## 🚀 Instalação

### Requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Passo a Passo

1. **Clone ou baixe o projeto:**
```bash
cd perfumery_system
```

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

3. **Execute o sistema:**
```bash
python main.py
```

---

## 💻 Como Usar

### Executar o Sistema

```bash
python main.py
```

### Interface do Menu Principal

```
==================================================================
  SISTEMA DE GESTÃO - PERFUMARIA
==================================================================

Opções:
  [1] 📦 Gerenciar Produtos
  [2] 👥 Gerenciar Clientes
  [3] 💰 Registrar Venda
  [4] 📊 Relatórios e Estatísticas
  [5] 📋 Listar Dados
  [0] 🚪 Sair

Escolha uma opção:
```

---

## 📂 Estrutura do Projeto

```
perfumery_system/
│
├── data/                          # Armazenamento CSV
│   ├── products.csv               # Produtos
│   ├── clients.csv                # Clientes
│   └── sales.csv                  # Vendas
│
├── src/                           # Código-fonte
│   ├── models/                    # Modelos de dados
│   │   ├── product.py             # Entidade Produto
│   │   ├── client.py              # Entidade Cliente
│   │   └── sale.py                # Entidade Venda
│   │
│   ├── repositories/              # Camada de dados
│   │   ├── base_repository.py    # Repositório base
│   │   ├── product_repository.py
│   │   ├── client_repository.py
│   │   └── sale_repository.py
│   │
│   ├── services/                  # Lógica de negócio
│   │   ├── product_service.py
│   │   ├── client_service.py
│   │   └── sale_service.py
│   │
│   ├── validators/                # Validações
│   │   └── client_validator.py   # CPF/CNPJ, telefone
│   │
│   ├── utils/                     # Utilitários
│   │   └── id_generator.py       # Geração de IDs
│   │
│   └── ui/                        # Interface do usuário
│       ├── menu.py                # Sistema de menus
│       └── display.py             # Formatação de dados
│
├── main.py                        # Ponto de entrada
├── requirements.txt               # Dependências
│
├── test_products_manual.py        # Testes de produtos
├── test_clients_manual.py         # Testes de clientes
├── test_sales_manual.py           # Testes de vendas
│
├── quick_example.py               # Exemplo rápido (produtos)
├── quick_example_clients.py       # Exemplo rápido (clientes)
└── quick_example_sales.py         # Exemplo rápido (vendas)
```

---

## 📊 Schemas dos Dados

### Products (produtos.csv)
```csv
CODIGO,PRODUTO,CATEGORIA,CUSTO,VALOR,ESTOQUE
AROMA001,Lavanda Premium,Aromas Florais,25.50,42.00,100
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| CODIGO | string | Código único do produto |
| PRODUTO | string | Nome do produto |
| CATEGORIA | string | Categoria do produto |
| CUSTO | float | Preço de custo unitário |
| VALOR | float | Preço de venda unitário |
| ESTOQUE | int | Quantidade em estoque |

### Clients (clients.csv)
```csv
ID_CLIENTE,CLIENTE,VENDEDOR,TIPO,IDADE,GENERO,PROFISSAO,CPF_CNPJ,TELEFONE,ENDERECO
CLI001,João Silva,Maria,pessoa,25-34,Masculino,Engenheiro,123.456.789-09,(11) 98765-4321,
```

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| ID_CLIENTE | string | Sim | ID único (CLI001, CLI002...) |
| CLIENTE | string | Sim | Nome do cliente |
| VENDEDOR | string | Sim | Nome do vendedor |
| TIPO | string | Sim | "pessoa" ou "empresa" |
| IDADE | string | Se pessoa | Faixa etária |
| GENERO | string | Se pessoa | Gênero |
| PROFISSAO | string | Não | Profissão |
| CPF_CNPJ | string | Se empresa | CPF ou CNPJ |
| TELEFONE | string | Não | Telefone formatado |
| ENDERECO | string | Se empresa | Endereço completo |

**Regras de Negócio:**
- **Pessoa:** IDADE e GENERO obrigatórios
- **Empresa:** CPF_CNPJ e ENDERECO obrigatórios, IDADE e GENERO vazios

### Sales (sales.csv)
```csv
ID_VENDA,ID_CLIENTE,CLIENTE,MEIO,DATA,PRODUTO,CATEGORIA,CODIGO,QUANTIDADE,PRECO_UNIT,PRECO_TOTAL
VND001,CLI001,João Silva,pix,18/12/2025,Lavanda Premium,Aromas Florais,AROMA001,5,42.00,210.00
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| ID_VENDA | string | ID único (VND001, VND002...) |
| ID_CLIENTE | string | Referência ao cliente |
| CLIENTE | string | Nome do cliente (auto-preenchido) |
| MEIO | string | Forma de pagamento |
| DATA | string | Data da venda (DD/MM/YYYY) |
| PRODUTO | string | Nome do produto (auto-preenchido) |
| CATEGORIA | string | Categoria (auto-preenchido) |
| CODIGO | string | Código do produto |
| QUANTIDADE | int | Quantidade vendida |
| PRECO_UNIT | float | Preço unitário no momento da venda |
| PRECO_TOTAL | float | Total (auto-calculado) |

---

## 🎯 Funcionalidades Detalhadas

### 1. Cadastro de Produtos

**Menu:** `[1] Gerenciar Produtos → [1] Cadastrar novo produto`

**Fluxo:**
1. Insira o código único do produto
2. Insira nome, categoria, custo e preço de venda
3. Defina estoque inicial
4. Sistema calcula margem automaticamente
5. Produto é salvo em `data/products.csv`

**Validações:**
- Código não pode ser duplicado
- Custo e preço devem ser > 0
- Estoque deve ser >= 0

---

### 2. Cadastro de Clientes

**Menu:** `[2] Gerenciar Clientes → [1] Cadastrar novo cliente`

**Para Pessoa Física:**
1. Nome e vendedor
2. Faixa etária (seleção de lista)
3. Gênero (obrigatório)
4. CPF (opcional)
5. Telefone e endereço (opcionais)

**Para Empresa:**
1. Nome e vendedor
2. CNPJ (obrigatório, validado)
3. Endereço (obrigatório)
4. Telefone (opcional)
5. Campos idade e gênero ficam vazios automaticamente

**Validações:**
- CPF: 11 dígitos com algoritmo de verificação
- CNPJ: 14 dígitos com algoritmo de verificação
- Telefone: (00) 00000-0000 ou (00) 0000-0000

---

### 3. Registro de Vendas

**Menu:** `[3] Registrar Venda`

**Fluxo Transacional:**
1. **Selecionar cliente** (por ID)
2. **Selecionar produto** (por código)
3. Sistema mostra: preço, estoque disponível
4. **Definir quantidade**
5. Sistema calcula e mostra total
6. **Confirmar venda**
7. **Selecionar meio de pagamento**
8. **Transação:**
   - ✅ Salva venda
   - ✅ Atualiza estoque automaticamente
   - ✅ Se falhar, faz rollback

**Segurança:**
- Verifica estoque antes de vender
- Transação all-or-nothing (atômica)
- Não permite venda sem estoque

---

### 4. Relatórios

#### Resumo de Vendas
**Menu:** `[4] Relatórios → [1] Resumo de vendas`

Exibe:
- Total de vendas
- Receita total
- Itens vendidos
- Ticket médio
- Vendas por meio de pagamento
- Vendas por categoria

#### Top Produtos
**Menu:** `[4] Relatórios → [2] Top produtos`

Lista produtos mais vendidos por:
- Quantidade total vendida
- Receita gerada

#### Top Clientes
**Menu:** `[4] Relatórios → [3] Top clientes`

Lista clientes por:
- Total gasto
- Número de compras

---

## 🧪 Testes

### Testar Produtos
```bash
python test_products_manual.py
```

Testa:
- Cadastro de produtos
- Atualização de dados
- Ajustes de estoque
- Validações
- Alertas de estoque baixo

### Testar Clientes
```bash
python test_clients_manual.py
```

Testa:
- Cadastro pessoa e empresa
- Validação CPF/CNPJ
- Regras de tipo (pessoa vs empresa)
- Busca e listagem

### Testar Vendas
```bash
python test_sales_manual.py
```

Testa:
- Registro de vendas
- Atualização de estoque
- Validações transacionais
- Cálculo de totais
- Rollback em caso de erro

### Exemplos Rápidos
```bash
# Produtos
python quick_example.py

# Clientes
python quick_example_clients.py

# Vendas
python quick_example_sales.py
```

---

## 🔧 Solução de Problemas

### Erro: "ModuleNotFoundError"
**Causa:** Executando de diretório errado

**Solução:**
```bash
# Certifique-se de estar na raiz do projeto
cd perfumery_system
python main.py
```

### Erro: Dados Perdidos após Migração
**Causa:** CSV com colunas acentuadas

**Solução:**
```bash
python fix_existing_clients.py
```

Ver `TROUBLESHOOTING.md` para detalhes.

### Erro: "Estoque insuficiente"
**Causa:** Tentando vender mais do que disponível

**Solução:**
1. Verifique estoque: `[1] Gerenciar Produtos → [5] Listar produtos`
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