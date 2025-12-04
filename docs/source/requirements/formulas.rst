Formulas
========

Catálogo de Fórmulas e Métricas
===============================

Este documento detalha a matemática aplicada no motor de regras do **APEX GOVERNANCE**.

1. Fórmulas Implementadas
-------------------------

A. Índice de Qualidade de Dados (DQI)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

O DQI é um KPI composto que pondera as quatro dimensões principais. É calculado separadamente para Staging e Produção.

.. math::

   DQI = (0.3 \times C) + (0.3 \times K) + (0.2 \times V) + (0.2 \times U)

Onde:

* **C (Completude):** Média de preenchimento dos campos obrigatórios.  
* **K (Consistência):** Média de aprovação das 20 últimas regras de negócio executadas.  
* **V (Validade):** Conformidade com formatos (ex.: UPN, tipos de dados).  
* **U (Unicidade):** Taxa de registros únicos vs. duplicados.

B. Unicidade Composta
~~~~~~~~~~~~~~~~~~~~~

Utilizada na análise personalizada e na detecção de clones.

.. math::

   \text{Unicidade \%} =
   \left( \frac{\text{Contagem de Tuplas Distintas}}{\text{Total de Linhas}} \right) \times 100

C. Risco de Obsolescência (Temporalidade)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Utilizada para classificar ativos de risco.

* **Inativo:** ``Data Atual - lastLogonTimestamp > 90 dias``  
* **Senha Crítica:** ``Data Atual - pwdLastSet > 365 dias``

2. Análise de Lacunas (O que faltou?)
-------------------------------------

Apesar da cobertura abrangente, as seguintes fórmulas matemáticas avançadas do DAMA não foram implementadas nesta versão:

1. **Taxa de Decaimento da Informação (Information Decay Rate):**  
   *O que é:* Estima a perda de validade dos dados ao longo do tempo (ex.: telefone muda a cada 2 anos).  
   *Por que faltou:* O AD não guarda histórico de alterações, impossibilitando séries temporais.

2. **Custo do Dado de Má Qualidade:**  
   *O que é:* Converte erro operacional em prejuízo financeiro (ex.: usuários inativos × custo de licença).  
   *Por que faltou:* O sistema não possui acesso a tabelas financeiras ou de licenciamento.

3. **Precisão Sintática (Syntactic Accuracy):**  
   *O que é:* Compara o dado com fonte externa confiável (ex.: CPF na Receita Federal).  
   *Por que faltou:* Escopo restrito aos dados internos; sem integrações com APIs externas.

==============================================================================
5. DIMENSÃO: REGRAS DE NEGÓCIO E AUDITORIA (SQL ENGINE)
==============================================================================

Diferente das métricas simples, estas regras são **binárias por registro (Passa/Falha)**.  
O sistema executa **33 regras distintas** divididas em 5 grupos.

Fórmula Geral do Indicador
--------------------------

.. math::

   \% \text{Conformidade} =
   \left(1 - \frac{\text{Total de Registros com Falha}}
   {\text{Total de Registros da Tabela}} \right) \times 100

Abaixo, a lógica técnica de detecção de falha para cada regra.

-------------------------------------------------------------------------------
GRUPO A: COMPLETUDE (Campos Obrigatórios de Negócio)
-------------------------------------------------------------------------------

1. **Usuários sem Gerente**  
   ``manager`` é nulo ou vazio.

2. **Usuários sem Departamento**  
   ``department`` é nulo ou vazio.

3. **Usuários sem Cargo (title)**  
   ``title`` é nulo ou vazio.

4. **Contato Incompleto**  
   ``mail`` **ou** ``telephoneNumber`` nulos ou vazios.

5. **Computadores sem Dono**  
   ``managedBy`` nulo ou vazio.

6. **Computadores sem Descrição**  
   ``description`` nulo ou vazio.

7. **Grupos sem Dono**  
   ``managedBy`` nulo ou vazio.

8. **Grupos sem Descrição**  
   ``description`` nulo ou vazio.

9. **OUs sem Descrição**  
   ``description`` nulo ou vazio.

10. **OUs sem Políticas (GPO)**  
    ``gPLink`` nulo ou vazio.

-------------------------------------------------------------------------------
GRUPO B: TEMPORALIDADE E HIGIENE (Dados Obsoletos)
-------------------------------------------------------------------------------

11. **Usuários Inativos (>90 dias)**  
    ``DataAtual - lastLogonTimestamp > 90 dias``

12. **Usuários Nunca Logados**  
    ``lastLogonTimestamp`` nulo.

13. **Senha Expirada ou Antiga**  
    ``DataAtual - pwdLastSet > 180 dias``

14. **Computadores Inativos**  
    ``DataAtual - lastLogonTimestamp > 90 dias``

-------------------------------------------------------------------------------
GRUPO C: CONSISTÊNCIA E INTEGRIDADE (Relacional)
-------------------------------------------------------------------------------

15. **Gerente Inválido**  
     ``manager`` não existe em ``distinguishedName`` de nenhum usuário.

16. **Gerente Desabilitado**  
     Usuário ativo cujo gerente está desabilitado.

17. **Conta Desabilitada com Grupos**  
     Usuário desabilitado **com** grupos em ``memberOf``.

18. **Privilégio Elevado (adminCount)**  
     ``adminCount = 1``.

19. **Computador Órfão**  
     ``managedBy`` aponta para usuário inexistente.

20. **Grupos Aninhados (Nested)**  
     ``memberOf`` preenchido.

21. **Computador Fora de Padrão**  
     ``distinguishedName`` contém ``CN=Computers``.

22. **Grupos "Admin" Desprotegidos**  
     Nome contém “Admin”, mas ``adminCount`` é 0 ou nulo.

23. **Grupos Vazios**  
     ``member`` nulo ou vazio.

-------------------------------------------------------------------------------
GRUPO D: VALIDADE E CONFORMIDADE
-------------------------------------------------------------------------------

24. **UPN Fora do Padrão**  
     Sufixo do ``userPrincipalName`` diferente de ``@office.ufs.br``.

25. **Logon Legado Extenso**  
     ``sAMAccountName`` > 20 caracteres.

26. **Sistemas Operacionais Obsoletos**  
     ``operatingSystem`` não contém:  
     *Windows 10*, *11*, *Server 2016*, *2019*, *2022*.

-------------------------------------------------------------------------------
GRUPO E: ESTRUTURAL E UNICIDADE AVANÇADA
-------------------------------------------------------------------------------

27. **Ciclos Hierárquicos**  
     Detecção via SQL recursivo: gerente A → B e B → A.

28. **Padronização de Departamento**  
     Departamentos com < 3 ocorrências.

29. **Zombie Containers (OUs)**  
     OU sem usuários ativos **e** sem computadores ativos.

30–33. **Duplicidade de Linha (Clones)**  
     Agrupamento de todos os campos (exceto ID); ``count > 1`` indica duplicidade.

34. **E-mail Duplicado**  
     Mais de um usuário com o mesmo ``mail``.

35. **Nome Completo (CN) Duplicado**  
     Mais de um usuário com o mesmo ``cn``.

36. **Contas Admin Vinculadas (Shadow Accounts)**  
     Login de usuário contido no login de conta administrativa (ex.: ``joao`` ↔ ``adm.joao``).