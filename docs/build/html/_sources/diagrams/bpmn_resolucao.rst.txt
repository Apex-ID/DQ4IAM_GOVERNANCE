Diagrama Resolução de Incidentes
================================


Resolução de Incidentes (BPMN-style)
====================================

.. uml::

   @startuml
   !theme plain
   skinparam linetype ortho
   title Fluxo de Resolução de Incidentes — Gestão

   |Gerente de Governança|
     start
     :Acessa painel de gestão;
     ->

   |PainelGestaoView|
     :Consulta incidentes pendentes;
     :Apresenta lista;
     ->

   |Gerente de Governança|
     partition "Decisão" {
       if (Aprovar Exceção?) then (sim)
         :Clica "Aprovar";
         -> PainelGestaoView : UPDATE status=APROVADO
       else (não)
         :Clica "Rejeitar / Solicitar correção";
         -> PainelGestaoView : UPDATE status=REJEITADO
       endif
     }
     ->

   |Postgres|
     stop
   @enduml
