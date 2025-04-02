from django.core.management.base import BaseCommand
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from project.models import Aluno, Professor, Coordenador, Admin
from project.utils import enviar_email_redefinicao_senha

class Command(BaseCommand):
    help = 'Test email sending functionality'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Recipient email address')
        parser.add_argument('--template', action='store_true', help='Test with HTML template')
        parser.add_argument('--reset', action='store_true', help='Test password reset email')
        parser.add_argument('--type', type=str, choices=['aluno', 'professor', 'coordenador', 'admin'], 
                           help='User type for password reset test')

    def handle(self, *args, **options):
        email = options['email']
        use_template = options['template']
        test_reset = options['reset']
        user_type = options.get('type')
        
        if test_reset:
            # Find user by email
            user = None
            if not user_type:
                # Try to find user automatically
                if Aluno.objects.filter(emailAluno=email).exists():
                    user = Aluno.objects.get(emailAluno=email)
                    user_type = 'aluno'
                elif Professor.objects.filter(emailProf=email).exists():
                    user = Professor.objects.get(emailProf=email)
                    user_type = 'professor'
                elif Coordenador.objects.filter(emailCoord=email).exists():
                    user = Coordenador.objects.get(emailCoord=email)
                    user_type = 'coordenador'
                elif Admin.objects.filter(emailAdmin=email).exists():
                    user = Admin.objects.get(emailAdmin=email)
                    user_type = 'admin'
            else:
                # Find by specified type
                if user_type == 'aluno':
                    user = Aluno.objects.filter(emailAluno=email).first()
                elif user_type == 'professor':
                    user = Professor.objects.filter(emailProf=email).first()
                elif user_type == 'coordenador':
                    user = Coordenador.objects.filter(emailCoord=email).first()
                elif user_type == 'admin':
                    user = Admin.objects.filter(emailAdmin=email).first()
            
            if not user:
                self.stdout.write(self.style.ERROR(f'No user found with email {email}'))
                return
            
            # Send password reset email
            success = enviar_email_redefinicao_senha(user, user_type)
            
            if success:
                self.stdout.write(self.style.SUCCESS(f'Password reset email sent to {email}'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to send password reset email'))
            
        elif use_template:
            # Send HTML email with template
            subject = 'Teste de Email HTML - Feedback 360°'
            context = {
                'nome': 'Usuário de Teste',
                'reset_link': 'http://example.com/reset',
                'token': 'test_token_123'
            }
            html_content = render_to_string('emails/reset_password_email.html', context)
            text_content = strip_tags(html_content)
            
            try:
                msg = EmailMultiAlternatives(
                    subject, text_content, settings.DEFAULT_FROM_EMAIL, [email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                
                self.stdout.write(self.style.SUCCESS(f'HTML test email sent to {email}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
                
        else:
            # Send simple plain text email
            try:
                send_mail(
                    'Teste de Email - Feedback 360°',
                    'Este é um email de teste do sistema Feedback 360°.',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS(f'Plain text test email sent to {email}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
