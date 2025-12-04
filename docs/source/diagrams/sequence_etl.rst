Sequence ETL Completo (Aprovado + Revisão de Estilo)
====================================================

.. uml::

   @startuml
   !theme plain
   autonumber

   actor "Administrador" as Admin

   box "Aplicação Web" #FFFFFF
       participant "PainelControleView" as View
   end box

   box "Infraestrutura Assíncrona" #F5F5F5
       queue "Redis (Broker)" as Redis
       participant "Celery Worker" as Worker
   end box

   box "Persistência" #EFEFEF
       database "PostgreSQL (Staging)" as Staging
       database "PostgreSQL (Produção)" as Prod
   end box

   participant "LDAP Server (AD)" as AD

   == Início ==
   Admin -> View : Clica "Executar Pipeline Completo"
   View -> Redis : enqueue(executar_pipeline_completo)
   View --> Admin : "Pipeline Iniciado"

   == Background ==
   Redis -> Worker : entregar tarefa
   activate Worker

   group Etapa 1: Extração
       Worker -> AD : Consulta LDAPS
       AD --> Worker : Objetos retornados
       Worker -> Worker : Gera arquivos CSV temporários
   end

   group Etapa 2: Limpeza (Pandas)
       Worker -> Worker : Remover caracteres nulos
       Worker -> Worker : Normalizar espaços e acentuação
   end

   group Etapa 3: Carga Staging
       Worker -> Staging : TRUNCATE
       Worker -> Staging : COPY BULK INSERT
       note right: Dados armazenados em TEXT
   end

   group Etapa 4: Transformação Produção
       Worker -> Prod : TRUNCATE
       Worker -> Prod : INSERT SELECT FROM staging
       note right
           Conversão de tipos:
           • INTEGER
           • TIMESTAMPTZ
           • UUID
       end note

       alt Erro de Conversão
           Prod --> Worker : SQLException
           Worker -> Prod : INSERT INTO etl_error_log
       end
   end

   Worker -> Prod : Atualizar ExecucaoPipeline(status="CONCLUÍDO")
   deactivate Worker

   @enduml
