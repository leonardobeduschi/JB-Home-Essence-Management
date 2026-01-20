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
    'PRECO_TOTAL', 'MEIO', 'VALOR_TOTAL_VENDA'  # ← Adicionado
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
    
    """
Substitua o método register_sale_multi_item no seu sale_service.py por este:
"""

    def register_sale_multi_item(
        self,
        id_cliente: str,
        meio: str,
        items: List[Dict],
        data: Optional[str] = None
    ) -> Dict:
        """
        Register a sale with MULTIPLE items - FIXED for new structure.
        
        Args:
            id_cliente: Client ID
            meio: Payment method
            items: List of dicts with 'codigo', 'quantidade', 'preco_unit' (optional)
            data: Sale date DD/MM/YYYY (uses today if None)
            
        Returns:
            Dict with sale info
            
        Raises:
            ValueError: If validation fails
        """
        from src.models.sale_item import SaleItem
        from src.repositories.sale_item_repository import SaleItemRepository
        from src.utils.id_generator import IDGenerator
        
        try:
            # === STEP 1: Validate Client ===
            client = self.client_repository.get_by_id(id_cliente)
            if not client:
                raise ValueError(f"Cliente '{id_cliente}' não encontrado")
            
            # === STEP 2: Generate single ID_VENDA for all items ===
            existing_ids = [s['ID_VENDA'] for s in self.sale_repository.get_all().to_dict('records')]
            id_venda = IDGenerator.generate_sale_id(existing_ids)
            
            # Use provided date or today's date
            if data is None:
                data = datetime.now().strftime('%d/%m/%Y')
            else:
                # Validate date format (DD/MM/YYYY)
                try:
                    datetime.strptime(data, '%d/%m/%Y')
                except ValueError:
                    raise ValueError("Formato de data inválido. Use DD/MM/YYYY")
            
            # === STEP 3: Validate all items and check stock ===
            validated_items = []
            total_venda = 0.0
            
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
                else:
                    preco_unit = float(preco_unit)
                
                preco_total = preco_unit * quantidade
                total_venda += preco_total
                
                validated_items.append({
                    'codigo': codigo,
                    'produto': product['PRODUTO'],
                    'categoria': product['CATEGORIA'],
                    'quantidade': quantidade,
                    'preco_unit': preco_unit,
                    'preco_total': preco_total,
                    'current_stock': current_stock
                })
            
            # === STEP 4: Create Sale header ===
            from src.models.sale import Sale
            
            sale = Sale(
                id_venda=id_venda,
                id_cliente=client['ID_CLIENTE'],
                cliente=client['CLIENTE'],
                meio=meio,
                data=data,
                valor_total_venda=total_venda
            )
            
            # === STEP 5: Create SaleItem instances ===
            sale_items = []
            for item in validated_items:
                sale_item = SaleItem(
                    id_venda=id_venda,
                    produto=item['produto'],
                    categoria=item['categoria'],
                    codigo=item['codigo'],
                    quantidade=item['quantidade'],
                    preco_unit=item['preco_unit'],
                    preco_total=item['preco_total']
                )
                sale_items.append(sale_item)
            
            # === STEP 6: Save sale header ===
            self.sale_repository.save(sale)
            
            # === STEP 7: Save all sale items ===
            item_repo = SaleItemRepository()
            try:
                item_repo.save_many(sale_items)
            except Exception as e:
                # Rollback: delete sale header
                self.sale_repository.delete(id_venda)
                raise Exception(f"Erro ao salvar itens (venda revertida): {str(e)}")
            
            # === STEP 8: Update inventory for all items ===
            try:
                for item in validated_items:
                    self.product_repository.update_stock(item['codigo'], -item['quantidade'])
            except Exception as e:
                # Rollback: delete sale header and items
                item_repo.delete_by_sale_id(id_venda)
                self.sale_repository.delete(id_venda)
                raise Exception(f"Erro ao atualizar estoque (venda revertida): {str(e)}")
            
            # === SUCCESS ===
            total_items = sum(item['quantidade'] for item in validated_items)
            
            print("✅ Venda registrada com sucesso!")
            print(f"  ID: {id_venda}")
            print(f"  Data: {data}")
            print(f"  Cliente: {client['CLIENTE']}")
            print(f"  Produtos: {len(sale_items)} diferentes")
            print(f"  Total de itens: {total_items} unidade(s)")
            print(f"  Valor total: R$ {total_venda:.2f}")
            print(f"  Pagamento: {meio}")
            
            return {
                'id_venda': id_venda,
                'total_items': len(sale_items),
                'total_quantity': total_items,
                'total_value': total_venda
            }
            
        except ValueError as e:
            raise ValueError(f"Erro ao registrar venda: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro inesperado ao registrar venda: {str(e)}")
    
    """
Substitua o método register_sale (legacy - single item) no seu sale_service.py:
"""

    def register_sale(
        self,
        id_cliente: str,
        codigo: str,
        quantidade: int,
        meio: str,
        preco_unit: Optional[float] = None,
        data: Optional[str] = None
    ) -> Dict:
        """
        Register a SINGLE item sale (LEGACY method - kept for compatibility).
        
        Now redirects to register_sale_multi_item with single item.
        
        Args:
            id_cliente: Client ID
            codigo: Product code
            quantidade: Quantity
            meio: Payment method
            preco_unit: Unit price (optional, uses product price if None)
            data: Sale date DD/MM/YYYY (uses today if None)
            
        Returns:
            Dict with sale info
        """
        # Get product to determine price if not specified
        product = self.product_repository.get_by_codigo(codigo)
        if not product:
            raise ValueError(f"Produto '{codigo}' não encontrado")
        
        if preco_unit is None:
            preco_unit = float(product['VALOR'])
        
        # Create single item list
        items = [{
            'codigo': codigo,
            'quantidade': quantidade,
            'preco_unit': preco_unit
        }]
        
        # Call multi-item method
        return self.register_sale_multi_item(
            id_cliente=id_cliente,
            meio=meio,
            items=items,
            data=data
        )
    
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
        """
        List all sales as objects - FIXED.
        
        Returns a FLAT list where each line represents one ITEM sold.
        """
        from src.repositories.sale_item_repository import SaleItemRepository
        
        # OTIMIZADO: Usa find_all() em vez de get_all()/_read_csv()
        sales = self.sale_repository.find_all()
        
        item_repo = SaleItemRepository()
        items = item_repo.find_all()
        
        if not items:
            return []
        
        # Cria map de vendas por ID para lookup rápido
        sales_map = {sale['ID_VENDA']: sale for sale in sales}
        
        # Convert to list
        converted_sales = []
        
        for item in items:
            # Find corresponding sale header
            sale = sales_map.get(item['ID_VENDA'])
            
            if not sale:
                continue  # Skip orphan items
            
            # Create SaleRecord with data from BOTH sources
            try:
                preco_total = float(item['PRECO_TOTAL'])
                quantidade = int(item['QUANTIDADE'])
                preco_unit = float(item['PRECO_UNIT'])
                valor_total_venda = float(sale['VALOR_TOTAL_VENDA'])
                
                produto_norm = str(item.get('PRODUTO', '')).strip().title()
                categoria_norm = str(item.get('CATEGORIA', '')).strip().title()
                
                sale_record = SaleRecord(
                    ID_VENDA=sale['ID_VENDA'],
                    DATA=sale['DATA'],
                    CLIENTE=sale['CLIENTE'],
                    ID_CLIENTE=sale['ID_CLIENTE'],
                    PRODUTO=produto_norm,
                    CODIGO=item['CODIGO'],
                    CATEGORIA=categoria_norm,
                    QUANTIDADE=quantidade,
                    PRECO_UNIT=preco_unit,
                    PRECO_TOTAL=preco_total,
                    MEIO=sale['MEIO'],
                    VALOR_TOTAL_VENDA=valor_total_venda
                )
                converted_sales.append(sale_record)
                
            except (ValueError, KeyError, TypeError) as e:
                print(f"Error processing sale item: {e}")
                continue
        
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
        """
        Get sales summary - FIXED for new structure.
        Uses sales.csv as SINGLE SOURCE OF TRUTH for revenue.
        """
        import pandas as pd
        
        # Get summary from repository (already correct)
        summary = self.sale_repository.get_sales_summary()
        
        # The repository already returns the correct data:
        # - total_sales: unique sales count from sales.csv
        # - total_revenue: sum of VALOR_TOTAL_VENDA from sales.csv ← CORRECT
        # - total_items_sold: sum of quantities from sales_items.csv
        # - average_sale_value: average from sales.csv
        # - by_payment_method: grouped by payment from sales.csv
        # - by_category: grouped from sales_items.csv
        
        # Print summary (clean version)
        print("\n" + "="*60)
        print("  RESUMO DE VENDAS")
        print("="*60)
        print(f"Total de vendas: {summary['total_sales']}")
        print(f"Receita total: R$ {summary['total_revenue']:.2f}")
        print(f"Itens vendidos: {summary['total_items_sold']}")
        print(f"Ticket médio: R$ {summary['average_sale_value']:.2f}")
        
        if summary['by_payment_method']:
            print("\nPor meio de pagamento:")
            for meio, valor in summary['by_payment_method'].items():
                print(f"  - {meio}: R$ {valor:.2f}")
        
        if summary['by_category']:
            print("\nPor categoria:")
            for cat, valor in sorted(summary['by_category'].items(), key=lambda x: x[1], reverse=True):
                print(f"  - {cat}: R$ {valor:.2f}")
        
        print("="*60 + "\n")
        
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
    
    """
Substitua o método cancel_sale no seu sale_service.py por este:
"""

    def cancel_sale(self, id_venda: str, restore_stock: bool = True) -> bool:
        """
        Cancel sale and restore stock (works with multi-item sales) - FIXED.
        
        Args:
            id_venda: Sale ID to cancel
            restore_stock: Whether to restore inventory
            
        Returns:
            True if successful
        """
        from src.repositories.sale_item_repository import SaleItemRepository
        
        # Get ALL items from this sale
        item_repo = SaleItemRepository()
        items = item_repo.get_by_sale_id(id_venda)
        
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
            item_repo.delete_by_sale_id(id_venda)
            
            # Delete sale header
            self.sale_repository.delete(id_venda)
            
            print(f"✅ Venda {id_venda} cancelada com sucesso ({len(items)} item(s))")
            return True
            
        except Exception as e:
            raise Exception(f"Erro ao cancelar venda: {str(e)}")