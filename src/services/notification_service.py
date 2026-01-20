"""
Notification Service - Sistema de alertas inteligente (CORRIGIDO)
"""

from typing import List, Dict
from datetime import datetime, timedelta
import pandas as pd
from src.repositories.product_repository import ProductRepository
from src.repositories.client_repository import ClientRepository
from src.repositories.sale_repository import SaleRepository
from src.repositories.sale_item_repository import SaleItemRepository
from src.repositories.notification_repository import NotificationRepository


# Tempos médios de duração por TIPO DE PRODUTO e tipo de cliente (em meses)
PRODUCT_DURATION = {
    'Home Spray 300Ml': {'pessoa': 6, 'empresa': 2},
    'Difusor De Varetas': {'pessoa': 3, 'empresa': 3},
    'Essência': {'pessoa': 2, 'empresa': 1},
    'Sabonete Líquido': {'pessoa': 2, 'empresa': 1},
    'Refil Home Spray': {'pessoa': 12, 'empresa': 3},
    'Refil Difusor De Varetas': {'pessoa': 6, 'empresa': 6},
    'Refil Sabonete Líquido': {'pessoa': 4, 'empresa': 2},
    'Água Perfumada': {'pessoa': 6, 'empresa': 2},
    'Kit Carro': {'pessoa': 6, 'empresa': None},
    'Velas Aromáticas': {'pessoa': 2, 'empresa': 2}
}


class NotificationService:
    """Service for managing notifications."""

    def __init__(self):
        self.product_repo = ProductRepository()
        self.client_repo = ClientRepository()
        self.sale_repo = SaleRepository()
        self.item_repo = SaleItemRepository()
        self.notification_repo = NotificationRepository()

    def _normalize_product_type(self, produto: str) -> str:
        """Normalize product type for matching (usa campo PRODUTO, não CATEGORIA)."""
        if not produto:
            return ''
        
        # Remove espaços extras e capitaliza
        normalized = str(produto).strip().title()
        
        # Mapeamento de variações para nomes padrão
        mapping = {
            'Home Spray 300Ml': ['Home Spray 300Ml', 'Home Spray', 'Homespray 300Ml'],
            'Difusor De Varetas': ['Difusor De Varetas', 'Difusor'],
            'Essência': ['Essência', 'Essencia'],
            'Sabonete Líquido': ['Sabonete Líquido', 'Sabonete Liquido'],
            'Refil Home Spray': ['Refil Home Spray', 'Refil Homespray'],
            'Refil Difusor De Varetas': ['Refil Difusor De Varetas', 'Refil Difusor'],
            'Refil Sabonete Líquido': ['Refil Sabonete Líquido', 'Refil Sabonete Liquido'],
            'Água Perfumada': ['Água Perfumada', 'Agua Perfumada'],
            'Kit Carro': ['Kit Carro', 'Kit'],
            'Velas Aromáticas': ['Velas Aromáticas', 'Velas', 'Vela Aromatica']
        }
        
        # Busca correspondência exata
        for standard, variations in mapping.items():
            for variation in variations:
                if variation.lower() == normalized.lower():
                    return standard
        
        # Se não encontrou correspondência exata, tenta match parcial
        produto_lower = normalized.lower()
        if 'home spray' in produto_lower or 'homespray' in produto_lower:
            return 'Home Spray 300Ml'
        elif 'difusor' in produto_lower and 'refil' not in produto_lower:
            return 'Difusor De Varetas'
        elif 'refil' in produto_lower and 'difusor' in produto_lower:
            return 'Refil Difusor De Varetas'
        elif 'refil' in produto_lower and ('home' in produto_lower or 'spray' in produto_lower):
            return 'Refil Home Spray'
        elif 'refil' in produto_lower and 'sabonete' in produto_lower:
            return 'Refil Sabonete Líquido'
        elif 'sabonete' in produto_lower:
            return 'Sabonete Líquido'
        elif 'essencia' in produto_lower or 'essência' in produto_lower:
            return 'Essência'
        elif 'agua' in produto_lower or 'água' in produto_lower:
            return 'Água Perfumada'
        elif 'vela' in produto_lower:
            return 'Velas Aromáticas'
        elif 'kit' in produto_lower:
            return 'Kit Carro'
        
        return normalized

    def get_low_stock_notifications(self) -> List[Dict]:
        """Get products with critically low stock (≤1)."""
        notifications = []
        
        try:
            print("[NOTIFICATIONS] Getting low stock products...")
            low_stock = self.product_repo.get_low_stock(threshold=1)
            print(f"[NOTIFICATIONS] Found {len(low_stock)} low stock products")
            
            for product in low_stock:
                notif_key = f"low_stock_{product['CODIGO']}"
                
                if not self.notification_repo.is_dismissed('low_stock', notif_key):
                    notifications.append({
                        'id': notif_key,
                        'type': 'low_stock',
                        'severity': 'critical',
                        'icon': 'bi-exclamation-triangle-fill',
                        'title': 'Estoque Crítico',
                        'message': f"{product['PRODUTO']} - {product['CATEGORIA']}",
                        'detail': f"Apenas {product['ESTOQUE']} unidade(s) em estoque",
                        'data': product
                    })
        
        except Exception as e:
            print(f"[NOTIFICATIONS] Error getting low stock: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[NOTIFICATIONS] Returning {len(notifications)} low stock notifications")
        return notifications

    def get_repurchase_reminders(self) -> List[Dict]:
        """Get repurchase reminders based on product duration (CORRIGIDO - usa PRODUTO)."""
        notifications = []
        
        try:
            print("[NOTIFICATIONS] Starting repurchase reminders calculation...")
            
            # Get all data at once (OPTIMIZED)
            sales_df = self.sale_repo.get_all()
            items_df = self.item_repo._read_csv()
            clients_df = self.client_repo.get_all()
            
            print(f"[NOTIFICATIONS] Loaded {len(sales_df)} sales, {len(items_df)} items, {len(clients_df)} clients")
            
            if sales_df.empty or items_df.empty or clients_df.empty:
                print("[NOTIFICATIONS] Empty data, skipping repurchase reminders")
                return []
            
            # Convert to dict for fast lookup
            clients = clients_df.set_index('ID_CLIENTE').to_dict('index')
            
            # Parse dates in sales
            sales_df['DATA_DT'] = pd.to_datetime(sales_df['DATA'], format='%Y-%m-%d', errors='coerce')
            # Fallback para formato brasileiro
            mask = sales_df['DATA_DT'].isna()
            if mask.any():
                sales_df.loc[mask, 'DATA_DT'] = pd.to_datetime(
                    sales_df.loc[mask, 'DATA'], 
                    format='%d/%m/%Y', 
                    errors='coerce'
                )
            
            sales_df = sales_df[sales_df['DATA_DT'].notna()]
            
            # Merge sales with items
            merged = items_df.merge(
                sales_df[['ID_VENDA', 'ID_CLIENTE', 'DATA_DT']], 
                on='ID_VENDA', 
                how='left'
            )
            
            # ⚠️ CORREÇÃO: Usa coluna PRODUTO (tipo do produto), não CATEGORIA (fragrância)
            merged['PRODUTO_NORM'] = merged['PRODUTO'].apply(self._normalize_product_type)
            
            print(f"[NOTIFICATIONS] Merged data: {len(merged)} rows")
            print(f"[NOTIFICATIONS] Sample normalized products: {merged['PRODUTO_NORM'].value_counts().head(10).to_dict()}")
            
            # Track last purchase per client and product type
            client_purchases = {}
            
            for _, row in merged.iterrows():
                client_id = row['ID_CLIENTE']
                produto_norm = row['PRODUTO_NORM']
                sale_date = row['DATA_DT']
                categoria_fragrancia = row['CATEGORIA']  # Nome da fragrância (ex: Havana)
                
                if pd.isna(client_id) or pd.isna(sale_date):
                    continue
                
                client = clients.get(client_id)
                if not client:
                    continue
                
                client_type = str(client.get('TIPO', '')).lower()
                if client_type not in ['pessoa', 'empresa']:
                    continue
                
                # Check if we have duration data for this product type
                if produto_norm not in PRODUCT_DURATION:
                    print(f"[NOTIFICATIONS] No duration config for product type: {produto_norm}")
                    continue
                
                duration_config = PRODUCT_DURATION[produto_norm]
                expected_duration = duration_config.get(client_type)
                
                # Skip if this product is not sold to this client type
                if expected_duration is None:
                    continue
                
                # Track this purchase (keep most recent per client + product type + fragrance)
                key = (client_id, produto_norm, categoria_fragrancia)
                if key not in client_purchases:
                    client_purchases[key] = {
                        'client': client,
                        'produto_tipo': produto_norm,
                        'fragrancia': categoria_fragrancia,
                        'last_purchase': sale_date,
                        'expected_duration': expected_duration
                    }
                else:
                    if sale_date > client_purchases[key]['last_purchase']:
                        client_purchases[key]['last_purchase'] = sale_date
            
            print(f"[NOTIFICATIONS] Found {len(client_purchases)} unique client-product combinations")
            
            # Generate notifications
            today = pd.Timestamp.now()
            
            for (client_id, produto_tipo, fragrancia), data in client_purchases.items():
                last_purchase = data['last_purchase']
                expected_duration = data['expected_duration']
                client = data['client']
                
                # Calculate expected repurchase date
                repurchase_date = last_purchase + pd.Timedelta(days=expected_duration * 30)
                days_until_repurchase = (repurchase_date - today).days
                
                # Show notification if within 7 days or overdue
                if days_until_repurchase <= 7:
                    notif_key = f"repurchase_{client_id}_{produto_tipo}_{fragrancia}"
                    
                    if not self.notification_repo.is_dismissed('repurchase', notif_key):
                        client_type_label = 'Pessoa Física' if client['TIPO'].lower() == 'pessoa' else 'Empresa'
                        
                        if days_until_repurchase < 0:
                            severity = 'warning'
                            detail = f"Produto deve ter acabado há {abs(days_until_repurchase)} dias"
                        elif days_until_repurchase == 0:
                            severity = 'warning'
                            detail = "Produto deve acabar hoje"
                        else:
                            severity = 'info'
                            detail = f"Produto deve acabar em {days_until_repurchase} dias"
                        
                        notifications.append({
                            'id': notif_key,
                            'type': 'repurchase',
                            'severity': severity,
                            'icon': 'bi-clock-history',
                            'title': f'Lembrete de Recompra ({client_type_label})',
                            'message': f"{client['CLIENTE']} - {produto_tipo} ({fragrancia})",
                            'detail': detail,
                            'data': {
                                'client_id': client_id,
                                'client_name': client['CLIENTE'],
                                'client_type': client['TIPO'],
                                'produto_tipo': produto_tipo,
                                'fragrancia': fragrancia,
                                'last_purchase': last_purchase.strftime('%d/%m/%Y'),
                                'expected_repurchase': repurchase_date.strftime('%d/%m/%Y'),
                                'days_until': int(days_until_repurchase),
                                'phone': client.get('TELEFONE', '')
                            }
                        })
        
        except Exception as e:
            print(f"[NOTIFICATIONS] Error getting repurchase reminders: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[NOTIFICATIONS] Returning {len(notifications)} repurchase notifications")
        return notifications

    def get_all_notifications(self) -> Dict:
        """Get all notifications grouped by type."""
        print("[NOTIFICATIONS] Getting all notifications...")
        
        low_stock = self.get_low_stock_notifications()
        repurchase = self.get_repurchase_reminders()
        
        # Separate repurchase by client type
        repurchase_pessoa = [n for n in repurchase if n['data']['client_type'].lower() == 'pessoa']
        repurchase_empresa = [n for n in repurchase if n['data']['client_type'].lower() == 'empresa']
        
        total = len(low_stock) + len(repurchase)
        
        print(f"[NOTIFICATIONS] Total: {total} (low_stock: {len(low_stock)}, pessoa: {len(repurchase_pessoa)}, empresa: {len(repurchase_empresa)})")
        
        return {
            'low_stock': low_stock,
            'repurchase_pessoa': repurchase_pessoa,
            'repurchase_empresa': repurchase_empresa,
            'total_count': total
        }

    def dismiss_notification(self, notification_type: str, notification_id: str) -> bool:
        """Dismiss a notification."""
        return self.notification_repo.dismiss(notification_type, notification_id)

    def undismiss_notification(self, notification_type: str, notification_id: str) -> bool:
        """Restore a dismissed notification."""
        return self.notification_repo.undismiss(notification_type, notification_id)