import os
import django
import sys

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FeedBack360.settings')
django.setup()

from project.models import Admin
from project.utils import hash_password

def fix_admin_login():
    """Reset admin password to a known value"""
    
    try:
        # Try to find admin
        admin = Admin.objects.filter(emailAdmin='admin@feedback360.com').first()
        
        if not admin:
            # Create a new admin
            admin = Admin.objects.create(
                nomeAdmin='Admin',
                emailAdmin='admin@feedback360.com',
                senhaAdmin=hash_password('admin123')
            )
            print(f"Created new admin: {admin.nomeAdmin}")
        else:
            # Reset existing admin password
            admin.senhaAdmin = hash_password('admin123')
            admin.save()
            print(f"Reset password for admin: {admin.nomeAdmin}")
        
        print("\nAdmin credentials:")
        print("Email: admin@feedback360.com")
        print("Password: admin123")
        print("\nUse these credentials to log in and access the debug tool at /custom-admin/debug/auth/")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    fix_admin_login()
