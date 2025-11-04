import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FeedBack360.settings')
import django
django.setup()

import requests, re
from project.models import Professor
from project.utils import hash_password

p = Professor.objects.get(idProfessor=1)
p.senhaProf = hash_password('prof123')
p.save()

s = requests.Session()
login_url = 'http://127.0.0.1:8000/'
lp = s.get(login_url)
m = re.search(r"name=[\"']csrfmiddlewaretoken[\"'] value=[\"']([^\"']+)[\"']", lp.text)
csrf = m.group(1) if m else s.cookies.get('csrftoken')
resp = s.post(login_url, data={'email': p.emailProf, 'password': 'prof123', 'csrfmiddlewaretoken': csrf}, headers={'Referer': login_url}, allow_redirects=True)
print('Login resp code:', resp.status_code)

url = 'http://127.0.0.1:8000/notas/professor/disciplina/1/turmas/'
resp = s.get(url, allow_redirects=True)
print('Final URL:', resp.url)
print('Status code:', resp.status_code)
print('History len:', len(resp.history))
for r in resp.history:
    print('  ->', r.status_code, r.headers.get('Location'))
print('\n--- body head ---\n')
print('\n'.join(resp.text.splitlines()[:160]))
