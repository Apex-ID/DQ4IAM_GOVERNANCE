Non Functional
==============

Requisitos Não Funcionais e Inversos
====================================

Requisitos Não Funcionais (RNF)
-------------------------------
Definem a qualidade e as restrições técnicas do sistema.

* **RNF001 - Processamento Assíncrono:** Todas as tarefas de análise e carga devem ser executadas em background (Celery/Redis) para não travar a interface.
* **RNF002 - Isolamento de Ambiente:** O sistema deve operar em ambiente Linux (devido à estabilidade do Celery fork), conectando-se remotamente ao AD (Windows).
* **RNF003 - Persistência Robusta:** Uso de PostgreSQL para garantir integridade transacional (ACID).
* **RNF004 - Auditoria Imutável:** Logs de auditoria (`AuditoriaAD`) não podem ser alterados ou excluídos pela interface.
* **RNF005 - Performance:** O sistema deve suportar a análise de tabelas com mais de 100.000 registros em menos de 5 minutos.

Requisitos Inversos (O que o sistema NÃO faz)
---------------------------------------------
Delimitações de escopo importantes para o TCC.

* **INV001 - Não é um IdM (Identity Manager):** O sistema **não** escreve diretamente no Active Directory. Ele apenas monitora e sugere correções. A escrita é responsabilidade dos técnicos.
* **INV002 - Não bloqueia o AD:** O sistema não atua "inline" no AD (não impede a criação de um usuário errado no momento da criação), ele atua "pós-evento" (detecta milissegundos depois e alerta).
* **INV003 - Não gerencia senhas:** O sistema não armazena nem reseta senhas, apenas analisa metadados de expiração (`pwdLastSet`).