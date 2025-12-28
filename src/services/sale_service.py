"""
Sale service for business logic - WITH MULTI-ITEM SUPPORT.
"""

from typing import Optional, List, Dict
from datetime import datetime
from collections import namedtuple
from src.models.sale import Sale, MeioPagamento
from src.repositories.sale_repository import SaleRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.client_repository import ClientRepository
from src.utils.id_generator import IDGenerator


SaleRecord = namedtuple('SaleRecord', [
    'ID_VENDA', 'DATA', 'CLIENTE', 'ID_CLIENTE', 'PRODUTO', 
    'CODIGO', 'CATEGORIA', 'QUANTIDADE', 'PRECO_UNIT', 
    'PRECO_TOTAL', 'MEIO'
])


class SaleService:
    """
    Service layer for sale business logic with multi-item support.
    """
    
    def __init__(
        self,
        sale_repository: Optional[SaleRepository] = None,
        product_repository: Optional[ProductRepository] = None,
        client_repository: Optional[ClientRepository] = None
    ):
        self.sale_repository = sale_repository or SaleRepository()
        self.product_repository = product_repository or ProductRepository()
        self.client_repository = client_repository or ClientRepository()
    
    def register_sale_multi_item(
        self,
        id_cliente: str,
        meio: str,
        items: List[Dict],
        data: Optional[str] = None
    ) -> List[Sale]:
        """
        Register a sale with MULTIPLE items (NEW METHOD).
        
        All items share the same ID_VENDA for grouping.
        Each item is saved as a separate CSV line for individual analysis.
        
        Args:
            id_cliente: Client ID
            meio: Payment method
            items: List of dicts with 'codigo', 'quantidade', 'preco_unit' (optional)
            data: Sale date DD/MM/YYYY (uses today if None)
            
        Returns:
            List of Sale instances
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # === STEP 1: Validate Client ===
            client = self.client_repository.get_by_id(id_cliente)
            if not client:
                raise ValueError(f"Cliente '{id_cliente}' não encontrado")
            
            # === STEP 2: Generate single ID_VENDA for all items ===
            existing_ids = [s['ID_VENDA'] for s in self.sale_repository.get_all().to_dict('records')]
            id_venda = IDGenerator.generate_sale_id(existing_ids)
            
            # Use today's date if not specified
            if data is None:
                data = datetime.now().strftime('%d/%m/%Y')
            
            # === STEP 3: Validate all items and check stock ===
            validated_items = []
            for item in items:
                codigo = item['codigo']
                quantidade = int(item['quantidade'])
                preco_unit = item.get('preco_unit')
                
                # Validate product
                product = self.product_repository.get_by_codigo(codigo)
                if not product:
                    raise ValueError(f"Produto '{codigo}' não encontrado")
                
                # Check stock
                current_stock = int(product['ESTOQUE'])
                if current_stock < quantidade:
                    raise ValueError(
                        f"Estoque insuficiente para '{product['PRODUTO']}'. "
                        f"Disponível: {current_stock}. Solicitado: {quantidade}."
                    )
                
                # Use current product price if not specified
                if preco_unit is None:
                    preco_unit = float(product['VALOR'])
                
                validated_items.append({
                    'codigo': codigo,
                    'produto': product['PRODUTO'],
                    'categoria': product['CATEGORIA'],
                    'quantidade': quantidade,
                    'preco_unit': preco_unit,
                    'current_stock': current_stock
                })
            
            # === STEP 4: Create Sale instances (all with same ID_VENDA) ===
            sales = []
            for item in validated_items:
                sale = Sale(
                    id_venda=id_venda,  # SAME ID for all items
                    id_cliente=client['ID_CLIENTE'],
                    cliente=client['CLIENTE'],
                    meio=meio,
                    data=data,
                    produto=item['produto'],
                    categoria=item['categoria'],
                    codigo=item['codigo'],
                    quantidade=item['quantidade'],
                    preco_unit=item['preco_unit']
                )
                sales.append(sale)
            
            # === STEP 5: Save all sales ===
            for sale in sales:
                self.sale_repository.save(sale)
            
            # === STEP 6: Update inventory for all items ===
            try:
                for item in validated_items:
                    self.product_repository.update_stock(item['codigo'], -item['quantidade'])
            except Exception as e:
                # Rollback: delete all sales
                for sale in sales:
                    self.sale_repository.delete(sale.id_venda)
                raise Exception(f"Erro ao atualizar estoque (venda revertida): {str(e)}")
            
            # === SUCCESS ===
            total_value = sum(s.preco_total for s in sales)
            total_items = sum(s.quantidade for s in sales)
            
            print(f"✅ Venda registrada com sucesso!")
            print(f"  ID: {id_venda}")
            print(f"  Cliente: {client['CLIENTE']}")
            print(f"  Produtos: {len(sales)} diferentes")
            print(f"  Total de itens: {total_items} unidade(s)")
            print(f"  Valor total: R$ {total_value:.2f}")
            print(f"  Pagamento: {meio}")
            
            return sales
            
        except ValueError as e:
            raise ValueError(f"Erro ao registrar venda: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro inesperado ao registrar venda: {str(e)}")
    
    def register_sale(
        self,
        id_cliente: str,
        codigo: str,
        quantidade: int,
        meio: str,
        preco_unit: Optional[float] = None,
        data: Optional[str] = None
    ) -> Sale:
        """
        Register a SINGLE item sale (LEGACY method - kept for compatibility).
        """
        try:
            client = self.client_repository.get_by_id(id_cliente)
            if not client:
                raise ValueError(f"Cliente '{id_cliente}' não encontrado")
            
            product = self.product_repository.get_by_codigo(codigo)
            if not product:
                raise ValueError(f"Produto '{codigo}' não encontrado")
            
            current_stock = int(product['ESTOQUE'])
            if current_stock < quantidade:
                raise ValueError(
                    f"Estoque insuficiente para '{product['PRODUTO']}'. "
                    f"Disponível: {current_stock} unidades. "
                    f"Solicitado: {quantidade} unidades."
                )
            
            if preco_unit is None:
                preco_unit = float(product['VALOR'])
            
            if data is None:
                data = datetime.now().strftime('%d/%m/%Y')
            
            existing_ids = [s['ID_VENDA'] for s in self.sale_repository.get_all().to_dict('records')]
            id_venda = IDGenerator.generate_sale_id(existing_ids)
            
            sale = Sale(
                id_venda=id_venda,
                id_cliente=client['ID_CLIENTE'],
                cliente=client['CLIENTE'],
                meio=meio,
                data=data,
                produto=product['PRODUTO'],
                categoria=product['CATEGORIA'],
                codigo=product['CODIGO'],
                quantidade=quantidade,
                preco_unit=preco_unit
            )
            
            self.sale_repository.save(sale)
            
            try:
                self.product_repository.update_stock(codigo, -quantidade)
            except Exception as e:
                self.sale_repository.delete(id_venda)
                raise Exception(f"Erro ao atualizar estoque (venda revertida): {str(e)}")
            
            new_stock = current_stock - quantidade
            
            print(f"✅ Venda registrada com sucesso!")
            print(f"  ID: {sale.id_venda}")
            print(f"  Cliente: {sale.cliente}")
            print(f"  Produto: {sale.produto}")
            print(f"  Quantidade: {sale.quantidade} unidade(s)")
            print(f"  Preço unitário: R$ {sale.preco_unit:.2f}")
            print(f"  Total: R$ {sale.preco_total:.2f}")
            print(f"  Pagamento: {sale.get_payment_method_display()}")
            print(f"  Estoque atualizado: {current_stock} → {new_stock} unidades")
            
            return sale
            
        except ValueError as e:
            raise ValueError(f"Erro ao registrar venda: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro inesperado ao registrar venda: {str(e)}")
    
    def get_sale(self, id_venda: str) -> Optional[dict]:
        """Retrieve sale information by ID."""
        return self.sale_repository.get_by_id(id_venda)
    
    def get_sale_group(self, id_venda: str) -> List[dict]:
        """
        Get ALL items from a sale (grouped by ID_VENDA).
        NEW METHOD for multi-item sales.
        """
        return self.sale_repository.get_by_sale_id(id_venda)
    
    def list_all_sales(self) -> List[SaleRecord]:
        """List all sales as objects."""
        df = self.sale_repository.get_all()
        sales_list = df.to_dict('records')
        converted_sales = []
        for item in sales_list:
            preco_total = item['PRECO_TOTAL']
            if isinstance(preco_total, str):
                preco_total = float(preco_total.replace('R$ ', '').replace(',', '.'))
            else:
                preco_total = float(preco_total)
            
            quantidade = int(item['QUANTIDADE'])
            preco_unit = float(item['PRECO_UNIT'])

            produto_norm = str(item.get('PRODUTO', '')).strip().title()
            categoria_norm = str(item.get('CATEGORIA', '')).strip().title()
            
            sale = SaleRecord(
                ID_VENDA=item['ID_VENDA'],
                DATA=item['DATA'],
                CLIENTE=item['CLIENTE'],
                ID_CLIENTE=item['ID_CLIENTE'],
                PRODUTO=produto_norm,
                CODIGO=item['CODIGO'],
                CATEGORIA=categoria_norm,
                QUANTIDADE=quantidade,
                PRECO_UNIT=preco_unit,
                PRECO_TOTAL=preco_total,
                MEIO=item['MEIO']
            )
            converted_sales.append(sale)
        return converted_sales
    
    def list_sales_by_client(self, id_cliente: str) -> List[dict]:
        return self.sale_repository.get_by_client(id_cliente)
    
    def list_sales_by_product(self, codigo: str) -> List[dict]:
        return self.sale_repository.get_by_product(codigo)
    
    def list_sales_by_date_range(self, start_date: str, end_date: str) -> List[dict]:
        return self.sale_repository.get_by_date_range(start_date, end_date)
    
    def list_sales_by_payment_method(self, meio: str) -> List[dict]:
        return self.sale_repository.get_by_payment_method(meio)
    
    def get_sales_summary(self) -> dict:
        """Get sales summary with CORRECT average ticket (by unique ID_VENDA)."""
        import pandas as pd
        
        summary = self.sale_repository.get_sales_summary()
        
        # Calculate unique sales count and correct average
        df = self.sale_repository.get_all()
        if not df.empty:
            unique_sales = df['ID_VENDA'].nunique()
            df['PRECO_TOTAL_NUM'] = pd.to_numeric(df['PRECO_TOTAL'], errors='coerce').fillna(0)
            
            # Group by ID_VENDA and sum totals
            grouped = df.groupby('ID_VENDA')['PRECO_TOTAL_NUM'].sum()
            correct_avg = grouped.mean()
            
            summary['unique_sales_count'] = unique_sales
            summary['average_sale_value'] = float(correct_avg)
        
        print("\n" + "="*60)
        print("  RESUMO DE VENDAS")
        print("="*60)
        print(f"Total de vendas únicas: {summary.get('unique_sales_count', summary['total_sales'])}")
        print(f"Total de linhas/itens: {summary['total_sales']}")
        print(f"Receita total: R$ {summary['total_revenue']:.2f}")
        print(f"Itens vendidos: {summary['total_items_sold']}")
        print(f"Ticket médio (CORRETO): R$ {summary['average_sale_value']:.2f}")
        
        if summary['by_payment_method']:
            print("\nPor meio de pagamento:")
            for meio, valor in summary['by_payment_method'].items():
                print(f"  - {meio.title()}: R$ {valor:.2f}")
        
        if summary['by_category']:
            print("\nPor categoria:")
            for cat, valor in summary['by_category'].items():
                print(f"  - {cat}: R$ {valor:.2f}")
        
        print("="*60)
        
        return summary
    
    def get_top_products(self, limit: int = 10) -> List[dict]:
        products = self.sale_repository.get_top_products(limit)
        
        if products:
            print(f"\n🏆 Top {len(products)} Produtos Mais Vendidos:")
            for i, p in enumerate(products, 1):
                print(f"{i}. {p['PRODUTO']} ({p['CODIGO']})")
                print(f"   Quantidade: {int(p['QUANTIDADE_TOTAL'])} unidades")
                print(f"   Receita: R$ {float(p['RECEITA_TOTAL']):.2f}")
        
        return products
    
    def get_top_clients(self, limit: int = 10) -> List[dict]:
        clients = self.sale_repository.get_top_clients(limit)
        
        if clients:
            print(f"\n🏆 Top {len(clients)} Melhores Clientes:")
            for i, c in enumerate(clients, 1):
                print(f"{i}. {c['CLIENTE']} ({c['ID_CLIENTE']})")
                print(f"   Compras: {int(c['NUM_COMPRAS'])}")
                print(f"   Total gasto: R$ {float(c['TOTAL_GASTO']):.2f}")
        
        return clients
    
    def get_available_payment_methods(self) -> List[str]:
        return [e.value for e in MeioPagamento]
    
    def calculate_sale_total(self, codigo: str, quantidade: int) -> dict:
        product = self.product_repository.get_by_codigo(codigo)
        if not product:
            raise ValueError(f"Produto '{codigo}' não encontrado")
        
        preco_unit = float(product['VALOR'])
        preco_total = preco_unit * quantidade
        estoque = int(product['ESTOQUE'])
        
        return {
            'produto': product['PRODUTO'],
            'codigo': codigo,
            'preco_unit': preco_unit,
            'quantidade': quantidade,
            'preco_total': preco_total,
            'estoque_disponivel': estoque,
            'estoque_suficiente': estoque >= quantidade
        }
    
    def cancel_sale(self, id_venda: str, restore_stock: bool = True) -> bool:
        """Cancel sale and restore stock (works with multi-item sales)."""
        # Get ALL items from this sale
        items = self.sale_repository.get_by_sale_id(id_venda)
        if not items:
            raise ValueError(f"Venda '{id_venda}' não encontrada")
        
        try:
            if restore_stock:
                for item in items:
                    codigo = item['CODIGO']
                    quantidade = int(item['QUANTIDADE'])
                    
                    product = self.product_repository.get_by_codigo(codigo)
                    if product:
                        self.product_repository.update_stock(codigo, quantidade)
                        print(f"✅ Estoque restaurado: +{quantidade} unidade(s) de {item['PRODUTO']}")
                    else:
                        print(f"⚠️ Produto {codigo} não existe mais. Estoque NÃO foi restaurado.")
            
            # Delete ALL items with this ID_VENDA
            self.sale_repository.delete_by_sale_id(id_venda)
            
            print(f"✅ Venda {id_venda} cancelada com sucesso ({len(items)} item(s))")
            return True
            
        except Exception as e:
            raise Exception(f"Erro ao cancelar venda: {str(e)}")