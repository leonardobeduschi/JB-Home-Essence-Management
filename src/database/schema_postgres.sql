-- Schema for JB Home Essence - PostgreSQL/Supabase Version
-- FIXED: Column names in UPPERCASE to match SQLite
-- PostgreSQL is case-sensitive when using quoted identifiers

-- PRODUCTS
CREATE TABLE IF NOT EXISTS products (
    "CODIGO" VARCHAR(50) PRIMARY KEY,
    "PRODUTO" VARCHAR(255) NOT NULL,
    "CATEGORIA" VARCHAR(100) NOT NULL,
    "CUSTO" NUMERIC(10, 2) NOT NULL DEFAULT 0,
    "VALOR" NUMERIC(10, 2) NOT NULL DEFAULT 0,
    "ESTOQUE" INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CLIENTS
CREATE TABLE IF NOT EXISTS clients (
    "ID_CLIENTE" VARCHAR(50) PRIMARY KEY,
    "CLIENTE" VARCHAR(255) NOT NULL,
    "VENDEDOR" VARCHAR(255),
    "TIPO" VARCHAR(50) NOT NULL,
    "IDADE" VARCHAR(50),
    "GENERO" VARCHAR(50),
    "PROFISSAO" VARCHAR(255),
    "CPF_CNPJ" VARCHAR(50),
    "TELEFONE" VARCHAR(50),
    "ENDERECO" TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SALES
CREATE TABLE IF NOT EXISTS sales (
    "ID_VENDA" VARCHAR(50) PRIMARY KEY,
    "ID_CLIENTE" VARCHAR(50),
    "CLIENTE" VARCHAR(255) NOT NULL,
    "MEIO" VARCHAR(50) NOT NULL,
    "DATA" VARCHAR(20) NOT NULL,
    "VALOR_TOTAL_VENDA" NUMERIC(10, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sales_cliente 
        FOREIGN KEY ("ID_CLIENTE") 
        REFERENCES clients("ID_CLIENTE") 
        ON DELETE SET NULL 
        ON UPDATE CASCADE
);

-- SALES ITEMS
CREATE TABLE IF NOT EXISTS sales_items (
    id SERIAL PRIMARY KEY,
    "ID_VENDA" VARCHAR(50) NOT NULL,
    "PRODUTO" VARCHAR(255) NOT NULL,
    "CATEGORIA" VARCHAR(100) NOT NULL,
    "CODIGO" VARCHAR(50),  -- Nullable para kits/promoções
    "QUANTIDADE" INTEGER NOT NULL,
    "PRECO_UNIT" NUMERIC(10, 2) NOT NULL,
    "PRECO_TOTAL" NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sales_items_venda 
        FOREIGN KEY ("ID_VENDA") 
        REFERENCES sales("ID_VENDA") 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_categoria ON products ("CATEGORIA");
CREATE INDEX IF NOT EXISTS idx_clients_tipo ON clients ("TIPO");
CREATE INDEX IF NOT EXISTS idx_sales_id_cliente ON sales ("ID_CLIENTE");
CREATE INDEX IF NOT EXISTS idx_sales_data ON sales ("DATA");
CREATE INDEX IF NOT EXISTS idx_sales_items_id_venda ON sales_items ("ID_VENDA");
CREATE INDEX IF NOT EXISTS idx_sales_items_codigo ON sales_items ("CODIGO");

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to tables
DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at 
    BEFORE UPDATE ON products 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_clients_updated_at ON clients;
CREATE TRIGGER update_clients_updated_at 
    BEFORE UPDATE ON clients 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();