Diagrama de Implantação (Infraestrutura Logica + Serviços)
==========================================================

.. uml::

   @startuml
   !theme plain
   skinparam linetype ortho
   title Arquitetura Interna — Módulos de Código e Serviços

   ' ============================================================
   ' FRONTEND e API
   ' ============================================================
   package "Camada Web (Django)" {

       component "Views MVT\n(HTML)" as MVT
       component "API REST\n(DRF)" as API

       package "Painéis / UI" {
           component "Painel ETL" as UI_ETL
           component "Painel Qualidade (DAMA)" as UI_DAMA
           component "Painel Relacional" as UI_REL
           component "Painel Governança" as UI_GOV
       }

       MVT --> UI_ETL
       MVT --> UI_DAMA
       MVT --> UI_REL
       MVT --> UI_GOV

       API --> MVT : Suporte híbrido
   }

   ' ============================================================
   ' CAMADA DE SERVIÇOS DE DOMÍNIO
   ' ============================================================
   package "Serviços Internos (Domain Services)" {

       component "PipelineService\n(ETL)" as Pipeline
       component "LogicaUnicidade\n(Utils)" as Unicidade
       component "MotorRegrasSQL\n(Service)" as Regras
       component "LogicaScorecard\n(Utils)" as Scorecard
       component "AuditSignals\n(Django Signals)" as Signals
   }

   ' ============================================================
   ' CAMADA DE TASKS (Celery)
   ' ============================================================
   package "Tarefas Assíncronas (Celery Tasks)" {

       component "ETLTasks" as ETLTasks
       component "SimplesTasks" as SimplesTasks
       component "RelacionalTasks" as RelacionalTasks
       component "EngenhariaTasks" as EngenhariaTasks
   }

   ' Ligações Views/API -> Tasks
   MVT --> ETLTasks : delay()
   MVT --> SimplesTasks : delay()
   MVT --> RelacionalTasks : delay()
   MVT --> EngenhariaTasks : delay()

   API --> ETLTasks : delay()
   API --> SimplesTasks : delay()
   API --> RelacionalTasks : delay()
   API --> EngenhariaTasks : delay()

   ' Tasks -> Domain Services
   ETLTasks ..> Pipeline : executa
   SimplesTasks ..> Unicidade : usa
   SimplesTasks ..> Regras : regras SQL simples
   RelacionalTasks ..> Regras : regras SQL avançadas
   RelacionalTasks ..> Scorecard : cálculos avançados

   ' ============================================================
   ' CAMADA DE MODELS (Django ORM)
   ' ============================================================
   package "Models (ORM)" {

       component "ExecucaoPipeline"
       component "LogEtapa"

       component "RelatorioCompletude"
       component "RelatorioValidade"
       component "RelatorioUnicidade"
       component "RelatorioUnicidadePersonalizada"

       component "RelatorioRegraNegocio"
       component "RelatorioAnaliseRelacional"

       component "RelatorioDQI"
       component "RelatorioRiscoSenha"
       component "RelatorioScorecard"

       component "MapeamentoCarga"
       component "HistoricoCarga"

       component "AuditoriaAD"
       component "IncidenteQualidade"
       component "PerfilGerente"
   }

   ' Conexões Services -> Models
   Pipeline --> ExecucaoPipeline
   Pipeline --> LogEtapa

   Unicidade --> RelatorioUnicidade
   SimplesTasks --> RelatorioRegraNegocio

   Regras --> RelatorioRegraNegocio
   Regras --> RelatorioAnaliseRelacional
   Regras --> RelatorioDQI

   Scorecard --> RelatorioScorecard

   Signals --> IncidenteQualidade
   Signals --> AuditoriaAD

   EngenhariaTasks --> MapeamentoCarga
   EngenhariaTasks --> HistoricoCarga

   @enduml
