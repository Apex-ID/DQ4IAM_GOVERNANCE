from django.contrib import admin
from .models import PerfilGerente, AuditoriaAD, IncidenteQualidade

# Configuração para o Perfil de Gerente
@admin.register(PerfilGerente)
class PerfilGerenteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'responsabilidade')
    list_filter = ('responsabilidade',)
    search_fields = ('usuario__username', 'responsabilidade')

# Configuração para os Logs de Auditoria (Visualização Técnica)
@admin.register(AuditoriaAD)
class AuditoriaADAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'tecnico_ad_login', 'tipo_acao', 'tipo_objeto', 'violou_regras')
    list_filter = ('violou_regras', 'tipo_acao', 'tipo_objeto', 'timestamp')
    search_fields = ('objeto_nome', 'tecnico_ad_login', 'dados_evento')
    readonly_fields = ('timestamp',) # Logs não devem ser editados

# Configuração para os Incidentes (Visualização de Gestão)
@admin.register(IncidenteQualidade)
class IncidenteQualidadeAdmin(admin.ModelAdmin):
    list_display = ('id', 'regra_violada', 'status', 'responsavel_resolucao', 'data_abertura')
    list_filter = ('status', 'responsavel_resolucao', 'data_abertura')
    search_fields = ('regra_violada', 'descricao_incidente')