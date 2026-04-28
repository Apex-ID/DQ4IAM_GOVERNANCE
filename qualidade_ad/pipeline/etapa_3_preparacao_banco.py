# Dentro de: qualidade_ad/pipeline/etapa_3_preparacao_banco.py

import psycopg2
import os
import subprocess
import sys
from dotenv import load_dotenv
import traceback
from django.utils import timezone
from qualidade_ad.models import LogEtapa
import logging

logger = logging.getLogger(__name__)

# Nomes de todas as tabelas que vamos criar
TABLE_NAMES = [
    "ad_users_staging", "ad_computers_staging", "ad_groups_staging", "ad_ous_staging",
    "ad_users", "ad_computers", "ad_groups", "ad_ous",
    "etl_error_log"
]

# Dicionário com todos os comandos SQL para criar as tabelas
SQL_COMMANDS = {
    # --- TABELAS DE STAGING (Tudo como TEXT, com id SERIAL PK) ---
    "ad_users_staging": """
        CREATE TABLE ad_users_staging (
            id SERIAL PRIMARY KEY, "accountExpires" TEXT, "adminCount" TEXT, "badPasswordTime" TEXT, "badPwdCount" TEXT, "c" TEXT, "cn" TEXT, "co" TEXT, "codePage" TEXT, "company" TEXT, "countryCode" TEXT, "dSCorePropagationData" TEXT, "department" TEXT, "description" TEXT, "directReports" TEXT, "displayName" TEXT, "distinguishedName" TEXT, "division" TEXT, "facsimileTelephoneNumber" TEXT, "givenName" TEXT, "homePhone" TEXT, "info" TEXT, "initials" TEXT, "instanceType" TEXT, "ipPhone" TEXT, "isCriticalSystemObject" TEXT, "lastKnownParent" TEXT, "lastLogoff" TEXT, "lastLogon" TEXT, "lastLogonTimestamp" TEXT, "lockoutTime" TEXT, "logonCount" TEXT, "logonHours" TEXT, "mS-DS-ConsistencyGuid" TEXT, "mail" TEXT, "managedObjects" TEXT, "manager" TEXT, "memberOf" TEXT, "mobile" TEXT, "msDS-FailedInteractiveLogonCount" TEXT, "msDS-FailedInteractiveLogonCountAtLastSuccessfulLogon" TEXT, "msDS-LastFailedInteractiveLogonTime" TEXT, "msDS-LastKnownRDN" TEXT, "msDS-LastSuccessfulInteractiveLogonTime" TEXT, "msDS-SupportedEncryptionTypes" TEXT, "msNPAllowDialin" TEXT, "name" TEXT, "objectCategory" TEXT, "objectClass" TEXT, "objectGUID" TEXT, "objectSid" TEXT, "pager" TEXT, "physicalDeliveryOfficeName" TEXT, "primaryGroupID" TEXT, "pwdLastSet" TEXT, "sAMAccountName" TEXT, "sAMAccountType" TEXT, "scriptPath" TEXT, "servicePrincipalName" TEXT, "showInAdvancedViewOnly" TEXT, "sn" TEXT, "streetAddress" TEXT, "telephoneNumber" TEXT, "thumbnailPhoto" TEXT, "title" TEXT, "uSNChanged" TEXT, "uSNCreated" TEXT, "uid" TEXT, "uidNumber" TEXT, "unixUserPassword" TEXT, "userAccountControl" TEXT, "userCertificate" TEXT, "userParameters" TEXT, "userPrincipalName" TEXT, "userWorkstations" TEXT, "whenChanged" TEXT, "whenCreated" TEXT
        );
    """,
    "ad_computers_staging": """
        CREATE TABLE ad_computers_staging (
            id SERIAL PRIMARY KEY, "accountExpires" TEXT, "adminCount" TEXT, "badPasswordTime" TEXT, "badPwdCount" TEXT, "cn" TEXT, "codePage" TEXT, "countryCode" TEXT, "dNSHostName" TEXT, "dSCorePropagationData" TEXT, "description" TEXT, "displayName" TEXT, "distinguishedName" TEXT, "instanceType" TEXT, "isCriticalSystemObject" TEXT, "lastLogoff" TEXT, "lastLogon" TEXT, "lastLogonTimestamp" TEXT, "localPolicyFlags" TEXT, "lockoutTime" TEXT, "logonCount" TEXT, "mS-DS-CreatorSID" TEXT, "managedBy" TEXT, "memberOf" TEXT, "msDFSR-ComputerReferenceBL" TEXT, "msDS-GroupMSAMembership" TEXT, "msDS-HostServiceAccount" TEXT, "msDS-HostServiceAccountBL" TEXT, "msDS-KeyCredentialLink" TEXT, "msDS-ManagedPasswordId" TEXT, "msDS-ManagedPasswordInterval" TEXT, "msDS-ManagedPasswordPreviousId" TEXT, "msDS-SupportedEncryptionTypes" TEXT, "name" TEXT, "netbootSCPBL" TEXT, "networkAddress" TEXT, "objectCategory" TEXT, "objectClass" TEXT, "objectGUID" TEXT, "objectSid" TEXT, "operatingSystem" TEXT, "operatingSystemServicePack" TEXT, "operatingSystemVersion" TEXT, "primaryGroupID" TEXT, "pwdLastSet" TEXT, "rIDSetReferences" TEXT, "sAMAccountName" TEXT, "sAMAccountType" TEXT, "serverReferenceBL" TEXT, "servicePrincipalName" TEXT, "uSNChanged" TEXT, "uSNCreated" TEXT, "userAccountControl" TEXT, "userCertificate" TEXT, "whenChanged" TEXT, "whenCreated" TEXT
        );
    """,
    "ad_groups_staging": """
        CREATE TABLE ad_groups_staging (
            id SERIAL PRIMARY KEY, "adminCount" TEXT, "cn" TEXT, "dSCorePropagationData" TEXT, "description" TEXT, "distinguishedName" TEXT, "groupType" TEXT, "instanceType" TEXT, "isCriticalSystemObject" TEXT, "managedBy" TEXT, "managedObjects" TEXT, "member" TEXT, "memberOf" TEXT, "name" TEXT, "objectCategory" TEXT, "objectClass" TEXT, "objectGUID" TEXT, "objectSid" TEXT, "sAMAccountName" TEXT, "sAMAccountType" TEXT, "systemFlags" TEXT, "uSNChanged" TEXT, "uSNCreated" TEXT, "whenChanged" TEXT, "whenCreated" TEXT
        );
    """,
    "ad_ous_staging": """
        CREATE TABLE ad_ous_staging (
            id SERIAL PRIMARY KEY, "dSCorePropagationData" TEXT, "description" TEXT, "displayName" TEXT, "distinguishedName" TEXT, "gPLink" TEXT, "gPOptions" TEXT, "instanceType" TEXT, "isCriticalSystemObject" TEXT, "managedBy" TEXT, "name" TEXT, "objectCategory" TEXT, "objectClass" TEXT, "objectGUID" TEXT, "ou" TEXT, "showInAdvancedViewOnly" TEXT, "systemFlags" TEXT, "uSNChanged" TEXT, "uSNCreated" TEXT, "whenChanged" TEXT, "whenCreated" TEXT
        );
    """,
    
    # --- TABELAS DE PRODUÇÃO (Tipos Corretos, com id SERIAL PK) ---
    "ad_users": """
        CREATE TABLE ad_users (
            id SERIAL PRIMARY KEY, "accountExpires" TIMESTAMPTZ, "adminCount" INTEGER, "badPasswordTime" TIMESTAMPTZ, "badPwdCount" INTEGER, "c" VARCHAR(255), "cn" VARCHAR(255), "co" VARCHAR(255), "codePage" INTEGER, "company" VARCHAR(255), "countryCode" INTEGER, "dSCorePropagationData" TEXT, "department" VARCHAR(255), "description" TEXT, "directReports" TEXT, "displayName" VARCHAR(255), "distinguishedName" TEXT, "division" VARCHAR(255), "facsimileTelephoneNumber" VARCHAR(255), "givenName" VARCHAR(255), "homePhone" VARCHAR(255), "info" TEXT, "initials" VARCHAR(255), "instanceType" INTEGER, "ipPhone" VARCHAR(255), "isCriticalSystemObject" BOOLEAN, "lastKnownParent" TEXT, "lastLogoff" TIMESTAMPTZ, "lastLogon" TIMESTAMPTZ, "lastLogonTimestamp" TIMESTAMPTZ, "lockoutTime" TIMESTAMPTZ, "logonCount" INTEGER, "logonHours" BYTEA, "mS-DS-ConsistencyGuid" TEXT, "mail" VARCHAR(255), "managedObjects" TEXT, "manager" TEXT, "memberOf" TEXT, "mobile" VARCHAR(255), "msDS-FailedInteractiveLogonCount" INTEGER, "msDS-FailedInteractiveLogonCountAtLastSuccessfulLogon" INTEGER, "msDS-LastFailedInteractiveLogonTime" TIMESTAMPTZ, "msDS-LastKnownRDN" TEXT, "msDS-LastSuccessfulInteractiveLogonTime" TIMESTAMPTZ, "msDS-SupportedEncryptionTypes" INTEGER, "msNPAllowDialin" BOOLEAN, "name" VARCHAR(255), "objectCategory" TEXT, "objectClass" TEXT, "objectGUID" UUID, "objectSid" VARCHAR(255), "pager" VARCHAR(255), "physicalDeliveryOfficeName" VARCHAR(255), "primaryGroupID" INTEGER, "pwdLastSet" TIMESTAMPTZ, "sAMAccountName" VARCHAR(255), "sAMAccountType" INTEGER, "scriptPath" TEXT, "servicePrincipalName" TEXT, "showInAdvancedViewOnly" BOOLEAN, "sn" VARCHAR(255), "streetAddress" TEXT, "telephoneNumber" VARCHAR(255), "thumbnailPhoto" BYTEA, "title" VARCHAR(255), "uSNChanged" BIGINT, "uSNCreated" BIGINT, "uid" VARCHAR(255), "uidNumber" INTEGER, "unixUserPassword" TEXT, "userAccountControl" INTEGER, "userCertificate" TEXT, "userParameters" TEXT, "userPrincipalName" VARCHAR(255), "userWorkstations" TEXT, "whenChanged" TIMESTAMPTZ, "whenCreated" TIMESTAMPTZ
        );
    """,
    "ad_computers": """
        CREATE TABLE ad_computers (
            id SERIAL PRIMARY KEY, "accountExpires" TIMESTAMPTZ, "adminCount" INTEGER, "badPasswordTime" TIMESTAMPTZ, "badPwdCount" INTEGER, "cn" VARCHAR(255), "codePage" INTEGER, "countryCode" INTEGER, "dNSHostName" VARCHAR(255), "dSCorePropagationData" TIMESTAMPTZ, "description" TEXT, "displayName" VARCHAR(255), "distinguishedName" TEXT, "instanceType" INTEGER, "isCriticalSystemObject" BOOLEAN, "lastLogoff" TIMESTAMPTZ, "lastLogon" TIMESTAMPTZ, "lastLogonTimestamp" TIMESTAMPTZ, "localPolicyFlags" INTEGER, "lockoutTime" TIMESTAMPTZ, "logonCount" INTEGER, "mS-DS-CreatorSID" TEXT, "managedBy" TEXT, "memberOf" TEXT, "msDFSR-ComputerReferenceBL" TEXT, "msDS-GroupMSAMembership" TEXT, "msDS-HostServiceAccount" TEXT, "msDS-HostServiceAccountBL" TEXT, "msDS-KeyCredentialLink" TEXT, "msDS-ManagedPasswordId" TEXT, "msDS-ManagedPasswordInterval" TEXT, "msDS-ManagedPasswordPreviousId" TEXT, "msDS-SupportedEncryptionTypes" INTEGER, "name" VARCHAR(255), "netbootSCPBL" TEXT, "networkAddress" TEXT, "objectCategory" TEXT, "objectClass" TEXT, "objectGUID" UUID, "objectSid" VARCHAR(255), "operatingSystem" VARCHAR(255), "operatingSystemServicePack" VARCHAR(255), "operatingSystemVersion" VARCHAR(255), "primaryGroupID" INTEGER, "pwdLastSet" TIMESTAMPTZ, "rIDSetReferences" TEXT, "sAMAccountName" VARCHAR(255), "sAMAccountType" INTEGER, "serverReferenceBL" TEXT, "servicePrincipalName" TEXT, "uSNChanged" BIGINT, "uSNCreated" BIGINT, "userAccountControl" INTEGER, "userCertificate" TEXT, "whenChanged" TIMESTAMPTZ, "whenCreated" TIMESTAMPTZ
        );
    """,
    "ad_groups": """
        CREATE TABLE ad_groups (
            id SERIAL PRIMARY KEY, "adminCount" INTEGER, "cn" VARCHAR(255), "dSCorePropagationData" TIMESTAMPTZ, "description" TEXT, "distinguishedName" TEXT, "groupType" INTEGER, "instanceType" INTEGER, "isCriticalSystemObject" BOOLEAN, "managedBy" TEXT, "managedObjects" TEXT, "member" TEXT, "memberOf" TEXT, "name" VARCHAR(255), "objectCategory" TEXT, "objectClass" TEXT, "objectGUID" UUID, "objectSid" VARCHAR(255), "sAMAccountName" VARCHAR(255), "sAMAccountType" INTEGER, "systemFlags" INTEGER, "uSNChanged" BIGINT, "uSNCreated" BIGINT, "whenChanged" TIMESTAMPTZ, "whenCreated" TIMESTAMPTZ
        );
    """,
    "ad_ous": """
        CREATE TABLE ad_ous (
            id SERIAL PRIMARY KEY, "dSCorePropagationData" TEXT, "description" TEXT, "displayName" VARCHAR(255), "distinguishedName" TEXT, "gPLink" TEXT, "gPOptions" VARCHAR(255), "instanceType" INTEGER, "isCriticalSystemObject" BOOLEAN, "managedBy" TEXT, "name" VARCHAR(255), "objectCategory" TEXT, "objectClass" TEXT, "objectGUID" UUID, "ou" VARCHAR(255), "showInAdvancedViewOnly" BOOLEAN, "systemFlags" INTEGER, "uSNChanged" BIGINT, "uSNCreated" BIGINT, "whenChanged" TIMESTAMPTZ, "whenCreated" TIMESTAMPTZ
        );
    """,
    
    "etl_error_log": """
        CREATE TABLE etl_error_log (
            log_id SERIAL PRIMARY KEY,
            table_name VARCHAR(255),
            staging_row_id INTEGER,
            error_message TEXT,
            error_timestamp TIMESTAMPTZ DEFAULT NOW(),
            raw_data JSONB
        );
    """
}

def executar_preparacao_banco(execucao_id):
    """
    Executa a Etapa 3 (Preparação do Banco) e registra um LogEtapa.
    """
    etapa_nome = 'ETAPA_3_PREPARACAO_BANCO'
    timestamp_inicio = timezone.now()
    resumo_da_etapa = ""
    status_final = "SUCESSO"
    
    conn = None
    try:
        logger.info(f"  [Etapa 3] Iniciando preparação do Banco (Execução ID: {execucao_id})...")
        load_dotenv()
        
        logger.info(f"    -> Conectando ao banco de dados em {os.getenv('DB_HOST')}...")
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS')
        )
        cursor = conn.cursor()
        logger.info("    -> SUCESSO: Conexão com o PostgreSQL estabelecida.")

        logger.info("    -> Recriando as tabelas de dados e de log...")
        for table_name in TABLE_NAMES:
            logger.info(f"      - Processando tabela: '{table_name}'")
            cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;')
            cursor.execute(SQL_COMMANDS[table_name])
            
        conn.commit()
        logger.info("    -> SUCESSO: Tabelas de dados e de log recriadas.")

        logger.info("    -> Executando o Django 'migrate' para tabelas de relatório...")
        
        python_executable = os.path.join(sys.prefix, 'bin', 'python3')
        if not os.path.exists(python_executable):
             python_executable = os.path.join(sys.prefix, 'bin', 'python')
        
        # --- INÍCIO DA CORREÇÃO 1 ---
        # Corrigido: Usando 3 'dirname' para chegar na raiz do projeto (DQ4IAM_GOVERNANCE)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # --- FIM DA CORREÇÃO 1 ---
        manage_py_path = os.path.join(base_dir, 'manage.py')
        
        if not os.path.exists(manage_py_path):
            logger.error(f"ERRO: manage.py não encontrado em: {manage_py_path}")
            raise FileNotFoundError("manage.py não encontrado. Verifique o cálculo do base_dir.")

        result = subprocess.run(
            [python_executable, manage_py_path, "migrate"],
            capture_output=True, text=True, check=True, cwd=base_dir
        )
        logger.info(f"    -> Saída do migrate: {result.stdout}")
        logger.info("    -> SUCESSO: Tabelas do Django e de relatórios criadas/atualizadas.")
        
        resumo_da_etapa = f"Banco de dados preparado com sucesso. {len(TABLE_NAMES)} tabelas de dados recriadas. Migrações do Django executadas."

    except Exception as e:
        status_final = "FALHOU"
        resumo_da_etapa = f"ERRO CRÍTICO: {e}\n{traceback.format_exc()}"
        logger.error(f"  [Etapa 3] ERRO: {resumo_da_etapa}")
        if conn:
            conn.rollback()
        
        # --- INÍCIO DA CORREÇÃO 2 ---
        # Em vez de levantar 'e' (que é um CalledProcessError complexo),
        # levantamos uma nova Exceção simples que o Celery pode serializar.
        raise Exception(f"Falha na Etapa 3 (preparacao_banco): {e}")
        # --- FIM DA CORREÇÃO 2 ---
    
    finally:
        if conn is not None:
            if 'cursor' in locals() and cursor is not None:
                cursor.close()
            conn.close()
        
        timestamp_fim = timezone.now()
        try:
            LogEtapa.objects.create(
                execucao_id=execucao_id,
                etapa_nome=etapa_nome,
                status=status_final,
                timestamp_inicio=timestamp_inicio,
                timestamp_fim=timestamp_fim,
                resumo_execucao=resumo_da_etapa
            )
            logger.info(f"  [Etapa 3] Log de execução salvo no banco de dados.")
        except Exception as db_error:
            logger.critical(f"  [Etapa 3] ERRO CRÍTICO AO SALVAR LOG: {db_error}")

    return resumo_da_etapa