# booking/utils.py

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.pdfgen import canvas
from io import BytesIO
import qrcode
from PIL import Image as PILImage
import os


def send_order_confirmation_email(order):
    """Send order confirmation email with tickets attached"""
    subject = f'Order Confirmation - {order.order_number}'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = order.email
    
    # Generate email context
    context = {
        'order': order,
        'order_items': order.items.select_related('event').all(),
        'site_name': 'Jersey Events',
        'site_url': settings.SITE_URL,
    }
    
    # Render email templates
    text_content = render_to_string('booking/emails/order_confirmation.txt', context)
    html_content = render_to_string('booking/emails/order_confirmation.html', context)
    
    # Create email
    email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    email.attach_alternative(html_content, "text/html")
    
    # Attach PDF tickets
    pdf_buffer = generate_ticket_pdf(order)
    email.attach(f'tickets_{order.order_number}.pdf', pdf_buffer.getvalue(), 'application/pdf')
    
    # Send email
    email.send()


def generate_ticket_pdf(order):
    """Generate PDF with all tickets for an order"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12
    )
    
    # Add header
    logo_path = os.path.join(settings.STATIC_ROOT, 'images/logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=2*inch, height=0.75*inch)
        elements.append(logo)
        elements.append(Spacer(1, 0.5*inch))
    
    # Add title
    elements.append(Paragraph("Event Tickets", title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Order information
    order_info = [
        ['Order Number:', order.order_number],
        ['Order Date:', order.created_at.strftime('%d %B %Y')],
        ['Customer:', f"{order.first_name} {order.last_name}"],
        ['Email:', order.email],
    ]
    
    order_table = Table(order_info, colWidths=[2*inch, 4*inch])
    order_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(order_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Generate tickets for each order item
    for order_item in order.items.all():
        for ticket in order_item.tickets.all():
            # Event header
            elements.append(Paragraph(order_item.event.title, heading_style))
            
            # Event details
            event_info = [
                ['Date:', order_item.event.date.strftime('%A, %d %B %Y')],
                ['Time:', order_item.event.time.strftime('%I:%M %p')],
                ['Venue:', order_item.event.venue],
                ['Location:', order_item.event.location],
            ]
            
            event_table = Table(event_info, colWidths=[1.5*inch, 4.5*inch])
            event_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
                ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(event_table)
            elements.append(Spacer(1, 0.25*inch))
            
            # Ticket information with QR code
            ticket_data = []
            
            # Add QR code if exists
            if ticket.qr_code:
                qr_img = Image(ticket.qr_code.path, width=2*inch, height=2*inch)
                ticket_info = [
                    ['Ticket Number:', ticket.ticket_number],
                    ['Price:', f'£{order_item.price:.2f}'],
                    ['Status:', 'Valid' if not ticket.is_used else 'Used'],
                ]
                
                ticket_info_table = Table(ticket_info, colWidths=[1.5*inch, 2.5*inch])
                ticket_info_table.setStyle(TableStyle([
                    ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
                    ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6b7280')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                
                # Create a table with ticket info and QR code side by side
                main_ticket_table = Table([[ticket_info_table, qr_img]], colWidths=[4*inch, 2.5*inch])
                main_ticket_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                
                elements.append(main_ticket_table)
            
            # Add separator
            elements.append(Spacer(1, 0.25*inch))
            separator = Table([[''] * 1], colWidths=[6.5*inch])
            separator.setStyle(TableStyle([
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#e5e7eb')),
            ]))
            elements.append(separator)
            elements.append(Spacer(1, 0.5*inch))
    
    # Footer
    footer_text = """
    <para align="center" fontSize="9" textColor="#6b7280">
    Please present this ticket at the venue entrance. 
    The QR code will be scanned for entry.<br/>
    For support, contact support@jerseyevents.com
    </para>
    """
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer


def validate_ticket(ticket_number):
    """Validate a ticket by its number"""
    from .models import Ticket
    
    try:
        ticket = Ticket.objects.select_related('order_item__event').get(
            ticket_number=ticket_number
        )
        
        if ticket.is_used:
            return {
                'valid': False,
                'message': 'Ticket has already been used',
                'used_at': ticket.used_at
            }
        
        # Check if event has passed
        event = ticket.event
        if event.has_passed:
            return {
                'valid': False,
                'message': 'Event has already passed'
            }
        
        return {
            'valid': True,
            'ticket': ticket,
            'event': event,
            'message': 'Valid ticket'
        }
        
    except Ticket.DoesNotExist:
        return {
            'valid': False,
            'message': 'Invalid ticket number'
        }


def process_refund(order, amount=None):
    """Process a refund for an order"""
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    if not order.stripe_payment_intent:
        return {'success': False, 'error': 'No payment intent found'}
    
    try:
        # If no amount specified, refund full amount
        if amount is None:
            refund = stripe.Refund.create(
                payment_intent=order.stripe_payment_intent
            )
        else:
            # Partial refund
            refund = stripe.Refund.create(
                payment_intent=order.stripe_payment_intent,
                amount=int(amount * 100)  # Convert to pence
            )
        
        # Update order status
        order.status = 'refunded'
        order.save()
        
        # Cancel tickets
        for item in order.items.all():
            for ticket in item.tickets.all():
                ticket.is_used = True
                ticket.save()
        
        return {'success': True, 'refund': refund}
        
    except stripe.error.StripeError as e:
        return {'success': False, 'error': str(e)}