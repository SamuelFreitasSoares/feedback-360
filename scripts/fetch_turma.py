import os, sys
import requests, re

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
m = re.search(r"name=[\"']csrfmiddlewaretoken[\"'] value=[\"']([^\"']+)[\"']", lp.text)
csrf = m.group(1) if m else s.cookies.get('csrftoken')
resp = s.post(login_url, data={'email': p.emailProf, 'password': 'prof123', 'csrfmiddlewaretoken': csrf}, headers={'Referer': login_url})
print('Login status:', resp.status_code)

# fetch specific turma page
url = 'http://127.0.0.1:8000/notas/turma/3/'
resp = s.get(url)
print('Fetch URL:', url)
print('Status code:', resp.status_code)
print('Final URL:', resp.url)
print('\n--- full body start ---\n')
print(resp.text[:8000])
print('\n--- full body end ---\n')
