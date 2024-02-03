# tenant_management.document_generator.py

import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os


def generate_pdf_document(tenant, action, action_steps):
    # Obtain the directory of the current script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct paths to the templates and documents directories
    templates_dir = os.path.join(base_dir, 'letter_templates')
    documents_dir = os.path.join(base_dir, 'documents')

    # Define a mapping of action to template filenames
    # Ayush
    action_to_template = {
        'warning': 'warning_template.txt',
        'cancellation': 'cancellation_template.txt',
        'eviction': 'eviction_template.txt',
        'lawsuit': 'lawsuit_template.txt',  
     }

    template_filename = action_to_template.get(action)
    if not template_filename:
        return False, f'No template found for the {action} action.'

    template_path = os.path.join(templates_dir, template_filename)
    if not os.path.exists(template_path):
        return False, f'Template file not found at {template_path}.'

    # The full path for the new PDF file
    document_path = os.path.join(documents_dir, f'{tenant.tenant_id}_{action}.pdf')

    try:
        # Create a canvas to write to the PDF
        c = canvas.Canvas(document_path, pagesize=letter)
        c.setFont("Helvetica", 12)

        # Open the template and read the content
        with open(template_path, 'r') as file:
            template_content = file.read()

        current_date = datetime.date.today()

        formatted_date = current_date.strftime("%d/%m/%Y")

        date_plus_ten = current_date + datetime.timedelta(days=10)

        formatted_date_ten = date_plus_ten.strftime("%d/%m/%Y")

        date_plus_thirty = current_date + datetime.timedelta(days=30)

        formatted_date_thirty = date_plus_thirty.strftime("%d/%m/%Y")

        # Replace placeholders with actual tenant information
        formatted_debt = "{:.2f}".format(tenant.debt)  # Format debt to two decimal places
        content = template_content.replace('[Tenant_Name]', tenant.name)
        content = content.replace('[Debt_Amount]', formatted_debt)  # Use formatted debt
        content = content.replace('[Unit_Nr]', str(tenant.unit_number))
        content = content.replace('[Rent]', str(tenant.rent))
        content = content.replace('[Current_Date]', formatted_date)
        content = content.replace('[Date_10]',formatted_date_ten)
        content = content.replace('[Date_30]', formatted_date_thirty)

        # Add the content to the PDF
        text = c.beginText(72, 720)
        for line in content.split('\n'):
            text.textLine(line)

        c.drawText(text)
        c.showPage()
        c.save()

        return True, document_path  # Indicate success and return the path
    except Exception as e:
        error_message = f"Error generating document for {tenant.name}: {e}"
        return False, error_message
    