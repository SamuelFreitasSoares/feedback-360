from django.test import TestCase, Client
from django.urls import reverse
from .models import Aluno, Professor, Coordenador, Admin, Curso
from .utils import hash_password

class ModelTests(TestCase):
    """Testes para os modelos do sistema"""
    
    def setUp(self):
        """Setup inicial para os testes"""
        # Criar curso para testes
        self.curso = Curso.objects.create(nome="Engenharia de Software")
        
        # Criar usuários para testes
        self.aluno = Aluno.objects.create(
            nomeAluno="Aluno Teste",
            emailAluno="aluno@teste.com",
            senhaAluno=hash_password("123456"),
            matricula="12345",
            curso=self.curso
        )
        
        self.professor = Professor.objects.create(
            nomeProf="Professor Teste",
            emailProf="professor@teste.com",
            senhaProf=hash_password("123456")
        )
        
        self.coordenador = Coordenador.objects.create(
            nomeCoord="Coordenador Teste",
            emailCoord="coordenador@teste.com",
            senhaCoord=hash_password("123456"),
            curso=self.curso
        )
        
        self.admin = Admin.objects.create(
            nomeAdmin="Admin Teste",
            emailAdmin="admin@teste.com",
            senhaAdmin=hash_password("123456")
        )
    
    def test_aluno_creation(self):
        """Teste de criação de aluno"""
        self.assertEqual(self.aluno.nomeAluno, "Aluno Teste")
        self.assertEqual(self.aluno.emailAluno, "aluno@teste.com")
        self.assertEqual(self.aluno.matricula, "12345")
        self.assertEqual(self.aluno.curso, self.curso)
    
    def test_professor_creation(self):
        """Teste de criação de professor"""
        self.assertEqual(self.professor.nomeProf, "Professor Teste")
        self.assertEqual(self.professor.emailProf, "professor@teste.com")
    
    def test_coordenador_creation(self):
        """Teste de criação de coordenador"""
        self.assertEqual(self.coordenador.nomeCoord, "Coordenador Teste")
        self.assertEqual(self.coordenador.emailCoord, "coordenador@teste.com")
        self.assertEqual(self.coordenador.curso, self.curso)
    
    def test_admin_creation(self):
        """Teste de criação de admin"""
        self.assertEqual(self.admin.nomeAdmin, "Admin Teste")
        self.assertEqual(self.admin.emailAdmin, "admin@teste.com")

class ViewTests(TestCase):
    """Testes para as views do sistema"""
    
    def setUp(self):
        """Setup inicial para os testes"""
        self.client = Client()
        
        # Criar curso para testes
        self.curso = Curso.objects.create(nome="Engenharia de Software")
        
        # Criar usuários para testes
        self.aluno = Aluno.objects.create(
            nomeAluno="Aluno Teste",
            emailAluno="aluno@teste.com",
            senhaAluno=hash_password("123456"),
            matricula="12345",
            curso=self.curso
        )
        
        self.admin = Admin.objects.create(
            nomeAdmin="Admin Teste",
            emailAdmin="admin@teste.com",
            senhaAdmin=hash_password("123456")
        )
    
    def test_login_page(self):
        """Teste de acesso à página de login"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
    
    def test_login_aluno(self):
        """Teste de login como aluno"""
        response = self.client.post(reverse('login'), {
            'email': 'aluno@teste.com',
            'password': '123456'
        })
        self.assertRedirects(response, reverse('home'))
        
        # Verificar se a sessão foi configurada corretamente
        self.assertEqual(self.client.session['user_type'], 'aluno')
        self.assertEqual(self.client.session['user_id'], self.aluno.idAluno)
        self.assertEqual(self.client.session['username'], self.aluno.nomeAluno)
    
    def test_login_admin(self):
        """Teste de login como admin"""
        response = self.client.post(reverse('login'), {
            'email': 'admin@teste.com',
            'password': '123456'
        })
        self.assertRedirects(response, reverse('home'))
        
        # Verificar se a sessão foi configurada corretamente
        self.assertEqual(self.client.session['user_type'], 'admin')
        self.assertEqual(self.client.session['user_id'], self.admin.id)
        self.assertEqual(self.client.session['username'], self.admin.nomeAdmin)
    
    def test_login_invalid(self):
        """Teste de login com credenciais inválidas"""
        response = self.client.post(reverse('login'), {
            'email': 'invalid@teste.com',
            'password': 'invalid'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        
        # Verificar se a mensagem de erro foi exibida
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Credenciais inválidas. Tente novamente.")
    
    def test_logout(self):
        """Teste de logout"""
        # Fazer login primeiro
        self.client.post(reverse('login'), {
            'email': 'aluno@teste.com',
            'password': '123456'
        })
        
        # Verificar se o login foi bem-sucedido
        self.assertTrue('user_type' in self.client.session)
        
        # Fazer logout
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        
        # Verificar se a sessão foi limpa
        self.assertFalse('user_type' in self.client.session)
