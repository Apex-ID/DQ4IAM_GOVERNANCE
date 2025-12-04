Diagrama Motor de Auditoria & DQI
=================================

Motor de Auditoria e Cálculo DQI
================================

.. uml::

   @startuml
   !theme plain
   !pragma useActivityDiagram
   skinparam linetype ortho

   title Motor de Auditoria (DQI) — Swimlanes
   end title

   |Auditor|
   start
   :Solicita "Executar Auditoria (Produção)";

   |Web / Django|
   :Enfileira tarefa executar_regras_producao;

   |Broker (Redis)|
   :Fila de auditoria;

   |Worker / Engine|
   :Carrega lista de regras (28);

   repeat
     :Executa SELECT COUNT(*) e SELECT WHERE <condição>;
     :Calcula % conformidade;
     :INSERT RelatorioAnaliseRelacional;
   repeat while (restam regras?) is (sim)

   :Calcula DQI (ponderado);
   :INSERT RelatorioDQI;

   |Persistência (Postgres)|
   stop

   @enduml