from django.core.management.base import BaseCommand
from django.utils import timezone
from project.models import (
    Curso, Aluno, Professor, Coordenador, Disciplina, 
    Turma, TurmaAluno, Semestre, Atividade, Grupo,
    Avaliacao, Competencia, Nota
)
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Creates demo data for the feedback360 application'

    def handle(self, *args, **kwargs):
        # Check if data already exists
        if Aluno.objects.count() > 0:
            self.stdout.write(self.style.WARNING('Data already exists. Skipping...'))
            return
            
        self.stdout.write(self.style.SUCCESS('Creating demo data...'))
        
        # Make sure we have courses and semesters
        if Curso.objects.count() == 0:
            self.stdout.write(self.style.WARNING('No courses found. Run "python manage.py loaddata initial_data" first.'))
            return

        if Semestre.objects.count() == 0:
            self.stdout.write(self.style.WARNING('No semesters found. Run "python manage.py loaddata initial_data" first.'))
            return
            
        # Get existing data
        cursos = list(Curso.objects.all())
        semestres = list(Semestre.objects.all())
        competencias = list(Competencia.objects.all())
        
        # Create professors
        professores = []
        professor_data = [
            {"nome": "João Silva", "email": "joao.silva@inatel.br"},
            {"nome": "Maria Santos", "email": "maria.santos@inatel.br"},
            {"nome": "Carlos Oliveira", "email": "carlos.oliveira@inatel.br"},
            {"nome": "Ana Ferreira", "email": "ana.ferreira@inatel.br"},
        ]
        
        for data in professor_data:
            professor = Professor.objects.create(
                nomeProf=data["nome"],
                emailProf=data["email"],
                senhaProf="password123"
            )
            professores.append(professor)
            self.stdout.write(f"Created professor: {professor.nomeProf}")
            
        # Create coordinators
        coordenadores = []
        for i, curso in enumerate(cursos):
            coordenador = Coordenador.objects.create(
                nomeCoord=f"Coordenador {curso.nome}",
                emailCoord=f"coordenador.{i+1}@inatel.br",
                senhaCoord="password123",
                curso=curso
            )
            coordenadores.append(coordenador)
            self.stdout.write(f"Created coordinator: {coordenador.nomeCoord}")
            
        # Create disciplines
        disciplinas = []
        disciplina_data = [
            {"nome": "Programação Orientada a Objetos", "codigo": "POO001"},
            {"nome": "Banco de Dados", "codigo": "BD001"},
            {"nome": "Engenharia de Software", "codigo": "ES001"},
            {"nome": "Redes de Computadores", "codigo": "RC001"},
            {"nome": "Inteligência Artificial", "codigo": "IA001"},
        ]
        
        for curso in cursos:
            for data in disciplina_data:
                disciplina = Disciplina.objects.create(
                    nome=data["nome"],
                    codigo=f"{data['codigo']}-{curso.id}",
                    curso=curso
                )
                disciplinas.append(disciplina)
                self.stdout.write(f"Created discipline: {disciplina.nome} for {curso.nome}")
                
        # Create classes (turmas)
        turmas = []
        for disciplina in disciplinas:
            for semestre in semestres:
                for letra in ['A', 'B']:
                    professor = random.choice(professores)
                    turma = Turma.objects.create(
                        codigo=letra,
                        disciplina=disciplina,
                        professor=professor,
                        semestre=semestre
                    )
                    turmas.append(turma)
                    self.stdout.write(f"Created class: {turma}")
                    
        # Create students
        alunos = []
        first_names = ["Miguel", "Arthur", "Gael", "Théo", "Heitor", "Ravi", "Davi", "Bernardo", "Noah", "Gabriel", 
                       "Helena", "Alice", "Laura", "Maria", "Sophia", "Olivia", "Isabella", "Manuela", "Julia", "Lua"]
        last_names = ["Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes"]
        
        for curso in cursos:
            for i in range(20):  # 20 students per course
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                name = f"{first_name} {last_name}"
                email = f"{first_name.lower()}.{last_name.lower()}{i}@aluno.inatel.br"
                matricula = f"{random.randint(10000, 99999)}"
                
                aluno = Aluno.objects.create(
                    nomeAluno=name,
                    emailAluno=email,
                    senhaAluno="password123",
                    matricula=matricula,
                    curso=curso
                )
                alunos.append(aluno)
                self.stdout.write(f"Created student: {aluno.nomeAluno}")
                
                # Enroll students in classes
                curso_disciplinas = [d for d in disciplinas if d.curso == curso]
                for disciplina in curso_disciplinas:
                    turmas_disciplina = [t for t in turmas if t.disciplina == disciplina]
                    if turmas_disciplina:
                        turma = random.choice(turmas_disciplina)
                        TurmaAluno.objects.create(
                            turma=turma,
                            aluno=aluno
                        )
                        self.stdout.write(f"Enrolled {aluno.nomeAluno} in {turma}")
                        
        # Create activities
        atividades = []
        atividade_titles = [
            "Projeto Final", 
            "Trabalho em Grupo", 
            "Desenvolvimento de Sistema", 
            "Análise de Caso", 
            "Pesquisa Aplicada"
        ]
        
        for turma in turmas:
            for i in range(2):  # 2 activities per class
                title = random.choice(atividade_titles)
                days_offset = random.randint(10, 60)
                entrega = timezone.now().date() + timedelta(days=days_offset)
                
                atividade = Atividade.objects.create(
                    titulo=f"{title} - {i+1}",
                    descricao=f"Descrição da atividade {title} para a turma {turma.codigo} de {turma.disciplina.nome}",
                    dataEntrega=entrega,
                    turma=turma
                )
                atividades.append(atividade)
                self.stdout.write(f"Created activity: {atividade.titulo}")
                
                # Create groups for each activity
                alunos_turma = [ta.aluno for ta in TurmaAluno.objects.filter(turma=turma)]
                if len(alunos_turma) > 0:
                    # Shuffle students
                    random.shuffle(alunos_turma)
                    
                    # Create groups of 3-5 students
                    group_size = random.randint(3, 5)
                    group_number = 1
                    
                    for i in range(0, len(alunos_turma), group_size):
                        group_members = alunos_turma[i:i+group_size]
                        if len(group_members) >= 2:  # Ensure at least 2 students per group
                            grupo = Grupo.objects.create(
                                nome=f"Grupo {group_number}",
                                atividade=atividade
                            )
                            for aluno in group_members:
                                grupo.alunos.add(aluno)
                            
                            self.stdout.write(f"Created group: {grupo.nome} with {len(group_members)} students")
                            
                            # Create evaluations between group members
                            for avaliador in group_members:
                                for avaliado in group_members:
                                    if avaliador != avaliado:
                                        avaliacao = Avaliacao.objects.create(
                                            avaliador_aluno=avaliador,
                                            avaliado_aluno=avaliado,
                                            atividade=atividade,
                                            concluida=(random.random() > 0.3)  # 70% chance of being completed
                                        )
                                        
                                        # If evaluation is completed, create notes
                                        if avaliacao.concluida:
                                            for competencia in competencias:
                                                nota = Nota.objects.create(
                                                    avaliacao=avaliacao,
                                                    competencia=competencia,
                                                    nota=random.randint(1, 5),
                                                    dataAvaliacao=timezone.now() - timedelta(days=random.randint(0, 10))
                                                )
                            
                            group_number += 1
        
        self.stdout.write(self.style.SUCCESS('Demo data created successfully!'))
