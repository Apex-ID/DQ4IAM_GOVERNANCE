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
    # rota para listar unidade do organograma
    path('organograma/', views.listar_organograma, name='listar_organograma'),
    # rota para upload unidade do organograma
    path('organograma/upload/', views.upload_organograma, name='upload_organograma'),
    # rota para confirmar importação do organograma
    path('organograma/confirmar/', views.confirmar_importacao, name='confirmar_importacao'),
    # rota para criar unidade do organograma
    path('organograma/novo/', views.criar_unidade, name='criar_unidade'),
    # rota para editar unidade do organograma
    path('organograma/editar/<str:pk>/', views.editar_unidade, name='editar_unidade'),
    # rota para deletar unidade do organograma
    path('organograma/deletar/<str:pk>/', views.deletar_unidade, name='deletar_unidade'),
    # rota para upload vínculos RH
    path('vinculos/upload/', views.upload_vinculos_rh, name='upload_vinculos_rh'),
    # rota para processar consolidação de identidades
    path('identidades/processar/', views.processar_consolidacao, name='processar_consolidacao'),
    # rota para listar identidades consolidadas
    path('identidades/listar/', views.listar_identidades, name='listar_identidades'),
]