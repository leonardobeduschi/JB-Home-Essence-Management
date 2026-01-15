"""
Service for budget (orçamento) generation.
"""
from datetime import datetime
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import os
import re

from src.repositories.client_repository import ClientRepository
from src.repositories.product_repository import ProductRepository


class BudgetService:
    """Service for generating budget PDFs."""
    
    def __init__(self):
        self.client_repo = ClientRepository()
        self.product_repo = ProductRepository()
        self.logo_path = Path(__file__).parent.parent / 'img' / 'logo' / 'jb-home-essence-logo-verde.png'
        # No __init__ da classe BudgetService, adicione:
        try:
            font_path = Path(__file__).parent.parent / 'fonts'
            pdfmetrics.registerFont(TTFont('Montserrat', str(font_path / 'Montserrat-Regular.ttf')))
            pdfmetrics.registerFont(TTFont('Montserrat-Bold', str(font_path / 'Montserrat-Bold.ttf')))
        except:
            pass  # Fallback para Helvetica
        
    def generate_budget_pdf(self, data: dict, return_bytes: bool = False):
        """
        Generate budget PDF.
        
        Args:
            data: Dictionary with budget data
                {
                    'date': 'DD/MM/YYYY',
                    'id_cliente': 'CLI_XXX',
                    'items': [
                        {'codigo': 'PROD_001', 'quantidade': 2},
                        ...
                    ]
                }
            return_bytes: If True, return BytesIO object instead of saving file
        
        Returns:
            str: Path to saved PDF or BytesIO object
        """
        # Get client data
        client = self.client_repo.get_by_id(data['id_cliente'])
        if not client:
            raise ValueError(f"Cliente não encontrado: {data['id_cliente']}")

        client_name = client['CLIENTE'].strip()

        # Limpa o nome para uso seguro no arquivo (remove acentos, caracteres especiais e espaços extras)
        safe_name = re.sub(r'[^a-zA-Z0-9\s]', '', client_name)  # remove caracteres especiais
        safe_name = re.sub(r'\s+', '_', safe_name.strip())      # espaços viram underscore

        # Se o nome ficou vazio por algum motivo, usa um fallback
        if not safe_name:
            safe_name = "cliente_desconhecido"
        
        # Get products data and calculate totals
        items_data = []
        total = 0.0
        
        for idx, item in enumerate(data['items'], 1):
            product = self.product_repo.get_by_codigo(item['codigo'])
            if not product:
                raise ValueError(f"Produto não encontrado: {item['codigo']}")
            
            quantidade = int(item['quantidade'])
            valor_unit = float(product['VALOR'])
            valor_total = quantidade * valor_unit
            total += valor_total
            
            items_data.append({
                'item': idx,
                'produto': product['PRODUTO'],
                'categoria': product['CATEGORIA'],
                'quantidade': quantidade,
                'valor_unit': valor_unit,
                'valor_total': valor_total
            })
        
        # Create PDF
        if return_bytes:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4,
                                  leftMargin=2*cm, rightMargin=2*cm,
                                  topMargin=2*cm, bottomMargin=2*cm)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"orcamento_{timestamp}_{safe_name}.pdf"
            filepath = Path('reports') / filename
            filepath.parent.mkdir(exist_ok=True)
            doc = SimpleDocTemplate(str(filepath), pagesize=A4,
                                    leftMargin=2*cm, rightMargin=2*cm,
                                    topMargin=2*cm, bottomMargin=2*cm)
        
        # Build PDF content
        story = []
        styles = getSampleStyleSheet()
        
        # Fallback fonts
        font_name = 'Helvetica'
        font_bold = 'Helvetica-Bold'
        
        # Custom styles
        green_color = colors.HexColor('#80a58d')
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=green_color,
            alignment=TA_LEFT,
            spaceAfter=20,
            fontName=font_bold
        )
        
        green_label_style = ParagraphStyle(
            'GreenLabel',
            parent=styles['Normal'],
            fontSize=12,
            textColor=green_color,
            fontName=font_bold,
            spaceAfter=6
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            spaceAfter=4,
            fontName=font_name
        )
        
        # Logo (top right - SMALLER SIZE)
        if self.logo_path.exists():
            logo = Image(str(self.logo_path), width=2.5*cm, height=2.5*cm)
            logo.hAlign = 'RIGHT'
            story.append(logo)
            story.append(Spacer(1, 0.3*cm))
        
        # Title (LEFT aligned)
        story.append(Paragraph("Orçamento", title_style))
        story.append(Spacer(1, 0.3*cm))
        
        # Date - apenas "Data:" em negrito
        story.append(Paragraph("<b>Data:</b> " + data['date'], normal_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Company info
        story.append(Paragraph("JB Home Essence", green_label_style))
        story.append(Paragraph("(47) 99715-2830", normal_style))
        story.append(Paragraph("R. 3130, 112 - Sala 04", normal_style))
        story.append(Paragraph("@jbhomessence", normal_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Client info - apenas os rótulos em negrito
        story.append(Paragraph("Cliente", green_label_style))
        story.append(Paragraph("<b>Nome:</b> " + client['CLIENTE'], normal_style))
        if client.get('TELEFONE'):
            story.append(Paragraph("<b>Telefone:</b> " + client['TELEFONE'], normal_style))
        if client.get('ENDERECO'):
            story.append(Paragraph("Endereço: " + client['ENDERECO'], normal_style))
        story.append(Spacer(1, 0.5*cm))
        
        # Items table
        table_data = [['Item', 'Produto', 'Categoria', 'Qtd.', 'Valor Unit.', 'Valor Total']]
        
        for item in items_data:
            table_data.append([
                str(item['item']),
                item['produto'],
                item['categoria'],
                str(item['quantidade']),
                f"R$ {item['valor_unit']:.2f}",
                f"R$ {item['valor_total']:.2f}"
            ])
        
        # Create table
        table = Table(table_data, colWidths=[1*cm, 5*cm, 3.5*cm, 1.5*cm, 2.5*cm, 2.5*cm])
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), green_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_bold),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Body
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),   # Item number
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),   # Quantity
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),   # Values
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)])
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.5*cm))
        
        # Total
        total_style = ParagraphStyle(
            'Total',
            parent=styles['Normal'],
            fontSize=14,
            textColor=green_color,
            fontName=font_bold,
            alignment=TA_RIGHT
        )
        story.append(Paragraph(f"Valor Total: R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), total_style))
        
        # Build PDF
        doc.build(story)
        
        if return_bytes:
            buffer.seek(0)
            return buffer
        else:
            return str(filepath)
    
    def get_client_data(self, id_cliente: str):
        """Get client data for budget form."""
        return self.client_repo.get_by_id(id_cliente)
    
    def get_product_data(self, codigo: str):
        """Get product data for budget form."""
        return self.product_repo.get_by_codigo(codigo)
    
    def list_all_clients(self):
        """Get all clients for dropdown."""
        from src.services.client_service import ClientService
        client_service = ClientService()
        return client_service.list_all_clients()
    
    def list_all_products(self):
        """Get all products for dropdown."""
        from src.services.product_service import ProductService
        product_service = ProductService()
        return product_service.list_all_products()