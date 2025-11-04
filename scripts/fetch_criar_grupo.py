import os, sys, re, requests
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

s = requests.Session()
login_url = 'http://127.0.0.1:8000/'
lp = s.get(login_url)
m = re.search(r"name=[\"']csrfmiddlewaretoken[\"'] value=[\"']([^\"']+)[\"']", lp.text)
csrf = m.group(1) if m else s.cookies.get('csrftoken')
resp = s.post(login_url, data={'email': p.emailProf, 'password': 'prof123', 'csrfmiddlewaretoken': csrf}, headers={'Referer': login_url})
print('Login status:', resp.status_code)

for aid in [1,2,3]:
    url = f'http://127.0.0.1:8000/criar-grupo/{aid}/'
    resp = s.get(url)
    print('\nFetch criar-grupo for', aid, 'status:', resp.status_code)
    print('\n'.join(resp.text.splitlines()[:200]))
