-- Schema for JB Home Essence (mirrors CSV files exactly in column names)
-- Notes:
--  - Column names are kept exactly as in the CSV files (uppercase)
--  - Numeric/monetary values use NUMERIC (SQLite affinity); integer counts use INTEGER
--  - Dates are stored as TEXT (CSV stores dates as dd/mm/yyyy)

-- PRODUCTS
CREATE TABLE IF NOT EXISTS products (
    CODIGO TEXT PRIMARY KEY,
    PRODUTO TEXT,
    CATEGORIA TEXT,
    CUSTO NUMERIC,
    VALOR NUMERIC,
    ESTOQUE INTEGER
);

-- CLIENTS
CREATE TABLE IF NOT EXISTS clients (
    ID_CLIENTE TEXT PRIMARY KEY,
    CLIENTE TEXT,
    VENDEDOR TEXT,
    TIPO TEXT,
    IDADE TEXT,
    GENERO TEXT,
    PROFISSAO TEXT,
    CPF_CNPJ TEXT,
    TELEFONE TEXT,
    ENDERECO TEXT
);

-- SALES
CREATE TABLE IF NOT EXISTS sales (
    ID_VENDA TEXT PRIMARY KEY,
    ID_CLIENTE TEXT,
    CLIENTE TEXT,
    MEIO TEXT,
    DATA TEXT,
    VALOR_TOTAL_VENDA NUMERIC,
    FOREIGN KEY (ID_CLIENTE) REFERENCES clients(ID_CLIENTE) ON DELETE SET NULL ON UPDATE CASCADE
);

-- SALES ITEMS
CREATE TABLE IF NOT EXISTS sales_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ID_VENDA TEXT NOT NULL,
    PRODUTO TEXT,
    CATEGORIA TEXT,
    CODIGO TEXT,
    QUANTIDADE INTEGER,
    PRECO_UNIT NUMERIC,
    PRECO_TOTAL NUMERIC,
    FOREIGN KEY (ID_VENDA) REFERENCES sales(ID_VENDA) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Indexes to speed lookups
CREATE INDEX IF NOT EXISTS idx_products_categoria ON products (CATEGORIA);
CREATE INDEX IF NOT EXISTS idx_sales_id_cliente ON sales (ID_CLIENTE);
CREATE INDEX IF NOT EXISTS idx_sales_items_id_venda ON sales_items (ID_VENDA);
CREATE INDEX IF NOT EXISTS idx_sales_items_codigo ON sales_items (CODIGO);
