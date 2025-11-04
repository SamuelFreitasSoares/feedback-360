import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FeedBack360.settings')
import django
django.setup()
from project.models import Professor, Disciplina, Turma
p = Professor.objects.get(idProfessor=1)
d = Disciplina.objects.get(id=1)
print('Professor:', p.idProfessor, p.nomeProf)
print('Disciplina:', d.id, d.nome)
qs = Turma.objects.filter(professor=p, disciplina=d)
print('Turmas count for professor & disciplina:', qs.count())
for t in qs:
    print('-', t.id, t.codigo, 'semestre:', t.semestre)
# Also list all turmas for disciplina
all_ts = Turma.objects.filter(disciplina=d)
print('\nAll turmas for disciplina:', all_ts.count())
for t in all_ts:
    print(' *', t.id, t.codigo, 'professor_id:', getattr(t.professor,'idProfessor', None))
