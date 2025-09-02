# Sistema de Feedback 360° - Inatel

Um sistema de avaliação 360 graus para atividades em grupo, onde os alunos podem avaliar o desempenho de seus colegas.

## Sobre o Projeto

O Sistema de Feedback 360° permite que estudantes avaliem seus colegas em trabalhos em grupo, com base em competências como comunicação, trabalho em equipe, liderança e outras habilidades importantes. Essas avaliações são analisadas para fornecer insights aos professores e coordenadores sobre o desenvolvimento das competências dos alunos.

## Características

- Sistema de login para diferentes perfis (alunos, professores, coordenadores, administradores)
- Cadastro e gerenciamento de cursos, disciplinas e turmas
- Criação de atividades e grupos de trabalho
- Avaliações 360° entre alunos do mesmo grupo
- Visualização de resultados com gráficos
- Sistema administrativo completo
- Importação em massa de usuários via CSV

## Tecnologias Utilizadas

- **Backend**: Django (Python)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Banco de Dados**: SQLite
- **Gráficos**: Chart.js

## Instalação para Desenvolvimento

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/feedback-360.git
   cd feedback-360
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   
   # Windows:
   venv\Scripts\activate
   
   # Linux/Mac:
   source venv/bin/activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Execute as migrações do banco de dados:
   ```bash
   python manage.py migrate
   ```

5. Crie um usuário administrador:
   ```bash
   python create_admin.py
   ```

6. Carregue os dados iniciais:
   ```bash
   python manage.py loaddata project/fixtures/initial_data.json
   ```

7. Inicie o servidor:
   ```bash
   python manage.py runserver
   ```

8. Acesse o sistema em: http://127.0.0.1:8000

## Implantação em Produção

### Pré-requisitos
- Servidor Linux (Ubuntu/Debian recomendado) com no mínimo 2GB de RAM e 1 CPU
- Python 3.9+ instalado
- PostgreSQL 12+
- Nginx ou Apache
- Domínio configurado com DNS
- Certificado SSL (pode ser obtido gratuitamente com Let's Encrypt)
- Pelo menos 10GB de espaço em disco disponível
- Acesso SSH ao servidor
- Firewall configurado para permitir tráfego nas portas 80 (HTTP), 443 (HTTPS) e 22 (SSH)

### Requisitos de Rede
- Conexão estável com a internet
- IP fixo ou serviço de DNS dinâmico configurado
- Largura de banda mínima recomendada: 5 Mbps

### 1. Preparação do Servidor

```bash
# Atualizar pacotes
sudo apt update
sudo apt upgrade -y

# Instalar dependências
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib nginx git

# Instalar ferramentas para compilar pacotes Python
sudo apt install -y build-essential libpq-dev python3-dev
```

### 2. Configuração do Banco de Dados PostgreSQL

```bash
# Acessar o PostgreSQL
sudo -u postgres psql

# Criar banco de dados e usuário
CREATE DATABASE feedback360;
CREATE USER feedback360user WITH PASSWORD 'senha_segura';
ALTER ROLE feedback360user SET client_encoding TO 'utf8';
ALTER ROLE feedback360user SET default_transaction_isolation TO 'read committed';
ALTER ROLE feedback360user SET timezone TO 'America/Sao_Paulo';
GRANT ALL PRIVILEGES ON DATABASE feedback360 TO feedback360user;
\q
```

### 3. Configuração do Projeto

1. Clone o repositório:
```bash
cd /var/www/
sudo git clone https://github.com/seu-usuario/feedback-360.git
sudo chown -R $USER:$USER /var/www/feedback-360
```

2. Configure o ambiente virtual:
```bash
cd /var/www/feedback-360
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

3. Crie um arquivo `.env` na raiz do projeto:
```bash
touch .env
```

4. Edite o arquivo `.env` com as seguintes configurações:
```bash
# Exemplo de configuração
DEBUG=False
SECRET_KEY=sua_chave_secreta
ALLOWED_HOSTS=seu_dominio.com
DATABASE_URL=postgres://feedback360user:senha_segura@localhost/feedback360
```

5. Execute as migrações e colete arquivos estáticos:
```bash
python manage.py migrate
python manage.py collectstatic
```

### 4. Configuração do Gunicorn

Crie um arquivo de serviço para o Gunicorn:
```bash
sudo nano /etc/systemd/system/feedback360.service
```

Adicione o seguinte conteúdo:
```bash
[Unit]
Description=Gunicorn instance to serve Feedback360
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/feedback-360
Environment="PATH=/var/www/feedback-360/venv/bin"
ExecStart=/var/www/feedback-360/venv/bin/gunicorn --workers 3 --bind unix:/var/www/feedback-360/feedback360.sock project.wsgi:application

[Install]
WantedBy=multi-user.target
```

Ative e inicie o serviço:
```bash
sudo systemctl start feedback360
sudo systemctl enable feedback360
```

### 5. Configuração do Nginx

Crie um arquivo de configuração para o Nginx:
```bash
sudo nano /etc/nginx/sites-available/feedback360
```

Adicione o seguinte conteúdo:
```bash
server {
    listen 80;
    server_name seu_dominio.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/feedback-360/feedback360.sock;
    }

    location /static/ {
        alias /var/www/feedback-360/static/;
    }

    location /media/ {
        alias /var/www/feedback-360/media/;
    }
}
```

Ative a configuração e reinicie o Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/feedback360 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Configuração de SSL

Instale o Certbot e configure o SSL:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d seu_dominio.com
```

### 7. Verificação

Verifique o status dos serviços:
```bash
sudo systemctl status feedback360
sudo systemctl status nginx
```

### Backups

Configure backups automáticos do banco de dados:

```bash
# Adicione ao crontab
0 2 * * * pg_dump -U feedback360user feedback360 | gzip > /path/to/backups/feedback360_$(date +\%Y\%m\%d).sql.gz
```

### Monitoramento

Para monitoramento do aplicativo, configure o Sentry adicionando sua DSN ao arquivo .env.

## Usuários Padrão

Após a configuração, o sistema terá um usuário administrador padrão:

- **Email**: admin@feedback360.com
- **Senha**: admin123

## Estrutura do Projeto

```
feedback-360/
│
├── FeedBack360/             # Configurações do projeto Django
│
├── project/                 # Aplicação principal
│   ├── fixtures/            # Dados iniciais
│   ├── management/          # Comandos personalizados
│   ├── migrations/          # Migrações do banco de dados
│   ├── static/              # Arquivos estáticos (CSS, JS)
│   ├── templates/           # Templates HTML
│   ├── admin.py             # Configuração do admin
│   ├── context_processors.py # Processadores de contexto
│   ├── middleware.py        # Middlewares personalizados
│   ├── models.py            # Modelos de dados
│   ├── urls.py              # Configuração de URLs
│   └── views.py             # Views (controladores)
│
├── static/                  # Arquivos estáticos globais
│
├── templates/               # Templates globais
│
├── media/                   # Arquivos de mídia (uploads)
│
├── create_admin.py          # Script para criar admin
├── manage.py                # Utilitário Django
├── requirements.txt         # Dependências do projeto
└── README.md                # Este arquivo
```

## Funcionalidades por Perfil

### Alunos
- Visualizar atividades atribuídas
- Realizar avaliações 360° de colegas
- Visualizar notas e feedback recebidos
- Acompanhar evolução em competências

### Professores
- Criar atividades e grupos
- Visualizar avaliações e notas
- Acompanhar o desenvolvimento dos alunos

### Coordenadores
- Visualizar estatísticas dos cursos
- Monitorar o desenvolvimento de competências
- Acompanhar o desempenho de turmas

### Administradores
- Gerenciar todos os aspectos do sistema
- Cadastrar cursos, disciplinas, semestres
- Gerenciar usuários
- Importar usuários em massa

## Licença

Este projeto é licenciado sob a Licença MIT.