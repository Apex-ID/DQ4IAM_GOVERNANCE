Domain Classes
==============

Modelo de Domínio (Conceitual)
==============================

O diagrama abaixo representa as entidades principais do domínio de governança de identidade.

.. uml::

   @startuml
   !theme plain
   hide empty members
   skinparam linetype ortho

   ' ============================================================
   ' PACOTE 1: DOMÍNIO CORPORATIVO (AD)
   ' ============================================================
   package "Domínio: Active Directory (Dados)" {

       entity "Tabelas Staging\n(Dados Brutos)" as Staging
       note right of Staging
         Todas as colunas são armazenadas como TEXT,
         representando o espelho bruto do AD.
       end note

       entity "Tabelas Produção\n(Dados Tipados)" as Prod
       note right of Prod
         Contém tipos fortes (INT, DATE, UUID),
         representando dados validados.
       end note
   }

   ' ============================================================
   ' PACOTE 2: MOTOR ETL & ENGENHARIA
   ' ============================================================
   package "Módulo: Engenharia de Dados (ETL)" {

       class ExecucaoPipeline <<Model>> {
           +id
           +timestamp_inicio
           +timestamp_fim
           +status
       }

       class LogEtapa <<Model>> {
           +etapa
           +status
           +registros_processados
           +mensagem_erro
       }

       class "ETL Service" <<Task>> {
           +extrair_ldap()
           +limpar_pandas()
           +carregar_staging()
           +transformar_producao()
       }

       ExecucaoPipeline "1" *-- "0..*" LogEtapa
       "ETL Service" ..> ExecucaoPipeline : registra
       "ETL Service" --> Staging : escreve
       "ETL Service" --> Prod : escreve
   }

   ' ============================================================
   ' PACOTE 3: IMPORTADOR & ARQUITETURA DINÂMICA
   ' ============================================================
   package "Módulo: Data Architect (Dinâmico)" {

       class MapeamentoCarga <<Model>> {
           +nome_mapeamento
           +tabela_origem
           +tabela_destino
           +mapa_colunas (JSON)
       }

       class HistoricoCarga <<Model>> {
           +data_execucao
           +status
           +total_linhas
       }

       class "ConstrutorSchema" <<Service>> {
           +ler_dicionario_docx()
           +criar_banco_ddl()
           +criar_tabela_ddl()
       }

       class "ImportadorCSV" <<Service>> {
           +upload_csv()
           +criar_banco_automatico()
       }

       MapeamentoCarga "1" -- "0..*" HistoricoCarga : gera
       "ConstrutorSchema" ..> Prod : cria DDL
       "ImportadorCSV" ..> Staging : cria DDL
   }

   ' ============================================================
   ' PACOTE 4: QUALIDADE DE DADOS
   ' ============================================================
   package "Módulo: Análises de Qualidade (DAMA)" {

       class RelatorioCompletude <<Model>>
       class RelatorioCompletudeGeral <<Model>>
       class RelatorioValidadeFormato <<Model>>
       class RelatorioUnicidadeGeral <<Model>>
       class RelatorioUnicidadePersonalizada <<Model>>

       class RelatorioRegraNegocio <<Model>>
       class RelatorioAnaliseRelacional <<Model>>

       class RelatorioRiscoSenha <<Model>>
       class RelatorioDQI <<Model>>
       class RelatorioScorecard <<Model>>

       class "MotorRegrasSQL" <<Service>> {
           +REGRAS_STAGING
           +REGRAS_PRODUCAO
           +executar_query()
       }

       "MotorRegrasSQL" ..> RelatorioRegraNegocio
       "MotorRegrasSQL" ..> RelatorioAnaliseRelacional

       RelatorioDQI ..> RelatorioCompletudeGeral : lê
       RelatorioDQI ..> RelatorioValidadeFormato : lê
       RelatorioDQI ..> RelatorioUnicidadeGeral : lê
       RelatorioDQI ..> RelatorioAnaliseRelacional : lê
   }

   @enduml