# tenant_database.py
# old

import json
import csv


class Tenant:
    def __init__(self, tenant_id, name, debt, rent, days_overdue, status='na', telephone='', email='', unit_number='',
                 lease_start='', notes=''):
        self.tenant_id = tenant_id
        self.name = name
        self.debt = debt
        self.rent = rent
        self.days_overdue = days_overdue
        self.status = status
        self.telephone = telephone
        self.email = email
        self.unit_number = unit_number
        self.lease_start = lease_start
        self.notes = notes

    def update_info(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TenantDatabase:
    def __init__(self):
        self.tenants = {}
        self.used_ids = set()  # Track used IDs
        self.next_tenant_id = 1 # Starting ID for automatic generation

    def generate_tenant_id(self):
        # Find the next available unique ID
        while f"{self.next_tenant_id:05d}" in self.used_ids:
            self.next_tenant_id += 1
        new_id = f"{self.next_tenant_id:05d}"  # Format the ID to be 5 digits long
        self.used_ids.add(new_id)  # Add the new ID to the set of used IDs
        self.next_tenant_id += 1  # Increment for the next ID
        return new_id

    def add_tenant(self, name, debt, rent, days_overdue, status='na', telephone='',
                   email='', unit_number='', lease_start='', notes=''):
        tenant_id = self.generate_tenant_id()
        new_tenant = Tenant(tenant_id, name, debt, rent, days_overdue, status,
                            telephone, email, unit_number, lease_start, notes)
        self.tenants[tenant_id] = new_tenant
        return tenant_id  # Return the new tenant's ID

    def update_tenant(self, tenant_id, **kwargs):
        tenant = self.tenants.get(tenant_id)
        if tenant:
            tenant.update_info(**kwargs)
            return True
        return False

    def get_tenant(self, tenant_id):
        return self.tenants.get(tenant_id)

    def get_all_tenants(self):
        return list(self.tenants.values())

    def save_tenants_to_file(self, file_path):
        with open(file_path, 'w') as file:
            json.dump({tenant_id: tenant.__dict__ for tenant_id, tenant in self.tenants.items()}, file, indent=4)

    def load_tenants_from_file(self, file_path):
        with open(file_path, 'r') as file:
            tenants_data = json.load(file)
            for tenant_id, tenant_data in tenants_data.items():
                # Ensure all keys are present
                full_tenant_data = {
                    'tenant_id': tenant_id,
                    'name': '',
                    'debt': 0.0,
                    'days_overdue': 0,
                    'status': 'active',
                    'telephone': '',
                    'email': '',
                    'unit_number': '',
                    'lease_start': '',
                    'notes': '',
                    **tenant_data  # This will override the default values with actual values
                }
                self.tenants[tenant_id] = Tenant(**full_tenant_data)

    def delete_tenant(self, tenant_id):
        if tenant_id in self.tenants:
            del self.tenants[tenant_id]
            return True
        return False

    def sort_tenants(self, sort_by=None, reverse=False):
        tenants = self.get_all_tenants()
        if sort_by:
            tenants.sort(key=lambda x: getattr(x, sort_by, ''), reverse=reverse)
        return tenants

    def filter_tenants(self, filter_by=None):
        if not filter_by:
            return self.get_all_tenants()

        key, value = filter_by
        return [tenant for tenant in self.get_all_tenants() if getattr(tenant, key, '') == value]

    def update_tenant_status(self, tenant_id, new_status):
        if tenant_id in self.tenants:
            self.tenants[tenant_id].status = new_status
            return True
        return False
