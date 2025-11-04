import os, sys
import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FeedBack360.settings')
import django
django.setup()

from project.models import Professor
from project.utils import hash_password

p = Professor.objects.get(idProfessor=1)
print('Professor 1:', p.nomeProf, p.emailProf)
# Reset password to 'prof123'
p.senhaProf = hash_password('prof123')
p.save()
print('Password reset to prof123')

s = requests.Session()
login_url = 'http://127.0.0.1:8000/'
# Fetch login page to get csrf token
lp = s.get(login_url)
if lp.status_code != 200:
    print('Failed to fetch login page, status', lp.status_code)

import re
m = re.search(r"name=[\"']csrfmiddlewaretoken[\"'] value=[\"']([^\"']+)[\"']", lp.text)
csrf = m.group(1) if m else s.cookies.get('csrftoken')
resp = s.post(login_url, data={'email': p.emailProf, 'password': 'prof123', 'csrfmiddlewaretoken': csrf}, headers={'Referer': login_url})
print('Login status:', resp.status_code)

# fetch notas professor disciplinas (view we added debug info to)
url = 'http://127.0.0.1:8000/notas/professor/disciplinas/'
resp = s.get(url)
print('Notas page status:', resp.status_code)
print('\n'.join(resp.text.splitlines()[:160]))
