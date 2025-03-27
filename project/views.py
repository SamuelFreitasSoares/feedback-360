from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Count
from django.utils import timezone
import pandas as pd
import json
from datetime import datetime

from .models import (
    Aluno, Professor, Coordenador, Nota, Atividade, Disciplina, TurmaAluno,
    Turma, Grupo, Competencia, Curso, Semestre, Avaliacao
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
            # Add more user types if needed
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
        user = Aluno.objects.filter(emailAluno=email, senhaAluno=password).first()
        if user:
            request.session['user_type'] = 'aluno'
            request.session['user_id'] = user.idAluno
            request.session['username'] = user.nomeAluno
            messages.success(request, f"Bem-vindo, {user.nomeAluno}!")
            return redirect("home")

        # Check if the user is a Professor
        user = Professor.objects.filter(emailProf=email, senhaProf=password).first()
        if user:
            request.session['user_type'] = 'professor'
            request.session['user_id'] = user.idProfessor
            request.session['username'] = user.nomeProf
            messages.success(request, f"Bem-vindo, Prof. {user.nomeProf}!")
            return redirect("home")
            
        # Check if the user is a Coordenador
        user = Coordenador.objects.filter(
            emailCoord=email, senhaCoord=password
        ).first()
        if user:
            request.session['user_type'] = 'coordenador'
            request.session['user_id'] = user.id
            request.session['username'] = user.nomeCoord
            messages.success(request, f"Bem-vindo, Coord. {user.nomeCoord}!")
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
            
        if user:
            # Here you would implement password reset logic
            # For now, just show a success message
            messages.success(request, "Um link de redefinição de senha foi enviado para o seu email.")
            return redirect('login')
        else:
            messages.error(request, "Email não encontrado.")
    
    return render(request, "forgot_password.html")

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
        pending_evaluations = Avaliacao.objects.filter(
            avaliador_aluno=aluno, 
            concluida=False
        ).count()
        
        # Get recent activities
        turmas_aluno = TurmaAluno.objects.filter(aluno=aluno)
        recent_activities = Atividade.objects.filter(
            turma__in=[ta.turma for ta in turmas_aluno]
        ).order_by('-dataEntrega', 'titulo')[:5]  # Sort by date and then alphabetically by title
        
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
        for atividade in atividades:
            grupos = Grupo.objects.filter(atividade=atividade, alunos=aluno)
            atividade.grupo = grupos.first() if grupos.exists() else None
            
            if atividade.grupo:
                avaliacoes_pendentes = Avaliacao.objects.filter(
                    avaliador_aluno=aluno,
                    avaliado_aluno__in=atividade.grupo.alunos.all(),
                    atividade=atividade,
                    concluida=False
                ).exists()
                atividade.pendente = avaliacoes_pendentes
    
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
    
    elif user_type in ['professor', 'coordenador']:
        grupos = Grupo.objects.filter(atividade=atividade).order_by('nome')  # Sort groups alphabetically
        return render(request, 'atividade_detalhe.html', {
            'atividade': atividade,
            'grupos': grupos,
            'user_type': user_type
        })

@login_required_custom
def avaliar_colega(request, id_avaliacao):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if user_type != 'aluno':
        messages.error(request, "Apenas alunos podem realizar avaliações.")
        return redirect('atividades')
    
    avaliacao = get_object_or_404(Avaliacao, id=id_avaliacao)
    aluno = Aluno.objects.get(idAluno=user_id)
    
    # Check if the logged user is the evaluator
    if avaliacao.avaliador_aluno != aluno:
        messages.error(request, "Você não tem permissão para realizar esta avaliação.")
        return redirect('atividades')
    
    competencias = Competencia.objects.all()
    
    if request.method == 'POST':
        for competencia in competencias:
            nota_valor = request.POST.get(f'competencia_{competencia.id}')
            if nota_valor:
                Nota.objects.create(
                    avaliacao=avaliacao,
                    competencia=competencia,
                    nota=int(nota_valor),
                    dataAvaliacao=timezone.now()
                )
        
        avaliacao.concluida = True
        avaliacao.save()
        
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
        if user_type == 'aluno' and user_data.senhaAluno != current_password:
            messages.error(request, "Senha atual incorreta.")
        elif user_type == 'professor' and user_data.senhaProf != current_password:
            messages.error(request, "Senha atual incorreta.")
        elif user_type == 'coordenador' and user_data.senhaCoord != current_password:
            messages.error(request, "Senha atual incorreta.")
        # Verify new passwords match
        elif new_password != confirm_password:
            messages.error(request, "As novas senhas não correspondem.")
        else:
            # Update password
            if user_type == 'aluno':
                user_data.senhaAluno = new_password
            elif user_type == 'professor':
                user_data.senhaProf = new_password
            elif user_type == 'coordenador':
                user_data.senhaCoord = new_password
            user_data.save()
            messages.success(request, "Senha atualizada com sucesso.")
        
    return render(request, 'perfil.html', {'user_data': user_data, 'user_type': user_type})

# Admin only views
@login_required_custom
def admin_dashboard(request):
    user_type = request.session.get('user_type')
    if user_type != 'admin':
        messages.error(request, "Acesso restrito aos administradores.")
        return redirect('home')
    
    cursos_count = Curso.objects.count()
    disciplinas_count = Disciplina.objects.count()
    alunos_count = Aluno.objects.count()
    professores_count = Professor.objects.count()
    
    context = {
        'cursos_count': cursos_count,
        'disciplinas_count': disciplinas_count,
        'alunos_count': alunos_count,
        'professores_count': professores_count,
        'user_type': user_type
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required_custom
def admin_import_users(request):
    user_type = request.session.get('user_type')
    if user_type != 'admin':
        messages.error(request, "Acesso restrito aos administradores.")
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
                # Expected columns: nome, email, matricula, curso, etc.
                for _, row in df.iterrows():
                    Aluno.objects.create(
                        nomeAluno=row['nome'],
                        emailAluno=row['email'],
                        matricula=row['matricula'],
                        senhaAluno='123456',  # Default password
                        curso_id=row['curso_id']
                    )
                messages.success(request, f"{df.shape[0]} alunos importados com sucesso.")
                
            elif import_type == 'professores':
                # Expected columns: nome, email, etc.
                for _, row in df.iterrows():
                    Professor.objects.create(
                        nomeProf=row['nome'],
                        emailProf=row['email'],
                        senhaProf='123456'  # Default password
                    )
                messages.success(request, f"{df.shape[0]} professores importados com sucesso.")
                
            else:
                messages.error(request, "Tipo de importação inválido.")
                
        except Exception as e:
            messages.error(request, f"Erro ao processar arquivo: {str(e)}")
    
    return render(request, 'admin/import_users.html', {'user_type': user_type})

# Professor views for creating activities and groups
@login_required_custom
def criar_atividade(request):
    user_type = request.session.get('user_type')
    user_id = request.session.get('user_id')
    
    if user_type not in ['professor', 'admin']:
        messages.error(request, "Apenas professores podem criar atividades.")
        return redirect('home')
    
    if user_type == 'professor':
        professor = Professor.objects.get(idProfessor=user_id)
        turmas = Turma.objects.filter(professor=professor)
    else:  # admin
        turmas = Turma.objects.all()
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        data_entrega = request.POST.get('data_entrega')
        turma_id = request.POST.get('turma')
        
        turma = get_object_or_404(Turma, id=turma_id)
        
        atividade = Atividade.objects.create(
            titulo=titulo,
            descricao=descricao,
            dataEntrega=datetime.strptime(data_entrega, '%Y-%m-%d').date(),
            turma=turma
        )
        
        messages.success(request, f"Atividade '{titulo}' criada com sucesso!")
        return redirect('atividade_detalhe', id_atividade=atividade.id)
    
    return render(request, 'criar_atividade.html', {
        'turmas': turmas,
        'user_type': user_type
    })

@login_required_custom
def criar_grupo(request, id_atividade):
    user_type = request.session.get('user_type')
    
    if user_type not in ['professor', 'admin']:
        messages.error(request, "Apenas professores podem criar grupos.")
        return redirect('home')
    
    atividade = get_object_or_404(Atividade, id=id_atividade)
    turma = atividade.turma
    alunos = TurmaAluno.objects.filter(turma=turma).select_related('aluno')
    
    # Get alunos that are not yet in any group for this activity
    alunos_em_grupos = Grupo.objects.filter(atividade=atividade).values_list('alunos', flat=True)
    alunos_disponiveis = [ta for ta in alunos if ta.aluno.idAluno not in alunos_em_grupos]
    
    # Sort available students alphabetically
    alunos_disponiveis.sort(key=lambda ta: ta.aluno.nomeAluno)
    
    if request.method == 'POST':
        nome_grupo = request.POST.get('nome_grupo')
        alunos_ids = request.POST.getlist('alunos')
        
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
                if avaliador != avaliado:  # Skip self-evaluation for now
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
        'user_type': user_type
    })
