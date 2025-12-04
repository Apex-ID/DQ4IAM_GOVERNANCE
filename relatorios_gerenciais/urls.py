from django.urls import path
from . import views

urlpatterns = [
    # O nome 'central_relatorios' deve ser idêntico ao usado no HTML
    path('', views.central_relatorios, name='central_relatorios'),
    
    # Rota para impressão
    path('oficial/<str:tipo_metrica>/<int:pk>/', views.relatorio_oficial_impressao, name='relatorio_oficial'),
]