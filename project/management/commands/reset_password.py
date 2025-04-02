from django.core.management.base import BaseCommand, CommandError
from project.models import Aluno, Professor, Coordenador, Admin
from project.utils import hash_password

class Command(BaseCommand):
    help = 'Reset password for a user by email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email')
        parser.add_argument('password', type=str, help='New password')
        parser.add_argument(
            '--type', 
            type=str, 
            choices=['aluno', 'professor', 'coordenador', 'admin'],
            help='User type (optional)'
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        user_type = options.get('type')
        
        user = None
        
        if user_type == 'aluno' or not user_type:
            try:
                user = Aluno.objects.get(emailAluno=email)
                user.senhaAluno = hash_password(password)
                user_type = 'aluno'
            except Aluno.DoesNotExist:
                if user_type:
                    raise CommandError(f"No student found with email {email}")
        
        if user_type == 'professor' or (not user_type and not user):
            try:
                user = Professor.objects.get(emailProf=email)
                user.senhaProf = hash_password(password)
                user_type = 'professor'
            except Professor.DoesNotExist:
                if user_type:
                    raise CommandError(f"No professor found with email {email}")
        
        if user_type == 'coordenador' or (not user_type and not user):
            try:
                user = Coordenador.objects.get(emailCoord=email)
                user.senhaCoord = hash_password(password)
                user_type = 'coordenador'
            except Coordenador.DoesNotExist:
                if user_type:
                    raise CommandError(f"No coordinator found with email {email}")
        
        if user_type == 'admin' or (not user_type and not user):
            try:
                user = Admin.objects.get(emailAdmin=email)
                user.senhaAdmin = hash_password(password)
                user_type = 'admin'
            except Admin.DoesNotExist:
                if user_type:
                    raise CommandError(f"No admin found with email {email}")
                
        if not user:
            raise CommandError(f"No user found with email {email}")
            
        user.save()
        self.stdout.write(self.style.SUCCESS(f'Successfully reset password for {user_type} with email {email}'))
