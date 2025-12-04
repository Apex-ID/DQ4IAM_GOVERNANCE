from django.urls import path
from . import views
urlpatterns = [
        # Construtor de Schemas
    path('dicionario/', views.upload_dicionario, name='upload_dicionario'),

        # Mapeamento de Carga
    path('mapeamento/', views.definir_mapeamento, name='definir_mapeamento'),

        # Visualização de Schemas
    path('api/tabelas/', views.api_listar_tabelas_banco, name='api_listar_tabelas'),

        # Histórico de Cargas
    path('historico-cargas/', views.historico_cargas, name='historico_cargas'),

        # API Auxiliar
    path('api/tabelas/', views.api_listar_tabelas_banco, name='api_listar_tabelas'),
]