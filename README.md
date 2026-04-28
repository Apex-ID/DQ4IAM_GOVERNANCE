# 🛡️ DQ4IAM Governance - Plataforma de Governança de Identidade e Qualidade de Dados (IGA)

> **Projeto de Trabalho de Conclusão de Curso (TCC)**
> **Instituição:** Universidade Federal de Sergipe (UFS)
> **Domínio:** Governança de TI, Gestão de Identidade (IAM) e Qualidade de Dados.

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![Django](https://img.shields.io/badge/Django-5.0-green?style=for-the-badge&logo=django)
![Celery](https://img.shields.io/badge/Celery-Async-orange?style=for-the-badge&logo=celery)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Relational-blue?style=for-the-badge&logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-Broker-red?style=for-the-badge&logo=redis)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple?style=for-the-badge&logo=bootstrap)

---

## 📑 Sumário
1. [Contextualização e Motivação (TCC)](#-contextualização-e-motivação-tcc)
2. [Arquitetura do Sistema](#-arquitetura-do-sistema)
3. [Módulos e Funcionalidades Detalhadas](#-módulos-e-funcionalidades-detalhadas)
    - [Gestão de Identidade (Core IGA)](#31-módulo-de-gestão-de-identidade-core-iga)
    - [Pipeline ETL e Staging](#32-pipeline-etl-e-staging)
    - [Gestão Organizacional (Organograma)](#33-módulo-de-gestão-organizacional)
    - [Melhoria Contínua e Incidentes](#34-módulo-de-melhoria-contínua)
    - [Análises e Métricas](#35-módulo-de-análises-e-métricas)
4. [Stack Tecnológico](#-stack-tecnológico)
5. [Guia de Instalação e Configuração](#-guia-de-instalação-e-configuração)
6. [Manual de Execução](#-manual-de-execução)
7. [Autor](#autor)

---

## 📖 Contextualização e Motivação (TCC)

Este software foi desenvolvido como artefato prático para o Trabalho de Conclusão de Curso, abordando a **desconexão entre os Sistemas de Gestão de Pessoas (RH/Acadêmico) e a Infraestrutura de TI (Active Directory)** em grandes instituições.

### O Problema de Pesquisa
Em ambientes universitários complexos como a UFS, a identidade de um usuário não é estática nem singular. Um indivíduo pode possuir múltiplos vínculos simultâneos (ex: Servidor Técnico que é aluno de Pós-Graduação e também atua como Professor Substituto).
Os scripts legados e processos manuais falham ao tratar essas nuances, gerando:
1.  **Contas Órfãs:** Usuários desligados que mantêm acesso.
2.  **Privilégios Incorretos:** Alunos com acesso de professor (ou vice-versa).
3.  **Estrutura de AD Caótica:** OUs (Unidades Organizacionais) que não refletem o organograma oficial.

### A Solução Proposta
O **DQ4IAM Governance** atua como uma camada de abstração e inteligência (Middleware de Governança). Ele ingere dados brutos, aplica regras de negócio hierárquicas e de prioridade, e gera um **"Golden Record" (Registro Dourado)** — uma versão única e higienizada da verdade digital do usuário, pronta para automatizar o Active Directory.

---

## 🏗️ Arquitetura do Sistema

O sistema utiliza uma arquitetura baseada em eventos e microsserviços lógicos dentro de um monólito modular (Modular Monolith), utilizando o padrão **MVT (Model-View-Template)**.

* **Camada de Ingestão:** Scripts Python/Pandas para leitura de CSVs e conexão LDAP com o AD.
* **Camada de Processamento Assíncrono:** Utiliza **Celery** com **Redis** (Message Broker) para desacoplar tarefas pesadas (ETL) da interface do usuário, garantindo alta performance mesmo processando milhares de registros.
* **Camada de Persistência:** PostgreSQL armazenando dados brutos (Staging), dados processados (Production) e logs de auditoria.
* **Camada de Apresentação:** Interface Web responsiva renderizada pelo Django Templates com Bootstrap 5.

---

## 📦 Módulos e Funcionalidades Detalhadas

O sistema é composto por diversas aplicações Django (`apps`), cada uma responsável por um domínio da governança:

### 3.1. Módulo de Gestão de Identidade (Core IGA)
O coração do sistema, responsável pela unificação de vínculos.
* **Consolidação Híbrida de Identidade:** Algoritmo heurístico que varre todos os vínculos de um CPF/Login (Técnico, Docente, Aluno, Terceirizado).
* **Sistema de Pesos Ponderados:** Resolve conflitos de atributos definindo a "Identidade Principal" baseada em hierarquia institucional (ex: *Docente (100) > Técnico (80) > Aluno (10)*).
* **Acumulação de Permissões (GGs):** Gera a lista de **Grupos de Governança** necessários. Se um usuário é Técnico e Aluno, ele herda as GGs de ambos os perfis.
* **Regex de Lotação Inteligente:** Extrai códigos de unidade (ex: `112406`) de strings não estruturadas vindas de sistemas legados para garantir o vínculo correto no organograma.

### 3.2. Pipeline ETL e Staging
Motor de processamento de dados.
* **Extração LDAP:** Conectores nativos para extração de Usuários, Computadores e Grupos do Active Directory.
* **Staging Area:** Tabelas temporárias que recebem os dados brutos, permitindo auditoria antes da transformação.
* **Tasks Assíncronas:**
    * `executar_pipeline_completo_task`: Orquestra todo o fluxo.
    * `importar_arquivos_existentes_task`: Permite reprocessamento (Replay) de dados históricos via CSV.

### 3.3. Módulo de Gestão Organizacional
Garante que a estrutura lógica de TI reflita a realidade administrativa.
* **Explorer do Organograma (Tree View):** Interface visual que renderiza a hierarquia da instituição (Pastas e Subpastas) utilizando lógica de *Materialized Path* (ex: `.605.18.144.` define a ancestralidade).
* **Gestão de De-Para:** Mapeamento entre Códigos Numéricos (Siape) e Siglas de Departamento (ex: 11040302 -> COSUP).
* **Exportação de Relatórios:** Geração de PDFs da estrutura hierárquica para fins de auditoria.

### 3.4. Módulo de Melhoria Contínua
Focado no ciclo PDCA (Plan-Do-Check-Act) da qualidade de dados.
* **Gestão de Incidentes de Dados:** Registro de anomalias encontradas durante o processo de ETL (ex: "Departamento não encontrado", "CPF duplicado").
* **Workflow de Resolução:** Interface para analistas de dados marcarem incidentes como "Investigando", "Resolvido" ou "Falso Positivo".
* **Auditoria de Correções:** Histórico de quem corrigiu o quê e quando.

### 3.5. Módulo de Análises e Métricas
Apps `analises_simples` e `analises_relacionais`.
* **Scorecard de Qualidade:** Dashboard que exibe métricas de Completude (campos vazios), Unicidade (duplicatas) e Conformidade (padrão de nomenclatura).
* **Análise Cruzada (Cross-Reference):** Compara a "Fonte da Verdade" (RH) com o "Ambiente Alvo" (AD) para identificar:
    * Contas no AD sem dono no RH (Contas Órfãs).
    * Contas no RH sem login no AD (Falha de Provisionamento).

---

## 🛠️ Stack Tecnológico

* **Linguagem:** Python 3.12+
* **Framework Web:** Django 5.0
* **Gerenciamento de Tarefas:** Celery 5.x
* **Broker de Mensagens:** Redis 7.x
* **Banco de Dados:** PostgreSQL 16 (Recomendado) ou SQLite (Dev)
* **Manipulação de Dados:** Pandas & NumPy
* **Conectividade LDAP:** ldap3
* **Frontend:** HTML5, CSS3, Bootstrap 5, FontAwesome 6

---

## 🐧 Guia de Instalação e Configuração

Este guia assume um ambiente Linux (Ubuntu/Debian ou WSL).

### 1. Preparação do Sistema Operacional
Instale as dependências de sistema necessárias:

sudo apt update
sudo apt install python3-pip python3-venv redis-server libpq-dev -y

---

2. Configuração do Redis
sudo service redis-server start
# Verifique se está rodando (deve responder PONG)
redis-cli ping

3. Clonagem e Ambiente Virtual


# Clone o repositório
git clone [https://github.com/seu-usuario/dq4iam-governance.git](https://github.com/seu-usuario/dq4iam-governance.git)
cd DQ4IAM-governance

# Crie o ambiente virtual
python3 -m venv dq4iamvirtual

# Ative o ambiente
source dq4iamvirtual/bin/activate


4. Instalação de Dependências Python

pip install --upgrade pip
pip install -r requirements.txt


5. Configuração de Variáveis de Ambiente (.env)

Crie um arquivo .env na raiz do projeto. Este arquivo não deve ser comitado no Git.

nano .env
Conteúdo do .env:

Ini, TOML

# Segurança
SECRET_KEY=sua_chave_secreta_super_segura_gerada_aleatoriamente
DEBUG=True

# Banco de Dados
DB_NAME=dq4iam_db
DB_USER=postgres
DB_PASS=sua_senha
DB_HOST=localhost
DB_PORT=5432

# Configuração do Celery/Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Configuração LDAP (Opcional em Dev)
AD_SERVER=ip_do_server_AD

AD_USER=dominio\usuario_servico

AD_PASSWORD=senha_do_ad

AD_SEARCH_BASE=DC=ufs,DC=br

6. Inicialização do Banco de Dados

# Cria as migrações iniciais e tabelas
python3 manage.py makemigrations

python3 manage.py migrate

# Cria o usuário administrador do sistema
python3 manage.py createsuperuser

▶️ Manual de Execução
Devido à arquitetura assíncrona, o sistema requer dois processos rodando simultaneamente em terminais separados.

Terminal 1: O Servidor Web (Interface)
Responsável por responder às requisições HTTP e servir o Painel.



# Certifique-se de estar com a venv ativada
source dq4iamvirtual/bin/activate
python3 manage.py runserver
Acesse em: http://127.0.0.1:8000/painel/

Terminal 2: O Worker (Processamento em Background)
Responsável por executar as tarefas de ETL, Consolidação de Identidade e Regras de Negócio.



# Certifique-se de estar com a venv ativada
source dq4iamvirtual/bin/activate

# Inicia o worker do Celery
celery -A dq4iam_project worker --loglevel=info


🧪 Fluxo de Teste Sugerido (Demo)

Acesse o Painel Web.

No card "Estrutura Organizacional", clique em Lista Plana e depois Importar CSV para carregar o organograma-ufs-2025.csv.

Volte ao Painel. No card "Pipeline de Identidade", clique em Upload CSV e carregue o arquivo de usuários (usuarios-vinculos.csv).

Ainda no fluxo de Identidade, clique em Processar.

Observe o Terminal 2 (Celery): Você verá os logs de execução processando os vínculos e calculando as GGs.

Clique em Visualizar para ver o Golden Record gerado, demonstrando a unificação dos usuários (ex: Técnico + Aluno consolidado).

Acesse o menu Incidentes para verificar se alguma anomalia foi detectada automaticamente.

## Autor: 
Sergio Santana dos Santos
Projeto Acadêmico conclusão de curso em SIstemas de Informação  - UFS, 2025