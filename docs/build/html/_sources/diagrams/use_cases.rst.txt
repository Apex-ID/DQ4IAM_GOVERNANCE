Use Cases
=========

... uml::

   @startuml
   !theme plain
   left to right direction

   ' ---- ATORES ----
   actor "Técnico de TI" as Tech
   actor "Agendador (Cron)" <<system>> as Cron
   actor "Agente Windows (Serviço AD)" <<system>> as Agent

   rectangle "Active Directory" <<external>> as AD

   actor "Gerente de Governança" as Manager
   actor "Super Admin" as SuperAdmin

   actor "Gerente Acadêmico (Graduação)" as MgrGrad
   actor "Gerente Acadêmico (Pós)" as MgrPos
   actor "Gerente RH (Efetivos)" as MgrEfetivo
   actor "Gerente RH (Terceirizados)" as MgrTerc
   actor "Gerente de Infra" as MgrInfra

   ' Herdam permissões do Gerente base
   MgrGrad -up-|> Manager
   MgrPos -up-|> Manager
   MgrEfetivo -up-|> Manager
   MgrTerc -up-|> Manager
   MgrInfra -up-|> Manager
   SuperAdmin -up-|> Manager


   ' ---- MÓDULO ETL ----
   package "Módulo 1: Engenharia & Carga (ETL)" {
     usecase "Executar Pipeline Completo" as UC_ETL
     usecase "Importar CSV Dinâmico" as UC_CSV
     usecase "Mapear Colunas De/Para" as UC_Map
   }

   ' ---- MÓDULO AUDITORIA PASSIVA ----
   package "Módulo 2: Auditoria Passiva" {
     usecase "Visualizar Dashboard" as UC_Dash
     usecase "Executar Auditoria" as UC_Audit
     usecase "Gerar Relatório (PDF)" as UC_PDF
     usecase "Gerar Scorecard (CSV)" as UC_Score
   }

   ' ---- MÓDULO GOVERNANÇA ATIVA ----
   package "Módulo 3: Governança Ativa" {
     usecase "Receber Evento via API" as UC_API
     usecase "Detectar Violação" as UC_Signal
     usecase "Gerenciar Incidentes" as UC_Incident
     usecase "Aprovar Exceção" as UC_Approve
     usecase "Rejeitar Correção" as UC_Reject
   }


   ' ---- RELAÇÕES (Linhas simples, SEM SETAS) ----

   Tech -- UC_Audit
   Tech -- UC_ETL
   Cron -- UC_ETL

   Agent -- UC_API

   SuperAdmin -- UC_ETL
   SuperAdmin -- UC_CSV
   SuperAdmin -- UC_Map

   Manager -- UC_Dash
   Manager -- UC_PDF
   Manager -- UC_Score
   Manager -- UC_Incident

   ' Extend / Include (único caso que tem seta)
   UC_API --> UC_Signal : "<<include>>"
   UC_Incident <.. UC_Approve : "<<extend>>"
   UC_Incident <.. UC_Reject : "<<extend>>"

   ' Nota explicando fluxo externo (não permitido como seta)
   note right of Agent
     O Agente Windows detecta eventos do AD
     e envia para o caso de uso "Receber Evento via API".
     (Fluxo detalhado é mostrado no diagrama de sequência.)
   end note

   @enduml
