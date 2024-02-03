document.addEventListener('DOMContentLoaded', function() {
    const tenantForm = document.getElementById('tenant-form');
    if (tenantForm) {
        tenantForm.addEventListener('submit', function(e) {
            // Example validation logic
            const tenantName = document.getElementById('tenant-name').value;
            if (tenantName === '') {
                alert('Please enter the tenant\'s name');
                e.preventDefault(); // Prevent form from submitting
            }
            // Add more validation as needed
        });
    }
});
