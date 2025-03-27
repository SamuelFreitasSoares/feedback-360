from django.core.management.base import BaseCommand
from django.conf import settings
import os
from pathlib import Path
import sys

class Command(BaseCommand):
    help = 'Fix common issues in the Feedback 360 application'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting diagnostic and fix process...'))
        
        # Check directories exist
        self._check_and_create_directory('project/fixtures')
        self._check_and_create_directory('project/templatetags')
        self._check_and_create_directory('project/management/commands')
        self._check_and_create_directory('static/css')
        self._check_and_create_directory('static/js')
        self._check_and_create_directory('templates')
        
        # Check for __init__.py files
        self._check_and_create_init_file('project/fixtures')
        self._check_and_create_init_file('project/templatetags')
        self._check_and_create_init_file('project/management')
        self._check_and_create_init_file('project/management/commands')
        
        # Check STATICFILES_DIRS setting
        self._check_staticfiles_setting()
        
        # Check context_processor setting
        self._check_context_processor_setting()
        
        # Check middleware setting
        self._check_middleware_setting()
        
        self.stdout.write(self.style.SUCCESS('Diagnostic and fix process completed!'))

    def _check_and_create_directory(self, directory_path):
        """Check if directory exists and create it if not."""
        full_path = os.path.join(settings.BASE_DIR, directory_path)
        if not os.path.exists(full_path):
            try:
                os.makedirs(full_path, exist_ok=True)
                self.stdout.write(self.style.SUCCESS(f'Created directory: {directory_path}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating directory {directory_path}: {str(e)}'))
        else:
            self.stdout.write(f'Directory exists: {directory_path}')

    def _check_and_create_init_file(self, directory_path):
        """Check if __init__.py exists in directory and create it if not."""
        init_file = os.path.join(settings.BASE_DIR, directory_path, '__init__.py')
        if not os.path.exists(init_file):
            try:
                with open(init_file, 'w') as f:
                    f.write('# This file marks this directory as a Python package\n')
                self.stdout.write(self.style.SUCCESS(f'Created __init__.py in {directory_path}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating __init__.py in {directory_path}: {str(e)}'))
        else:
            self.stdout.write(f'__init__.py exists in {directory_path}')
            
    def _check_staticfiles_setting(self):
        """Check if STATICFILES_DIRS is configured correctly."""
        if hasattr(settings, 'STATICFILES_DIRS'):
            static_dir = Path(settings.BASE_DIR) / 'static'
            if any(str(static_dir) == str(path) for path in settings.STATICFILES_DIRS):
                self.stdout.write('STATICFILES_DIRS setting is configured correctly.')
            else:
                self.stdout.write(self.style.WARNING('STATICFILES_DIRS setting does not include the static directory.'))
        else:
            self.stdout.write(self.style.ERROR('STATICFILES_DIRS setting is not defined.'))
            
    def _check_context_processor_setting(self):
        """Check if the custom context processor is configured correctly."""
        for template in settings.TEMPLATES:
            processors = template.get('OPTIONS', {}).get('context_processors', [])
            if 'project.context_processors.user_data' in processors:
                self.stdout.write('Custom context processor is configured correctly.')
                return
        self.stdout.write(self.style.ERROR('Custom context processor is not configured correctly.'))

    def _check_middleware_setting(self):
        """Check if the custom middleware is configured correctly."""
        if 'project.middleware.LoginRequiredMiddleware' in settings.MIDDLEWARE:
            self.stdout.write('Custom middleware is configured correctly.')
        else:
            self.stdout.write(self.style.ERROR('Custom middleware is not configured correctly.'))
