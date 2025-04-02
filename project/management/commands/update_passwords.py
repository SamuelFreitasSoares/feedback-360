from django.core.management.base import BaseCommand
from project.models import Aluno, Professor, Coordenador, Admin
from project.utils import hash_password

class Command(BaseCommand):
    help = 'Updates all user passwords to use secure hashing'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando atualização de senhas...')
        
        # Update Aluno passwords
        alunos = Aluno.objects.all()
        for aluno in alunos:
            if len(aluno.senhaAluno) < 64:  # Not hashed if less than 64 chars (SHA-256 length)
                self.stdout.write(f'Atualizando senha para aluno: {aluno.nomeAluno}')
                aluno.senhaAluno = hash_password(aluno.senhaAluno)
                aluno.save()
        
        # Update Professor passwords
        professores = Professor.objects.all()
        for professor in professores:
            if len(professor.senhaProf) < 64:
                self.stdout.write(f'Atualizando senha para professor: {professor.nomeProf}')
                professor.senhaProf = hash_password(professor.senhaProf)
                professor.save()
        
        # Update Coordenador passwords
        coordenadores = Coordenador.objects.all()
        for coordenador in coordenadores:
            if len(coordenador.senhaCoord) < 64:
                self.stdout.write(f'Atualizando senha para coordenador: {coordenador.nomeCoord}')
                coordenador.senhaCoord = hash_password(coordenador.senhaCoord)
                coordenador.save()
        
        # Update Admin passwords
        admins = Admin.objects.all()
        for admin in admins:
            if len(admin.senhaAdmin) < 64:
                self.stdout.write(f'Atualizando senha para admin: {admin.nomeAdmin}')
                admin.senhaAdmin = hash_password(admin.senhaAdmin)
                admin.save()
        
        self.stdout.write(self.style.SUCCESS('Todas as senhas foram atualizadas com sucesso!'))
