from django.db import models
from django.core import validators

class Aluno(models.Model):
    idAluno = models.AutoField(primary_key=True)
    nomeAluno = models.CharField(max_length=255)
    emailAluno = models.EmailField(unique=True)
    senhaAluno = models.CharField(max_length=128)  # Aumentei o tamanho da senha
    matriculaAluno = models.IntegerField()
    
    def __str__(self):
        return self.nomeAluno

class Disciplina(models.Model):
    idDisciplina = models.AutoField(primary_key=True)
    nomeDisciplina = models.CharField(max_length=60)
    codigoDisciplina = models.CharField(max_length=10)
    
    def __str__(self):
        return self.nomeDisciplina
    

class Professor(models.Model):
    idProfessor = models.AutoField(primary_key=True)
    nomeProf = models.CharField(max_length=255)
    emailProf = models.EmailField(unique=True)
    senhaProf = models.CharField(max_length=128)  # Aumentei o tamanho da senha
    disciplinaProf = models.ForeignKey(Disciplina, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return self.nomeProf

class Competencia(models.Model):  # Nome corrigido para singular
    idCompetencia = models.AutoField(primary_key=True)
    descricao = models.TextField()
    
    def __str__(self):
        return self.descricao

class Curso(models.Model):
    idCurso = models.AutoField(primary_key=True)
    nomeCurso = models.CharField(max_length=30)
    codigoCurso = models.CharField(max_length=10)
    
    def __str__(self):
        return self.nomeCurso

class Coordenador(models.Model):
    nomeCoord = models.CharField(max_length=255)
    emailCoord = models.EmailField(unique=True)
    senhaCoord = models.CharField(max_length=128)  # Aumentei o tamanho da senha
    cursoCoord = models.ForeignKey(Curso, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return self.nomeCoord

class Turma(models.Model):
    idTurma = models.AutoField(primary_key=True)
    sigla = models.CharField(max_length=20, null=True, blank=True)
    semestre = models.CharField(max_length=20)
    
    def __str__(self):
        return self.sigla

class Atividade(models.Model):
    idAtividade = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=200)
    atividadeProf = models.ForeignKey(Professor, on_delete=models.CASCADE, null=True, blank=True)
    atividadeDisc = models.ForeignKey(Disciplina, on_delete=models.CASCADE, null=True, blank=True)
    atividadeTurma = models.ForeignKey(Turma, on_delete=models.CASCADE, null=True, blank=True)
    data = models.DateField()
    
    def __str__(self):
        return self.titulo

class Nota(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name="notas_recebidas")
    atividade = models.ForeignKey(Atividade, on_delete=models.CASCADE)
    competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE, null=True, blank=True)
    avaliador_aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, null=True, blank=True, related_name="notas_dadas_aluno")
    avaliador_professor = models.ForeignKey(Professor, on_delete=models.CASCADE, null=True, blank=True, related_name="notas_dadas_professor")
    nota = models.FloatField(validators=[validators.MinValueValidator(0.0), validators.MaxValueValidator(5.0)])
    data = models.DateField()

    def __str__(self):
        if self.avaliador_professor:
            return f"{self.avaliador_professor.nomeProf} avaliou {self.aluno.nomeAluno}"
        elif self.avaliador_aluno:
            return f"{self.avaliador_aluno.nomeAluno} avaliou {self.aluno.nomeAluno}"
        return f"Avaliação de {self.aluno.nomeAluno}"


class TurmaAluno(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, null=True, blank=True)
    semestre = models.CharField(max_length=30)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f'{self.aluno} - {self.disciplina} - {self.turma}'
