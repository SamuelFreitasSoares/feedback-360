import requests
import json

# Fazer login
session = requests.Session()

# Primeira requisição para obter o CSRF token
login_page = session.get('http://127.0.0.1:8000/')
csrf_token = None

# Parse the CSRF token from the response
if 'csrftoken' in session.cookies:
    csrf_token = session.cookies['csrftoken']

# Login data
login_data = {
    'username': 'ana',
    'password': '123456',
    'csrfmiddlewaretoken': csrf_token
}

# Headers
headers = {
    'Referer': 'http://127.0.0.1:8000/',
    'X-CSRFToken': csrf_token
}

# Tentar fazer login
response = session.post('http://127.0.0.1:8000/', data=login_data, headers=headers)
print(f"Login response status: {response.status_code}")
print(f"Login response redirected to: {response.url}")

# Tentar acessar a página de notas
notas_response = session.get('http://127.0.0.1:8000/notas/')
print(f"Notas response status: {notas_response.status_code}")
print(f"Notas response redirected to: {notas_response.url}")

# Tentar acessar a nova página de disciplinas do professor
disciplinas_response = session.get('http://127.0.0.1:8000/notas/professor/disciplinas/')
print(f"Disciplinas professor response status: {disciplinas_response.status_code}")
print(f"Disciplinas professor response URL: {disciplinas_response.url}")

if disciplinas_response.status_code == 200:
    print("✅ Sucesso! A nova interface está funcionando!")
else:
    print("❌ Algo não está funcionando corretamente.")
