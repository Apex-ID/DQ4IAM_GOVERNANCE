Sequence Motor de Auditoria / DQI (Aprovado + Refinado)
=======================================================

.. uml::

   @startuml
   !theme plain
   autonumber

   actor "Auditor" as User
   participant "DashboardView" as View
   queue "Redis" as Redis
   participant "Celery Worker" as Worker
   participant "Motor de Regras" as Engine
   database "PostgreSQL" as DB

   User -> View : "Executar Auditoria (Produção)"
   View -> Redis : enqueue(executar_regras_producao)

   Redis -> Worker : consumir tarefa
   activate Worker

   Worker -> Engine : carregar lista de 28 regras

   loop Para cada regra
       Engine -> DB : SELECT COUNT(*)
       Engine -> DB : SELECT WHERE condição_falha
       DB --> Engine : registros irregulares

       Engine -> Engine : calcular conformidade
       Engine -> DB : INSERT RelatorioAnaliseRelacional
   end

   Worker -> Worker : calcular DQI

   note right
      DQI = 0.3*C + 0.3*K + 0.2*V + 0.2*U
   end note

   Worker -> DB : INSERT RelatorioDQI
   deactivate Worker

   User -> View : Recarregar Dashboard
   View -> DB : SELECT relatórios recentes
   View --> User : Renderizar Dashboard

   @enduml
