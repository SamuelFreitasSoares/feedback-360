from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('resetPassword/', views.resetPassword, name='reset'),
    path("home/", views.home, name="home"),
    path('atividades/', views.atividades, name='atividade'),
    path('notas', views.notas, name='notas'),
    path('disciplinas', views.disciplinas, name='disciplinas'),
    path('perfil', views.perfil, name='perfil')
]
