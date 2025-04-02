from django.core.management.base import BaseCommand
from project.models import Admin

class Command(BaseCommand):
    help = 'Creates an admin user for the system'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, default='Admin', help='Admin name')
        parser.add_argument('--email', type=str, default='admin@feedback360.com', help='Admin email')
        parser.add_argument('--password', type=str, default='admin123', help='Admin password')

    def handle(self, *args, **options):
        name = options['name']
        email = options['email']
        password = options['password']
        
        try:
            # Check if admin already exists
            existing_admin = Admin.objects.filter(emailAdmin=email).first()
            if existing_admin:
                self.stdout.write(self.style.WARNING(f'Admin with email {email} already exists!'))
                return
                
            # Create admin user
            admin = Admin.objects.create(
                nomeAdmin=name,
                emailAdmin=email,
                senhaAdmin=password
            )
            self.stdout.write(self.style.SUCCESS(f'Admin user created successfully!'))
            self.stdout.write(self.style.SUCCESS(f'Name: {name}'))
            self.stdout.write(self.style.SUCCESS(f'Email: {email}'))
            self.stdout.write(self.style.SUCCESS(f'Password: {password}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating admin: {str(e)}'))
