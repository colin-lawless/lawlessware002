# tenant_management.report_generator.py
# Ayush

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import os
from datetime import datetime
from models import Tenant


def wrap_text(text, max_chars):
    """Wrap text to avoid breaking words across lines."""
    wrapped_lines = []
    words = text.split()
    current_line = words.pop(0)

    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars:
            current_line += ' ' + word
        else:
            wrapped_lines.append(current_line)
            current_line = word
    wrapped_lines.append(current_line)  # Add the last line

    return '\n'.join(wrapped_lines)


def calculate_col_widths(data, page_width, padding=0.15):
    """Calculate dynamic column widths based on content."""
    if not data or not data[0]:
        return []

    num_cols = len(data[0])
    col_widths = [0] * num_cols
    max_width = (page_width - padding * 2) / num_cols

    for row in data:
        for i in range(num_cols):
            if i >= len(row):
                continue  # Skip if the column index is out of range
            cell_content = str(row[i])

            cell_content = wrap_text(cell_content, int(max_width * 10))

            cell_width = min(max(len(line) for line in cell_content.split('\n')) * 0.1, max_width)
            col_widths[i] = max(col_widths[i], cell_width)

    return [width * inch for width in col_widths]


def split_header(header, max_length=10):
    """Splits header into two rows if it's longer than a specified length."""
    if len(header) > max_length:
        split_point = header.find(' ', max_length // 2)  # Find a space near the middle
        if split_point == -1:  # No space found, split at max_length
            split_point = max_length
        return [header[:split_point], header[split_point:].strip()]
    return [header]


def handle_long_content(cell_content, max_length=30):
    """Breaks down long content into smaller chunks."""
    if len(cell_content) > max_length:
        return '\n'.join([cell_content[i:i+max_length] for i in range(0, len(cell_content), max_length)])
    return cell_content


def generate_pdf_report(data, filename, report_title):
    """Generate a PDF report with dynamic layout and word wrapping."""

    # Define the directory for saving documents
    documents_dir = os.path.join(os.path.dirname(__file__), 'documents')
    if not os.path.exists(documents_dir):
        os.makedirs(documents_dir)

    # Define the path for the new document
    document_path = os.path.join(documents_dir, filename)
    pdf = SimpleDocTemplate(document_path, pagesize=landscape(A4), rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=18)

    # Define styles
    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle('DataCellStyle', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10)
    header_style = ParagraphStyle('HeaderCellStyle', parent=cell_style, fontSize=12)

    # Define report title and date
    title = Paragraph(report_title, styles['Title'])
    report_date = Paragraph(f"Report Date: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal'])
    report_time = Paragraph(f"Report Time: {datetime.now().strftime('%H:%M:%S')}", styles['Normal'])

    # Define table style with word wrap
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('WORDWRAP', (0, 0), (-1, -1), 'LTR'),
    ])
    max_lines_per_cell = 4

    # Convert headers and data to Paragraphs for proper formatting
    for i, row in enumerate(data):
        for j, cell in enumerate(row):
            cell_style_used = header_style if i == 0 else cell_style
            wrapped_text = wrap_text(str(cell), 15)  # Adjust '15' as needed for your layout
            wrapped_text_lines = wrapped_text.split('\n')[:max_lines_per_cell]
            data[i][j] = Paragraph('\n'.join(wrapped_text_lines), cell_style_used)

    # Calculate dynamic column widths
    col_widths = calculate_col_widths(data, 11)  # Use the calculate_col_widths function

    # Create a table for the data
    table = Table(data, colWidths=col_widths)
    table.setStyle(table_style)

    # Build the PDF document
    elements = [title, report_date, report_time, Spacer(1, 0.25 * inch), table]
    pdf.build(elements)

    return f'PDF report "{filename}" has been generated.'


def generate_tenant_summary_report_pdf(session):
    try:
        title = ["ID", "Name", "Debt", "Rent", "Days Overdue", "Status",
                "Telephone", "Email", "Unit Number", "Lease Start", "Notes"]
        data = [title]
        tenants = session.query(Tenant).all()
        for tenant in tenants:
            row = [
                tenant.tenant_id, tenant.name, f"{tenant.debt:.2f}", f"{tenant.rent:.2f}",
                tenant.days_overdue, tenant.status, tenant.telephone, tenant.email,
                tenant.unit_number, tenant.lease_start, tenant.notes
            ]
            data.append(row)
        return generate_pdf_report(session, data, 'Tenant_Summary_Report.pdf', 'Tenant Summary Report')
        return "Tenant Summary Report generated successfully."
    except Exception as e:
        return f"Failed to generate Tenant Summary Report: {e}"


def generate_debt_report_pdf(session):
    try:
        title = ["ID", "Name", "Debt", "Rent", "Days Overdue", "Telephone", "Email", "Unit Number", "Lease Start"]
        data = [title]
        tenants = session.query(Tenant).filter(Tenant.debt > 0).all()
        for tenant in tenants:
            row = [
                tenant.tenant_id, tenant.name, f"{tenant.debt:.2f}", f"{tenant.rent:.2f}",
                tenant.days_overdue, tenant.telephone, tenant.email,
                tenant.unit_number, tenant.lease_start
            ]
            data.append(row)
        return generate_pdf_report(data, 'Debt_Report.pdf', 'Debt Report')
        return "Tenant Summary Report generated successfully."
    except Exception as e:
        return f"Failed to generate Tenant Summary Report: {e}"


def generate_status_report_pdf(session):
    try:    
        title = ["ID", "Name", "Status", "Telephone", "Email", "Unit Number", "Lease Start"]
        data = [title]
        tenants = session.query(Tenant).all()
        for tenant in tenants:
            row = [
                tenant.tenant_id, tenant.name, tenant.status, tenant.telephone, tenant.email,
                tenant.unit_number, tenant.lease_start
            ]
            data.append(row)
        return generate_pdf_report(data, 'Status_Report.pdf', 'Status Report')
        return "Tenant Summary Report generated successfully."
    except Exception as e:
        return f"Failed to generate Tenant Summary Report: {e}"



def generate_overdue_report_pdf(session):
    try:
        title = ["ID", "Name", "Days Overdue", "Debt", "Rent", "Telephone", "Email", "Unit Number", "Lease Start"]
        data = [title]
        tenants = session.query(Tenant).filter(Tenant.days_overdue > 0).all()
        for tenant in tenants:
                row = [
                tenant.tenant_id, tenant.name, tenant.days_overdue, f"{tenant.debt:.2f}", f"{tenant.rent:.2f}",
                tenant.telephone, tenant.email, tenant.unit_number, tenant.lease_start
        ]
        data.append(row)
        return generate_pdf_report(data, 'Overdue_Report.pdf', 'Overdue Report')
        return "Tenant Summary Report generated successfully."
    except Exception as e:
        return f"Failed to generate Tenant Summary Report: {e}"
    

