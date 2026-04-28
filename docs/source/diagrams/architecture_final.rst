Arquitetura Geral do Sistema
===============================================


@startuml
left to right direction
skinparam componentStyle rectangle

actor "Usuario / Gestor" as User

package "Apresentacao HTTP" {
  component Browser
  component "Django Views / APIs" as DjangoView
}

package "Aplicacao / Servicos" {
  component IdentityService
  component OrgService
  component IncidentService
  component AnalyticsService
}

package "Dominio Django" {
  component qualidade_ad
  component construtor_schemas
  component melhoria_continua
  component analises_relacionais
}

package "Assincrono" {
  component Redis
  component "Celery Worker" as Worker
  component "Celery Beat" as Beat
}

package "Dados" {
  database PostgreSQL
  folder "File Storage"
}

package "Externos" {
  component "Active Directory"
  component "RH / SIGAA"
}

User --> Browser
Browser --> DjangoView

DjangoView --> IdentityService
DjangoView --> OrgService
DjangoView --> IncidentService
DjangoView --> AnalyticsService

IdentityService --> qualidade_ad
OrgService --> construtor_schemas
IncidentService --> melhoria_continua
AnalyticsService --> analises_relacionais

qualidade_ad --> PostgreSQL
construtor_schemas --> PostgreSQL
melhoria_continua --> PostgreSQL
analises_relacionais --> PostgreSQL

IdentityService ..> Redis
OrgService ..> Redis
Beat ..> Redis
Redis ..> Worker

Worker --> "Active Directory"
Worker --> "File Storage"
Worker --> PostgreSQL
"RH / SIGAA" --> "File Storage"

@enduml
