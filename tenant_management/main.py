# tenant_management.main.py
# old 

from models import Tenant, Session
from config_manager import ConfigManager
from decision_logic import decide_next_action
from document_generator import generate_pdf_document
import report_generator as rg
import csv


# Create an instance of the ConfigManager
config_manager = ConfigManager('config.json')

# You can now access the configuration data like this:
config_data = config_manager.get_config()

# Path to the tenant data file
tenant_file_path = 'tenants.json'

VALID_STATUSES = ['eviction', 'cancellation', 'warning', 'lawsuit', 'na']

# Load tenants from file on startup


csv_file_path = 'import.csv'

# Function to display the main menu
def main_menu():
    while True:
        print("\nMain Menu:")
        print("1. Add Tenant")
        print("2. Update Tenant")
        print("3. View Tenant")
        print("4. View All Tenants")
        print("5. View Configuration")
        print("6. Update Configuration")
        print("7. Evaluate Tenant Status")
        print("9. Import Data from CSV")
        print("10. Mass Evaluate All Tenants")
        print("11. Delete Tenant")
        print("12. Reports")
        print("13. View Sorted Tenants")
        print("14. View Filtered Tenants")
        print("15. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            add_tenant()
        elif choice == '2':
            update_tenant()
        elif choice == '3':
            view_tenant()
        elif choice == '4':
            view_all_tenants()
        elif choice == '5':
            pass
        elif choice == '6':
            view_configuration()
        elif choice == '7':
            update_configuration()
        elif choice == '8':
            evaluate_tenant_status()
        elif choice == '9':
            import_from_csv(csv_file_path)
        elif choice == '10':
            mass_evaluate_tenants()
        elif choice == '11':
            delete_tenant()
        elif choice == '12':
            report_submenu()
        elif choice == '13':
            view_sorted_tenants()
        elif choice == '14':
            view_filtered_tenants()
        elif choice == '15':
            print("Exiting program.")
            break
        else:
            print("Invalid choice, please try again.")

def report_submenu():
    while True:
        print("\nReports:")
        print("1. Generate overdue report")
        print("2. Generate status report")
        print("3. Generate tenant summary report")
        print("4. Exit to main menu")

        choice = input("Enter your choice: ")

        if choice == '1':
            rg.generate_overdue_report_pdf(session)
        elif choice == '2':
            rg.generate_status_report_pdf(session)
        elif choice == '3':
            rg.generate_tenant_summary_report_pdf(session)
        elif choice == '4':
            print("Exiting reports.")
            break
        else:
            print("Invalid choice, please try again.")


# Function to add a tenant
def add_tenant():
    print("\nAdd a new tenant:")
    name = input("Enter tenant's name: ")
    debt = float(input("Enter tenant's debt: "))
    rent = float(input("Enter tenant's rent: "))
    days_overdue = int(input("Enter days overdue: "))
    status = input("Enter tenant's status (eviction/warning/cancellation/lawsuit/na): ")
    if status not in VALID_STATUSES:
        print("Invalid status. Please enter a valid status.")
        return
    telephone = input("Enter tenant's telephone number: ")
    email = input("Enter tenant's email: ")
    unit_number = input("Enter tenant's unit number: ")
    lease_start = input("Enter lease start date (YYYY-MM-DD): ")
    notes = input("Enter any notes: ")

    tenant = Tenant(name=name, debt=debt, rent=rent, days_overdue=days_overdue, status=status,
                    telephone=telephone, email=email, unit_number=unit_number, lease_start=lease_start, notes=notes)
    session = Session()
    session.add(tenant)
    session.commit()
    print(f"Tenant added successfully with ID: {tenant.tenant_id}")
    session.close()



# Function to update a tenant
def update_tenant():
    print("\nUpdate a tenant:")
    tenant_id = input("Enter tenant ID: ")
    session = Session()
    tenant = session.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if tenant:
        name = input("Enter tenant's new name (leave blank to keep current): ")
        debt = input("Enter tenant's new debt (leave blank to keep current): ")
        days_overdue = input("Enter new days overdue (leave blank to keep current): ")
        status = input("Enter tenant's new status (leave blank to keep current): ")
        if status and status not in VALID_STATUSES:
            print("Invalid status. Please enter a valid status.")
            return

        if name:
            tenant.name = name
        if debt:
            tenant.debt = float(debt)
        if days_overdue:
            tenant.days_overdue = int(days_overdue)
        if status:
            tenant.status = status

        session.commit()
        print("Tenant updated successfully.")
    else:
        print("Tenant not found.")
    session.close()



# Function to view a single tenant's details
def view_tenant():
    tenant_id = input("Enter tenant ID to view: ")
    session = Session()
    tenant = session.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if tenant:
        print("\nTenant Details:")
        for key, value in vars(tenant).items():
            if key != '_sa_instance_state':  # Filter out SQLAlchemy-specific attribute
                print(f"{key}: {value}")
    else:
        print("Tenant not found.")
    session.close()



# Function to view all tenants
def view_all_tenants():
    session = Session()
    tenants = session.query(Tenant).all()
    print("\nAll Tenants:")
    for tenant in tenants:
        print(f"ID: {tenant.tenant_id}, Name: {tenant.name}, Debt: {tenant.debt:.2f}, "
              f"Days Overdue: {tenant.days_overdue}, Status: {tenant.status}")
    session.close()


def view_configuration():
    print("\nCurrent Configuration:")
    config_data = config_manager.get_config()
    for section, settings in config_data.items():
        print(f"\n{section}:")
        for setting, value in settings.items():
            print(f"  {setting}: {value}")


def update_configuration():
    print("\nUpdate Configuration:")
    section = input("Enter section to update (e.g., 'decision_thresholds'): ")
    setting = input(f"Enter setting to update (e.g., 'warning_threshold'): ")
    value = input("Enter new value: ")

    try:
        # Attempt to convert the input to a number if appropriate
        value = int(value) if value.isdigit() else float(value) if '.' in value else value
    except ValueError:
        pass  # Keep value as string if conversion fails

    if config_manager.update_config(section, setting, value):
        print("Configuration updated successfully.")
    else:
        print("Failed to update configuration. Please check the section and setting names.")


def evaluate_tenant_status():
    tenant_id = input("Enter tenant ID to evaluate: ")
    session = Session()
    tenant = session.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if tenant:
        action, action_steps, recommended_status = decide_next_action(tenant, config_manager.get_config())
        if action == 'na' or tenant.status == action:
            print(f"No new action required for {tenant.name} (Tenant ID: {tenant_id}).")
        else:
            if recommended_status != tenant.status:
                tenant.status = recommended_status
                session.commit()
                print(f"Tenant status updated to {recommended_status}.")
            if action != 'na':
                document_message = generate_pdf_document(tenant, action, action_steps)
                print(document_message)
    else:
        print("Tenant not found.")
    session.close()



def import_from_csv(csv_file_path):
    with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        session = Session()
        for row in reader:
            new_tenant = Tenant(
                name=row['name'],
                debt=float(row.get('debt', 0)),
                rent=float(row.get('rent', 0)),
                days_overdue=int(row.get('days_overdue', 0)),
                status=row.get('status', 'na'),
                telephone=row.get('telephone', ''),
                email=row.get('email', ''),
                unit_number=row.get('unit_number', ''),
                lease_start=row.get('lease_start', ''),
                notes=row.get('notes', '')
            )
            session.add(new_tenant)
        session.commit()
        session.close()
        print(f"Imported tenants from {csv_file_path}")




# Function to mass evaluate the status of all tenants
def mass_evaluate_tenants():
    print("\nMass Evaluation of All Tenants:")
    session = Session()
    tenants = session.query(Tenant).all()
    for tenant in tenants:
        action, action_steps, recommended_status = decide_next_action(tenant, config_manager.get_config())
        print(f"Tenant ID: {tenant.tenant_id}, Tenant Name: {tenant.name}, Current Status: {tenant.status}")

        if action != 'na' and tenant.status != recommended_status:
            tenant.status = recommended_status
            session.commit()
            print(f"Tenant status updated to {recommended_status}.")
            if action != 'na':
                document_message = generate_pdf_document(tenant, action, action_steps)
                print(document_message)

    print("\nMass evaluation completed.")
    session.close()



def delete_tenant():
    print("\nDelete a Tenant:")
    tenant_id = input("Enter tenant ID to delete: ")
    session = Session()
    tenant = session.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if tenant:
        session.delete(tenant)
        session.commit()
        print("Tenant deleted successfully.")
    else:
        print("Tenant not found.")
    session.close()



def view_sorted_tenants():
    sort_by = input("Enter field to sort by (e.g., 'name', 'debt'): ")
    reverse = input("Sort in reverse order? (yes/no): ").lower() == 'yes'

    session = Session()
    if reverse:
        sorted_tenants = session.query(Tenant).order_by(getattr(Tenant, sort_by).desc()).all()
    else:
        sorted_tenants = session.query(Tenant).order_by(getattr(Tenant, sort_by)).all()
    
    for tenant in sorted_tenants:
        print_tenant_info(tenant)
    
    session.close()

    if sorted_tenants:
        if input("Generate PDF report for this view? (yes/no): ").lower() == 'yes':
            filename = input("Enter filename for the report (e.g., 'sorted_report.pdf'): ")
            data = prepare_tenant_data_for_report(sorted_tenants)
            rg.generate_pdf_report(data, filename, 'Sorted Tenants Report')



def prepare_tenant_data_for_report(tenants):
    title = ["ID", "Name", "Debt", "Rent", "Days Overdue", "Status", "Telephone", "Email", "Unit Number", "Lease Start", "Notes"]
    data = [title]
    for tenant in tenants:
        row = [
            tenant.tenant_id, tenant.name, f"{tenant.debt:.2f}", f"{tenant.rent:.2f}",
            tenant.days_overdue, tenant.status, tenant.telephone, tenant.email,
            tenant.unit_number, tenant.lease_start, tenant.notes
        ]
        data.append(row)
    return data


def view_filtered_tenants():
    filter_field = input("Enter field to filter by (e.g., 'status', 'unit_number'): ")
    filter_value = input(f"Enter value for {filter_field}: ")

    session = Session()
    filtered_tenants = session.query(Tenant).filter(getattr(Tenant, filter_field) == filter_value).all()

    for tenant in filtered_tenants:
        print_tenant_info(tenant)
    
    session.close()

    if filtered_tenants:
        if input("Generate PDF report for this view? (yes/no): ").lower() == 'yes':
            filename = input("Enter filename for the report (e.g., 'filtered_report.pdf'): ")
            data = prepare_tenant_data_for_report(filtered_tenants)
            rg.generate_pdf_report(data, filename, 'Filtered Tenants Report')



def print_tenant_info(tenant):
    print(f"ID: {tenant.tenant_id}, Name: {tenant.name}, Debt: {tenant.debt}, Rent: {tenant.rent}, "
          f"Days Overdue: {tenant.days_overdue}, Status: {tenant.status}, Telephone: {tenant.telephone}, "
          f"Email: {tenant.email}, Unit Number: {tenant.unit_number}, Lease Start: {tenant.lease_start}, Notes: {tenant.notes}")


# Run the main menu in a loop
if __name__ == "__main__":
    main_menu()
