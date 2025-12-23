Sequence Governança Ativa (Tempo Real)
======================================

.. uml::

   @startuml
   !theme plain
   autonumber

   actor "Técnico AD" as Tech
   participant "Windows Server (AD)" as Windows
   participant "Agente Python" as Agent
   participant "API Django" as API
   participant "Signal (Observer)" as Signal
   database "AuditoriaAD" as LogDB
   database "Incidentes" as TicketDB

   Tech -> Windows : Cria Usuário (fora do padrão)
   Windows -> Windows : Gera Event Viewer

   Windows -> Agent : Novo evento detectado
   activate Agent
   Agent -> Agent : Formatar JSON
   Agent -> API : POST /api/auditoria/
   deactivate Agent

   activate API
   API -> LogDB : INSERT AuditoriaAD
   API -> Signal : post_save()
   activate Signal

   Signal -> LogDB : consultar evento
   Signal -> Signal : verificar regras

   alt Violação Detectada
       Signal -> TicketDB : INSERT Incidente(status="PENDENTE")
       Signal -> LogDB : UPDATE violou_regras=True
   end

   deactivate Signal
   API --> Agent : HTTP 201
   deactivate API

   @enduml
