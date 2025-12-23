Diagrama Governança Ativa (Monitoramento em Tempo Real)
=======================================================

Governança Ativa (BPMN-style)
=============================

.. uml::

   @startuml
   !theme plain
   skinparam linetype ortho
   title Governança Ativa — Monitoramento em Tempo Real

   |Técnico AD|
     start
     :Altera / Cria objeto no AD;
     ->

   |Active Directory|
     :Event Viewer registra evento;
     ->

   |Agente Windows (Serviço)|
     :Detecta novo log;
     :Formata JSON;
     :POST /api/auditoria/receber/;
     ->

   |API Django|
     :INSERT AuditoriaAD (evento bruto);
     :Dispara post_save / signal;
     ->

   |Motor de Sinais|
     :Valida regras em tempo real;
     if (violation?) then (sim)
        :INSERT IncidenteQualidade (PENDENTE);
        :Marcar AuditoriaAD.violou_regras = True;
     else (não)
        :OK;
     endif
     ->

   |Painel / Gestão|
     stop
   @enduml
