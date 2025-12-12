from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from . import views

# Configuração do Swagger
schema_view = get_schema_view(
   openapi.Info(
      title="APEX Governance API",
      default_version='v1',
      description="API para o Frontend React (Produção)",
      contact=openapi.Contact(email="ti@ufs.br"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

# Roteador Automático para ViewSets
router = DefaultRouter()
router.register(r'incidentes', views.IncidenteViewSet, basename='incidente')

urlpatterns = [
    # Autenticação JWT (Login do React)
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Endpoints de Negócio
    path('dashboard/resumo/', views.DashboardAPIView.as_view(), name='api_dashboard'),
    path('pipeline/executar/', views.PipelineAPIView.as_view(), name='api_pipeline'),
    
    # Rotas do Router (CRUD Incidentes)
    path('', include(router.urls)),

    # Documentação (Swagger)
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]