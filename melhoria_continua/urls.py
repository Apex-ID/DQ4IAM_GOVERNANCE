from django.urls import path
from . import views

urlpatterns = [
    # URL: http://SEU_IP:8000/api/auditoria/receber/
    path('api/auditoria/receber/', views.api_receber_auditoria, name='api_receber_auditoria'),    
    path('gestao/', views.painel_gestao_incidentes, name='painel_gestao_incidentes'),
    path('gestao/tratar/<int:pk>/', views.tratar_incidente, name='tratar_incidente'),
]