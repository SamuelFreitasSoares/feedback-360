import hashlib
import random
import string
import csv
import io
import secrets
import uuid
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse

def hash_password(password):
    """
    Cria um hash da senha usando SHA-256
    
    Args:
        password (str): A senha em texto plano
        
    Returns:
        str: Hash da senha
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    """
    Verifica se a senha corresponde ao hash armazenado
    
    Args:
        password (str): A senha em texto plano
        hashed_password (str): Hash da senha armazenada
        
    Returns:
        bool: True se a senha for válida, False caso contrário
    """
    return hash_password(password) == hashed_password

def generate_random_password(length=8):
    """
    Gera uma senha aleatória com o comprimento especificado
    
    Args:
        length (int): Comprimento da senha (padrão: 8)
        
    Returns:
        str: Senha aleatória
    """
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

def process_csv_file(file, user_type):
    """
    Processa um arquivo CSV de importação de usuários
    
    Args:
        file: O arquivo CSV enviado
        user_type (str): Tipo de usuário ('aluno', 'professor' ou 'coordenador')
        
    Returns:
        list: Lista de dicionários com os dados dos usuários
    """
    decoded_file = file.read().decode('utf-8')
    io_string = io.StringIO(decoded_file)
    reader = csv.reader(io_string)
    
    # Pular cabeçalho
    next(reader)
    
    users = []
    line_num = 2  # Começando com a linha 2 (depois do cabeçalho)
    
    for row in reader:
        # Validar quantidade de colunas
        if user_type == 'aluno' and len(row) != 4:
            raise ValueError(f"A linha {line_num} não possui 4 colunas para aluno. Formato esperado: nome,email,matricula,curso_id")
        elif user_type == 'professor' and len(row) != 2:
            raise ValueError(f"A linha {line_num} não possui 2 colunas para professor. Formato esperado: nome,email")
        elif user_type == 'coordenador' and len(row) != 3:
            raise ValueError(f"A linha {line_num} não possui 3 colunas para coordenador. Formato esperado: nome,email,curso_id")
        
        # Criar dicionário de usuário baseado no tipo
        user = {}
        if user_type == 'aluno':
            user = {
                'nome': row[0],
                'email': row[1],
                'matricula': row[2],
                'curso_id': row[3]
            }
        elif user_type == 'professor':
            user = {
                'nome': row[0],
                'email': row[1]
            }
        elif user_type == 'coordenador':
            user = {
                'nome': row[0],
                'email': row[1],
                'curso_id': row[2]
            }
        
        users.append(user)
        line_num += 1
    
    return users

def criar_notificacao(titulo, mensagem, destinatario, tipo='info', link=None):
    """
    Cria uma nova notificação para um usuário
    
    Args:
        titulo (str): Título da notificação
        mensagem (str): Conteúdo da notificação
        destinatario (obj): Objeto do usuário (Aluno, Professor, Coordenador ou Admin)
        tipo (str): Tipo da notificação (info, warning, success, danger)
        link (str): Link opcional para redirecionamento
    
    Returns:
        Notificacao: Objeto da notificação criada
    """
    from .models import Notificacao, Aluno, Professor, Coordenador, Admin
    
    if isinstance(destinatario, Aluno):
        return Notificacao.objects.create(
            titulo=titulo,
            mensagem=mensagem,
            aluno=destinatario,
            tipo=tipo,
            link=link
        )
    elif isinstance(destinatario, Professor):
        return Notificacao.objects.create(
            titulo=titulo,
            mensagem=mensagem,
            professor=destinatario,
            tipo=tipo,
            link=link
        )
    elif isinstance(destinatario, Coordenador):
        return Notificacao.objects.create(
            titulo=titulo,
            mensagem=mensagem,
            coordenador=destinatario,
            tipo=tipo,
            link=link
        )
    elif isinstance(destinatario, Admin):
        return Notificacao.objects.create(
            titulo=titulo,
            mensagem=mensagem,
            admin=destinatario,
            tipo=tipo,
            link=link
        )
    return None

def tem_permissao_competencias(request):
    """Verifica se o usuário tem permissão para gerenciar competências"""
    user_type = request.session.get('user_type')
    return user_type in ['professor', 'coordenador', 'admin']

def obter_notificacoes_usuario(request):
    """
    Obtém as notificações do usuário atual
    
    Args:
        request: Objeto da requisição
    
    Returns:
        QuerySet: Notificações do usuário
    """
    from .models import Notificacao, Aluno, Professor, Coordenador, Admin
    
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if not user_type or not user_id:
        return Notificacao.objects.none()
    
    if user_type == 'aluno':
        return Notificacao.objects.filter(aluno_id=user_id)
    elif user_type == 'professor':
        return Notificacao.objects.filter(professor_id=user_id)
    elif user_type == 'coordenador':
        return Notificacao.objects.filter(coordenador_id=user_id)
    elif user_type == 'admin':
        return Notificacao.objects.filter(admin_id=user_id)
    
    return Notificacao.objects.none()

def generate_token():
    """
    Gera um token único e seguro para redefinição de senha
    
    Returns:
        str: Token único
    """
    return secrets.token_urlsafe(32)

def enviar_email_redefinicao_senha(user, user_type, request=None):
    """
    Envia email de redefinição de senha para o usuário
    
    Args:
        user: Objeto do usuário (Aluno, Professor, Coordenador ou Admin)
        user_type (str): Tipo de usuário ('aluno', 'professor', 'coordenador' ou 'admin')
        request: Objeto da requisição (opcional, usado para gerar URLs absolutas)
        
    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrário
    """
    # Gerar token de redefinição
    token = generate_token()
    
    # Salvar token no usuário correspondente
    if user_type == 'aluno':
        user.reset_token = token
        user.save()
        nome = user.nomeAluno
        email = user.emailAluno
    elif user_type == 'professor':
        user.reset_token = token
        user.save()
        nome = user.nomeProf
        email = user.emailProf
    elif user_type == 'coordenador':
        user.reset_token = token
        user.save()
        nome = user.nomeCoord
        email = user.emailCoord
    elif user_type == 'admin':
        user.reset_token = token
        user.save()
        nome = user.nomeAdmin
        email = user.emailAdmin
    else:
        return False
    
    # Construir URL de redefinição
    if request:
        reset_url = request.build_absolute_uri(
            reverse('reset_password_confirm', kwargs={'token': token})
        )
    else:
        # Caso não tenha request, usa o domínio padrão das configurações
        domain = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000'
        reset_url = f"http://{domain}{reverse('reset_password_confirm', kwargs={'token': token})}"
    
    # Renderizar o template HTML
    context = {
        'nome': nome,
        'reset_link': reset_url,
        'token': token
    }
    html_content = render_to_string('emails/reset_password_email.html', context)
    text_content = strip_tags(html_content)  # Versão texto plano do email
    
    # Enviar email
    try:
        subject = 'Redefinição de Senha - Feedback 360°'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = email
        
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        return True
    except Exception as e:
        print(f"Erro ao enviar email: {str(e)}")
        return False
