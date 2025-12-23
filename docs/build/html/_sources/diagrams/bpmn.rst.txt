Pipeline ETL (BPMN-style)
=========================

Pipeline ETL
============


.. uml::

   @startuml
   !theme plain
   skinparam linetype ortho
   title Pipeline de Engenharia de Dados (ETL) — Swimlanes

   |Administrador|
     start
     :Aciona "Executar Pipeline Completo";
     ->

   |Web / Django|
     :Recebe requisição;
     :Enfileira tarefa no Redis;
     ->

   |Broker (Redis)|
     :Fila: executar_pipeline_completo;
     ->

   |Celery Worker|
     :Consume tarefa;
     partition "Extração" {
       :Conecta ao LDAP/AD via LDAPS;
       :Obtém objetos (users, groups, computers);
       :Gerar CSVs temporários;
     }
     partition "Limpeza" {
       :Pandas - limpeza e normalização;
       :Remover caracteres nulos, trim, normalização;
     }
     partition "Carga Staging" {
       :TRUNCATE / COPY (bulk insert);
     }
     partition "Transformação Produção" {
       :INSERT ... SELECT ... FROM staging;
       if (erro conversão?) then (sim)
         :Registra etl_error_log;
       endif
     }
     :Atualiza ExecucaoPipeline(status=CONCLUÍDO);
     ->

   |Persistência (Postgres)|
     stop
   @enduml
