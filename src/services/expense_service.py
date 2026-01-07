"""
Expense Service - Gerenciamento de custos com modelo financeiro correto.

Separação clara:
- Custos Variáveis: variam com cada venda (taxas, embalagens)
- Despesas Fixas: mensais independentes do volume

IMPORTANTE: Margem de produto NÃO usa despesas fixas.
"""

import json
import os
from typing import Dict, List, Optional


class ExpenseService:
    """Service para gerenciar custos e calcular margens corretas."""
    
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
                "variable_costs": {
                    "payment_fee": {
                        "name": "Taxa de Pagamento",
                        "type": "percentage",
                        "value": 3.5,
                        "description": "Taxa de processamento (%)",
                        "applies_to": ["pix", "cartao_credito", "cartao_debito"]
                    },
                    "packaging": {
                        "name": "Embalagem",
                        "type": "fixed_per_unit",
                        "value": 2.00,
                        "description": "Custo por produto"
                    },
                    "shipping_materials": {
                        "name": "Material de Envio",
                        "type": "fixed_per_sale",
                        "value": 1.50,
                        "description": "Etiquetas, fitas"
                    }
                },
                "monthly_fixed_expenses": {
                    "imposto": {"name": "Impostos", "value": 76.90},
                    "transportadora": {"name": "Transportadora", "value": 200.00},
                    "marketing": {"name": "Marketing", "value": 100.00},
                    "tim": {"name": "TIM", "value": 65.00},
                    "celesc": {"name": "CELESC", "value": 50.00},
                    "santho_aroma": {"name": "Santho Aroma", "value": 1500.00}
                }
            }
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
    
    # ========== CUSTOS VARIÁVEIS ==========
    
    def get_variable_costs(self) -> Dict:
        """Get all variable cost configurations."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('variable_costs', {})
        except Exception as e:
            print(f"Erro ao carregar custos variáveis: {e}")
            return {}
    
    def calculate_variable_costs(
        self,
        sale_revenue: float,
        quantity: int,
        payment_method: str = 'pix'
    ) -> Dict[str, float]:
        """
        Calcular custos variáveis de uma venda.
        
        Args:
            sale_revenue: Receita total da venda
            quantity: Quantidade de unidades
            payment_method: Meio de pagamento
            
        Returns:
            Dicionário com breakdown dos custos variáveis
        """
        variable_costs = self.get_variable_costs()
        costs = {}
        
        # Taxa de pagamento (% da receita)
        payment_fee_config = variable_costs.get('payment_fee', {})
        payment_lower = payment_method.lower().replace(' ', '_')
        applies_to = [m.lower().replace(' ', '_') for m in payment_fee_config.get('applies_to', [])]
        
        if payment_lower in applies_to:
            fee_pct = float(payment_fee_config.get('value', 0))
            costs['payment_fee'] = sale_revenue * (fee_pct / 100)
        else:
            costs['payment_fee'] = 0.0
        
        # Embalagem (por unidade)
        packaging_config = variable_costs.get('packaging', {})
        costs['packaging'] = float(packaging_config.get('value', 0)) * quantity
        
        # Materiais por venda
        shipping_config = variable_costs.get('shipping_materials', {})
        costs['shipping_materials'] = float(shipping_config.get('value', 0))
        
        # Cartões/adesivos (se existir)
        card_config = variable_costs.get('card_materials', {})
        if card_config:
            costs['card_materials'] = float(card_config.get('value', 0)) * quantity
        
        costs['total'] = sum(costs.values())
        
        return costs
    
    # ========== DESPESAS FIXAS ==========
    
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
    
    # ========== CÁLCULO DE MARGEM CORRETO ==========
    
    def calculate_product_margin(
        self,
        sale_price: float,
        cost_price: float,
        quantity: int = 1,
        payment_method: str = 'pix'
    ) -> Dict:
        """
        Calcular margem de contribuição do produto (CORRETO).
        
        Fórmula:
        - Receita = Preço × Quantidade
        - Custo = COGS × Quantidade
        - Custos Variáveis = Taxas + Embalagem + Materiais
        - Margem de Contribuição = Receita - Custo - Custos Variáveis
        - Margem % = (Contribuição / Receita) × 100
        
        IMPORTANTE: Despesas fixas NÃO entram na margem do produto.
        
        Args:
            sale_price: Preço unitário de venda
            cost_price: Custo unitário (COGS)
            quantity: Quantidade vendida
            payment_method: Meio de pagamento
            
        Returns:
            Dicionário com cálculos de margem
        """
        # Receita e custo de produto
        revenue = sale_price * quantity
        cogs = cost_price * quantity
        gross_profit = revenue - cogs
        gross_margin_pct = (gross_profit / revenue * 100) if revenue > 0 else 0
        
        # Custos variáveis
        var_costs = self.calculate_variable_costs(revenue, quantity, payment_method)
        
        # Margem de contribuição (o que realmente importa)
        contribution_margin = gross_profit - var_costs['total']
        contribution_margin_pct = (contribution_margin / revenue * 100) if revenue > 0 else 0
        
        return {
            'revenue': revenue,
            'cogs': cogs,
            'gross_profit': gross_profit,
            'gross_margin_pct': gross_margin_pct,
            'variable_costs_breakdown': var_costs,
            'variable_costs_total': var_costs['total'],
            'contribution_margin': contribution_margin,
            'contribution_margin_pct': contribution_margin_pct,
            'unit_contribution': contribution_margin / quantity if quantity > 0 else 0
        }
    
    # ========== MÉTODOS LEGADOS (compatibilidade) ==========
    
    def get_expense_per_sale(self, monthly_sales_count: int) -> float:
        """
        DEPRECATED: Este método não deve ser usado para margem de produto.
        
        Mantido apenas para compatibilidade com código antigo.
        Use calculate_monthly_pnl() para análise de negócio.
        """
        if monthly_sales_count == 0:
            return 0.0
        return self.get_total_monthly_expenses() / monthly_sales_count
    
    def calculate_real_profit_margin(
        self,
        sale_price: float,
        cost_price: float,
        quantity: int,
        monthly_sales_count: int  # IGNORADO agora
    ) -> Dict:
        """
        COMPATIBILIDADE: Redireciona para calculate_product_margin.
        
        ATENÇÃO: monthly_sales_count agora é IGNORADO.
        Margem de produto não depende do volume mensal.
        
        Returns formato antigo para não quebrar código existente.
        """
        margin_data = self.calculate_product_margin(
            sale_price=sale_price,
            cost_price=cost_price,
            quantity=quantity,
            payment_method='pix'  # Assume pix por padrão
        )
        
        # Mapeia para formato antigo
        return {
            'total_revenue': margin_data['revenue'],
            'total_cost': margin_data['cogs'],
            'gross_profit': margin_data['gross_profit'],
            'gross_margin_pct': margin_data['gross_margin_pct'],
            'allocated_expense': margin_data['variable_costs_total'],  # Agora são custos variáveis
            'net_profit': margin_data['contribution_margin'],
            'net_margin_pct': margin_data['contribution_margin_pct'],
            'monthly_total_expenses': self.get_total_monthly_expenses()  # Apenas info
        }
    
    def get_product_real_margin(
        self,
        sale_price: float,
        cost_price: float,
        estimated_monthly_sales: int = 100  # IGNORADO
    ) -> Dict:
        """
        COMPATIBILIDADE: Calcula margem do produto.
        
        estimated_monthly_sales agora é IGNORADO.
        """
        return self.calculate_real_profit_margin(
            sale_price=sale_price,
            cost_price=cost_price,
            quantity=1,
            monthly_sales_count=estimated_monthly_sales  # Ignorado internamente
        )
    
    # ========== ANÁLISE DE NEGÓCIO (onde despesas fixas entram) ==========
    
    def calculate_monthly_pnl(
        self,
        total_contribution_margin: float,
        actual_fixed_expenses: Optional[float] = None
    ) -> Dict:
        """
        Calcular P&L mensal (análise de negócio).
        
        AQUI é onde as despesas fixas entram.
        
        Args:
            total_contribution_margin: Soma de todas as contribuições de vendas
            actual_fixed_expenses: Override de despesas fixas se necessário
            
        Returns:
            Dicionário com dados de P&L
        """
        fixed_expenses = actual_fixed_expenses if actual_fixed_expenses is not None \
                        else self.get_total_monthly_expenses()
        
        net_profit = total_contribution_margin - fixed_expenses
        
        return {
            'total_contribution_margin': total_contribution_margin,
            'fixed_expenses': fixed_expenses,
            'net_profit': net_profit,
            'profit_margin_pct': (net_profit / total_contribution_margin * 100) \
                                if total_contribution_margin > 0 else 0
        }
    
    def calculate_breakeven(self, avg_contribution_per_sale: float) -> Dict:
        """
        Calcular ponto de equilíbrio.
        
        Break-even = Despesas Fixas / Margem de Contribuição Média
        """
        fixed_expenses = self.get_total_monthly_expenses()
        
        if avg_contribution_per_sale <= 0:
            return {
                'breakeven_sales': float('inf'),
                'message': 'Margem negativa - impossível break-even'
            }
        
        breakeven_sales = fixed_expenses / avg_contribution_per_sale
        
        return {
            'fixed_expenses': fixed_expenses,
            'avg_contribution_per_sale': avg_contribution_per_sale,
            'breakeven_sales': breakeven_sales,
            'message': f'Necessário {breakeven_sales:.0f} vendas para cobrir custos fixos'
        }
    
    # ========== BREAKDOWN & RELATÓRIOS ==========
    
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
        
        breakdown.sort(key=lambda x: x['value'], reverse=True)
        
        return breakdown
    
    def get_variable_costs_breakdown(self) -> List[Dict]:
        """Obter breakdown de custos variáveis."""
        var_costs = self.get_variable_costs()
        breakdown = []
        
        for key, data in var_costs.items():
            breakdown.append({
                'id': key,
                'name': data.get('name', key),
                'type': data.get('type', 'unknown'),
                'value': data.get('value', 0),
                'description': data.get('description', '')
            })
        
        return breakdown
    
    # ========== GESTÃO DE CONFIGURAÇÃO ==========
    
    def update_expense(self, expense_id: str, new_value: float) -> bool:
        """Update a fixed expense value."""
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
    
    def update_variable_cost(self, cost_id: str, new_value: float) -> bool:
        """Atualizar um custo variável."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if cost_id in config.get('variable_costs', {}):
                config['variable_costs'][cost_id]['value'] = float(new_value)
                
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                
                return True
            raise ValueError(f"Custo variável '{cost_id}' não encontrado")
        except Exception as e:
            print(f"Erro ao atualizar custo: {e}")
            return False
    
    def add_expense(self, expense_id: str, name: str, value: float, description: str = "") -> bool:
        """Add a new fixed expense."""
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
        """Remove a fixed expense."""
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
        
    # ========== PROJEÇÕES E METAS ==========

    def get_salary_goals(self) -> Dict:
        """Obter metas salariais configuradas."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('salary_goals', {
                    'employees': 3,
                    'target_salary_per_employee': 2000.00,
                    'total_monthly_salary_goal': 6000.00
                })
        except Exception as e:
            print(f"Erro ao carregar metas: {e}")
            return {
                'employees': 3,
                'target_salary_per_employee': 2000.00,
                'total_monthly_salary_goal': 6000.00
            }

    def calculate_required_revenue(
        self,
        avg_contribution_margin_pct: float,
        target_net_profit: Optional[float] = None
    ) -> Dict:
        """
        Calcular receita necessária para atingir meta de lucro.
        
        Args:
            avg_contribution_margin_pct: Margem de contribuição média (%)
            target_net_profit: Meta de lucro líquido (usa salary_goal se None)
            
        Returns:
            Análise de receita necessária
        """
        fixed_expenses = self.get_total_monthly_expenses()
        
        if target_net_profit is None:
            salary_goals = self.get_salary_goals()
            target_net_profit = salary_goals['total_monthly_salary_goal']
        
        # Receita necessária = (Despesas Fixas + Meta de Lucro) / Margem %
        if avg_contribution_margin_pct <= 0:
            return {
                'error': 'Margem de contribuição deve ser positiva',
                'required_revenue': float('inf')
            }
        
        required_revenue = (fixed_expenses + target_net_profit) / (avg_contribution_margin_pct / 100)
        
        return {
            'fixed_expenses': fixed_expenses,
            'target_net_profit': target_net_profit,
            'avg_contribution_margin_pct': avg_contribution_margin_pct,
            'required_monthly_revenue': required_revenue,
            'current_gap': None  # Será preenchido pelo caller se tiver receita atual
        }

    def calculate_sales_needed(
        self,
        avg_ticket: float,
        avg_contribution_per_sale: float,
        target_net_profit: Optional[float] = None
    ) -> Dict:
        """
        Calcular número de vendas necessárias para atingir meta.
        
        Args:
            avg_ticket: Ticket médio por venda
            avg_contribution_per_sale: Margem de contribuição média por venda
            target_net_profit: Meta de lucro (usa salary_goal se None)
            
        Returns:
            Número de vendas necessárias
        """
        fixed_expenses = self.get_total_monthly_expenses()
        
        if target_net_profit is None:
            salary_goals = self.get_salary_goals()
            target_net_profit = salary_goals['total_monthly_salary_goal']
        
        if avg_contribution_per_sale <= 0:
            return {
                'error': 'Margem de contribuição por venda deve ser positiva',
                'sales_needed': float('inf')
            }
        
        # Vendas necessárias = (Despesas + Meta) / Contribuição por Venda
        sales_needed = (fixed_expenses + target_net_profit) / avg_contribution_per_sale
        revenue_needed = sales_needed * avg_ticket
        
        return {
            'fixed_expenses': fixed_expenses,
            'target_net_profit': target_net_profit,
            'avg_ticket': avg_ticket,
            'avg_contribution_per_sale': avg_contribution_per_sale,
            'sales_needed_monthly': sales_needed,
            'sales_needed_daily': sales_needed / 30,
            'revenue_needed_monthly': revenue_needed,
            'revenue_needed_daily': revenue_needed / 30
        }

    def analyze_current_performance(
        self,
        current_monthly_revenue: float,
        current_monthly_contribution: float,
        current_sales_count: int
    ) -> Dict:
        """
        Analisar performance atual vs metas.
        
        Args:
            current_monthly_revenue: Receita do mês atual
            current_monthly_contribution: Margem de contribuição do mês
            current_sales_count: Número de vendas no mês
            
        Returns:
            Análise completa de performance
        """
        fixed_expenses = self.get_total_monthly_expenses()
        salary_goals = self.get_salary_goals()
        target_profit = salary_goals['total_monthly_salary_goal']
        
        # Performance atual
        current_net_profit = current_monthly_contribution - fixed_expenses
        current_margin_pct = (current_monthly_contribution / current_monthly_revenue * 100) if current_monthly_revenue > 0 else 0
        
        # O que precisa
        required_revenue = self.calculate_required_revenue(current_margin_pct, target_profit)
        
        # Gap
        revenue_gap = required_revenue['required_monthly_revenue'] - current_monthly_revenue
        profit_gap = target_profit - current_net_profit
        
        # Projeção
        if current_sales_count > 0:
            avg_ticket = current_monthly_revenue / current_sales_count
            avg_contribution = current_monthly_contribution / current_sales_count
            
            additional_sales_needed = profit_gap / avg_contribution if avg_contribution > 0 else float('inf')
        else:
            avg_ticket = 0
            avg_contribution = 0
            additional_sales_needed = float('inf')
        
        return {
            'current_performance': {
                'revenue': current_monthly_revenue,
                'contribution_margin': current_monthly_contribution,
                'net_profit': current_net_profit,
                'margin_pct': current_margin_pct,
                'sales_count': current_sales_count,
                'avg_ticket': avg_ticket
            },
            'targets': {
                'fixed_expenses': fixed_expenses,
                'salary_goal': target_profit,
                'total_needed_profit': target_profit,
                'required_revenue': required_revenue['required_monthly_revenue']
            },
            'gaps': {
                'revenue_gap': revenue_gap,
                'profit_gap': profit_gap,
                'additional_sales_needed': additional_sales_needed,
                'pct_of_goal_achieved': (current_net_profit / target_profit * 100) if target_profit > 0 else 0
            },
            'status': 'above_goal' if current_net_profit >= target_profit else 'below_goal'
        }