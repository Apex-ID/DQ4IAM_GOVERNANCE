Diagrama de Implantação (Infraestrutura Física)
===============================================

.. uml::

   @startuml
   !theme plain
   skinparam linetype ortho
   title Implantação Física — APEX GOVERNANCE

   node "Servidor de Aplicação (Linux) - App Server" as LinuxNode {
       component "Django (Gunicorn / Uvicorn)" as Django
       component "Celery Workers" as Celery
       queue "Redis (Broker)" as Redis
       folder "Static / Media" as Static
   }

   node "Servidor de Banco (Windows / DB Server)" as WinNode {
       database "PostgreSQL 16" as Postgres
   }

   node "Agente na Rede (Windows Service)" as AgentNode {
       [Agente AD Monitor] as AgentService
   }

   node "Infraestrutura Corporativa" as Corp {
       [Active Directory (Domain Controller)] as AD
   }

   ' Conexões principais
   LinuxNode --> WinNode : TCP/IP (5432) - conexões DB
   LinuxNode --> Redis : TCP/IP (6379) - broker
   AgentNode --> LinuxNode : HTTPS (443) / API POST /api/auditoria/
   AgentNode --> AD : Leitura local / Event Viewer
   LinuxNode --> Corp : LDAP/LDAPS (389/636) - leitura AD (quando aplicável)

   ' Observações de implantação
   note left of LinuxNode
     App Server:
     • Ubuntu 24.04 LTS
     • Gunicorn/Uvicorn + Nginx
     • Celery workers (auto-scale via systemd / supervisor)
   end note

   note right of WinNode
     DB Server:
     • Windows 10/Server
     • PostgreSQL 16 (standalone / replica opcional)
   end note

   note bottom: Backup / Snapshot schedule, Firewall rules, TLS mutual auth (agent ↔ API)
   @enduml
