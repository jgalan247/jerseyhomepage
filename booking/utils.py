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
from reportlab.platypus import PageBreak, Spacer


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
        to=[order.email]
    )
    
    email.attach_alternative(html_message, "text/html")
    
    # Attach PDF tickets if order is paid
    if order.status == 'confirmed':
        pdf_buffer = generate_tickets_pdf(order)
        email.attach(f'tickets_{order.order_number}.pdf', pdf_buffer.getvalue(), 'application/pdf')
    
    # Send email
    email.send()


def generate_tickets_pdf(order):
    """Generate PDF with all tickets for an order"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
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
        fontSize=18,
        textColor=colors.HexColor('#374151'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    # Page 1: Order Summary
    story.append(Paragraph('Order Confirmation', title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Order information table
    order_info = [
        ['Order Number:', order.order_number],
        ['Order Date:', order.created_at.strftime('%d %B %Y at %H:%M')],
        ['Customer:', f"{order.first_name} {order.last_name}"],
        ['Email:', order.email],
        ['Total Amount:', f"£{order.total_amount}"],
    ]
    
    order_table = Table(order_info, colWidths=[2.5 * inch, 4 * inch])
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
    
    # Tickets summary
    story.append(Paragraph('Tickets Included', heading_style))
    
    ticket_summary = []
    ticket_number = 1
    for item in order.items.all():
        for i in range(item.quantity):
            ticket_summary.append([
                f"Ticket {ticket_number}",
                item.event.title,
                item.event.date.strftime('%d %b %Y at %H:%M'),
                item.event.venue
            ])
            ticket_number += 1
    
    if ticket_summary:
        summary_table = Table(
            [['#', 'Event', 'Date', 'Venue']] + ticket_summary,
            colWidths=[0.8 * inch, 2.5 * inch, 2 * inch, 1.5 * inch]
        )
        summary_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(summary_table)
    
    # Important notice
    story.append(Spacer(1, 0.5 * inch))
    notice_text = """
    <b>Important Information:</b><br/>
    • Each ticket has a unique QR code - do not share or duplicate<br/>
    • Present tickets on your phone or printed at the venue<br/>
    • Doors open 30 minutes before event start time<br/>
    • Keep this PDF safe - it contains all your tickets
    """
    story.append(Paragraph(notice_text, styles['Normal']))
    
    # Page break before individual tickets
    story.append(PageBreak())
    
    # Individual ticket pages
    ticket_count = 1
    total_tickets = sum(item.quantity for item in order.items.all())
    
    for item in order.items.all():
        event = item.event
        
        # Generate tickets for this event
        tickets = item.tickets.all()
        if not tickets.exists():
            # If tickets haven't been created yet, generate temporary ones
            for i in range(item.quantity):
                ticket_number = f"{order.order_number}-{event.id}-{i+1}"
                story.extend(generate_single_ticket_page(
                    event, ticket_number, order, ticket_count, total_tickets
                ))
                story.append(PageBreak())
                ticket_count += 1
        else:
            # Use actual tickets
            for ticket in tickets:
                story.extend(generate_single_ticket_page(
                    event, ticket.ticket_number, order, ticket_count, total_tickets
                ))
                story.append(PageBreak())
                ticket_count += 1
    
    # Remove last page break
    if story and isinstance(story[-1], PageBreak):
        story.pop()
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer

def generate_single_ticket_pdf(ticket):
    """Generate PDF for a single ticket"""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from PIL import Image
    import base64
    from io import BytesIO
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    p.setFont("Helvetica-Bold", 24)
    p.drawString(50, height - 50, "Event Ticket")
    
    # Ticket border
    p.setStrokeColor(colors.black)
    p.setLineWidth(2)
    p.rect(40, height - 350, width - 80, 300)
    
    # Event details
    p.setFont("Helvetica-Bold", 18)
    p.drawString(60, height - 100, ticket.event.title)
    
    p.setFont("Helvetica", 14)
    p.drawString(60, height - 130, f"Date: {ticket.event.date.strftime('%B %d, %Y at %I:%M %p')}")
    p.drawString(60, height - 150, f"Venue: {ticket.event.venue}")
    p.drawString(60, height - 170, f"Address: {ticket.event.address}")
    
    # Ticket info
    p.setFont("Helvetica-Bold", 12)
    p.drawString(60, height - 210, "Ticket Information:")
    p.setFont("Helvetica", 12)
    p.drawString(60, height - 230, f"Ticket ID: {ticket.ticket_number}")
    p.drawString(60, height - 250, f"Order: {ticket.order.order_number}")
    p.drawString(60, height - 270, f"Purchaser: {ticket.order.customer_name}")
    
    # QR Code
    if ticket.qr_code:
        # Decode base64 QR code
        qr_data = base64.b64decode(ticket.qr_code)
        qr_image = Image.open(BytesIO(qr_data))
        
        # Draw QR code
        p.drawInlineImage(qr_image, width - 240, height - 320, width=150, height=150)
        
        p.setFont("Helvetica", 10)
        p.drawString(width - 235, height - 340, "Scan at entrance")
    
    # Instructions
    p.setFont("Helvetica", 10)
    p.setFillColor(colors.grey)
    p.drawString(60, height - 320, "Present this ticket at the venue entrance.")
    p.drawString(60, height - 335, "This ticket is valid for one admission only.")
    
    # Footer
    p.setFont("Helvetica", 8)
    p.drawString(50, 50, f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M')}")
    p.drawString(50, 35, "Jersey Homepage - Your Local Event Platform")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer

def generate_single_ticket_page(event, ticket_number, order, current_num, total_num):
    """Generate a single ticket page with all details and QR code"""
    story = []
    styles = getSampleStyleSheet()
    
    # Header with logo placeholder
    header_data = [
        ['JERSEY EVENTS', f'TICKET {current_num} OF {total_num}']
    ]
    header_table = Table(header_data, colWidths=[4 * inch, 2.5 * inch])
    header_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, 0), 'Helvetica-Bold', 20),
        ('FONT', (1, 0), (1, 0), 'Helvetica', 12),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1f2937')),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.5 * inch))
    
    # Event title
    event_title = ParagraphStyle(
        'EventTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#1f2937'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    story.append(Paragraph(event.title, event_title))
    
    # Main ticket content in a bordered box
    ticket_data = []
    
    # QR Code generation
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr_data = f"TICKET:{ticket_number}|EVENT:{event.id}|ORDER:{order.order_number}|DATE:{event.date.strftime('%Y%m%d')}"
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_image = Image(qr_buffer, width=2.5 * inch, height=2.5 * inch)
    
    # Event details
    details_html = f"""
    <b>Date & Time</b><br/>
    {event.date.strftime('%A, %d %B %Y')}<br/>
    {event.date.strftime('%H:%M')}<br/>
    <br/>
    <b>Venue</b><br/>
    {event.venue}<br/>
    {event.address}<br/>
    <br/>
    <b>Ticket Details</b><br/>
    Ticket ID: {ticket_number}<br/>
    Type: General Admission<br/>
    Price: £{item.price if 'item' in locals() else event.price}<br/>
    """
    
    details_para = Paragraph(details_html, styles['Normal'])
    
    # Create main ticket table with QR code and details
    ticket_main = Table(
        [[details_para, qr_image]],
        colWidths=[3.5 * inch, 3 * inch]
    )
    ticket_main.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9fafb')),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 20),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
    ]))
    
    story.append(ticket_main)
    story.append(Spacer(1, 0.3 * inch))
    
    # Ticket holder info
    holder_info = f"""
    <b>Ticket Holder</b><br/>
    {order.first_name} {order.last_name}<br/>
    Order: {order.order_number}
    """
    story.append(Paragraph(holder_info, styles['Normal']))
    story.append(Spacer(1, 0.5 * inch))
    
    # Footer with terms
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6b7280'),
        alignment=TA_CENTER
    )
    footer_text = """
    This ticket is valid for one admission only. Duplication is prohibited.
    Please have this ticket ready for scanning at the venue entrance.
    """
    story.append(Paragraph(footer_text, footer_style))
    
    return story