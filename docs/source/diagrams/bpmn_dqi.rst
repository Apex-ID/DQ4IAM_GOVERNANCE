Diagrama Motor de Auditoria & DQI
=================================

Motor de Auditoria e Cálculo DQI
================================

.. uml::

   @startuml
   !theme plain
   skinparam linetype ortho
   title Motor de Auditoria (DQI) — Swimlanes

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
   repeat while (Restam regras?) is yes

   :Calcula DQI (ponderado);
   :INSERT RelatorioDQI;

   |Persistência (Postgres)|
   stop

   @enduml