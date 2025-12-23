Project Classes
===============

.. uml::

@startuml
!theme plain
skinparam linetype ortho
hide empty members

' ============================================================
' MÓDULO 1: QUALIDADE_AD (ETL CORE)
' ============================================================
package qualidade_ad {

class PainelControleView <<View>> {
+get(request)
+post(request)
}

class ETLTasks <<CeleryTask>> {
+executar_pipeline_completo()
+importar_arquivos_existentes()
}

class PipelineService <<Service>> {
+extrair_ldap()
+limpar_pandas()
+carregar_staging()
+transformar_producao()
}

class ExecucaoPipeline <<Model>>
class LogEtapa <<Model>>

PainelControleView ..> ETLTasks : delay()
ETLTasks ..> PipelineService : executa
PipelineService ..> ExecucaoPipeline : grava
}

' ============================================================
' MÓDULO 2: ANALISES_SIMPLES (MÉTRICAS DAMA)
' ============================================================
package analises_simples {

class DashboardAnalisesView <<View>> {
+dashboard_analises()
+configuracao_unicidade()
}

class SimplesTasks <<CeleryTask>> {
+executar_analise_completude()
+executar_analise_validade()
+executar_analise_unicidade()
+executar_unicidade_personalizada(cols)
+executar_regras_staging()
+executar_regras_producao()
}

class LogicaUnicidade <<Utils>> {
+analisar_unicidade_coluna()
+analisar_unicidade_tabela()
+analisar_unicidade_multicoluna()
}

class RelatorioCompletude <<Model>>
class RelatorioValidade <<Model>>
class RelatorioUnicidade <<Model>>
class RelatorioRegraNegocio <<Model>>
class RelatorioUnicidadePersonalizada <<Model>>

DashboardAnalisesView ..> SimplesTasks : delay()
SimplesTasks ..> LogicaUnicidade : usa
SimplesTasks ..> RelatorioRegraNegocio : persiste
}

' ============================================================
' MÓDULO 3: ANALISES_RELACIONAIS
' ============================================================
package analises_relacionais {

class DashboardRelacionalView <<View>> {
+dashboard_relacional()
+dashboard_scorecard()
+baixar_csv_scorecard()
}

class RelacionalTasks <<CeleryTask>> {
+executar_analises_relacionais()
+executar_metricas_avancadas()
+executar_scorecard_completo()
-_executar_lista_regras(lista)
}

class LogicaScorecard <<Utils>> {
+gerar_scorecard_detalhado(engine)
}

class RegrasRepository <<Config>> {
+REGRAS_STAGING
+REGRAS_PRODUCAO
+REGRAS_SQL
}

class RelatorioAnaliseRelacional <<Model>>
class RelatorioDQI <<Model>>
class RelatorioRiscoSenha <<Model>>
class RelatorioScorecard <<Model>>

DashboardRelacionalView ..> RelacionalTasks : delay()
RelacionalTasks ..> RegrasRepository : lê
RelacionalTasks ..> LogicaScorecard : usa
RelacionalTasks ..> RelatorioDQI : salva
}

' ============================================================
' MÓDULO 4: MELHORIA_CONTINUA (GOVERNANÇA)
' ============================================================
package melhoria_continua {

class APIView <<View>> {
+api_receber_auditoria(request)
}

class GestaoView <<View>> {
+painel_gestao_incidentes()
+tratar_incidente()
}

class AuditSignals <<Signal>> {
+validar_evento_ad(post_save)
}

class AuditoriaAD <<Model>>
class IncidenteQualidade <<Model>>
class PerfilGerente <<Model>>

APIView ..> AuditoriaAD : create()
AuditoriaAD ..> AuditSignals : trigger
AuditSignals ..> IncidenteQualidade : create()
GestaoView ..> IncidenteQualidade : update status
}

' ============================================================
' MÓDULO 5: FERRAMENTAS (IMPORTADOR / CONSTRUTOR)
' ============================================================
package ferramentas {

class ImportadorView <<View>>
class ConstrutorView <<View>>

class EngenhariaTasks <<CeleryTask>> {
+executar_importacao_dinamica()
+executar_criacao_schema()
+executar_carga_mapeada()
}

class DocParser <<Utils>> {
+ler_docx()
+ler_pdf()
}

ConstrutorView ..> DocParser
ConstrutorView ..> EngenhariaTasks : delay()
ImportadorView ..> EngenhariaTasks : delay()
}

' ============================================================
' MÓDULO 6: RELATÓRIOS GERENCIAIS
' ============================================================
package relatorios_gerenciais {

class CentralRelatoriosView <<View>> {
+central_relatorios()
+relatorio_oficial_impressao()
}

class DicionarioDados <<Config>> {
+obter_info_coluna()
}

class CatalogoFormulas <<Config>>

CentralRelatoriosView ..> DicionarioDados : consulta
}

' ============================================================
' SCRIPTS EXTERNOS
' ============================================================
package scripts_externos {

class agente_ad_monitor <<Script>> {
+monitorar_event_viewer()
+enviar_post()
}

class iniciar_sistema <<Orchestrator>> {
+abrir_terminais()
}
}

agente_ad_monitor ..> APIView : POST

@enduml
