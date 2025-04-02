from django.core.management.base import BaseCommand
from django.utils import timezone
from project.models import (
    Curso, Aluno, Professor, Coordenador, Admin, Disciplina, 
    Turma, TurmaAluno, Semestre, Atividade, Grupo,
    Avaliacao, Competencia, Nota
)
from project.utils import hash_password
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Cria dados de teste para facilitar testes rápidos da aplicação'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Força a criação mesmo se já existirem dados')

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        # Verificar se já existem dados
        if not force and Aluno.objects.count() > 0:
            self.stdout.write(self.style.WARNING(
                'Já existem dados no banco. Use --force para sobrescrever. '
                'Cuidado: isso não excluirá dados existentes, apenas criará novos.'
            ))
            return
        
        self.stdout.write(self.style.SUCCESS('Criando dados de teste...'))
        
        # Verificar pré-requisitos
        if Curso.objects.count() == 0 or Semestre.objects.count() == 0 or Competencia.objects.count() == 0:
            self.stdout.write(self.style.WARNING(
                'Dados básicos não encontrados. Execute antes:\n'
                'python manage.py loaddata project/fixtures/initial_data.json'
            ))
            return
        
        # Obter dados existentes
        cursos = list(Curso.objects.all())
        semestres = list(Semestre.objects.all())
        competencias = list(Competencia.objects.all())
        
        # 1. Criar usuários principais para testes
        # Admin para teste
        admin, created = Admin.objects.get_or_create(
            emailAdmin='admin@teste.com',
            defaults={
                'nomeAdmin': 'Administrador Teste',
                'senhaAdmin': hash_password('123456')
            }
        )
        if created:
            self.stdout.write(f"Admin criado: {admin.nomeAdmin} (admin@teste.com / 123456)")
        
        # Professores para teste
        professores = []
        for i in range(1, 4):
            prof, created = Professor.objects.get_or_create(
                emailProf=f'professor{i}@teste.com',
                defaults={
                    'nomeProf': f'Professor Teste {i}',
                    'senhaProf': hash_password('123456')
                }
            )
            professores.append(prof)
            if created:
                self.stdout.write(f"Professor criado: {prof.nomeProf} (professor{i}@teste.com / 123456)")
        
        # Coordenadores para teste - um por curso
        coordenadores = []
        for i, curso in enumerate(cursos):
            coord, created = Coordenador.objects.get_or_create(
                emailCoord=f'coordenador{i+1}@teste.com',
                defaults={
                    'nomeCoord': f'Coordenador de {curso.nome}',
                    'senhaCoord': hash_password('123456'),
                    'curso': curso
                }
            )
            coordenadores.append(coord)
            if created:
                self.stdout.write(f"Coordenador criado: {coord.nomeCoord} (coordenador{i+1}@teste.com / 123456)")
        
        # 2. Criar disciplinas para cada curso
        disciplinas = []
        disciplina_nomes = [
            ("Algoritmos", "ALG"),
            ("Programação Orientada a Objetos", "POO"),
            ("Banco de Dados", "BD"),
            ("Estrutura de Dados", "ED"),
            ("Redes de Computadores", "RC"),
            ("Inteligência Artificial", "IA")
        ]
        
        for curso in cursos:
            for nome, codigo in disciplina_nomes:
                disc, created = Disciplina.objects.get_or_create(
                    codigo=f"{codigo}-{curso.id}",
                    nome=nome,
                    curso=curso
                )
                disciplinas.append(disc)
                if created:
                    self.stdout.write(f"Disciplina criada: {disc.nome} ({disc.codigo}) para {curso.nome}")
        
        # 3. Criar turmas para cada disciplina
        turmas = []
        for disciplina in disciplinas:
            for semestre in semestres[:1]:  # Apenas para o semestre mais recente
                for codigo in ['A', 'B']:
                    professor = random.choice(professores)
                    turma, created = Turma.objects.get_or_create(
                        codigo=codigo,
                        disciplina=disciplina,
                        semestre=semestre,
                        defaults={'professor': professor}
                    )
                    if not created:
                        turma.professor = professor
                        turma.save()
                    turmas.append(turma)
                    if created:
                        self.stdout.write(f"Turma criada: {turma}")
        
        # 4. Criar 10 alunos por curso para testes
        alunos = []
        for curso in cursos:
            for i in range(1, 11):
                aluno, created = Aluno.objects.get_or_create(
                    emailAluno=f'aluno{curso.id}{i}@teste.com',
                    defaults={
                        'nomeAluno': f'Aluno {i} de {curso.nome}',
                        'senhaAluno': hash_password('123456'),
                        'matricula': f'{10000 + curso.id*100 + i}',
                        'curso': curso
                    }
                )
                alunos.append(aluno)
                if created:
                    self.stdout.write(f"Aluno criado: {aluno.nomeAluno} (aluno{curso.id}{i}@teste.com / 123456)")
        
        # 5. Matricular alunos em turmas de disciplinas do seu curso
        for aluno in alunos:
            # Pegar turmas do curso do aluno
            turmas_curso = [t for t in turmas if t.disciplina.curso == aluno.curso]
            
            # Matricular em 3 turmas aleatórias
            for turma in random.sample(turmas_curso, min(3, len(turmas_curso))):
                matricula, created = TurmaAluno.objects.get_or_create(
                    aluno=aluno,
                    turma=turma
                )
                if created:
                    self.stdout.write(f"Matrícula: {aluno.nomeAluno} em {turma}")
        
        # 6. Criar atividades para cada turma
        atividades = []
        for turma in turmas:
            # Criar 2 atividades por turma
            for i in range(1, 3):
                # Uma atividade passada e uma futura
                if i == 1:
                    data_entrega = timezone.now().date() - timedelta(days=random.randint(1, 10))
                else:
                    data_entrega = timezone.now().date() + timedelta(days=random.randint(5, 20))
                
                atividade, created = Atividade.objects.get_or_create(
                    titulo=f"Atividade {i} - {turma.disciplina.nome}",
                    turma=turma,
                    defaults={
                        'descricao': f"Descrição da atividade {i} da turma {turma.codigo} de {turma.disciplina.nome}",
                        'dataEntrega': data_entrega
                    }
                )
                atividades.append(atividade)
                if created:
                    self.stdout.write(f"Atividade criada: {atividade.titulo} para {turma}")
                    
                    # 7. Criar grupos para cada atividade
                    alunos_turma = [ta.aluno for ta in TurmaAluno.objects.filter(turma=turma)]
                    
                    if alunos_turma:
                        # Embaralhar alunos
                        random.shuffle(alunos_turma)
                        
                        # Criar grupos de 3-4 alunos
                        grupo_size = 3
                        for g in range(0, len(alunos_turma), grupo_size):
                            membros_grupo = alunos_turma[g:g+grupo_size]
                            if len(membros_grupo) >= 2:  # Pelo menos 2 alunos por grupo
                                grupo, g_created = Grupo.objects.get_or_create(
                                    nome=f"Grupo {g//grupo_size + 1}",
                                    atividade=atividade
                                )
                                
                                # Adicionar alunos ao grupo
                                for aluno in membros_grupo:
                                    grupo.alunos.add(aluno)
                                
                                if g_created:
                                    self.stdout.write(f"  Grupo criado: {grupo.nome} com {len(membros_grupo)} alunos")
                                
                                # 8. Criar avaliações entre membros do grupo
                                for avaliador in membros_grupo:
                                    for avaliado in membros_grupo:
                                        if avaliador != avaliado:
                                            avaliacao, av_created = Avaliacao.objects.get_or_create(
                                                avaliador_aluno=avaliador,
                                                avaliado_aluno=avaliado,
                                                atividade=atividade,
                                                defaults={'concluida': i == 1}  # Concluída apenas para atividade passada
                                            )
                                            
                                            # Criar notas para avaliações concluídas
                                            if av_created and avaliacao.concluida:
                                                for competencia in competencias:
                                                    Nota.objects.create(
                                                        avaliacao=avaliacao,
                                                        competencia=competencia,
                                                        nota=random.randint(3, 5),
                                                        dataAvaliacao=timezone.now() - timedelta(days=random.randint(1, 5))
                                                    )
        
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS('Dados de teste criados com sucesso!'))
        self.stdout.write("")
        
        # Exibir resumo dos dados criados
        self.stdout.write("CONTAS PARA TESTES:")
        self.stdout.write("")
        self.stdout.write(f"ADMIN: admin@teste.com / 123456")
        for i, prof in enumerate(professores[:2]):
            self.stdout.write(f"PROFESSOR: professor{i+1}@teste.com / 123456")
        for i, curso in enumerate(cursos[:2]):
            self.stdout.write(f"COORDENADOR: coordenador{i+1}@teste.com / 123456")
            for j in range(1, 3):
                self.stdout.write(f"ALUNO: aluno{curso.id}{j}@teste.com / 123456")
        
        self.stdout.write("")
        self.stdout.write("Execute as seguintes migrações se ainda não executou:")
        self.stdout.write("python manage.py migrate")
        self.stdout.write("")
        self.stdout.write("Para testar as funcionalidades de email:")
        self.stdout.write("python manage.py test_email aluno11@teste.com --reset")
