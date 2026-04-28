"""
Configuração de URLs do projeto DQ4IAM GOVERNANCE.

A lista `urlpatterns` define as rotas para as views.
Inclui rotas para:
- Admin
- Autenticação
- Apps do sistema
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    #  ROTAS DE AUTENTICAÇÃO USUÁRIO
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # URLs do Pipeline (Carga)
    path('', include('qualidade_ad.urls')),
    
    # URLs de Análises Simples
    path('', include('analises_simples.urls')),
    
    # URLs de Análises Relacionais
    path('', include('analises_relacionais.urls')),

    # URLs do Importador Dinâmico
    path('', include('importador_dinamico.urls')),

    # URLs dos Relatórios Gerenciais (Report Center)
    path('relatorios/', include('relatorios_gerenciais.urls')),

    # URLs da Melhoria Contínua
    path('', include('melhoria_continua.urls')),

    # URLs do Construtor de Schemas
    path('', include('construtor_schemas.urls')),

    # Rota para  API (PARA O REACT) 
    path('api/v1/', include('api.urls')),
]
