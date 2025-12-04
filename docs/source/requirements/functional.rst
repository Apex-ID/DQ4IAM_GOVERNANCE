Functional
==========

Requisitos Funcionais (RF)
==========================

O sistema atende às seguintes funcionalidades, divididas por módulos:

Módulo 1: Engenharia de Dados (ETL)
-----------------------------------
* **RF001 - Extração LDAP:** O sistema deve conectar-se ao AD e extrair metadados de Usuários, Grupos, Computadores e OUs.
* **RF002 - Staging Area:** O sistema deve armazenar dados brutos (texto) em tabelas intermediárias (`_staging`) antes do processamento.
* **RF003 - Transformação Tipada:** O sistema deve converter dados brutos para tipos fortes (Inteiro, Data, UUID) nas tabelas de Produção.
* **RF004 - Importação Dinâmica:** O sistema deve permitir o upload de CSVs arbitrários e criar tabelas no banco automaticamente ("God Mode").

Módulo 2: Qualidade de Dados (DAMA-DMBOK)
-----------------------------------------
* **RF005 - Análise de Completude:** Calcular o percentual de preenchimento de campos críticos (Geral e Específica).
* **RF006 - Validade de Formato:** Verificar se os dados atendem aos padrões de sintaxe (ex: Email, UPN, UUID).
* **RF007 - Unicidade:** Identificar duplicatas em chaves primárias e chaves compostas definidas pelo usuário.
* **RF008 - Consistência Relacional:** Validar integridade referencial (ex: Gerente existe? Grupo tem dono?).
* **RF009 - Cálculo de DQI:** Gerar um índice único (0-100) ponderado para Staging e Produção separadamente.

Módulo 3: Governança Ativa e Segurança
--------------------------------------
* **RF010 - Monitoramento via API:** Receber eventos JSON de agentes externos instalados nos servidores Windows.
* **RF011 - Detecção de Incidentes:** Analisar eventos em tempo real e abrir tickets automáticos se violarem regras.
* **RF012 - Painel de Gestão:** Interface para aprovação ou rejeição de incidentes por perfil de responsabilidade.
* **RF013 - Risco de Senha:** Gerar histograma de idade das senhas para análise de vulnerabilidade.

Módulo 4: Relatórios e Auditoria
--------------------------------
* **RF014 - Relatórios Oficiais:** Gerar PDFs formatados com cabeçalho, metodologia e evidências de falhas.
* **RF015 - Scorecard Individual:** Gerar CSV detalhado listando quais regras cada objeto específico violou.