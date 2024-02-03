# app.py

from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory, current_app, flash, Response
from flask_sqlalchemy import SQLAlchemy
from tenant_management.config_manager import ConfigManager
from tenant_management.decision_logic import decide_next_action, STATUSES, advance_status
import csv
import io
from io import StringIO
from reportlab.lib.pagesizes import letter
import os
from tenant_management.report_generator import generate_pdf_report
from datetime import datetime
from tenant_management.document_generator import generate_pdf_document
from models import db, Tenant
import traceback

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'default_key_for_development')
config_manager = ConfigManager('config.json')
app.config['DOCUMENTS_FOLDER'] = os.path.join(app.root_path, 'tenant_management', 'documents')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tenants.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

# Ensure the directory exists when starting the app
if not os.path.exists(app.config['DOCUMENTS_FOLDER']):
    os.makedirs(app.config['DOCUMENTS_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add-tenant', methods=['GET', 'POST'])
def add_tenant():
    try:
        if request.method == 'POST':
            # Extract data from form
            name = request.form['name']
            debt = float(request.form.get('debt', 0))
            rent = float(request.form.get('rent', 0))
            days_overdue = int(request.form.get('days_overdue', 0))
            status = request.form.get('status', 'active')
            telephone = request.form.get('telephone', '')
            email = request.form.get('email', '')
            unit_number = request.form.get('unit_number', '')
            lease_start = request.form.get('lease_start', '')
            notes = request.form.get('notes', '')

            # Add the tenant to the database
            new_tenant = Tenant(
                name=name,
                debt=debt,
                rent=rent,
                days_overdue=days_overdue,
                status=status,
                telephone=telephone,
                email=email,
                unit_number=unit_number,
                lease_start=lease_start,
                notes=notes
            )

            db.session.add(new_tenant)
            db.session.commit()

            flash('New tenant added successfully!', 'success')
            return redirect(url_for('index'))  # Redirect to the home page after adding

        # GET request or other non-POST request
        return render_template('add_tenant.html', STATUSES=STATUSES)

    except Exception as e:
        # Log the exception and return the error page
        app.logger.error('Failed to add tenant: %s\n%s', e, traceback.format_exc())
        flash('An error occurred while adding the tenant.', 'error')
        return render_template('add_tenant.html', STATUSES=STATUSES), 500


@app.route('/view-all-tenants')
def view_all_tenants():
    tenants = Tenant.query.all()
    return render_template('view_all_tenants.html', tenants=tenants)

@app.route('/update-tenant/<int:tenant_id>', methods=['GET', 'POST'])
def update_tenant(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)
    if request.method == 'POST':
        # Update tenant details based on form input
        tenant.name = request.form['name']
        tenant.debt = float(request.form['debt'])
        tenant.rent = float(request.form['rent'])
        tenant.days_overdue = int(request.form['days_overdue'])
        tenant.status = request.form['status']
        tenant.telephone = request.form['telephone']
        tenant.email = request.form['email']
        tenant.unit_number = request.form['unit_number']
        tenant.lease_start = request.form['lease_start']
        tenant.notes = request.form['notes']
        requested_status = request.form['status']
        if requested_status in STATUSES:
            # Only update status if it's advanced by one step
            if STATUSES.index(requested_status) == STATUSES.index(tenant.status) + 1:
                tenant.status = requested_status

        db.session.commit()
        flash('Tenant updated successfully')
        return redirect(url_for('view_tenant', tenant_id=tenant_id))

    return render_template('update_tenant.html', tenant=tenant, STATUSES=STATUSES)


@app.route('/view-tenant/<int:tenant_id>')
def view_tenant(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)
    return render_template('view_tenant.html', tenant=tenant)

@app.route('/delete-tenant/<tenant_id>', methods=['POST'])
def delete_tenant(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)  # Delete the tenant from the database
    db.session.delete(tenant)
    db.session.commit()
    return redirect(url_for('view_all_tenants'))

@app.route('/view-configuration')
def view_configuration():
    config = config_manager.get_config()
    return render_template('view_configuration.html', config=config)

@app.route('/export_data')
def export_data():
    # Create an in-memory string buffer for the CSV data
    si = StringIO()
    cw = csv.writer(si)

    # Write the header row
    cw.writerow(['ID', 'Name', 'Debt', 'Rent', 'Days Overdue', 'Status', 'Telephone', 'Email', 'Unit Number', 'Lease Start Date', 'Notes'])

    # Query the database for all tenants
    tenants = Tenant.query.all()
    
    # Write tenant data rows
    for tenant in tenants:
        cw.writerow([
            tenant.tenant_id,
            tenant.name,
            tenant.debt,
            tenant.rent,
            tenant.days_overdue,
            tenant.status,
            tenant.telephone,
            tenant.email,
            tenant.unit_number,
            tenant.lease_start,
            tenant.notes
        ])

    # Reset the buffer's position to the start
    si.seek(0)
    # Create a response object, setting the correct MIME type and headers for file download
    response = Response(si.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=tenants.csv'
    return response

# Ayush
@app.route('/update-configuration', methods=['GET', 'POST'])
def update_configuration():
    if request.method == 'POST':
        try:
            new_config_data = {
                "decision_thresholds": {
                    "should_be_warned_threshold": int(request.form['should_be_warned_threshold']),
                    "warned_threshold": int(request.form['warned_threshold']),
                    "should_be_cancelled_threshold": int(request.form['should_be_cancelled_threshold']),
                    "cancelled_threshold": int(request.form['cancelled_threshold']),
                    "should_be_sued_threshold": int(request.form['should_be_sued_threshold']),
                    "lawsuit_threshold": int(request.form['lawsuit_threshold']),
                    "should_be_evicted_threshold": int(request.form['should_be_evicted_threshold']),
                    "eviction_threshold": int(request.form['eviction_threshold'])
                },
                # Add "action_steps" data similarly
            }

            # Update and validate the new configuration
            config_manager.update_config(new_config_data)
            config_manager.save_config()
            return redirect(url_for('some_route_after_success'))  # Redirect to a success page or the same page
        except Exception as e:
            # Handle exceptions, e.g., validation errors, type errors
            print(f"Error updating configuration: {e}")
            # Optionally, redirect to an error page or show an error message

    # Render the configuration form
    return render_template('update_configuration.html', config=config_manager.get_config())

# Ayush
@app.route('/evaluate-tenant-status/<tenant_id>', methods=['GET', 'POST'])
def evaluate_tenant_status(tenant_id):
    # Fetch tenant from the database
    tenant = Tenant.query.get(tenant_id)
    if not tenant:
        flash("Tenant not found", "error")
        return redirect(url_for('index'))

    if request.method == 'POST':
        action, action_steps, recommended_status = decide_next_action(tenant, config_manager.get_config())

        # Update tenant's status and possibly take further actions
        if recommended_status != tenant.status:
            tenant.status = recommended_status
            try:
                db.session.commit()
                flash("Tenant status updated successfully", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred: {e}", "error")
        
        return redirect(url_for('view_tenant', tenant_id=tenant_id))

    return render_template('evaluate_tenant_status.html', tenant=tenant)


# Ayush
@app.route('/mass-evaluate-tenants', methods=['POST'])
def mass_evaluate_tenants():
    tenants = Tenant.query.all()
    for tenant in tenants:
        # Get the recommended status based on your decision logic
        action, action_steps, recommended_status = decide_next_action(tenant, config_manager.get_config())

        # Check if the recommended status is a 'should be' status and update
        if recommended_status in STATUSES and 'should_be' in recommended_status:
            tenant.status = recommended_status

    db.session.commit()
    flash('Mass evaluation completed successfully.')
    return redirect(url_for('view_all_tenants'))


@app.route('/import-data', methods=['GET', 'POST'])
def import_data():
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            flash('No file selected', 'error')
            return redirect(url_for('import_data'))

        try:
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.DictReader(stream)
            import_errors = []

            for row in csv_input:
                try:
                    # Convert and validate the fields as necessary
                    tenant_data = {
                        'name': row.get('name', '').strip(),
                        'debt': float(row.get('debt', 0)),
                        'rent': float(row.get('rent', 0)),
                        'days_overdue': int(row.get('days_overdue', 0)),
                        'status': row.get('status', 'na').strip(),
                        'telephone': row.get('telephone', '').strip(),
                        'email': row.get('email', '').strip(),
                        'unit_number': row.get('unit_number', '').strip(),
                        'lease_start': row.get('lease_start', '').strip(),
                        'notes': row.get('notes', '').strip()
                    }
                    new_tenant = Tenant(**tenant_data)
                    db.session.add(new_tenant)
                except ValueError as e:
                    import_errors.append(f"Row {csv_input.line_num}: Invalid data format - {e}")
                    continue
                except KeyError as e:
                    import_errors.append(f"Row {csv_input.line_num}: Missing field - {e}")
                    continue

            if import_errors:
                db.session.rollback()  # Rollback if there are errors
                for error in import_errors:
                    flash(error, 'error')
            else:
                db.session.commit()  # Commit only if there are no errors
                flash('Data imported successfully', 'success')

        except Exception as e:
            db.session.rollback()  # Rollback in case of any other exceptions
            flash(f'Error during import: {e}', 'error')

        return redirect(url_for('view_all_tenants'))

    return render_template('import_data.html')

# Ayush
@app.route('/generate-tenant-document/<int:tenant_id>', methods=['POST'])
def generate_tenant_document(tenant_id):
    # Fetch the tenant from the database
    tenant = Tenant.query.get_or_404(tenant_id)
    
    # Specify the action type; you can modify this based on different buttons/forms if needed
    action = 'warning'
    action_steps = {}  # Define action steps if necessary for document content customization
    
    # Call the document generation function
    success, document_path_or_message = generate_pdf_document(tenant, action, action_steps)
    
    if success:
        # If the document was generated successfully, redirect to the document download route
        # Assuming the document's filename can be inferred from the tenant ID and action
        filename = f'{tenant_id}_{action}.pdf'
        flash('Document generated successfully.', 'success')
        return redirect(url_for('documents', filename=filename))
    else:
        # If document generation failed, show an error message
        flash(f'Failed to generate document: {document_path_or_message}', 'error')
        return redirect(url_for('view_tenant', tenant_id=tenant_id))

# Ayush
@app.route('/generate-tenant-summary-report')
def generate_tenant_summary_report():
    try:
        message = report_generator.generate_tenant_summary_report_pdf()
        flash(message)
    except Exception as e:
        flash(f'Error generating report: {e}', 'error')
    return redirect(url_for('reports_page'))

# Ayush
@app.route('/generate-tenant-debt-report')
def generate_tenant_debt_report():
    # Call the function to generate the Tenant Debt Report
    message = report_generator.generate_debt_report_pdf()
    flash(message)
    return redirect(url_for('reports_page'))

# Ayush
@app.route('/generate-tenant-status-report')
def generate_tenant_status_report():
    # Call the function to generate the Tenant Status Report
    message = report_generator.generate_status_report_pdf()
    flash(message)
    return redirect(url_for('reports_page'))

# Ayush
@app.route('/generate-tenant-overdue-report')
def generate_tenant_overdue_report():
    # Call the function to generate the Tenant Overdue Report
    message = report_generator.generate_overdue_report_pdf()
    flash(message)
    return redirect(url_for('reports_page'))

@app.route('/reports')
def reports_page():
    # Render the reports page template
    return render_template('reports.html')

@app.route('/sort-tenants')
def sort_tenants():
    sort_by = request.args.get('sort_by', 'name')  # Default sort by name
    reverse = request.args.get('reverse', 'false') == 'true'  # Convert to boolean

    # Using getattr to dynamically get the attribute to sort by
    sort_attribute = getattr(Tenant, sort_by, None)
    if sort_attribute is None:
        flash(f"Invalid sort attribute: {sort_by}", "error")
        return redirect(url_for('view_all_tenants'))

    # Sorting in ascending or descending order based on the 'reverse' flag
    if reverse:
        sorted_tenants = Tenant.query.order_by(sort_attribute.desc())
    else:
        sorted_tenants = Tenant.query.order_by(sort_attribute)

    return render_template('view_all_tenants.html', tenants=sorted_tenants.all())

@app.route('/filter-tenants')
def filter_tenants():
    filter_by = request.args.get('filter_by', 'status')  # Default filter by status
    filter_value = request.args.get('filter_value', '')

    # Ensure the filter column exists to prevent SQL injection
    if hasattr(Tenant, filter_by):
        # Use SQLAlchemy's ilike for case-insensitive search
        filter_column = getattr(Tenant, filter_by)
        filtered_tenants = Tenant.query.filter(filter_column.ilike(f'%{filter_value}%'))
    else:
        flash(f"Invalid filter attribute: {filter_by}", "error")
        return redirect(url_for('view_all_tenants'))

    return render_template('view_all_tenants.html', tenants=filtered_tenants.all())


@app.route('/download-document/<filename>')
def download_document(filename):
    directory = app.config['DOCUMENTS_FOLDER']
    return send_from_directory(directory, filename, as_attachment=True)

def generate_document(tenant, action, action_steps):
    # Call your existing function to generate the PDF
    document_path = generate_pdf_document(tenant, action, action_steps)

    # Check if the PDF was generated successfully and return the path
    if document_path:
        return document_path
    else:
        # Handle the case where PDF generation failed
        return None

@app.route('/documents/<filename>')
def documents(filename):
    return send_from_directory(app.config['DOCUMENTS_FOLDER'], filename)

@app.route('/search-results')
def search_results():
    query = request.args.get('query', '')

    # Search Tenants
    tenant_results = Tenant.query.filter(
        Tenant.name.ilike(f'%{query}%') |
        Tenant.email.ilike(f'%{query}%') |
        Tenant.telephone.ilike(f'%{query}%')
    ).all()

    # Add other searches for functionalities based on your application's needs
    # ...

    return render_template('search_results.html', tenants=tenant_results, query=query)


if __name__ == '__main__':

    app.run(debug=True)
