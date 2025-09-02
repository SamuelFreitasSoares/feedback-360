from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Count
from django.utils import timezone
from django.urls import reverse
import pandas as pd
import json
from datetime import datetime

from .models import (
    Aluno, Professor, Coordenador, Nota, Atividade, Disciplina, TurmaAluno,
    Turma, Grupo, Competencia, Curso, Semestre, Avaliacao, Notificacao
)
from .utils import (
    hash_password, verify_password, enviar_email_redefinicao_senha,
    generate_token, tem_permissao_competencias, obter_notificacoes_usuario,
    criar_notificacao
)

# Helper functions for role checks
def is_aluno(user_type):
    return user_type == 'aluno'

def is_professor(user_type):
    return user_type == 'professor'

def is_coordenador(user_type):
    return user_type == 'coordenador'

def is_admin(user_type):
    return user_type == 'admin'

# Helper functions for password hashing and verification
def hash_password(password):
    """
    Create a hash of the password using SHA-256
    """
    from .utils import hash_password as utils_hash_password
    return utils_hash_password(password)

def verify_password(input_password, stored_password):
    """
    Verify if the password matches the stored hash
    """
    from .utils import verify_password as utils_verify_password
    return utils_verify_password(input_password, stored_password)

# Update the login_required_custom decorator to handle middleware bypass
def login_required_custom(view_func):
    def wrapper(request, *args, **kwargs):
        if 'user_type' not in request.session or 'user_id' not in request.session:
            messages.error(request, "Você precisa estar logado para acessar esta página.")
            return redirect('login')
        
        # Add additional validation to check if user_id is valid for the user_type
        user_type = request.session['user_type']
        user_id = request.session['user_id']
        
        try:
            if user_type == 'aluno':
                Aluno.objects.get(idAluno=user_id)
            elif user_type == 'professor':
                Professor.objects.get(idProfessor=user_id)
            elif user_type == 'coordenador':
                Coordenador.objects.get(id=user_id)
            elif user_type == 'admin':
                from .models import Admin
                Admin.objects.get(id=user_id)
            else:
                # Unrecognized user type
                messages.error(request, "Tipo de usuário não reconhecido.")
                request.session.flush()
                return redirect('login')
        except Exception:
            # If the user record doesn't exist, clear session and redirect to login
            messages.error(request, "Sua sessão expirou ou é inválida. Por favor, faça login novamente.")
            request.session.flush()
            return redirect('login')
            
        return view_func(request, *args, **kwargs)
    return wrapper

def login(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]

        # Check if the user is an Aluno
        user = Aluno.objects.filter(emailAluno=email).first()
        if user and verify_password(password, user.senhaAluno):
            request.session['user_type'] = 'aluno'
            request.session['user_id'] = user.idAluno
            request.session['username'] = user.nomeAluno
            messages.success(request, f"Bem-vindo, {user.nomeAluno}!")
            return redirect("home")

        # Check if the user is a Professor
        user = Professor.objects.filter(emailProf=email).first()
        if user and verify_password(password, user.senhaProf):
            request.session['user_type'] = 'professor'
            request.session['user_id'] = user.idProfessor
            request.session['username'] = user.nomeProf
            messages.success(request, f"Bem-vindo, Prof. {user.nomeProf}!")
            return redirect("home")
            
        # Check if the user is a Coordenador
        user = Coordenador.objects.filter(emailCoord=email).first()
        if user and verify_password(password, user.senhaCoord):
            request.session['user_type'] = 'coordenador'
            request.session['user_id'] = user.id
            request.session['username'] = user.nomeCoord
            messages.success(request, f"Bem-vindo, Coord. {user.nomeCoord}!")
            return redirect("home")
        
        # Check if the user is an Admin
        from .models import Admin
        user = Admin.objects.filter(emailAdmin=email).first()
        if user and verify_password(password, user.senhaAdmin):
            request.session['user_type'] = 'admin'
            request.session['user_id'] = user.id
            request.session['username'] = user.nomeAdmin
            messages.success(request, f"Bem-vindo, Admin {user.nomeAdmin}!")
            return redirect("home")
        else:
            # Add an error message if credentials are incorrect
            messages.error(request, "Email ou senha incorretos.")
    
    return render(request, "index.html")

def logout(request):
    if 'user_type' in request.session:
        user_type = request.session.get('user_type')
        username = request.session.get('username', '')
        request.session.flush()
        messages.success(request, f"Logout realizado com sucesso. Até logo, {username}!")
    return redirect('login')

def resetPassword(request):
    if request.method == "POST":
        email = request.POST.get("email", "")
        
        # Import Admin model
        from .models import Admin
        from .utils import enviar_email_redefinicao_senha
        
        # Check in all user types
        user = None
        user_type = None
        
        if Aluno.objects.filter(emailAluno=email).exists():
            user = Aluno.objects.get(emailAluno=email)
            user_type = "aluno"
        elif Professor.objects.filter(emailProf=email).exists():
            user = Professor.objects.get(emailProf=email)
            user_type = "professor"
        elif Coordenador.objects.filter(emailCoord=email).exists():
            user = Coordenador.objects.get(emailCoord=email)
            user_type = "coordenador"
        elif Admin.objects.filter(emailAdmin=email).exists():
            user = Admin.objects.get(emailAdmin=email)
            user_type = "admin"
            
        if user:
            # Generate token and send email
            email_sent = enviar_email_redefinicao_senha(user, user_type, request)
            
            if email_sent:
                messages.success(request, "Um link de redefinição de senha foi enviado para o seu email.")
            else:
                messages.warning(request, "Não foi possível enviar o email de redefinição. Por favor, contate o administrador.")
            
            return redirect('login')
        else:
            messages.error(request, "Email não encontrado.")
    
    return render(request, "forgot_password.html")

def reset_password_confirm(request, token):
    """
    View for confirming password reset using a token
    """
    # Find which user has this reset token
    user = None
    user_type = None
    
    # Check in all user types
    aluno = Aluno.objects.filter(reset_token=token).first()
    if aluno:
        user = aluno
        user_type = 'aluno'
    else:
        professor = Professor.objects.filter(reset_token=token).first()
        if professor:
            user = professor
            user_type = 'professor'
        else:
            coordenador = Coordenador.objects.filter(reset_token=token).first()
            if coordenador:
                user = coordenador
                user_type = 'coordenador'
            else:
                from .models import Admin
                admin = Admin.objects.filter(reset_token=token).first()
                if admin:
                    user = admin
                    user_type = 'admin'
    
    if not user:
        messages.error(request, "Token inválido ou expirado. Por favor, solicite uma nova redefinição de senha.")
        return redirect('login')
    
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, "As senhas não correspondem.")
            return render(request, 'reset_password_confirm.html', {'token': token})
        
        # Update password based on user type
        if user_type == 'aluno':
            user.senhaAluno = hash_password(password)
        elif user_type == 'professor':
            user.senhaProf = hash_password(password)
        elif user_type == 'coordenador':
            user.senhaCoord = hash_password(password)
        elif user_type == 'admin':
            user.senhaAdmin = hash_password(password)
        
        # Clear the reset token
        user.reset_token = None
        user.save()
        
        messages.success(request, "Senha redefinida com sucesso. Você já pode fazer login com sua nova senha.")
        return redirect('login')
    
    return render(request, 'reset_password_confirm.html', {'token': token})

@login_required_custom
def home(request):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    username = request.session.get('username', '')
    
    context = {
        'user_type': user_type,
        'username': username
    }
    
    # Customized dashboard based on user type
    if user_type == 'aluno':
        aluno = Aluno.objects.get(idAluno=user_id)
        
        # Get pending evaluations the same way they're calculated in atividades view
        turmas_aluno = TurmaAluno.objects.filter(aluno=aluno)
        all_atividades = Atividade.objects.filter(
            turma__in=[ta.turma for ta in turmas_aluno]
        ).order_by('-dataEntrega', 'titulo')
        
        pending_evaluations = 0
        for atividade in all_atividades:
            grupos = Grupo.objects.filter(atividade=atividade, alunos=aluno)
            if grupos.exists():
                grupo = grupos.first()
                colegas = grupo.alunos.exclude(idAluno=aluno.idAluno)
                
                for colega in colegas:
                    try:
                        avaliacao = Avaliacao.objects.get(
                            avaliador_aluno=aluno,
                            avaliado_aluno=colega,
                            atividade=atividade
                        )
                        
                        if not avaliacao.concluida:
                            pending_evaluations += 1
                    except Avaliacao.DoesNotExist:
                        pending_evaluations += 1
        
        # Get recent activities
        recent_activities = all_atividades[:5]  # First 5 activities
        
        context.update({
            'pending_evaluations': pending_evaluations,
            'recent_activities': recent_activities
        })
        
    elif user_type == 'professor':
        professor = Professor.objects.get(idProfessor=user_id)
        turmas = Turma.objects.filter(professor=professor)
        recent_activities = Atividade.objects.filter(
            turma__in=turmas
        ).order_by('-dataEntrega', 'titulo')[:5]  # Sort by date and then alphabetically by title
        
        context.update({
            'turmas_count': turmas.count(),
            'recent_activities': recent_activities
        })
    
    elif user_type == 'coordenador':
        coordenador = Coordenador.objects.get(id=user_id)
        # Fix the FieldError by filtering using the correct relationship
        if coordenador.curso:
            cursos = [coordenador.curso]  # Just use the coordinator's course directly
        else:
            cursos = []
        
        context.update({
            'cursos': cursos
        })
    
    return render(request, "home.html", context)

@login_required_custom
def atividades(request):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if user_type == 'aluno':
        aluno = Aluno.objects.get(idAluno=user_id)
        turmas_aluno = TurmaAluno.objects.filter(aluno=aluno)
        atividades = Atividade.objects.filter(
            turma__in=[ta.turma for ta in turmas_aluno]
        ).order_by('-dataEntrega', 'titulo')  # Sort by date and then alphabetically by title
        
        # Add group info and pending evaluations
        pending_count = 0  # Count to verify total pending evaluations
        for atividade in atividades:
            grupos = Grupo.objects.filter(atividade=atividade, alunos=aluno)
            atividade.grupo = grupos.first() if grupos.exists() else None
            
            # Set default to False
            atividade.pendente = False
            
            # Only check for pending evaluations if student is in a group for this activity
            if atividade.grupo:
                # Get all group members except the current student
                colegas = atividade.grupo.alunos.exclude(idAluno=aluno.idAluno)
                
                for colega in colegas:
                    try:
                        avaliacao = Avaliacao.objects.get(
                            avaliador_aluno=aluno,
                            avaliado_aluno=colega,
                            atividade=atividade
                        )
                        
                        # If evaluation is not completed, mark as pending
                        if not avaliacao.concluida:
                            atividade.pendente = True
                            pending_count += 1
                            break
                    except Avaliacao.DoesNotExist:
                        # If evaluation doesn't exist, it's considered pending
                        atividade.pendente = True
                        pending_count += 1
                        break
        
        # For debugging
        print(f"Total pending evaluations in atividades view: {pending_count}")
    
    elif user_type == 'professor':
        professor = Professor.objects.get(idProfessor=user_id)
        turmas = Turma.objects.filter(professor=professor)
        atividades = Atividade.objects.filter(
            turma__in=turmas
        ).order_by('-dataEntrega', 'titulo')  # Sort by date and then alphabetically by title
        
    elif user_type == 'coordenador':
        coordenador = Coordenador.objects.get(id=user_id)
        # Use the coordinator's course directly
        if coordenador.curso:
            disciplinas = Disciplina.objects.filter(curso=coordenador.curso)
            turmas = Turma.objects.filter(disciplina__in=disciplinas)
            atividades = Atividade.objects.filter(
                turma__in=turmas
            ).order_by('-dataEntrega', 'titulo')  # Sort by date and then alphabetically by title
        else:
            atividades = Atividade.objects.none()
    
    else:
        atividades = Atividade.objects.all().order_by('-dataEntrega', 'titulo')  # Sort by date and then alphabetically by title
    
    return render(request, 'atividades.html', {'atividades': atividades, 'user_type': user_type})

@login_required_custom
def atividade_detalhe(request, id_atividade):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    atividade = get_object_or_404(Atividade, id=id_atividade)
    
    if user_type == 'aluno':
        aluno = Aluno.objects.get(idAluno=user_id)
        grupos = Grupo.objects.filter(atividade=atividade, alunos=aluno)
        if not grupos.exists():
            messages.error(request, "Você não pertence a nenhum grupo nesta atividade.")
            return redirect('atividades')
        
        grupo = grupos.first()
        colegas = grupo.alunos.all().order_by('nomeAluno')  # Sort colleagues alphabetically
        
        # Check for pending evaluations
        avaliacoes = []
        for colega in colegas:
            avaliacao, created = Avaliacao.objects.get_or_create(
                avaliador_aluno=aluno,
                avaliado_aluno=colega,
                atividade=atividade,
                defaults={'concluida': False}
            )
            avaliacoes.append({
                'colega': colega,
                'avaliacao': avaliacao
            })
        
        return render(request, 'atividade_detalhe.html', {
            'atividade': atividade,
            'grupo': grupo,
            'avaliacoes': avaliacoes,
            'user_type': user_type
        })
    
    elif user_type in ['professor', 'coordenador', 'admin']:
        grupos = Grupo.objects.filter(atividade=atividade).order_by('nome')  # Sort groups alphabetically
        return render(request, 'atividade_detalhe.html', {
            'atividade': atividade,
            'grupos': grupos,
            'user_type': user_type
        })
    
    # Fallback for any unhandled user types
    messages.error(request, "Você não tem permissão para visualizar esta atividade.")
    return redirect('atividades')

@login_required_custom
def avaliar_colega(request, id_avaliacao):
    """View para avaliar um colega"""
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if user_type != 'aluno':
        messages.error(request, "Apenas alunos podem realizar avaliações.")
        return redirect('home')
    
    avaliacao = get_object_or_404(Avaliacao, id=id_avaliacao)
    aluno = Aluno.objects.get(idAluno=user_id)
    
    # Check if the logged user is the evaluator
    if avaliacao.avaliador_aluno != aluno:
        messages.error(request, "Você não tem permissão para realizar esta avaliação.")
        return redirect('atividades')
    
    # Get competências from the activity
    competencias = avaliacao.atividade.competencias.all()
    
    if request.method == 'POST':
        # Verify if the evaluation is already completed
        if avaliacao.concluida:
            messages.warning(request, "Esta avaliação já foi concluída.")
            return redirect('atividade_detalhe', id_atividade=avaliacao.atividade.id)
        
        for competencia in competencias:
            nota_valor = request.POST.get(f'competencia_{competencia.id}')
            if not nota_valor:
                messages.error(request, f"A nota para a competência {competencia.nome} é obrigatória.")
                return redirect('avaliar_colega', id_avaliacao=id_avaliacao)
            
            try:
                nota_valor = int(nota_valor)
                if nota_valor < 1 or nota_valor > 5:
                    messages.error(request, "As notas devem estar entre 1 e 5.")
                    return redirect('avaliar_colega', id_avaliacao=id_avaliacao)
                
                Nota.objects.create(
                    avaliacao=avaliacao,
                    competencia=competencia,
                    nota=nota_valor,
                    dataAvaliacao=timezone.now()
                )
            except ValueError:
                messages.error(request, "Valor de nota inválido.")
                return redirect('avaliar_colega', id_avaliacao=id_avaliacao)
        
        avaliacao.concluida = True
        avaliacao.save()
        
        # Notificar o aluno avaliado
        criar_notificacao(
            titulo="Nova avaliação recebida",
            mensagem=f"{aluno.nomeAluno} concluiu sua avaliação na atividade '{avaliacao.atividade.titulo}'.",
            destinatario=avaliacao.avaliado_aluno,
            tipo="info",
            link=f"/atividade/{avaliacao.atividade.id}/"
        )
        
        messages.success(request, "Avaliação realizada com sucesso!")
        return redirect('atividade_detalhe', id_atividade=avaliacao.atividade.id)
    
    return render(request, 'avaliar_colega.html', {
        'avaliacao': avaliacao,
        'competencias': competencias,
        'user_type': user_type
    })

@login_required_custom
def notas(request):
    user_type = request.session.get('user_type', '')
    user_id = request.session.get('user_id', '')
    
    if user_type == 'aluno':
        aluno = Aluno.objects.get(idAluno=user_id)
        
        # Get all evaluations received by the student
        avaliacoes = Avaliacao.objects.filter(
            avaliado_aluno=aluno,
            concluida=True
        )
        
        # Get notes from these evaluations
        notas = Nota.objects.filter(avaliacao__in=avaliacoes).select_related(
            'competencia', 'avaliacao', 'avaliacao__atividade'
        )
        
        # Prepare data for charts - evolution over time
        competencias = Competencia.objects.all()
        chart_data = {}
        for competencia in competencias:
            notas_competencia = notas.filter(competencia=competencia)
            if notas_competencia.exists():
                chart_data[competencia.nome] = {
                    'labels': [],
                    'data': []
                }
                
                # Group by semester
                semestres = Semestre.objects.all().order_by('ano', 'periodo')
                for semestre in semestres:
                    notas_semestre = notas_competencia.filter(
                        avaliacao__atividade__turma__semestre=semestre
                    )
                    if notas_semestre.exists():
                        media = notas_semestre.aggregate(Avg('nota'))['nota__avg']
                        chart_data[competencia.nome]['labels'].append(f"{semestre.ano}/{semestre.periodo}")
                        chart_data[competencia.nome]['data'].append(float(media))
        
        # Calculate average by competency for radar chart
        radar_data = {
            'labels': [c.nome for c in competencias],
            'data': []
        }
        
        for competencia in competencias:
            notas_comp = notas.filter(competencia=competencia)
            if notas_comp.exists():
                media = notas_comp.aggregate(Avg('nota'))['nota__avg']
                radar_data['data'].append(float(media))
            else:
                radar_data['data'].append(0)
        
        context = {
            'notas': notas,
            'chart_data': json.dumps(chart_data),
            'radar_data': json.dumps(radar_data),
            'user_type': user_type
        }
    
    elif user_type == 'professor':
        professor = Professor.objects.get(idProfessor=user_id)
        
        # Get notes from evaluations where this professor created the activity
        turmas = Turma.objects.filter(professor=professor)
        atividades = Atividade.objects.filter(turma__in=turmas)
        avaliacoes = Avaliacao.objects.filter(atividade__in=atividades, concluida=True)
        notas = Nota.objects.filter(avaliacao__in=avaliacoes)
        
        context = {
            'notas': notas,
            'turmas': turmas,
            'user_type': user_type
        }
        
    elif user_type == 'coordenador':
        coordenador = Coordenador.objects.get(id=user_id)
        cursos = Curso.objects.filter(coordenador=coordenador)
        
        context = {
            'cursos': cursos,
            'user_type': user_type
        }
    
    else:
        # Without proper authentication, just show sample data
        notas = Nota.objects.all()[:10]  # Limit to 10 for demo
        context = {'notas': notas}
        
    return render(request, 'notas.html', context)

@login_required_custom
def disciplinas(request):
    user_type = request.session.get('user_type', '')
    user_id = request.session.get('user_id', '')
    
    if user_type == 'aluno':
        aluno = Aluno.objects.get(idAluno=user_id)
        # Fixed: Get the turmas first, then get the disciplinas from those turmas
        turmas_aluno = TurmaAluno.objects.filter(aluno=aluno)
        turmas = [ta.turma for ta in turmas_aluno]
        disciplinas = Disciplina.objects.filter(
            turmas__in=turmas  # Use the correct reverse relation name
        ).distinct().order_by('nome')  # Sort disciplines alphabetically
    
    elif user_type == 'professor':
        professor = Professor.objects.get(idProfessor=user_id)
        # Fixed: Use the correct relation name
        disciplinas = Disciplina.objects.filter(
            turmas__professor=professor  # Use the correct reverse relation name
        ).distinct().order_by('nome')  # Sort disciplines alphabetically
    
    elif user_type == 'coordenador':
        coordenador = Coordenador.objects.get(id=user_id)
        # This is correct as we're filtering by the curso field
        disciplinas = Disciplina.objects.filter(
            curso=coordenador.curso
        ).distinct().order_by('nome') if coordenador.curso else Disciplina.objects.none()  # Sort disciplines alphabetically
    
    else:
        disciplinas = Disciplina.objects.all().order_by('nome')  # Sort disciplines alphabetically
    
    return render(request, 'disciplinas.html', {
        'disciplinas': disciplinas,
        'user_type': user_type
    })

@login_required_custom
def disciplina_detalhe(request, id_disciplina):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    disciplina = get_object_or_404(Disciplina, id=id_disciplina)
    
    if user_type == 'aluno':
        aluno = Aluno.objects.get(idAluno=user_id)
        # Get turmas for this student in this discipline
        turmas_aluno = TurmaAluno.objects.filter(aluno=aluno, turma__disciplina=disciplina)
        turmas = [ta.turma for ta in turmas_aluno]
        
    elif user_type == 'professor':
        professor = Professor.objects.get(idProfessor=user_id)
        turmas = Turma.objects.filter(professor=professor, disciplina=disciplina).order_by('codigo')  # Sort turmas alphabetically
        
    elif user_type in ['coordenador', 'admin']:
        turmas = Turma.objects.filter(disciplina=disciplina).order_by('codigo')  # Sort turmas alphabetically
        
    else:
        turmas = []
    
    atividades = Atividade.objects.filter(turma__in=turmas).order_by('-dataEntrega', 'titulo')  # Sort by date and then alphabetically by title
    
    return render(request, 'disciplina_detalhe.html', {
        'disciplina': disciplina,
        'turmas': turmas,
        'atividades': atividades,
        'user_type': user_type
    })

@login_required_custom
def perfil(request):
    # Get the user type and ID from session
    user_type = request.session.get('user_type', '')
    user_id = request.session.get('user_id', '')
    
    user_data = None
    if user_type == 'aluno':
        user_data = Aluno.objects.get(idAluno=user_id)
    elif user_type == 'professor':
        user_data = Professor.objects.get(idProfessor=user_id)
    elif user_type == 'coordenador':
        user_data = Coordenador.objects.get(id=user_id)
    
    # Handle form submission for password update
    if request.method == 'POST' and 'action' in request.POST and request.POST['action'] == 'change_password':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Verify current password
        if user_type == 'aluno' and not verify_password(current_password, user_data.senhaAluno):
            messages.error(request, "Senha atual incorreta.")
        elif user_type == 'professor' and not verify_password(current_password, user_data.senhaProf):
            messages.error(request, "Senha atual incorreta.")
        elif user_type == 'coordenador' and not verify_password(current_password, user_data.senhaCoord):
            messages.error(request, "Senha atual incorreta.")
        # Verify new passwords match
        elif new_password != confirm_password:
            messages.error(request, "As novas senhas não correspondem.")
        else:
            # Update password
            if user_type == 'aluno':
                user_data.senhaAluno = hash_password(new_password)
            elif user_type == 'professor':
                user_data.senhaProf = hash_password(new_password)
            elif user_type == 'coordenador':
                user_data.senhaCoord = hash_password(new_password)
            user_data.save()
            messages.success(request, "Senha atualizada com sucesso.")
        
    return render(request, 'perfil.html', {'user_data': user_data, 'user_type': user_type})

@login_required_custom
def competencias(request):
    """View para listar todas as competências"""
    if not tem_permissao_competencias(request):
        messages.error(request, "Você não tem permissão para acessar esta página.")
        return redirect('home')
    
    competencias = Competencia.objects.all().order_by('nome')
    
    return render(request, 'competencias.html', {
        'competencias': competencias,
        'user_type': request.session.get('user_type'),
        'username': request.session.get('username')
    })

@login_required_custom
def criar_competencia(request):
    """View para criar uma nova competência"""
    if not tem_permissao_competencias(request):
        messages.error(request, "Você não tem permissão para criar competências.")
        return redirect('competencias')
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        
        if not nome or not descricao:
            messages.error(request, "Todos os campos são obrigatórios.")
            return redirect('competencias')
        
        # Verificar se já existe uma competência com o mesmo nome
        if Competencia.objects.filter(nome=nome).exists():
            messages.error(request, f"Já existe uma competência com o nome '{nome}'.")
            return redirect('competencias')
        
        Competencia.objects.create(
            nome=nome,
            descricao=descricao
        )
        
        messages.success(request, f"Competência '{nome}' criada com sucesso!")
        return redirect('competencias')
    
    return redirect('competencias')

@login_required_custom
def editar_competencia(request, competencia_id):
    """View para editar uma competência existente"""
    if not tem_permissao_competencias(request):
        messages.error(request, "Você não tem permissão para editar competências.")
        return redirect('competencias')
    
    try:
        competencia = Competencia.objects.get(id=competencia_id)
    except Competencia.DoesNotExist:
        messages.error(request, "Competência não encontrada.")
        return redirect('competencias')
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        
        if not nome or not descricao:
            messages.error(request, "Todos os campos são obrigatórios.")
            return redirect('competencias')
        
        # Verificar se já existe outra competência com o mesmo nome
        if Competencia.objects.filter(nome=nome).exclude(id=competencia_id).exists():
            messages.error(request, f"Já existe outra competência com o nome '{nome}'.")
            return redirect('competencias')
        
        competencia.nome = nome
        competencia.descricao = descricao
        competencia.save()
        
        messages.success(request, f"Competência '{nome}' atualizada com sucesso!")
    
    return redirect('competencias')

@login_required_custom
def excluir_competencia(request, competencia_id):
    """View para excluir uma competência"""
    if not tem_permissao_competencias(request):
        messages.error(request, "Você não tem permissão para excluir competências.")
        return redirect('competencias')
    
    try:
        competencia = Competencia.objects.get(id=competencia_id)
    except Competencia.DoesNotExist:
        messages.error(request, "Competência não encontrada.")
        return redirect('competencias')
    
    # Verificar se a competência está sendo usada em alguma atividade
    if competencia.atividades.exists():
        messages.error(request, f"Não é possível excluir a competência '{competencia.nome}' pois está sendo utilizada em {competencia.atividades.count()} atividade(s).")
        return redirect('competencias')
    
    nome = competencia.nome
    competencia.delete()
    
    messages.success(request, f"Competência '{nome}' excluída com sucesso!")
    return redirect('competencias')

@login_required_custom
def criar_atividade(request):
    """View para criar uma nova atividade"""
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if user_type not in ['professor', 'coordenador', 'admin']:
        messages.error(request, "Você não tem permissão para criar atividades.")
        return redirect('atividades')
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        turma_id = request.POST.get('turma')
        data_entrega = request.POST.get('data_entrega')
        competencias_ids = request.POST.getlist('competencias')
        
        if not titulo or not descricao or not turma_id or not data_entrega or not competencias_ids:
            messages.error(request, "Todos os campos são obrigatórios.")
            return redirect('criar_atividade')
        
        try:
            turma = Turma.objects.get(id=turma_id)
            
            # Verificar permissão
            if user_type == 'professor' and turma.professor.idProfessor != user_id:
                messages.error(request, "Você não tem permissão para criar atividades para esta turma.")
                return redirect('atividades')
            
            atividade = Atividade.objects.create(
                titulo=titulo,
                descricao=descricao,
                turma=turma,
                dataEntrega=datetime.strptime(data_entrega, '%Y-%m-%d').date()
            )
            
            # Adicionar competências selecionadas
            competencias = Competencia.objects.filter(id__in=competencias_ids)
            atividade.competencias.set(competencias)
            
            messages.success(request, f"Atividade '{titulo}' criada com sucesso!")
            return redirect('atividade_detalhe', id_atividade=atividade.id)
        
        except (Turma.DoesNotExist, ValueError) as e:
            messages.error(request, f"Erro ao criar atividade: {str(e)}")
            return redirect('criar_atividade')
    
    # Obter turmas do professor
    if user_type == 'professor':
        professor = Professor.objects.get(idProfessor=user_id)
        turmas = Turma.objects.filter(professor=professor)
    elif user_type == 'coordenador':
        coordenador = Coordenador.objects.get(id=user_id)
        if coordenador.curso:
            disciplinas = Disciplina.objects.filter(curso=coordenador.curso)
            turmas = Turma.objects.filter(disciplina__in=disciplinas)
        else:
            turmas = []
    else:  # admin
        turmas = Turma.objects.all()
    
    # Obter todas as competências
    competencias = Competencia.objects.all().order_by('nome')
    
    return render(request, 'criar_atividade.html', {
        'turmas': turmas,
        'competencias': competencias,
        'user_type': user_type,
        'username': request.session.get('username')
    })

@login_required_custom
def criar_grupo(request, id_atividade):
    """View para criar um novo grupo para uma atividade"""
    user_type = request.session.get('user_type')
    
    if user_type not in ['professor', 'admin']:
        messages.error(request, "Apenas professores podem criar grupos.")
        return redirect('home')
    
    atividade = get_object_or_404(Atividade, id=id_atividade)
    turma = atividade.turma
    
    # Improved query to get students enrolled in this class
    alunos_turma = TurmaAluno.objects.filter(turma=turma).select_related('aluno')
    
    if not alunos_turma.exists():
        messages.warning(request, "Não há alunos matriculados nesta turma.")
    
    # Get IDs of students already in groups for this activity
    alunos_em_grupos = Grupo.objects.filter(atividade=atividade).values_list('alunos', flat=True)
    
    # Filter available students (those not already in groups)
    alunos_disponiveis = [ta for ta in alunos_turma if ta.aluno.idAluno not in alunos_em_grupos]
    
    # Check if we have any available students
    if not alunos_disponiveis:
        if alunos_turma.exists():
            messages.warning(request, "Todos os alunos desta turma já estão em grupos.")
        
    # Get existing groups for this activity to display
    grupos_existentes = Grupo.objects.filter(atividade=atividade).prefetch_related('alunos')
    
    if request.method == 'POST':
        nome_grupo = request.POST.get('nome_grupo')
        alunos_ids = request.POST.getlist('alunos')
        
        if not nome_grupo or not alunos_ids:
            messages.error(request, "O nome do grupo e pelo menos um aluno são obrigatórios.")
            return redirect('criar_grupo', id_atividade=id_atividade)
        
        grupo = Grupo.objects.create(
            nome=nome_grupo,
            atividade=atividade
        )
        
        for aluno_id in alunos_ids:
            aluno = Aluno.objects.get(idAluno=aluno_id)
            grupo.alunos.add(aluno)
        
        # Create evaluation entries for each group member to evaluate others
        alunos_grupo = grupo.alunos.all()
        for avaliador in alunos_grupo:
            for avaliado in alunos_grupo:
                if avaliador != avaliado:  # Skip self-evaluation
                    Avaliacao.objects.create(
                        avaliador_aluno=avaliador,
                        avaliado_aluno=avaliado,
                        atividade=atividade,
                        concluida=False
                    )
        
        messages.success(request, f"Grupo '{nome_grupo}' criado com sucesso!")
        return redirect('atividade_detalhe', id_atividade=id_atividade)
    
    return render(request, 'criar_grupo.html', {
        'atividade': atividade,
        'alunos_disponiveis': alunos_disponiveis,
        'grupos_existentes': grupos_existentes,
        'user_type': user_type
    })

# Admin redirection view
@login_required_custom
def admin_redirect(request):
    """
    Redirects users to the appropriate admin page based on their role
    """
    user_type = request.session.get('user_type')
    
    if is_admin(user_type):
        return render(request, 'admin_redirect.html')
    else:
        messages.error(request, "Você não tem permissão para acessar o painel administrativo.")
        return redirect('home')

# Admin only views
@login_required_custom
def admin_dashboard(request):
    """View for the admin dashboard"""
    # Ensure user is admin
    if request.session.get('user_type') != 'admin':
        messages.error(request, 'Acesso negado. Você não é um administrador.')
        return redirect('home')
    
    # Get counts for the dashboard
    cursos_count = Curso.objects.count()
    disciplinas_count = Disciplina.objects.count()
    alunos_count = Aluno.objects.count()
    professores_count = Professor.objects.count()
    coordenadores_count = Coordenador.objects.count()
    
    # Get all courses and coordinators
    cursos = Curso.objects.all().prefetch_related('disciplinas', 'alunos')
    coordenadores = Coordenador.objects.all().select_related('curso')
    
    # Get recent activities
    atividades_recentes = Atividade.objects.all().order_by('-id')[:10]
    
    context = {
        'cursos_count': cursos_count,
        'disciplinas_count': disciplinas_count,
        'alunos_count': alunos_count,
        'professores_count': professores_count,
        'coordenadores_count': coordenadores_count,
        'cursos': cursos,
        'coordenadores': coordenadores,
        'atividades_recentes': atividades_recentes,
        'user_type': 'admin',
        'username': request.session.get('username')
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required_custom
def admin_import_users(request):
    """View for importing users from CSV or Excel files"""
    # Ensure user is admin
    if request.session.get('user_type') != 'admin':
        messages.error(request, 'Acesso negado. Você não é um administrador.')
        return redirect('home')
    
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        import_type = request.POST.get('import_type')
        
        try:
            # Read CSV or Excel file
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
            else:
                messages.error(request, "Formato de arquivo não suportado. Use CSV ou Excel.")
                return redirect('admin_import_users')
            
            # Process based on import type
            if import_type == 'alunos':
                # Expected columns: nome, email, matricula, curso_id
                success_count = 0
                for _, row in df.iterrows():
                    try:
                        # Validate required fields
                        if not all(field in row and pd.notna(row[field]) for field in ['nome', 'email', 'matricula', 'curso_id']):
                            continue
                            
                        # Check if curso_id exists
                        curso = Curso.objects.filter(id=row['curso_id']).first()
                        if not curso:
                            continue
                            
                        # Check if email or matricula already exists
                        if Aluno.objects.filter(emailAluno=row['email']).exists() or Aluno.objects.filter(matricula=row['matricula']).exists():
                            continue
                            
                        # Create student
                        Aluno.objects.create(
                            nomeAluno=row['nome'],
                            emailAluno=row['email'],
                            matricula=str(row['matricula']),  # Convert to string in case it's a number
                            senhaAluno=hash_password('123456'),  # Default password
                            curso=curso
                        )
                        success_count += 1
                    except Exception as e:
                        # Skip problematic rows
                        print(f"Error importing student: {str(e)}")
                        continue
                        
                messages.success(request, f"{success_count} alunos importados com sucesso.")
                
            elif import_type == 'professores':
                # Expected columns: nome, email
                success_count = 0
                for _, row in df.iterrows():
                    try:
                        # Validate required fields
                        if not all(field in row and pd.notna(row[field]) for field in ['nome', 'email']):
                            continue
                            
                        # Check if email already exists
                        if Professor.objects.filter(emailProf=row['email']).exists():
                            continue
                            
                        # Create professor
                        Professor.objects.create(
                            nomeProf=row['nome'],
                            emailProf=row['email'],
                            senhaProf=hash_password('123456')  # Default password
                        )
                        success_count += 1
                    except Exception as e:
                        # Skip problematic rows
                        print(f"Error importing professor: {str(e)}")
                        continue
                        
                messages.success(request, f"{success_count} professores importados com sucesso.")
                
            elif import_type == 'coordenadores':
                # Expected columns: nome, email, curso_id
                success_count = 0
                for _, row in df.iterrows():
                    try:
                        # Validate required fields
                        if not all(field in row and pd.notna(row[field]) for field in ['nome', 'email', 'curso_id']):
                            continue
                            
                        # Check if curso_id exists
                        curso = Curso.objects.filter(id=row['curso_id']).first()
                        if not curso:
                            continue
                            
                        # Check if email already exists
                        if Coordenador.objects.filter(emailCoord=row['email']).exists():
                            continue
                            
                        # Create coordinator
                        Coordenador.objects.create(
                            nomeCoord=row['nome'],
                            emailCoord=row['email'],
                            senhaCoord=hash_password('123456'),  # Default password
                            curso=curso
                        )
                        success_count += 1
                    except Exception as e:
                        # Skip problematic rows
                        print(f"Error importing coordinator: {str(e)}")
                        continue
                        
                messages.success(request, f"{success_count} coordenadores importados com sucesso.")
                
            else:
                messages.error(request, "Tipo de importação inválido.")
                
        except Exception as e:
            messages.error(request, f"Erro ao processar arquivo: {str(e)}")
    
    # Get all courses for the form
    cursos = Curso.objects.all().order_by('nome')
    
    context = {
        'cursos': cursos,
        'user_type': 'admin',
        'username': request.session.get('username')
    }
    
    return render(request, 'admin/import_users.html', context)

@login_required_custom
def admin_users(request):
    """View for managing users in the admin dashboard"""
    # Ensure user is admin
    if request.session.get('user_type') != 'admin':
        messages.error(request, 'Acesso negado. Você não é um administrador.')
        return redirect('home')
    
    # Get all users of each type
    from .models import Admin
    alunos = Aluno.objects.all().select_related('curso').order_by('nomeAluno')
    professores = Professor.objects.all().order_by('nomeProf')
    coordenadores = Coordenador.objects.all().select_related('curso').order_by('nomeCoord')
    admins = Admin.objects.all().order_by('nomeAdmin')
    
    context = {
        'alunos': alunos,
        'professores': professores,
        'coordenadores': coordenadores,
        'admins': admins,
        'user_type': 'admin',
        'username': request.session.get('username')
    }
    
    return render(request, 'admin/users.html', context)

@login_required_custom
def admin_create_user(request):
    """View for creating new users in the admin dashboard"""
    # Ensure user is admin
    if request.session.get('user_type') != 'admin':
        messages.error(request, 'Acesso negado. Você não é um administrador.')
        return redirect('home')
    
    from .models import Admin
    
    # Handle form submission
    if request.method == 'POST':
        user_role = request.POST.get('user_role')
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        
        # Use default password if none provided
        if not senha:
            senha = '123456'
        
        # Hash the password
        senha_hash = hash_password(senha)
        
        try:
            # Create user based on role
            if user_role == 'aluno':
                matricula = request.POST.get('matricula')
                curso_id = request.POST.get('curso')
                
                # Validate required fields
                if not matricula or not curso_id:
                    messages.error(request, "Matrícula e curso são obrigatórios para alunos.")
                    return redirect('admin_create_user')
                
                # Check if curso exists
                curso = get_object_or_404(Curso, id=curso_id)
                
                # Check if email or matricula already exists
                if Aluno.objects.filter(emailAluno=email).exists():
                    messages.error(request, f"Já existe um aluno com o email '{email}'.")
                    return redirect('admin_create_user')
                
                if Aluno.objects.filter(matricula=matricula).exists():
                    messages.error(request, f"Já existe um aluno com a matrícula '{matricula}'.")
                    return redirect('admin_create_user')
                
                # Create aluno
                aluno = Aluno.objects.create(
                    nomeAluno=nome,
                    emailAluno=email,
                    senhaAluno=senha_hash,
                    matricula=matricula,
                    curso=curso
                )
                messages.success(request, f"Aluno '{nome}' criado com sucesso!")
                
            elif user_role == 'professor':
                # Check if email already exists
                if Professor.objects.filter(emailProf=email).exists():
                    messages.error(request, f"Já existe um professor com o email '{email}'.")
                    return redirect('admin_create_user')
                
                # Create professor
                professor = Professor.objects.create(
                    nomeProf=nome,
                    emailProf=email,
                    senhaProf=senha_hash
                )
                messages.success(request, f"Professor '{nome}' criado com sucesso!")
                
            elif user_role == 'coordenador':
                curso_id = request.POST.get('curso')
                
                # Validate required fields
                if not curso_id:
                    messages.error(request, "Curso é obrigatório para coordenadores.")
                    return redirect('admin_create_user')
                
                # Check if curso exists
                curso = get_object_or_404(Curso, id=curso_id)
                
                # Check if email already exists
                if Coordenador.objects.filter(emailCoord=email).exists():
                    messages.error(request, f"Já existe um coordenador com o email '{email}'.")
                    return redirect('admin_create_user')
                
                # Create coordenador
                coordenador = Coordenador.objects.create(
                    nomeCoord=nome,
                    emailCoord=email,
                    senhaCoord=senha_hash,
                    curso=curso
                )
                messages.success(request, f"Coordenador '{nome}' criado com sucesso!")
                
            elif user_role == 'admin':
                # Check if email already exists
                if Admin.objects.filter(emailAdmin=email).exists():
                    messages.error(request, f"Já existe um administrador com o email '{email}'.")
                    return redirect('admin_create_user')
                
                # Create admin
                admin = Admin.objects.create(
                    nomeAdmin=nome,
                    emailAdmin=email,
                    senhaAdmin=senha_hash
                )
                messages.success(request, f"Administrador '{nome}' criado com sucesso!")
                
            else:
                messages.error(request, "Tipo de usuário inválido.")
                return redirect('admin_create_user')
                
            # Redirect to users list
            return redirect('admin_users')
            
        except Exception as e:
            messages.error(request, f"Erro ao criar usuário: {str(e)}")
    
    # GET request - render form
    cursos = Curso.objects.all().order_by('nome')
    
    return render(request, 'admin/create_user.html', {
        'cursos': cursos,
        'user_type': 'admin',
        'username': request.session.get('username')
    })

@login_required_custom
def admin_edit_user(request, role, user_id):
    """View for editing users in the admin dashboard"""
    # Ensure user is admin
    if request.session.get('user_type') != 'admin':
        messages.error(request, 'Acesso negado. Você não é um administrador.')
        return redirect('home')
    
    from .models import Admin
    user = None
    
    # Get the user object based on role and ID
    try:
        if role == 'aluno':
            user = Aluno.objects.get(idAluno=user_id)
        elif role == 'professor':
            user = Professor.objects.get(idProfessor=user_id)
        elif role == 'coordenador':
            user = Coordenador.objects.get(id=user_id)
        elif role == 'admin':
            user = Admin.objects.get(id=user_id)
        else:
            messages.error(request, f"Tipo de usuário inválido: {role}")
            return redirect('admin_users')
    except Exception as e:
        messages.error(request, f"Usuário não encontrado: {str(e)}")
        return redirect('admin_users')
    
    # Handle form submission
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        
        try:
            # Update user based on role
            if role == 'aluno':
                matricula = request.POST.get('matricula')
                curso_id = request.POST.get('curso')
                
                # Validate required fields
                if not nome or not email or not matricula or not curso_id:
                    messages.error(request, "Todos os campos são obrigatórios.")
                    return redirect('admin_edit_user', role=role, user_id=user_id)
                
                # Check if curso exists
                curso = get_object_or_404(Curso, id=curso_id)
                
                # Check if email already exists with another user
                if Aluno.objects.filter(emailAluno=email).exclude(idAluno=user_id).exists():
                    messages.error(request, f"Já existe outro aluno com o email '{email}'.")
                    return redirect('admin_edit_user', role=role, user_id=user_id)
                
                # Check if matricula already exists with another user
                if Aluno.objects.filter(matricula=matricula).exclude(idAluno=user_id).exists():
                    messages.error(request, f"Já existe outro aluno com a matrícula '{matricula}'.")
                    return redirect('admin_edit_user', role=role, user_id=user_id)
                
                # Update user data
                user.nomeAluno = nome
                user.emailAluno = email
                user.matricula = matricula
                user.curso = curso
                
                # Update password if provided
                if senha:
                    user.senhaAluno = hash_password(senha)
                
                user.save()
                
            elif role == 'professor':
                # Validate required fields
                if not nome or not email:
                    messages.error(request, "Nome e email são obrigatórios.")
                    return redirect('admin_edit_user', role=role, user_id=user_id)
                
                # Check if email already exists with another user
                if Professor.objects.filter(emailProf=email).exclude(idProfessor=user_id).exists():
                    messages.error(request, f"Já existe outro professor com o email '{email}'.")
                    return redirect('admin_edit_user', role=role, user_id=user_id)
                
                # Update user data
                user.nomeProf = nome
                user.emailProf = email
                
                # Update password if provided
                if senha:
                    user.senhaProf = hash_password(senha)
                
                user.save()
                
            elif role == 'coordenador':
                curso_id = request.POST.get('curso')
                
                # Validate required fields
                if not nome or not email or not curso_id:
                    messages.error(request, "Nome, email e curso são obrigatórios.")
                    return redirect('admin_edit_user', role=role, user_id=user_id)
                
                # Check if curso exists
                curso = get_object_or_404(Curso, id=curso_id)
                
                # Check if email already exists with another user
                if Coordenador.objects.filter(emailCoord=email).exclude(id=user_id).exists():
                    messages.error(request, f"Já existe outro coordenador com o email '{email}'.")
                    return redirect('admin_edit_user', role=role, user_id=user_id)
                
                # Update user data
                user.nomeCoord = nome
                user.emailCoord = email
                user.curso = curso
                
                # Update password if provided
                if senha:
                    user.senhaCoord = hash_password(senha)
                
                user.save()
                
            elif role == 'admin':
                # Validate required fields
                if not nome or not email:
                    messages.error(request, "Nome e email são obrigatórios.")
                    return redirect('admin_edit_user', role=role, user_id=user_id)
                
                # Check if email already exists with another user
                if Admin.objects.filter(emailAdmin=email).exclude(id=user_id).exists():
                    messages.error(request, f"Já existe outro administrador com o email '{email}'.")
                    return redirect('admin_edit_user', role=role, user_id=user_id)
                
                # Update user data
                user.nomeAdmin = nome
                user.emailAdmin = email
                
                # Update password if provided
                if senha:
                    user.senhaAdmin = hash_password(senha)
                
                user.save()
            
            messages.success(request, "Usuário atualizado com sucesso!")
            return redirect('admin_users')
            
        except Exception as e:
            messages.error(request, f"Erro ao atualizar usuário: {str(e)}")
    
    # Prepare context for template rendering
    context = {
        'user': user,
        'role': role,
        'user_type': 'admin',
        'username': request.session.get('username')
    }
    
    # Add courses for alunos and coordenadores
    if role in ['aluno', 'coordenador']:
        context['cursos'] = Curso.objects.all().order_by('nome')
    
    return render(request, 'admin/edit_user.html', context)

@login_required_custom
def admin_delete_user(request, role, user_id):
    """View for deleting users in the admin dashboard"""
    # Ensure user is admin
    if request.session.get('user_type') != 'admin':
        messages.error(request, 'Acesso negado. Você não é um administrador.')
        return redirect('home')
    
    from .models import Admin
    
    try:
        # Get user based on role
        if role == 'aluno':
            user = get_object_or_404(Aluno, idAluno=user_id)
            # Check if user can be deleted (check dependencies)
            if Avaliacao.objects.filter(avaliador_aluno=user).exists() or Avaliacao.objects.filter(avaliado_aluno=user).exists():
                messages.error(request, f"Não é possível excluir o aluno '{user.nomeAluno}' pois existem avaliações associadas a ele.")
                return redirect('admin_users')
            
            nome = user.nomeAluno
            user.delete()
            messages.success(request, f"Aluno '{nome}' excluído com sucesso!")
            
        elif role == 'professor':
            user = get_object_or_404(Professor, idProfessor=user_id)
            # Check if professor has turmas
            if Turma.objects.filter(professor=user).exists():
                messages.error(request, f"Não é possível excluir o professor '{user.nomeProf}' pois existem turmas associadas a ele.")
                return redirect('admin_users')
            
            nome = user.nomeProf
            user.delete()
            messages.success(request, f"Professor '{nome}' excluído com sucesso!")
            
        elif role == 'coordenador':
            user = get_object_or_404(Coordenador, id=user_id)
            nome = user.nomeCoord
            user.delete()
            messages.success(request, f"Coordenador '{nome}' excluído com sucesso!")
            
        elif role == 'admin':
            # Prevent deleting the last admin
            if Admin.objects.count() <= 1:
                messages.error(request, "Não é possível excluir o último administrador do sistema.")
                return redirect('admin_users')
            
            user = get_object_or_404(Admin, id=user_id)
            nome = user.nomeAdmin
            user.delete()
            messages.success(request, f"Administrador '{nome}' excluído com sucesso!")
            
        else:
            messages.error(request, f"Tipo de usuário inválido: {role}")
            
    except Exception as e:
        messages.error(request, f"Erro ao excluir usuário: {str(e)}")
    
    return redirect('admin_users')

@login_required_custom
def admin_courses(request):
    """View for managing courses in the admin dashboard"""
    # Ensure user is admin
    if request.session.get('user_type') != 'admin':
        messages.error(request, 'Acesso negado. Você não é um administrador.')
        return redirect('home')
    
    # Handle form actions
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Create new course
        if action == 'create':
            nome_curso = request.POST.get('nome_curso')
            if nome_curso:
                if Curso.objects.filter(nome=nome_curso).exists():
                    messages.error(request, f"Já existe um curso com o nome '{nome_curso}'.")
                else:
                    Curso.objects.create(nome=nome_curso)
                    messages.success(request, f"Curso '{nome_curso}' criado com sucesso!")
            else:
                messages.error(request, "O nome do curso é obrigatório.")
        
        # Update existing course
        elif action == 'update':
            curso_id = request.POST.get('curso_id')
            nome_curso = request.POST.get('nome_curso')
            
            if curso_id and nome_curso:
                curso = get_object_or_404(Curso, id=curso_id)
                if Curso.objects.filter(nome=nome_curso).exclude(id=curso_id).exists():
                    messages.error(request, f"Já existe outro curso com o nome '{nome_curso}'.")
                else:
                    curso.nome = nome_curso
                    curso.save()
                    messages.success(request, f"Curso atualizado para '{nome_curso}'.")
            else:
                messages.error(request, "ID e nome do curso são obrigatórios.")
        
        # Delete course
        elif action == 'delete':
            curso_id = request.POST.get('curso_id')
            if curso_id:
                curso = get_object_or_404(Curso, id=curso_id)
                
                # Check if course can be deleted (no associated students or disciplines)
                if curso.alunos.exists():
                    messages.error(request, f"Não é possível excluir o curso '{curso.nome}' pois existem alunos matriculados.")
                elif curso.disciplinas.exists():
                    messages.error(request, f"Não é possível excluir o curso '{curso.nome}' pois existem disciplinas associadas.")
                elif Coordenador.objects.filter(curso=curso).exists():
                    messages.error(request, f"Não é possível excluir o curso '{curso.nome}' pois existem coordenadores associados.")
                else:
                    nome = curso.nome
                    curso.delete()
                    messages.success(request, f"Curso '{nome}' excluído com sucesso!")
            else:
                messages.error(request, "ID do curso é obrigatório.")
    
    # Get all courses
    cursos = Curso.objects.all().prefetch_related('alunos', 'disciplinas', 'coordenadores').order_by('nome')
    
    context = {
        'cursos': cursos,
        'user_type': 'admin',
        'username': request.session.get('username')
    }
    
    return render(request, 'admin/courses.html', context)

@login_required_custom
def admin_disciplines(request):
    """View for managing disciplines in the admin dashboard"""
    # Ensure user is admin
    if request.session.get('user_type') != 'admin':
        messages.error(request, 'Acesso negado. Você não é um administrador.')
        return redirect('home')
    
    # Handle form actions
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Create new discipline
        if action == 'create':
            nome = request.POST.get('nome')
            codigo = request.POST.get('codigo')
            curso_id = request.POST.get('curso')
            
            if nome and codigo and curso_id:
                # Check if code already exists
                if Disciplina.objects.filter(codigo=codigo).exists():
                    messages.error(request, f"Já existe uma disciplina com o código '{codigo}'.")
                    return redirect('admin_disciplines')
                
                # Check if curso exists
                curso = get_object_or_404(Curso, id=curso_id)
                
                # Create the discipline
                Disciplina.objects.create(
                    nome=nome,
                    codigo=codigo,
                    curso=curso
                )
                messages.success(request, f"Disciplina '{nome}' criada com sucesso!")
            else:
                messages.error(request, "Todos os campos são obrigatórios.")
        
        # Update existing discipline
        elif action == 'update':
            disciplina_id = request.POST.get('disciplina_id')
            nome = request.POST.get('nome')
            codigo = request.POST.get('codigo')
            curso_id = request.POST.get('curso')
            
            if disciplina_id and nome and codigo and curso_id:
                disciplina = get_object_or_404(Disciplina, id=disciplina_id)
                
                # Check if code already exists with another discipline
                if Disciplina.objects.filter(codigo=codigo).exclude(id=disciplina_id).exists():
                    messages.error(request, f"Já existe outra disciplina com o código '{codigo}'.")
                    return redirect('admin_disciplines')
                
                # Check if curso exists
                curso = get_object_or_404(Curso, id=curso_id)
                
                # Update the discipline
                disciplina.nome = nome
                disciplina.codigo = codigo
                disciplina.curso = curso
                disciplina.save()
                
                messages.success(request, f"Disciplina '{nome}' atualizada com sucesso!")
            else:
                messages.error(request, "Todos os campos são obrigatórios.")
        
        # Delete discipline
        elif action == 'delete':
            disciplina_id = request.POST.get('disciplina_id')
            
            if disciplina_id:
                disciplina = get_object_or_404(Disciplina, id=disciplina_id)
                
                # Check if discipline has turmas
                if disciplina.turmas.exists():
                    messages.error(request, f"Não é possível excluir a disciplina '{disciplina.nome}' pois existem turmas associadas.")
                    return redirect('admin_disciplines')
                
                nome = disciplina.nome
                disciplina.delete()
                messages.success(request, f"Disciplina '{nome}' excluída com sucesso!")
            else:
                messages.error(request, "ID da disciplina é obrigatório.")
    
    # Get all disciplines and courses
    disciplinas = Disciplina.objects.all().select_related('curso').order_by('curso__nome', 'nome')
    cursos = Curso.objects.all().order_by('nome')
    
    context = {
        'disciplinas': disciplinas,
        'cursos': cursos,
        'user_type': 'admin',
        'username': request.session.get('username')
    }
    
    return render(request, 'admin/disciplines.html', context)

@login_required_custom
def admin_classes(request):
    """View for managing classes (turmas) in the admin dashboard"""
    # Ensure user is admin
    if request.session.get('user_type') != 'admin':
        messages.error(request, 'Acesso negado. Você não é um administrador.')
        return redirect('home')
    
    # Handle form actions
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Create new class
        if action == 'create':
            codigo = request.POST.get('codigo')
            disciplina_id = request.POST.get('disciplina')
            professor_id = request.POST.get('professor')
            semestre_id = request.POST.get('semestre')
            
            if not all([codigo, disciplina_id, professor_id, semestre_id]):
                messages.error(request, "Todos os campos são obrigatórios.")
                return redirect('admin_classes')
            
            try:
                # Get related objects
                disciplina = get_object_or_404(Disciplina, id=disciplina_id)
                professor = get_object_or_404(Professor, idProfessor=professor_id)
                semestre = get_object_or_404(Semestre, id=semestre_id)
                
                # Check if a class with the same code, discipline and semester already exists
                if Turma.objects.filter(codigo=codigo, disciplina=disciplina, semestre=semestre).exists():
                    messages.error(request, f"Já existe uma turma com código '{codigo}' para esta disciplina neste semestre.")
                    return redirect('admin_classes')
                
                # Create the class
                Turma.objects.create(
                    codigo=codigo,
                    disciplina=disciplina,
                    professor=professor,
                    semestre=semestre
                )
                
                messages.success(request, f"Turma '{codigo}' da disciplina '{disciplina.nome}' criada com sucesso!")
            except Exception as e:
                messages.error(request, f"Erro ao criar turma: {str(e)}")
                
        # Update existing class
        elif action == 'update':
            turma_id = request.POST.get('turma_id')
            codigo = request.POST.get('codigo')
            disciplina_id = request.POST.get('disciplina')
            professor_id = request.POST.get('professor')
            semestre_id = request.POST.get('semestre')
            
            if not all([turma_id, codigo, disciplina_id, professor_id, semestre_id]):
                messages.error(request, "Todos os campos são obrigatórios.")
                return redirect('admin_classes')
            
            try:
                # Get the class and related objects
                turma = get_object_or_404(Turma, id=turma_id)
                disciplina = get_object_or_404(Disciplina, id=disciplina_id)
                professor = get_object_or_404(Professor, idProfessor=professor_id)
                semestre = get_object_or_404(Semestre, id=semestre_id)
                
                # Check if another class with the same code, discipline and semester already exists
                if Turma.objects.filter(codigo=codigo, disciplina=disciplina, semestre=semestre).exclude(id=turma_id).exists():
                    messages.error(request, f"Já existe outra turma com código '{codigo}' para esta disciplina neste semestre.")
                    return redirect('admin_classes')
                
                # Update the class
                turma.codigo = codigo
                turma.disciplina = disciplina
                turma.professor = professor
                turma.semestre = semestre
                turma.save()
                
                messages.success(request, f"Turma atualizada com sucesso!")
            except Exception as e:
                messages.error(request, f"Erro ao atualizar turma: {str(e)}")
                
        # Delete class
        elif action == 'delete':
            turma_id = request.POST.get('turma_id')
            
            if not turma_id:
                messages.error(request, "ID da turma é obrigatório.")
                return redirect('admin_classes')
            
            try:
                turma = get_object_or_404(Turma, id=turma_id)
                
                # Check if class has activities
                if Atividade.objects.filter(turma=turma).exists():
                    messages.error(request, f"Não é possível excluir a turma pois existem atividades associadas a ela.")
                    return redirect('admin_classes')
                
                # Check if class has students
                if TurmaAluno.objects.filter(turma=turma).exists():
                    messages.error(request, f"Não é possível excluir a turma pois existem alunos matriculados.")
                    return redirect('admin_classes')
                
                disciplina_nome = turma.disciplina.nome
                codigo = turma.codigo
                turma.delete()
                
                messages.success(request, f"Turma '{codigo}' da disciplina '{disciplina_nome}' excluída com sucesso!")
            except Exception as e:
                messages.error(request, f"Erro ao excluir turma: {str(e)}")
    
    # Get all classes, disciplines, professors and semesters
    turmas = Turma.objects.all().select_related('disciplina', 'professor', 'semestre')
    disciplinas = Disciplina.objects.all().order_by('nome')
    professores = Professor.objects.all().order_by('nomeProf')
    semestres = Semestre.objects.all().order_by('-ano', '-periodo')
    
    context = {
        'turmas': turmas,
        'disciplinas': disciplinas,
        'professores': professores,
        'semestres': semestres,
        'user_type': 'admin',
        'username': request.session.get('username')
    }
    
    return render(request, 'admin/classes.html', context)

@login_required_custom
def admin_class_students(request, turma_id):
    """View for managing students in a class"""
    # Ensure user has permission (admin or professor)
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if user_type not in ['admin', 'professor']:
        messages.error(request, 'Acesso negado. Você não tem permissão para gerenciar alunos de turmas.')
        return redirect('home')
    
    turma = get_object_or_404(Turma, id=turma_id)
    
    # If professor, check if they're teaching this class
    if user_type == 'professor' and turma.professor.idProfessor != user_id:
        messages.error(request, 'Você não tem permissão para gerenciar alunos desta turma.')
        return redirect('home')
    
    # Handle form actions
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Add single student
        if action == 'add_student':
            aluno_id = request.POST.get('aluno_id')
            
            if not aluno_id:
                messages.error(request, "ID do aluno é obrigatório.")
                return redirect('admin_class_students', turma_id=turma_id)
            
            try:
                aluno = get_object_or_404(Aluno, idAluno=aluno_id)
                
                # Check if student is already enrolled
                if TurmaAluno.objects.filter(turma=turma, aluno=aluno).exists():
                    messages.warning(request, f"O aluno {aluno.nomeAluno} já está matriculado nesta turma.")
                else:
                    TurmaAluno.objects.create(turma=turma, aluno=aluno)
                    messages.success(request, f"Aluno {aluno.nomeAluno} adicionado à turma com sucesso.")
            except Aluno.DoesNotExist:
                messages.error(request, f"Aluno com ID {aluno_id} não encontrado.")
                
        # Add multiple students
        elif action == 'add_multiple':
            alunos_ids = request.POST.getlist('alunos')
            
            if not alunos_ids:
                messages.error(request, "Selecione pelo menos um aluno.")
                return redirect('admin_class_students', turma_id=turma_id)
            
            count = 0
            for aluno_id in alunos_ids:
                try:
                    aluno = Aluno.objects.get(idAluno=aluno_id)
                    if not TurmaAluno.objects.filter(turma=turma, aluno=aluno).exists():
                        TurmaAluno.objects.create(turma=turma, aluno=aluno)
                        count += 1
                except:
                    pass
            
            if count > 0:
                messages.success(request, f"{count} alunos adicionados à turma com sucesso.")
            else:
                messages.warning(request, "Nenhum aluno novo foi adicionado à turma.")
                
        # Remove student
        elif action == 'remove_student':
            matricula_id = request.POST.get('matricula_id')
            
            if not matricula_id:
                messages.error(request, "ID da matrícula é obrigatório.")
                return redirect('admin_class_students', turma_id=turma_id)
            
            try:
                matricula = get_object_or_404(TurmaAluno, id=matricula_id)
                nome_aluno = matricula.aluno.nomeAluno
                
                # Check if student is in groups for this class
                atividades = Atividade.objects.filter(turma=turma)
                grupos = Grupo.objects.filter(atividade__in=atividades, alunos=matricula.aluno)
                
                if grupos.exists():
                    messages.error(request, f"Não é possível remover o aluno {nome_aluno} pois ele está em grupos nesta turma.")
                    return redirect('admin_class_students', turma_id=turma_id)
                
                matricula.delete()
                messages.success(request, f"Aluno {nome_aluno} removido da turma com sucesso.")
            except Exception as e:
                messages.error(request, f"Erro ao remover aluno: {str(e)}")
    
    # Get enrolled students and available students
    matriculas = TurmaAluno.objects.filter(turma=turma).select_related('aluno', 'aluno__curso')
    
    # Get list of student IDs already enrolled
    alunos_matriculados_ids = matriculas.values_list('aluno__idAluno', flat=True)
    
    # Get available students (not enrolled in this class)
    alunos_disponiveis = Aluno.objects.exclude(idAluno__in=alunos_matriculados_ids).select_related('curso')
    
    context = {
        'turma': turma,
        'matriculas': matriculas,
        'alunos_disponiveis': alunos_disponiveis,
        'user_type': user_type,
        'username': request.session.get('username')
    }
    
    return render(request, 'admin/class_students.html', context)

@login_required_custom
def admin_semesters(request):
    """View for managing semesters in the admin dashboard"""
    # Ensure user is admin
    if request.session.get('user_type') != 'admin':
        messages.error(request, 'Acesso negado. Você não é um administrador.')
        return redirect('home')
    
    # Get current year for the default value in the create form
    current_year = timezone.now().year
    
    # Handle form actions
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Create new semester
        if action == 'create':
            ano = request.POST.get('ano')
            periodo = request.POST.get('periodo')
            
            if ano and periodo:
                try:
                    ano = int(ano)
                    periodo = int(periodo)
                    
                    # Validate period value (1 or 2)
                    if periodo not in [1, 2]:
                        messages.error(request, "O período deve ser 1 (primeiro semestre) ou 2 (segundo semestre).")
                        return redirect('admin_semesters')
                    
                    # Check if semester already exists
                    if Semestre.objects.filter(ano=ano, periodo=periodo).exists():
                        messages.error(request, f"O semestre {ano}/{periodo} já existe.")
                    else:
                        Semestre.objects.create(ano=ano, periodo=periodo)
                        messages.success(request, f"Semestre {ano}/{periodo} criado com sucesso!")
                except ValueError:
                    messages.error(request, "Ano e período devem ser valores numéricos.")
            else:
                messages.error(request, "Ano e período são obrigatórios.")
        
        # Delete semester
        elif action == 'delete':
            semestre_id = request.POST.get('semestre_id')
            
            if semestre_id:
                try:
                    semestre = get_object_or_404(Semestre, id=semestre_id)
                    
                    # Check if semester has turmas
                    if semestre.turmas.exists():
                        messages.error(request, f"Não é possível excluir o semestre {semestre} pois existem turmas associadas.")
                        return redirect('admin_semesters')
                    
                    nome = str(semestre)
                    semestre.delete()
                    messages.success(request, f"Semestre {nome} excluído com sucesso!")
                except Exception as e:
                    messages.error(request, f"Erro ao excluir semestre: {str(e)}")
            else:
                messages.error(request, "ID do semestre é obrigatório.")
    
    # Get all semesters ordered by year and period
    semestres = Semestre.objects.all().order_by('-ano', '-periodo')
    
    context = {
        'semestres': semestres,
        'current_year': current_year,
        'user_type': 'admin',
        'username': request.session.get('username')
    }
    
    return render(request, 'admin/semesters.html', context)

@login_required_custom
def debug_auth(request):
    """View for debugging authentication and password management (admin only)"""
    # Ensure user is admin
    if request.session.get('user_type') != 'admin':
        messages.error(request, 'Acesso negado. Você não é um administrador.')
        return redirect('home')
    
    from .models import Admin
    from .utils import generate_token, enviar_email_redefinicao_senha
    
    reset_link = None
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Reset a user's password directly
        if action == 'reset_password':
            email = request.POST.get('email')
            password = request.POST.get('password', '123456')  # Default to 123456 if not provided
            user_role = request.POST.get('user_role')
            
            if not email or not user_role:
                messages.error(request, "Email e tipo de usuário são obrigatórios.")
                return redirect('debug_auth')
            
            try:
                # Find the user and reset their password
                user = None
                if user_role == 'aluno':
                    user = Aluno.objects.get(emailAluno=email)
                    user.senhaAluno = hash_password(password)
                elif user_role == 'professor':
                    user = Professor.objects.get(emailProf=email)
                    user.senhaProf = hash_password(password)
                elif user_role == 'coordenador':
                    user = Coordenador.objects.get(emailCoord=email)
                    user.senhaCoord = hash_password(password)
                elif user_role == 'admin':
                    user = Admin.objects.get(emailAdmin=email)
                    user.senhaAdmin = hash_password(password)
                
                if user:
                    user.save()
                    messages.success(request, f"Senha do usuário {email} redefinida para: {password}")
                else:
                    messages.error(request, f"Usuário {email} não encontrado como {user_role}.")
            except Exception as e:
                messages.error(request, f"Erro ao redefinir senha: {str(e)}")
        
        # Generate a password reset link
        elif action == 'generate_reset_link':
            email = request.POST.get('reset_email')
            
            if not email:
                messages.error(request, "Email é obrigatório.")
                return redirect('debug_auth')
            
            # Try to find the user in each user type
            user = None
            user_type = None
            
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
            
            if user:
                # Generate token and create reset URL
                token = generate_token()
                
                # Save token to user
                if user_type == 'aluno':
                    user.reset_token = token
                elif user_type == 'professor':
                    user.reset_token = token
                elif user_type == 'coordenador':
                    user.reset_token = token
                elif user_type == 'admin':
                    user.reset_token = token
                
                user.save()
                
                # Generate the reset URL
                reset_url = request.build_absolute_uri(
                    reverse('reset_password_confirm', kwargs={'token': token})
                )
                
                reset_link = reset_url
                messages.success(request, f"Link de redefinição gerado para {email} ({user_type}).")
            else:
                messages.error(request, f"Usuário com email {email} não encontrado.")
    
    # Get sample users for display
    samples = []
    
    # Get a few users of each type
    for aluno in Aluno.objects.all()[:3]:
        samples.append({
            'type': 'aluno',
            'name': aluno.nomeAluno,
            'email': aluno.emailAluno,
            'password_hash': aluno.senhaAluno[:20] + '...',
            'id': aluno.idAluno
        })
    
    for professor in Professor.objects.all()[:3]:
        samples.append({
            'type': 'professor',
            'name': professor.nomeProf,
            'email': professor.emailProf,
            'password_hash': professor.senhaProf[:20] + '...',
            'id': professor.idProfessor
        })
    
    for coordenador in Coordenador.objects.all()[:2]:
        samples.append({
            'type': 'coordenador',
            'name': coordenador.nomeCoord,
            'email': coordenador.emailCoord,
            'password_hash': coordenador.senhaCoord[:20] + '...',
            'id': coordenador.id
        })
    
    for admin in Admin.objects.all()[:2]:
        samples.append({
            'type': 'admin',
            'name': admin.nomeAdmin,
            'email': admin.emailAdmin,
            'password_hash': admin.senhaAdmin[:20] + '...',
            'id': admin.id
        })
    
    context = {
        'samples': samples,
        'reset_link': reset_link,
        'user_type': 'admin',
        'username': request.session.get('username')
    }
    
    return render(request, 'admin/debug_auth.html', context)

@login_required_custom
def notificacoes(request):
    """View for displaying all notifications for a user"""
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    # Get all notifications for the current user
    from .utils import obter_notificacoes_usuario
    notificacoes = obter_notificacoes_usuario(request).order_by('-data_criacao')
    
    # Count unread notifications
    nao_lidas = notificacoes.filter(lida=False).count()
    
    # Handle marking all as read
    if request.method == 'POST' and 'marcar_todas_como_lidas' in request.POST:
        notificacoes.filter(lida=False).update(lida=True)
        messages.success(request, "Todas as notificações foram marcadas como lidas.")
        return redirect('notificacoes')
    
    context = {
        'notificacoes': notificacoes,
        'nao_lidas': nao_lidas,
        'user_type': user_type,
        'username': request.session.get('username')
    }
    
    return render(request, 'notificacoes.html', context)

@login_required_custom
def marcar_notificacao_como_lida(request, notificacao_id):
    """View for marking a notification as read"""
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    # Get notification and check if it belongs to this user
    notificacao = get_object_or_404(Notificacao, id=notificacao_id)
    
    # Check if this notification belongs to the current user
    if ((user_type == 'aluno' and notificacao.aluno_id == user_id) or 
        (user_type == 'professor' and notificacao.professor_id == user_id) or
        (user_type == 'coordenador' and notificacao.coordenador_id == user_id) or
        (user_type == 'admin' and notificacao.admin_id == user_id)):
        
        notificacao.lida = True
        notificacao.save()
        
        # If there's a link, redirect to it
        if notificacao.link:
            return redirect(notificacao.link)
    
    # Redirect back to notifications page
    return redirect('notificacoes')

@login_required_custom
def excluir_notificacao(request, notificacao_id):
    """View for deleting a notification"""
    if request.method != 'POST':
        return redirect('notificacoes')
    
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    # Get notification and check if it belongs to this user
    notificacao = get_object_or_404(Notificacao, id=notificacao_id)
    
    # Check if this notification belongs to the current user
    if ((user_type == 'aluno' and notificacao.aluno_id == user_id) or 
        (user_type == 'professor' and notificacao.professor_id == user_id) or
        (user_type == 'coordenador' and notificacao.coordenador_id == user_id) or
        (user_type == 'admin' and notificacao.admin_id == user_id)):
        
        notificacao.delete()
        messages.success(request, "Notificação excluída com sucesso.")
    else:
        messages.error(request, "Você não tem permissão para excluir esta notificação.")
    
    return redirect('notificacoes')