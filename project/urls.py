from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('reset-password/', views.resetPassword, name='reset_password'),
    
    # Main pages
    path('home/', views.home, name='home'),
    path('atividades/', views.atividades, name='atividades'),
    path('atividade/<int:id_atividade>/', views.atividade_detalhe, name='atividade_detalhe'),
    path('avaliar/<int:id_avaliacao>/', views.avaliar_colega, name='avaliar_colega'),
    path('notas/', views.notas, name='notas'),
    path('disciplinas/', views.disciplinas, name='disciplinas'),
    path('disciplina/<int:id_disciplina>/', views.disciplina_detalhe, name='disciplina_detalhe'),
    path('perfil/', views.perfil, name='perfil'),
    
    # Professor functionalities
    path('criar-atividade/', views.criar_atividade, name='criar_atividade'),
    path('criar-grupo/<int:id_atividade>/', views.criar_grupo, name='criar_grupo'),
    
    # Admin functionalities
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/import-users/', views.admin_import_users, name='admin_import_users'),
]
