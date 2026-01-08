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
    df['DATA_DT'] = pd.to_datetime(df['DATA'], dayfirst=True, errors='coerce')
    start_date = datetime.now() - timedelta(days=last_days)
    recent = df[df['DATA_DT'] >= pd.Timestamp(start_date)]
    recent['VALOR_TOTAL_VENDA'] = pd.to_numeric(recent['VALOR_TOTAL_VENDA'], errors='coerce').fillna(0)
    return float(recent['VALOR_TOTAL_VENDA'].sum())


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
