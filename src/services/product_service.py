"""
Product service for business logic.

This module orchestrates product operations, validation, and business rules.
"""

from typing import Optional, List, Dict
from src.models.product import Product
from src.repositories.product_repository import ProductRepository


class ProductService:
    """
    Service layer for product business logic.
    
    Handles product registration, updates, and inventory management
    while enforcing business rules and validation.
    """
    
    def __init__(self, repository: Optional[ProductRepository] = None):
        """
        Initialize the product service.
        
        Args:
            repository: ProductRepository instance (creates new if None)
        """
        self.repository = repository or ProductRepository()
    
    def register_product(
        self,
        codigo: str,
        produto: str,
        categoria: str,
        custo: float,
        valor: float,
        estoque: int
    ) -> Product:
        """
        Register a new product in the system.
        
        Validates all inputs and ensures CODIGO uniqueness before saving.
        
        Args:
            codigo: Unique product code
            produto: Product name
            categoria: Product category
            custo: Unit cost (must be > 0)
            valor: Unit selling price (must be > 0)
            estoque: Initial stock quantity (must be >= 0)
            
        Returns:
            Product instance if successful
            
        Raises:
            ValueError: If validation fails or CODIGO already exists
        """
        try:
            # Create Product instance (validates automatically)
            product = Product(
                codigo=codigo,
                produto=produto,
                categoria=categoria,
                custo=custo,
                valor=valor,
                estoque=estoque
            )
            
            # Save to repository
            self.repository.save(product)
            
            margin = product.calculate_margin()
            print(f"✓ Produto '{product.produto}' cadastrado com sucesso!")
            print(f"  Código: {product.codigo}")
            print(f"  Custo: R$ {product.custo:.2f}")
            print(f"  Preço de venda: R$ {product.valor:.2f}")
            print(f"  Margem de lucro: {margin:.1f}%")
            print(f"  Estoque inicial: {product.estoque} unidades")
            
            return product
            
        except ValueError as e:
            # Re-raise validation errors with context
            raise ValueError(f"Erro ao cadastrar produto: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro inesperado ao cadastrar produto: {str(e)}")
    
    def update_product_info(
        self,
        codigo: str,
        **updates
    ) -> bool:
        """
        Update product information (name, category, cost, price).
        
        Args:
            codigo: Product code to update
            **updates: Fields to update (produto, categoria, custo, valor)
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If product not found or validation fails
        """
        try:
            # Verify product exists
            product = self.repository.get_by_codigo(codigo)
            if not product:
                raise ValueError(f"Produto '{codigo}' não encontrado")
            
            # Filter valid update fields (exclude ESTOQUE - use adjust_stock for that)
            valid_updates = {}
            for key in ['PRODUTO', 'CATEGORIA', 'CUSTO', 'VALOR']:
                if key.lower() in updates:
                    valid_updates[key] = updates[key.lower()]
            
            if not valid_updates:
                raise ValueError("Nenhum campo válido para atualizar")
            
            # Update via repository
            self.repository.update(codigo, valid_updates)
            
            print(f"✓ Produto '{codigo}' atualizado com sucesso!")
            
            # Show new margin if price or cost changed
            if 'CUSTO' in valid_updates or 'VALOR' in valid_updates:
                updated = self.repository.get_by_codigo(codigo)
                custo = float(updated['CUSTO'])
                valor = float(updated['VALOR'])
                margin = ((valor - custo) / custo) * 100 if custo > 0 else 0
                print(f"  Nova margem de lucro: {margin:.1f}%")
            
            return True
            
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Erro ao atualizar produto: {str(e)}")
    
    def adjust_stock(
        self,
        codigo: str,
        quantity: int,
        reason: str = "ajuste manual"
    ) -> bool:
        """
        Manually adjust product stock.
        
        Use this for inventory corrections, not for sales.
        Sales should use the SaleService which calls this automatically.
        
        Args:
            codigo: Product code
            quantity: Quantity to add (positive) or subtract (negative)
            reason: Reason for adjustment (for logging/audit)
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If product not found or insufficient stock
        """
        try:
            # Verify product exists
            product = self.repository.get_by_codigo(codigo)
            if not product:
                raise ValueError(f"Produto '{codigo}' não encontrado")
            
            # Update stock
            self.repository.update_stock(codigo, quantity)
            
            current_stock = int(product['ESTOQUE'])
            new_stock = current_stock + quantity
            
            action = "adicionadas" if quantity > 0 else "removidas"
            print(f"✓ Estoque ajustado ({reason})")
            print(f"  Produto: {product['PRODUTO']}")
            print(f"  Quantidade {action}: {abs(quantity)} unidades")
            print(f"  Estoque anterior: {current_stock}")
            print(f"  Estoque atual: {new_stock}")
            
            return True
            
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Erro ao ajustar estoque: {str(e)}")
    
    def get_product(self, codigo: str) -> Optional[Dict]:
        """
        Retrieve product information by code.
        
        Args:
            codigo: Product code
            
        Returns:
            Product data dictionary or None if not found
        """
        return self.repository.get_by_codigo(codigo)
    
    def list_all_products(self) -> List[Dict]:
        """
        List all products in the system.
        
        Returns:
            List of all products
        """
        products = self.repository.find_all()
        # Sort by category (alpha) then by product name (alpha)
        return sorted(products, key=lambda p: (str(p.get('CATEGORIA', '')).lower(), str(p.get('PRODUTO', '')).lower()))
    
    def list_by_category(self, categoria: str) -> List[Dict]:
        """
        List products in a specific category.
        
        Args:
            categoria: Category name
            
        Returns:
            List of products in the category
        """
        return self.repository.get_by_category(categoria)
    
    def check_low_stock(self, threshold: int = 5) -> List[Dict]:
        """
        Get products with low stock levels.
        
        Useful for inventory alerts and reordering.
        
        Args:
            threshold: Stock level threshold (default: 5)
            
        Returns:
            List of products below threshold
        """
        products = self.repository.get_low_stock(threshold)
        
        if products:
            print(f"\n⚠️  {len(products)} produto(s) com estoque baixo:")
            for p in products:
                print(f"  - {p['PRODUTO']} ({p['CODIGO']}): {p['ESTOQUE']} unidades")
        else:
            print(f"✓ Nenhum produto com estoque abaixo de {threshold} unidades")
        
        return products
    
    def product_exists(self, codigo: str) -> bool:
        """
        Check if a product exists in the system.
        
        Args:
            codigo: Product code
            
        Returns:
            True if product exists
        """
        return self.repository.exists(codigo)
    
    def get_stock_quantity(self, codigo: str) -> Optional[int]:
        """
        Get current stock quantity for a product.
        
        Args:
            codigo: Product code
            
        Returns:
            Stock quantity or None if product not found
        """
        product = self.repository.get_by_codigo(codigo)
        if product:
            return int(product['ESTOQUE'])
        return None
    
    def get_product_price(self, codigo: str) -> Optional[float]:
        """
        Get selling price for a product.
        
        Args:
            codigo: Product code
            
        Returns:
            Selling price (VALOR) or None if product not found
        """
        product = self.repository.get_by_codigo(codigo)
        if product:
            return float(product['VALOR'])
        return None
    
    def get_inventory_summary(self) -> Dict:
        """
        Get comprehensive inventory summary.
        
        Returns:
            Dictionary with inventory statistics
        """
        all_products = self.repository.find_all()
        values = self.repository.get_inventory_value()
        
        total_products = len(all_products)
        total_items = sum(int(p.get('ESTOQUE', 0)) for p in all_products)
        
        summary = {
            'total_products': total_products,
            'total_items': int(total_items),
            'inventory_cost_value': values['cost_value'],
            'inventory_retail_value': values['retail_value'],
            'potential_profit': values['retail_value'] - values['cost_value']
        }
        
        print("\n" + "="*60)
        print("  RESUMO DO INVENTÁRIO")
        print("="*60)
        print(f"Total de produtos cadastrados: {summary['total_products']}")
        print(f"Total de itens em estoque: {summary['total_items']}")
        print(f"Valor do estoque (custo): R$ {summary['inventory_cost_value']:.2f}")
        print(f"Valor do estoque (varejo): R$ {summary['inventory_retail_value']:.2f}")
        print(f"Lucro potencial: R$ {summary['potential_profit']:.2f}")
        print("="*60)
        
        return summary
    
    def delete_product(self, codigo: str) -> bool:
        """
        Delete a product from the system.
        
        Use with caution - this is permanent.
        Consider checking for existing sales before deleting.
        
        Args:
            codigo: Product code to delete
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If product not found
        """
        try:
            product = self.repository.get_by_codigo(codigo)
            if not product:
                raise ValueError(f"Produto '{codigo}' não encontrado")
            
            self.repository.delete(codigo)
            
            print(f"✓ Produto '{product['PRODUTO']}' ({codigo}) removido do sistema")
            return True
            
        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Erro ao deletar produto: {str(e)}")