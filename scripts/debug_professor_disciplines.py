import os
import sys
import django
# Ensure project root is on sys.path so Django settings package can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FeedBack360.settings')
django.setup()

from project.models import Professor, Disciplina

print('Professors and disciplinas via turmas__professor filter:')
for p in Professor.objects.all():
    disciplinas = Disciplina.objects.filter(turmas__professor=p).distinct()
    print(f'- Professor idProfessor={p.idProfessor} nome={p.nomeProf} -> disciplinas_count={disciplinas.count()}')
    for d in disciplinas:
        print(f'    * Disciplina id={d.id} nome={d.nome} codigo={d.codigo} turmas_count={d.turmas.count()}')
