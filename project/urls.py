from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('reset-password/', views.resetPassword, name='reset_password'),
    path('reset-password-confirm/<str:token>/', views.reset_password_confirm, name='reset_password_confirm'),
    
    # Main pages
    path('home/', views.home, name='home'),
    path('atividades/', views.atividades, name='atividades'),
    path('atividade/<int:id_atividade>/', views.atividade_detalhe, name='atividade_detalhe'),
    path('avaliar/<int:id_avaliacao>/', views.avaliar_colega, name='avaliar_colega'),
    path('auto-avaliar/<int:id_avaliacao>/', views.auto_avaliar, name='auto_avaliar'),
    path('notas/', views.notas, name='notas'),
    path('disciplinas/', views.disciplinas, name='disciplinas'),
    path('disciplina/<int:id_disciplina>/', views.disciplina_detalhe, name='disciplina_detalhe'),
    path('perfil/', views.perfil, name='perfil'),
    
    # Professor functionalities
    path('criar-atividade/', views.criar_atividade, name='criar_atividade'),
    path('criar-grupo/<int:id_atividade>/', views.criar_grupo, name='criar_grupo'),
    
    # Admin functionalities - change the URL pattern to avoid conflict with Django admin
    path('custom-admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('custom-admin/import-users/', views.admin_import_users, name='admin_import_users'),
    path('custom-admin/users/', views.admin_users, name='admin_users'),
    path('custom-admin/users/create/', views.admin_create_user, name='admin_create_user'),
    path('custom-admin/users/edit/<str:role>/<int:user_id>/', views.admin_edit_user, name='admin_edit_user'),
    path('custom-admin/users/delete/<str:role>/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    path('custom-admin/courses/', views.admin_courses, name='admin_courses'),
    path('custom-admin/disciplines/', views.admin_disciplines, name='admin_disciplines'),
    path('custom-admin/classes/', views.admin_classes, name='admin_classes'),
    path('custom-admin/classes/<int:turma_id>/students/', views.admin_class_students, name='admin_class_students'),
    path('custom-admin/semesters/', views.admin_semesters, name='admin_semesters'),
    
    # Add debug URL
    path('custom-admin/debug/auth/', views.debug_auth, name='debug_auth'),
    
    # Admin redirect page
    path('admin-redirect/', views.admin_redirect, name='admin_redirect'),
    
    # Notifications
    path('notificacoes/', views.notificacoes, name='notificacoes'),
    path('notificacoes/<int:notificacao_id>/ler/', views.marcar_notificacao_como_lida, name='marcar_notificacao_como_lida'),
    path('notificacoes/<int:notificacao_id>/excluir/', views.excluir_notificacao, name='excluir_notificacao'),
    
    # Competências
    path('competencias/', views.competencias, name='competencias'),
    path('competencias/criar/', views.criar_competencia, name='criar_competencia'),
    path('competencias/editar/<int:competencia_id>/', views.editar_competencia, name='editar_competencia'),
    path('competencias/excluir/<int:competencia_id>/', views.excluir_competencia, name='excluir_competencia'),
    
    # Professor grades interface
    path('notas/professor/disciplinas/', views.notas_professor_disciplinas, name='notas_professor_disciplinas'),
    path('notas/professor/disciplina/<int:disciplina_id>/turmas/', views.notas_professor_turmas, name='notas_professor_turmas'),
    path('notas/turma/<int:turma_id>/', views.notas_turma_geral, name='notas_turma_geral'),
    path('notas/turma/<int:turma_id>/aluno/<int:aluno_id>/', views.notas_aluno_individual, name='notas_aluno_individual'),
]
