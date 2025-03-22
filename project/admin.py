from django.contrib import admin
from .models import (Aluno,Atividade,Professor,Competencia,Coordenador,Curso,Nota,Turma,TurmaAluno,Disciplina)

admin.site.register(Aluno)
admin.site.register(Atividade)
admin.site.register(Professor)
admin.site.register(Coordenador)
admin.site.register(Competencia)
admin.site.register(Curso)
admin.site.register(Nota)
admin.site.register(Turma)
admin.site.register(TurmaAluno)
admin.site.register(Disciplina)
