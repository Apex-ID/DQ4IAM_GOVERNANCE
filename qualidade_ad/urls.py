from django.urls import path
from . import views

urlpatterns = [
    # rota para o painel de controle do pipeline ETL
    path('painel/', views.painel_de_controle, name='painel_de_controle'),
    # rota para listar o organograma
    path('organograma/', views.listar_organograma, name='listar_organograma'),
    # rota para criar nova unidade no organograma
    path('organograma/novo/', views.criar_unidade, name='criar_unidade'),
    # rota para editar unidade existente no organograma
    path('organograma/editar/<str:pk>/', views.editar_unidade, name='editar_unidade'),
]