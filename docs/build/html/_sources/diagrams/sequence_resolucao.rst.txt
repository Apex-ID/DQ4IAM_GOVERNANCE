Sequence Resolução de Incidentes
================================

.. uml::

   @startuml
   !theme plain
   autonumber

   actor "Gerente de Governança" as Manager
   participant "PainelGestaoView" as View
   database "PostgreSQL" as DB

   Manager -> View : Acessa /gestao/
   View -> DB : SELECT incidentes pendentes
   View --> Manager : lista de incidentes

   Manager -> View : Abrir Incidente #123

   alt Rejeitar (erro do técnico)
       Manager -> View : Clica "Rejeitar"
       View -> DB : UPDATE status="REJEITADO"
   else Aprovar Exceção
       Manager -> View : Clica "Aprovar"
       View -> DB : UPDATE status="APROVADO"
   end

   View --> Manager : Confirmação "Salvo"

   @enduml
