"""
URL configuration for feedback project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from project import views

urlpatterns = [
    # Replace the default admin URL pattern with a redirect to our custom admin
    path('admin/', views.admin_redirect, name='admin_redirect'),
    path('', include('project.urls')),
    path('custom-admin/classes/<int:turma_id>/students/', views.admin_class_students, name='admin_class_students'),
    
    # Password reset URLs
    path('reset-password/', views.resetPassword, name='reset_password'),
    path('reset-password/confirm/<str:token>/', views.reset_password_confirm, name='reset_password_confirm'),
    
    # Debug tool
    path('custom-admin/debug/auth/', views.debug_auth, name='debug_auth'),
]

# Add static and media URLs for development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
