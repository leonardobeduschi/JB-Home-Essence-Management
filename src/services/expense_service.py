"""
Expense Service - Gerenciamento de despesas fixas mensais.

Este serviço calcula o impacto das despesas fixas na margem de lucro.
"""

import json
import os
from typing import Dict, List


class ExpenseService:
    """Service para gerenciar despesas e calcular impactos na margem."""
    
    def __init__(self, config_file: str = 'data/expenses_config.json'):
        """
        Initialize expense service.
        
        Args:
            config_file: Path to expenses configuration JSON
        """
        self.config_file = config_file
        self._ensure_config_file()
    
    def _ensure_config_file(self) -> None:
        """Ensure config file exists with default values."""
        if not os.path.exists(self.config_file):
            default_config = {
                "monthly_fixed_expenses": {
                    "imposto": {"name": "Impostos", "value": 76.90, "description": "Impostos mensais fixos"},
                    "transportadora": {"name": "Transportadora", "value": 200.00, "description": "Frete e transporte mensal"},
                    "marketing": {"name": "Marketing", "value": 300.00, "description": "Despesas com marketing"},
                    "tim": {"name": "TIM (Telefonia)", "value": 65.00, "description": "Conta de telefone"},
                    "celesc": {"name": "CELESC (Energia)", "value": 110.00, "description": "Conta de energia"}
                }
            }
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
    
    def get_monthly_expenses(self) -> Dict:
        """
        Get all monthly fixed expenses.
        
        Returns:
            Dictionary with expense data
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('monthly_fixed_expenses', {})
        except Exception as e:
            print(f"Erro ao carregar despesas: {e}")
            return {}
    
    def get_total_monthly_expenses(self) -> float:
        """
        Calculate total monthly fixed expenses.
        
        Returns:
            Total monthly expenses
        """
        expenses = self.get_monthly_expenses()
        total = sum(exp.get('value', 0) for exp in expenses.values())
        return float(total)
    
    def get_expense_per_sale(self, monthly_sales_count: int) -> float:
        """
        Calculate expense allocation per sale.
        
        Distributes monthly fixed expenses across all sales in the month.
        
        Args:
            monthly_sales_count: Number of sales in the month
            
        Returns:
            Expense per sale
        """
        if monthly_sales_count == 0:
            return 0.0
        
        total_expenses = self.get_total_monthly_expenses()
        return total_expenses / monthly_sales_count
    
    def calculate_real_profit_margin(
        self,
        sale_price: float,
        cost_price: float,
        quantity: int,
        monthly_sales_count: int
    ) -> Dict:
        """
        Calculate real profit margin considering fixed expenses.
        
        Formula:
        - Gross Profit = (Sale Price - Cost Price) * Quantity
        - Allocated Expense = Monthly Expenses / Monthly Sales Count
        - Net Profit = Gross Profit - Allocated Expense
        - Net Margin % = (Net Profit / Total Revenue) * 100
        
        Args:
            sale_price: Unit selling price
            cost_price: Unit cost price
            quantity: Quantity sold
            monthly_sales_count: Total sales in the month
            
        Returns:
            Dictionary with profit calculations
        """
        # Basic calculations
        total_revenue = sale_price * quantity
        total_cost = cost_price * quantity
        gross_profit = total_revenue - total_cost
        gross_margin_pct = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Allocated expense
        expense_per_sale = self.get_expense_per_sale(monthly_sales_count)
        
        # Net profit
        net_profit = gross_profit - expense_per_sale
        net_margin_pct = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        return {
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'gross_profit': gross_profit,
            'gross_margin_pct': gross_margin_pct,
            'allocated_expense': expense_per_sale,
            'net_profit': net_profit,
            'net_margin_pct': net_margin_pct,
            'monthly_total_expenses': self.get_total_monthly_expenses()
        }
    
    def get_product_real_margin(
        self,
        sale_price: float,
        cost_price: float,
        estimated_monthly_sales: int = 100
    ) -> Dict:
        """
        Calculate product's real margin estimate.
        
        Uses estimated monthly sales for calculation.
        
        Args:
            sale_price: Product selling price
            cost_price: Product cost
            estimated_monthly_sales: Estimated sales per month
            
        Returns:
            Margin calculations
        """
        return self.calculate_real_profit_margin(
            sale_price=sale_price,
            cost_price=cost_price,
            quantity=1,
            monthly_sales_count=estimated_monthly_sales
        )
    
    def get_expenses_breakdown(self) -> List[Dict]:
        """
        Get detailed breakdown of all expenses.
        
        Returns:
            List of expenses with details
        """
        expenses = self.get_monthly_expenses()
        breakdown = []
        
        for key, data in expenses.items():
            breakdown.append({
                'id': key,
                'name': data.get('name', key),
                'value': data.get('value', 0),
                'description': data.get('description', '')
            })
        
        # Sort by value (descending)
        breakdown.sort(key=lambda x: x['value'], reverse=True)
        
        return breakdown
    
    def update_expense(self, expense_id: str, new_value: float) -> bool:
        """
        Update an expense value.
        
        Args:
            expense_id: Expense identifier
            new_value: New value
            
        Returns:
            True if successful
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if expense_id in config.get('monthly_fixed_expenses', {}):
                config['monthly_fixed_expenses'][expense_id]['value'] = float(new_value)
                
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                
                return True
            else:
                raise ValueError(f"Despesa '{expense_id}' não encontrada")
                
        except Exception as e:
            print(f"Erro ao atualizar despesa: {e}")
            return False
    
    def add_expense(self, expense_id: str, name: str, value: float, description: str = "") -> bool:
        """
        Add a new expense.
        
        Args:
            expense_id: Unique identifier
            name: Display name
            value: Monthly value
            description: Description
            
        Returns:
            True if successful
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if expense_id in config.get('monthly_fixed_expenses', {}):
                raise ValueError(f"Despesa '{expense_id}' já existe")
            
            if 'monthly_fixed_expenses' not in config:
                config['monthly_fixed_expenses'] = {}
            
            config['monthly_fixed_expenses'][expense_id] = {
                'name': name,
                'value': float(value),
                'description': description
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Erro ao adicionar despesa: {e}")
            return False
    
    def remove_expense(self, expense_id: str) -> bool:
        """
        Remove an expense.
        
        Args:
            expense_id: Expense identifier
            
        Returns:
            True if successful
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if expense_id not in config.get('monthly_fixed_expenses', {}):
                raise ValueError(f"Despesa '{expense_id}' não encontrada")
            
            del config['monthly_fixed_expenses'][expense_id]
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Erro ao remover despesa: {e}")
            return False