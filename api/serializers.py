from rest_framework import serializers
from melhoria_continua.models import IncidenteQualidade
from analises_relacionais.models import RelatorioDQI
from qualidade_ad.models import UsuarioUnificado

# --- Serializer para o Dashboard (DQI) ---
class DQISerializer(serializers.ModelSerializer):
    class Meta:
        model = RelatorioDQI
        fields = '__all__'

# --- Serializer para Incidentes (Gestão) ---
class IncidenteSerializer(serializers.ModelSerializer):
    # Campo calculado para mostrar o texto do status bonitinho (ex: "Em Análise")
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = IncidenteQualidade
        fields = [
            'id', 
            'status', 
            'status_display', 
            'regra_violada', 
            'data_abertura',       
            'observacao_gerente', 
            'responsavel_resolucao' 
        ]

# --- Serializer para Detalhes do Usuário (Consulta) ---
class UsuarioUnificadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioUnificado
        fields = '__all__'