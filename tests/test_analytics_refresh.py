import pytest
from datetime import datetime, timedelta
import pandas as pd
from src.repositories.sale_repository import SaleRepository
from src.services.sale_service import SaleService


def compute_recent_revenue(last_days=365):
    repo = SaleRepository()
    df = repo.get_all()
    if df.empty:
        return 0.0
    df['data_dt'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    start_date = datetime.now() - timedelta(days=last_days)
    recent = df[df['data_dt'] >= pd.Timestamp(start_date)]
    recent['valor_total_venda'] = pd.to_numeric(recent['valor_total_venda'], errors='coerce').fillna(0)
    return float(recent['valor_total_venda'].sum())


def test_monthly_revenue_reflects_new_sale():
    repo = SaleRepository()
    ss = SaleService()

    before = compute_recent_revenue()

    # Use an existing product and client from fixtures in DB
    res = ss.register_sale_multi_item(id_cliente='CLI000', meio='pix', items=[{'codigo': 'ABR01', 'quantidade': 1}])
    assert 'id_venda' in res
    sale_value = res['total_value']

    after = compute_recent_revenue()

    # Clean up
    repo.delete(res['id_venda'])

    assert after >= before + sale_value - 0.001
