from rest_framework import viewsets, views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from melhoria_continua.models import IncidenteQualidade
from analises_relacionais.models import RelatorioDQI
from qualidade_ad.tasks import executar_pipeline_completo_task

from .serializers import IncidenteSerializer, DQISerializer

# --- Endpoint 1: Dashboard Principal ---
class DashboardAPIView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ultimo_dqi = RelatorioDQI.objects.order_by('-data_calculo').first()
        dqi_data = DQISerializer(ultimo_dqi).data if ultimo_dqi else {}

        pendentes = IncidenteQualidade.objects.filter(status='PENDENTE').count()
        em_tratamento = IncidenteQualidade.objects.exclude(status__in=['PENDENTE', 'RESOLVIDO', 'REJEITADO']).count()

        dados = {
            "dqi": dqi_data,
            "incidentes": {
                "pendentes": pendentes,
                "em_tratamento": em_tratamento,
                "total": pendentes + em_tratamento
            },
            "status_sistema": "Operacional"
        }
        return Response(dados)

# --- Endpoint 2: Gestão de Incidentes ---
class IncidenteViewSet(viewsets.ModelViewSet):
    queryset = IncidenteQualidade.objects.all().order_by('-data_abertura')
    serializer_class = IncidenteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    @action(detail=True, methods=['post'])
    def aprovar_excecao(self, request, pk=None):
        incidente = self.get_object()
        incidente.status = 'APROVADO' 
        incidente.observacao_gerente = request.data.get('observacao', 'Aprovado via API')
        incidente.save()
        return Response({'status': 'Incidente aprovado como exceção'})

# --- Endpoint 3: Disparar Processos ---
class PipelineAPIView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        executar_pipeline_completo_task.delay()
        return Response({"mensagem": "Pipeline iniciado em background"}, status=status.HTTP_202_ACCEPTED)