import requests

urls = [
    'http://127.0.0.1:8000/',
    'http://127.0.0.1:8000/atividades/',
    'http://127.0.0.1:8000/disciplinas/',
    'http://127.0.0.1:8000/notas/',
    'http://127.0.0.1:8000/admin/'
]

for u in urls:
    print('\n---', u, '---')
    try:
        r = requests.get(u, timeout=10)
        print('Status:', r.status_code)
        lines = r.text.splitlines()
        for l in lines[:80]:
            print(l)
    except Exception as e:
        print('ERROR:', e)
