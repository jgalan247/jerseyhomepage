from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from io import BytesIO
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def send_order_confirmation_email(order):
    """Send order confirmation email with tickets attached"""
    context = {
        'order': order,
        'domain': settings.SITE_DOMAIN if hasattr(settings, 'SITE_DOMAIN') else 'localhost:8000',
    }
    
    # Render email templates
    subject = f'Order Confirmation - {order.order_number}'
    html_message = render_to_string('booking/emails/order_confirmation.html', context)
    plain_message = render_to_string('booking/emails/order_confirmation.txt', context)
    
    # Create email
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.customer_email]
    )
    
    email.attach_alternative(html_message, "text/html")
    
    # Attach PDF tickets if order is paid
    if order.payment_status == 'completed':
        pdf_buffer = generate_tickets_pdf(order)
        email.attach(f'tickets_{order.order_number}.pdf', pdf_buffer.getvalue(), 'application/pdf')
    
    # Send email
    email.send()


def generate_tickets_pdf(order):
    """Generate PDF with all tickets for an order"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#374151'),
        spaceAfter=12
    )
    
    # Add title
    story.append(Paragraph('Event Tickets', title_style))
    story.append(Spacer(1, 0.5 * inch))
    
    # Order information
    order_info = [
        ['Order Number:', order.order_number],
        ['Order Date:', order.created_at.strftime('%d %B %Y')],
        ['Customer:', order.customer_name],
        ['Email:', order.customer_email],
    ]
    
    order_table = Table(order_info, colWidths=[2 * inch, 4 * inch])
    order_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(order_table)
    story.append(Spacer(1, 0.5 * inch))
    
    # Generate tickets for each order item
    for order_item in order.items.all():
        event = order_item.event
        
        # Event header
        story.append(Paragraph(event.title, heading_style))
        
        event_info = [
            ['Date:', event.date.strftime('%A, %d %B %Y at %H:%M')],
            ['Venue:', event.venue],
            ['Address:', event.address],
            ['Quantity:', f'{order_item.quantity} ticket(s)'],
        ]
        
        event_table = Table(event_info, colWidths=[1.5 * inch, 4.5 * inch])
        event_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(event_table)
        story.append(Spacer(1, 0.3 * inch))
        
        # Generate individual tickets
        tickets = order_item.tickets.all()
        if not tickets.exists():
            # If tickets haven't been created yet, show placeholder
            for i in range(order_item.quantity):
                ticket_number = f"{order.order_number}-{event.id}-{i+1}"
                story.append(generate_ticket_element(event, ticket_number, order))
                story.append(Spacer(1, 0.3 * inch))
        else:
            # Use actual ticket numbers
            for ticket in tickets:
                story.append(generate_ticket_element(event, ticket.ticket_number, order))
                story.append(Spacer(1, 0.3 * inch))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer


def generate_ticket_element(event, ticket_number, order):
    """Generate a single ticket element for the PDF"""
    # Create QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr_data = f"TICKET:{ticket_number}|EVENT:{event.id}|ORDER:{order.order_number}"
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    # Create ticket table
    ticket_data = [
        ['TICKET', ticket_number],
        ['', ''],  # Space for QR code
    ]
    
    ticket_table = Table(ticket_data, colWidths=[4 * inch, 2 * inch])
    
    # Add QR code image
    qr_image = Image(qr_buffer, width=1.5 * inch, height=1.5 * inch)
    ticket_table._argW[1] = 2 * inch
    ticket_table._argH[1] = 1.5 * inch
    
    ticket_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 14),
        ('FONTSIZE', (1, 0), (1, 0), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#e5e7eb')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
    ]))
    
    # Replace the empty cell with QR code
    ticket_table._cellvalues[1][1] = qr_image
    
    return ticket_table