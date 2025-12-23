Diagrama de Implantação (Infraestrutura Física)
===============================================

.. uml::

   @startuml
   !theme plain
   skinparam linetype ortho
   title Arquitetura Completa — Implantação Física + Componentes Lógicos

   ' ============================================================
   ' FRONTEND
   ' ============================================================
   node "Frontend Layer (Cliente)" as Front {
       [Navegador (Painel Django)] as BrowserOld
       [React App (Novo Painel)] as React
   }

   ' ============================================================
   ' SERVIDOR LINUX (BACKEND + CELERY + REDIS)
   ' ============================================================
   node "Servidor de Aplicação (Linux)" as LinuxNode {

       node "Backend Layer (Django)" as Backend {
           component "Django Core" as DjangoCore {
               [Views MVT] as MVT
               [API REST (DRF)] as API
               [Admin Panel] as Admin
           }
       }

       node "Execução Assíncrona" as Async {
           [Celery Workers] as Workers
           queue "Redis (Broker / Cache)" as Redis
       }

       folder "Static / Media" as Static
   }

   ' ============================================================
   ' SERVIDOR WINDOWS (POSTGRES)
   ' ============================================================
   node "Servidor de Banco (Windows)" as WinNode {
       database "PostgreSQL 16" as Postgres
   }

   ' ============================================================
   ' AGENTE DA REDE
   ' ============================================================
   node "Agente na Rede (Windows Service)" as AgentNode {
       [Agente AD Monitor] as AgentService
   }

   ' ============================================================
   ' INFRAESTRUTURA CORPORATIVA
   ' ============================================================
   node "Infraestrutura Corporativa" as Corp {
       [Active Directory (Domain Controller)] as AD
   }

   ' ============================================================
   ' FLUXOS E CONEXÕES
   ' ============================================================

   ' Frontend <-> Backend
   BrowserOld --> MVT : HTTP (HTML)
   React --> API : HTTPS (REST / JWT)

   ' Backend <-> DB
   MVT ..> Postgres : lê/escreve
   API ..> Postgres : lê/escreve
   Workers --> Postgres : ETL / Auditoria / Scorecard

   ' Backend <-> Redis
   MVT --> Redis : enqueue task
   API --> Redis : enqueue task
   Redis --> Workers : entrega tarefa

   ' Linux <-> Windows Server
   LinuxNode --> WinNode : TCP/IP 5432 (DB)

   ' Agente AD
   AgentService --> API : HTTPS 443 (POST /api/auditoria/)
   AgentService --> AD : leitura direta (Event Viewer)

   ' Backend <-> Active Directory
   DjangoCore --> AD : LDAP/LDAPS (389/636)

   ' Observações
   note left of LinuxNode
     App Server:
     • Ubuntu 24.04 LTS
     • Gunicorn/Uvicorn + Nginx
     • Celery workers (systemd/supervisor)
   end note

   note right of WinNode
     DB Server:
     • Windows Server
     • PostgreSQL 16 Standalone/Replica
   end note

   note bottom
     Segurança:
     • TLS entre Agente e API
     • Firewall restritivo entre Linux <-> Windows
     • Snapshots do DB e Backup incremental
   end note

   @enduml
