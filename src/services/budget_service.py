"""
Service for budget (orçamento) generation with professional design.
"""
from datetime import datetime
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, Line
from reportlab.graphics import renderPDF
from io import BytesIO
import os
import re

from src.repositories.client_repository import ClientRepository
from src.repositories.product_repository import ProductRepository


class BudgetService:
    """Service for generating professional budget PDFs."""
    
    def __init__(self):
        self.client_repo = ClientRepository()
        self.product_repo = ProductRepository()
        self.logo_path = Path(__file__).parent.parent / 'img' / 'logo' / 'jb-home-essence-logo-verde.png'
        
        # Brand colors - Professional palette
        self.primary_green = colors.HexColor('#80a58d')
        self.dark_green = colors.HexColor('#5a7a65')
        self.light_green = colors.HexColor('#e8f0eb')
        self.accent_color = colors.HexColor('#d4af37')
        self.text_dark = colors.HexColor('#2c2c2c')
        self.text_gray = colors.HexColor('#6c6c6c')
        
        # Register fonts
        try:
            font_path = Path(__file__).parent.parent / 'fonts'
            pdfmetrics.registerFont(TTFont('Montserrat', str(font_path / 'Montserrat-Regular.ttf')))
            pdfmetrics.registerFont(TTFont('Montserrat-Bold', str(font_path / 'Montserrat-Bold.ttf')))
            self.font_regular = 'Montserrat'
            self.font_bold = 'Montserrat-Bold'
        except:
            self.font_regular = 'Helvetica'
            self.font_bold = 'Helvetica-Bold'
    
    def _add_header(self, story, data):
        """Add professional header with logo and company info."""
        # Header table: logo on left, title on right
        header_content = []
        
        # Logo section
        if self.logo_path.exists():
            logo_img = Image(str(self.logo_path), width=4*cm, height=4*cm)
            logo_cell = logo_img
        else:
            # Fallback: company initial in circle
            logo_cell = Paragraph("", getSampleStyleSheet()['Normal'])
        
        # Title section
        title_style = ParagraphStyle(
            'TitleStyle',
            fontName=self.font_bold,
            fontSize=36,
            textColor=self.primary_green,
            alignment=TA_RIGHT,
            leading=36,
            spaceAfter=2
        )
        
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            fontName=self.font_regular,
            fontSize=10,
            textColor=self.text_gray,
            alignment=TA_RIGHT,
            leading=11
        )
        
        company_style = ParagraphStyle(
            'CompanyStyle',
            fontName=self.font_bold,
            fontSize=12,
            textColor=self.dark_green,
            alignment=TA_RIGHT,
            leading=14,
            spaceAfter=1
        )
        
        title_cell = [
            Paragraph("ORÇAMENTO", title_style),
            Spacer(1, 4*mm),
            Paragraph("JB Home Essence", company_style),
            Paragraph("(47) 99715-2830", subtitle_style),
            Paragraph("R. 3130, 112 - Sala 04", subtitle_style),
            Paragraph("@jbhomessence", subtitle_style),
            Paragraph("CNPJ: 57.495.867/0001-82", subtitle_style),
            Paragraph("Balneario Camboriu - SC", subtitle_style),
        ]
        
        header_table = Table([[logo_cell, title_cell]], colWidths=[5*cm, 12*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 4*mm))
        
        # Elegant separator line
        line = Drawing(17*cm, 3*mm)
        line.add(Rect(0, 1*mm, 17*cm, 2*mm, fillColor=self.primary_green, strokeColor=None))
        story.append(line)
        story.append(Spacer(1, 4*mm))
    
    def _add_client_info(self, story, client_data, date):
        """Add client information in elegant box."""
        # Date and client header
        header_style = ParagraphStyle(
            'InfoHeader',
            fontName=self.font_bold,
            fontSize=11,
            textColor=colors.white,
            alignment=TA_LEFT,
            leftIndent=4*mm,
            leading=14
        )
        
        info_text_style = ParagraphStyle(
            'InfoText',
            fontName=self.font_regular,
            fontSize=10,
            textColor=self.text_dark,
            alignment=TA_LEFT,
            leading=15
        )
        
        # Date section
        date_box = Table([
            [Paragraph(f"DATA: {date}", header_style)]
        ], colWidths=[17*cm])
        date_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.dark_green),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(date_box)
        story.append(Spacer(1, 3*mm))
        
        # Client info box
        client_header = Table([
            [Paragraph("CLIENTE", header_style)]
        ], colWidths=[17*cm])
        client_header.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.primary_green),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(client_header)
        
        # Client details
        client_details = []
        client_details.append([Paragraph(f"<b>Nome:</b> {client_data['CLIENTE']}", info_text_style)])
        
        if client_data.get('TELEFONE'):
            client_details.append([Paragraph(f"<b>Telefone:</b> {client_data['TELEFONE']}", info_text_style)])
        
        if client_data.get('ENDERECO'):
            client_details.append([Paragraph(f"<b>Endereço:</b> {client_data['ENDERECO']}", info_text_style)])
        
        client_table = Table(client_details, colWidths=[17*cm])
        client_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.light_green),
            ('TOPPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 4*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4*mm),
        ]))
        story.append(client_table)
        story.append(Spacer(1, 5*mm))
    
    def _add_items_table(self, story, items_data):
        """Add elegant product table."""
        # Table header
        table_data = [[
            Paragraph('<b>#</b>', getSampleStyleSheet()['Normal']),
            Paragraph('<b>PRODUTO</b>', getSampleStyleSheet()['Normal']),
            Paragraph('<b>CATEGORIA</b>', getSampleStyleSheet()['Normal']),
            Paragraph('<b>QTD</b>', getSampleStyleSheet()['Normal']),
            Paragraph('<b>VALOR UNIT.</b>', getSampleStyleSheet()['Normal']),
            Paragraph('<b>TOTAL</b>', getSampleStyleSheet()['Normal'])
        ]]
        
        # Table rows
        for item in items_data:
            table_data.append([
                str(item['item']),
                item['produto'],
                item['categoria'],
                str(item['quantidade']),
                f"R$ {item['valor_unit']:.2f}".replace('.', ','),
                f"R$ {item['valor_total']:.2f}".replace('.', ',')
            ])
        
        # Create table with optimized column widths
        table = Table(
            table_data, 
            colWidths=[1*cm, 6*cm, 3*cm, 1.5*cm, 2.75*cm, 2.75*cm],
            repeatRows=1
        )
        
        table_style = TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_green),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.font_bold),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('TOPPADDING', (0, 0), (-1, 0), 3*mm),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 3*mm),
            
            # Body style
            ('FONTNAME', (0, 1), (-1, -1), self.font_regular),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.text_dark),
            
            # Alignment
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Item number
            ('ALIGN', (1, 1), (2, -1), 'LEFT'),    # Product and category
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),  # Quantity
            ('ALIGN', (4, 1), (5, -1), 'RIGHT'),   # Values
            
            # Padding
            ('TOPPADDING', (0, 1), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 1), (-1, -1), 2*mm),
            ('RIGHTPADDING', (0, 1), (-1, -1), 2*mm),
            
            # Borders
            ('BOX', (0, 0), (-1, -1), 1.5, self.dark_green),
            ('LINEBELOW', (0, 0), (-1, 0), 2, self.dark_green),
            ('LINEBELOW', (0, 1), (-1, -2), 0.5, colors.HexColor('#e0e0e0')),
            ('LINEBELOW', (0, -1), (-1, -1), 1.5, self.dark_green),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.light_green]),
        ])
        
        table.setStyle(table_style)
        story.append(table)
        story.append(Spacer(1, 4*mm))
    
    def _add_total_section(self, story, total, discount=0.0):
        """Add total with elegant styling, including discount."""
        
        # Calculate final total
        final_total = max(0, total - discount)
        
        # Styles
        subtotal_style = ParagraphStyle(
            'SubtotalStyle',
            fontName=self.font_regular,
            fontSize=10,
            textColor=self.text_gray,
            alignment=TA_RIGHT,
            rightIndent=4*mm,
            leading=14
        )
        
        discount_style = ParagraphStyle(
            'DiscountStyle',
            fontName=self.font_regular,
            fontSize=10,
            textColor=colors.red,
            alignment=TA_RIGHT,
            rightIndent=4*mm,
            leading=14
        )
        
        total_style = ParagraphStyle(
            'TotalStyle',
            fontName=self.font_bold,
            fontSize=16,
            textColor=self.dark_green,
            alignment=TA_RIGHT,
            rightIndent=4*mm,
            leading=20
        )
        
        rows = []
        
        # Subtotal (only if there is a discount)
        if discount > 0:
            subtotal_fmt = f"Subtotal: R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            rows.append([Paragraph(subtotal_fmt, subtotal_style)])
            
            discount_fmt = f"Desconto: - R$ {discount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            rows.append([Paragraph(discount_fmt, discount_style)])
            
        # Final Total
        total_fmt = f"VALOR TOTAL: R$ {final_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        rows.append([Paragraph(total_fmt, total_style)])
        
        total_table = Table(rows, colWidths=[17*cm])
        
        total_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.light_green),
            ('BOX', (0, 0), (-1, -1), 1.5, self.primary_green),
            ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        story.append(total_table)

    def _add_notes_section(self, story, notes):
        """Add notes section if present."""
        if not notes:
            return
            
        story.append(Spacer(1, 3*mm))
        
        header_style = ParagraphStyle(
            'NotesHeader',
            fontName=self.font_bold,
            fontSize=10,
            textColor=self.dark_green,
            alignment=TA_LEFT,
            leading=12
        )
        
        text_style = ParagraphStyle(
            'NotesText',
            fontName=self.font_regular,
            fontSize=9,
            textColor=self.text_gray,
            alignment=TA_LEFT,
            leading=11
        )
        
        story.append(Paragraph("Observações:", header_style))
        story.append(Paragraph(notes.replace('\n', '<br/>'), text_style))
    
    def _add_footer(self, story):
        """Add professional footer."""
        story.append(Spacer(1, 8*mm))
        
        
        # Separator line
        line = Drawing(17*cm, 1*mm)
        line.add(Rect(0, 0, 17*cm, 1*mm, fillColor=self.primary_green, strokeColor=None))
        story.append(line)
        story.append(Spacer(1, 2*mm))
        
        # Contact footer
        footer_style = ParagraphStyle(
            'FooterStyle',
            fontName=self.font_regular,
            fontSize=8,
            textColor=self.text_gray,
            alignment=TA_CENTER,
            leading=10
        )
        
        story.append(Paragraph(
            "JB Home Essence | (47) 99715-2830 | R. 3130, 112 - Sala 04 | @jbhomessence", 
            footer_style
        ))
        
        gratitude_style = ParagraphStyle(
            'GratitudeStyle',
            fontName=self.font_bold,
            fontSize=9,
            textColor=self.primary_green,
            alignment=TA_CENTER,
            leading=12
        )
        
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("Obrigado pela preferência!", gratitude_style))
        
    def generate_budget_pdf(self, data: dict, return_bytes: bool = False):
        """
        Generate professional budget PDF with support for custom client/product data.
        
        Args:
            data: Dictionary with budget data
                {
                    'date': 'DD/MM/YYYY',
                    'id_cliente': 'CLI_XXX' or 'custom',
                    'client_data': {  # Only if id_cliente is 'custom'
                        'name': 'Nome',
                        'phone': 'Telefone',
                        'address': 'Endereço'
                    },
                    'items': [
                        {
                            'codigo': 'PROD_001', 
                            'quantidade': 2,
                            'produto': 'Nome',  # Only for custom products
                            'categoria': 'Cat',  # Only for custom products
                            'valor_unit': 100.00  # Only for custom products
                        },
                        ...
                    ]
                }
            return_bytes: If True, return BytesIO object instead of saving file
        
        Returns:
            str: Path to saved PDF or BytesIO object
        """
        # Get or create client data
        id_cliente = str(data.get('id_cliente', '')).strip().lower()
        
        if id_cliente == 'custom' or 'client_data' in data:
            # Use custom client data (not saved to database)
            client_data = data.get('client_data', {})
            client = {
                'CLIENTE': client_data.get('name') or client_data.get('CLIENTE') or 'Cliente Personalizado',
                'TELEFONE': client_data.get('phone') or client_data.get('TELEFONE') or '',
                'ENDERECO': client_data.get('address') or client_data.get('ENDERECO') or ''
            }
            safe_name = re.sub(r'[^a-zA-Z0-9\s]', '', client['CLIENTE'])
            safe_name = re.sub(r'\s+', '_', safe_name.strip()) or 'cliente'
        else:
            # Get client from database
            client = self.client_repo.get_by_id(data['id_cliente'])
            if not client:
                # Fallback instead of raising error
                client = {
                    'CLIENTE': 'Cliente Não Encontrado',
                    'TELEFONE': '',
                    'ENDERECO': ''
                }
            
            client_name = client.get('CLIENTE', 'Cliente').strip()
            safe_name = re.sub(r'[^a-zA-Z0-9\s]', '', client_name)
            safe_name = re.sub(r'\s+', '_', safe_name.strip()) or 'cliente_desconhecido'
        
        # Process items and calculate totals
        items_data = []
        total = 0.0
        
        for idx, item in enumerate(data['items'], 1):
            codigo = str(item.get('codigo', '')).strip()
            
            # Check if it's a custom product
            if codigo.upper().startswith('CUSTOM') or ('produto' in item and 'categoria' in item):
                # Use custom product data
                produto_nome = item.get('produto') or item.get('PRODUTO') or 'Produto Personalizado'
                categoria = item.get('categoria') or item.get('CATEGORIA') or 'Diversos'
                try:
                    valor_unit = float(item.get('valor_unit') or item.get('VALOR') or 0)
                except (ValueError, TypeError):
                    valor_unit = 0.0
            else:
                # Get product from database
                product = self.product_repo.get_by_codigo(item['codigo'])
                if not product:
                    # Fallback instead of raising error
                    produto_nome = f"Produto Não Encontrado ({item['codigo']})"
                    categoria = "-"
                    valor_unit = 0.0
                else:
                    produto_nome = product.get('PRODUTO', 'Produto')
                    categoria = product.get('CATEGORIA', '-')
                    valor_unit = float(product.get('VALOR', 0))
            
            quantidade = int(item['quantidade'])
            valor_total = quantidade * valor_unit
            total += valor_total
            
            items_data.append({
                'item': idx,
                'produto': produto_nome,
                'categoria': categoria,
                'quantidade': quantidade,
                'valor_unit': valor_unit,
                'valor_total': valor_total
            })
        
        # Create PDF document
        if return_bytes:
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer, 
                pagesize=A4,
                leftMargin=2*cm, 
                rightMargin=2*cm,
                topMargin=2*cm, 
                bottomMargin=2*cm
            )
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"orcamento_{timestamp}_{safe_name}.pdf"
            filepath = Path('reports') / filename
            filepath.parent.mkdir(exist_ok=True)
            doc = SimpleDocTemplate(
                str(filepath), 
                pagesize=A4,
                leftMargin=2*cm, 
                rightMargin=2*cm,
                topMargin=2*cm, 
                bottomMargin=2*cm
            )
        
        # Build PDF content
        story = []
        
        # Add all sections
        self._add_header(story, data)
        self._add_client_info(story, client, data['date'])
        # Get additional data
        notes = data.get('notes', '')
        try:
            discount = float(data.get('discount', 0))
        except (ValueError, TypeError):
            discount = 0.0

        self._add_items_table(story, items_data)
        self._add_total_section(story, total, discount)
        self._add_notes_section(story, notes)
        self._add_footer(story)
        
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