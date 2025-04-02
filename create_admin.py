import os
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FeedBack360.settings')
django.setup()

from project.models import Admin
from project.utils import hash_password

def create_admin():
    # Check if admin already exists
    admin = Admin.objects.filter(emailAdmin='admin@feedback360.com').first()
    
    if admin:
        print(f"Admin already exists: {admin.nomeAdmin} ({admin.emailAdmin})")
        # Update password to ensure it's correct and hashed
        admin.senhaAdmin = hash_password('admin123')
        admin.save()
        print("Admin password has been reset and secured.")
    else:
        # Create new admin with hashed password
        admin = Admin.objects.create(
            nomeAdmin='Admin',
            emailAdmin='admin@feedback360.com',
            senhaAdmin=hash_password('admin123')
        )
        print(f"New admin created: {admin.nomeAdmin}")
        print("Email: admin@feedback360.com")
        print("Password: admin123")
    
    # Print all admins for verification
    all_admins = Admin.objects.all()
    print("\nAll admins in the system:")
    for admin in all_admins:
        print(f"- {admin.nomeAdmin} ({admin.emailAdmin})")

if __name__ == '__main__':
    create_admin()
