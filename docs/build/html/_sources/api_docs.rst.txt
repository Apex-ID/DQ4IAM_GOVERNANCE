API REST (Backend Headless)
===========================

O APEX GOVERNANCE evoluiu para uma arquitetura desacoplada. Este módulo expõe os dados e funcionalidades do sistema via **JSON**, permitindo a conexão com interfaces modernas (como React, Vue ou Mobile).

Especificações Técnicas
=======================

* **Padrão:** RESTful
* **Formato de Dados:** JSON
* **Autenticação:** JWT (JSON Web Token)
* **Base URL:** ``/api/v1/``
* **Documentação Interativa:** Swagger UI / OpenAPI 3.0

.. note::
   Para visualizar a documentação interativa e testar as requisições em tempo real, acesse a rota:
   **http://localhost:8000/api/v1/docs/**

Autenticação (JWT)
------------------

Para acessar qualquer endpoint protegido, o cliente deve primeiro obter um token.

1. **Obter Token (Login):**
   * **POST** ``/api/v1/token/``
   * **Body:** ``{"username": "admin", "password": "..."}``
   * **Response:** ``{"access": "...", "refresh": "..."}``

2. **Usar Token:**
   Envie o cabeçalho em todas as requisições subsequentes:
   ``Authorization: Bearer <seu_token_access>``

Endpoints Principais
--------------------

Abaixo estão listados os principais controladores da API.

Dashboard & KPIs
^^^^^^^^^^^^^^^^

.. http:get:: /api/v1/dashboard/resumo/

   Retorna os indicadores consolidados para a tela inicial do Frontend.

   **Exemplo de Resposta:**

   .. code-block:: json

      {
        "dqi": {"score_total": 98.5, "score_completude": 100},
        "incidentes": {"pendentes": 12, "em_tratamento": 5},
        "status_sistema": "Operacional"
      }

Gestão de Incidentes
^^^^^^^^^^^^^^^^^^^^

.. http:get:: /api/v1/incidentes/

   Lista todos os incidentes de qualidade detectados. Suporta filtros via query params (ex: ``?status=PENDENTE``).

.. http:post:: /api/v1/incidentes/{id}/aprovar_excecao/

   Ação executada pelo Gerente para ignorar uma violação de regra, justificando como exceção de negócio.

   :param observacao: Texto justificando a aprovação.

Engenharia de Dados (ETL)
^^^^^^^^^^^^^^^^^^^^^^^^^

.. http:post:: /api/v1/pipeline/executar/

   Dispara o pipeline de extração e transformação do Active Directory em background (Celery).

   **Status Code:** 202 Accepted

Estrutura do Código (Views)
---------------------------

Abaixo, a documentação automática das Classes (Views) implementadas no Django Rest Framework.

.. automodule:: api.views
   :members:
   :undoc-members:
   :show-inheritance: