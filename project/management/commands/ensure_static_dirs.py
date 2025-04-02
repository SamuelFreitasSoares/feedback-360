from django.core.management.base import BaseCommand
import os

class Command(BaseCommand):
    help = 'Creates necessary static directories for the application'

    def handle(self, *args, **options):
        # Define paths to create
        paths = [
            'static/csv_templates',
        ]
        
        # Get base directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        for path in paths:
            full_path = os.path.join(base_dir, path)
            if not os.path.exists(full_path):
                os.makedirs(full_path)
                self.stdout.write(self.style.SUCCESS(f'Created directory: {full_path}'))
            else:
                self.stdout.write(f'Directory already exists: {full_path}')
