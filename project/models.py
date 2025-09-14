from django.db import models
from django.core import validators
from django.utils import timezone

class Curso(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nome

class Coordenador(models.Model):
    id = models.AutoField(primary_key=True)
    nomeCoord = models.CharField(max_length=100)
    emailCoord = models.EmailField(unique=True)
    senhaCoord = models.CharField(max_length=100)
    curso = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True, related_name='coordenadores')
    reset_token = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return self.nomeCoord

class Aluno(models.Model):
    idAluno = models.AutoField(primary_key=True)
    nomeAluno = models.CharField(max_length=100)
    emailAluno = models.EmailField(unique=True)
    senhaAluno = models.CharField(max_length=100)
    matricula = models.CharField(max_length=20, unique=True)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='alunos')
    reset_token = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return f"{self.nomeAluno} ({self.matricula})"

class Professor(models.Model):
    idProfessor = models.AutoField(primary_key=True)
    nomeProf = models.CharField(max_length=100)
    emailProf = models.EmailField(unique=True)
    senhaProf = models.CharField(max_length=100)
    reset_token = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return self.nomeProf

class Semestre(models.Model):
    id = models.AutoField(primary_key=True)
    ano = models.IntegerField()
    periodo = models.IntegerField()  # 1 for first semester, 2 for second
    
    def __str__(self):
        return f"{self.ano}/{self.periodo}"

class Disciplina(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='disciplinas')
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"

class Turma(models.Model):
    id = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20)  # e.g. "A", "B", "C"
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, related_name='turmas')
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, related_name='turmas')
    semestre = models.ForeignKey(Semestre, on_delete=models.CASCADE, related_name='turmas')
    
    def __str__(self):
        return f"{self.disciplina} - Turma {self.codigo} ({self.semestre})"

class TurmaAluno(models.Model):
    id = models.AutoField(primary_key=True)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='matriculas')
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='turmas')
    
    class Meta:
        unique_together = ('turma', 'aluno')
    
    def __str__(self):
        return f"{self.aluno} - {self.turma}"

class Atividade(models.Model):
    id = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=100)
    descricao = models.TextField()
    dataEntrega = models.DateField()
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='atividades')
    competencias = models.ManyToManyField('Competencia', related_name='atividades', blank=True)
    
    def __str__(self):
        return f"{self.titulo} ({self.turma})"

class Grupo(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    atividade = models.ForeignKey(Atividade, on_delete=models.CASCADE, related_name='grupos')
    alunos = models.ManyToManyField(Aluno, related_name='grupos')
    
    def __str__(self):
        return f"{self.nome} - {self.atividade}"

class Competencia(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    
    def __str__(self):
        return self.nome

class Avaliacao(models.Model):
    id = models.AutoField(primary_key=True)
    avaliador_aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='avaliacoes_realizadas')
    avaliado_aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='avaliacoes_recebidas')
    atividade = models.ForeignKey(Atividade, on_delete=models.CASCADE, related_name='avaliacoes')
    concluida = models.BooleanField(default=False)
    is_self_assessment = models.BooleanField(default=False, help_text="Indica se é uma auto-avaliação")
    
    class Meta:
        unique_together = ('avaliador_aluno', 'avaliado_aluno', 'atividade')
    
    def __str__(self):
        return f"Avaliação de {self.avaliador_aluno} para {self.avaliado_aluno} - {self.atividade}"

class Nota(models.Model):
    id = models.AutoField(primary_key=True)
    avaliacao = models.ForeignKey(Avaliacao, on_delete=models.CASCADE, related_name='notas')
    competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE, related_name='notas')
    nota = models.IntegerField()
    dataAvaliacao = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('avaliacao', 'competencia')
    
    def __str__(self):
        return f"Nota {self.nota} para {self.competencia} - {self.avaliacao}"

class Admin(models.Model):
    id = models.AutoField(primary_key=True)
    nomeAdmin = models.CharField(max_length=100)
    emailAdmin = models.EmailField(unique=True)
    senhaAdmin = models.CharField(max_length=100)
    reset_token = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return self.nomeAdmin

class Notificacao(models.Model):
    """Modelo para notificações do sistema"""
    TIPO_CHOICES = (
        ('info', 'Informação'),
        ('warning', 'Aviso'),
        ('success', 'Sucesso'),
        ('danger', 'Erro'),
    )
    
    DESTINATARIO_CHOICES = (
        ('aluno', 'Aluno'),
        ('professor', 'Professor'),
        ('coordenador', 'Coordenador'),
        ('admin', 'Administrador'),
    )
    
    titulo = models.CharField(max_length=100)
    mensagem = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    lida = models.BooleanField(default=False)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='info')
    
    # Destinatário (apenas um destes campos será preenchido)
    aluno = models.ForeignKey(Aluno, null=True, blank=True, on_delete=models.CASCADE, related_name='notificacoes')
    professor = models.ForeignKey(Professor, null=True, blank=True, on_delete=models.CASCADE, related_name='notificacoes')
    coordenador = models.ForeignKey(Coordenador, null=True, blank=True, on_delete=models.CASCADE, related_name='notificacoes')
    admin = models.ForeignKey(Admin, null=True, blank=True, on_delete=models.CASCADE, related_name='notificacoes')
    
    # Link para redirecionamento
    link = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        ordering = ['-data_criacao']
    
    def __str__(self):
        return self.titulo
    
    @property
    def destinatario_tipo(self):
        """Retorna o tipo de destinatário"""
        if self.aluno:
            return 'aluno'
        elif self.professor:
            return 'professor'
        elif self.coordenador:
            return 'coordenador'
        elif self.admin:
            return 'admin'
        return None
