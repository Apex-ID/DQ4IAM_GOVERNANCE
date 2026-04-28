from celery import shared_task
from sqlalchemy import create_engine, text
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import logging
import pandas as pd
from .models import HistoricoCarga

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def executar_criacao_schema_task(self, config):
    """
    Executa a criação física do banco de dados e das tabelas baseada no dicionário.
    
    config = {
        'nome_banco': 'dq4iam_producao',
        'criar_banco': True/False,
        'nome_tabela': 'ad_users',
        'colunas': [{'nome': 'cn', 'tipo': 'VARCHAR(255)'}, ...]
    }
    """
    nome_banco = config['nome_banco']
    criar_banco = config.get('criar_banco', False)
    nome_tabela = config['nome_tabela']
    colunas = config['colunas']

    # Credenciais do Admin (Do .env)
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_host = os.getenv('DB_HOST')
    
    log_msgs = []

    try:
        # ETAPA 1: GERENCIAMENTO DO BANCO DE DADOS 
        # Conecta no banco 'postgres' (padrão) para poder criar outros bancos
        conn_admin = psycopg2.connect(
            user=db_user, password=db_pass, host=db_host, dbname='postgres'
        )
        conn_admin.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT) # Necessário para CREATE DATABASE
        cursor = conn_admin.cursor()
        
        # Verifica se o banco alvo existe
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{nome_banco}'")
        existe = cursor.fetchone()
        
        if criar_banco:
            if not existe:
                logger.info(f"[DDL] Criando banco de dados: {nome_banco}")
                cursor.execute(f'CREATE DATABASE "{nome_banco}"')
                log_msgs.append(f"Banco '{nome_banco}' criado com sucesso.")
            else:
                log_msgs.append(f"Banco '{nome_banco}' já existia. Usando ele.")
        elif not existe:
            return {'estado': 'FALHOU', 'mensagem': f"O banco '{nome_banco}' não existe e a opção de criar não foi marcada."}
            
        cursor.close()
        conn_admin.close()

        # ETAPA 2: CRIAÇÃO DA TABELA 
        logger.info(f"[DDL] Conectando em {nome_banco} para criar tabela {nome_tabela}...")
        
        # Conecta no banco ALVO
        target_db_url = f"postgresql://{db_user}:{db_pass}@{db_host}/{nome_banco}"
        engine = create_engine(target_db_url)

        # Monta o SQL DDL Dinamicamente
        # 1. Adiciona ID automático como PK
        definicoes_colunas = ['id SERIAL PRIMARY KEY']
        
        # 2. Adiciona colunas do dicionário
        for col in colunas:
            # Sanitização básica para evitar SQL Injection direto nos nomes
            c_nome = col['nome'].replace('"', '').replace("'", "") 
            c_tipo = col['tipo'] 
            
            definicoes_colunas.append(f'"{c_nome}" {c_tipo}')
            
        # 3. Adiciona colunas de controle de auditoria
        definicoes_colunas.append('"metadata_data_carga" TIMESTAMPTZ DEFAULT NOW()')
        definicoes_colunas.append('"metadata_origem" VARCHAR(100) DEFAULT \'Dicionario\'')

        sql_create = f"""
            CREATE TABLE IF NOT EXISTS "{nome_tabela}" (
                {', '.join(definicoes_colunas)}
            );
        """

        with engine.connect() as connection:
            connection.execute(text(sql_create))
            connection.commit()
            
        log_msgs.append(f"Tabela '{nome_tabela}' criada/atualizada com {len(colunas)} campos de negócio.")
        
        return {'estado': 'CONCLUÍDO', 'mensagem': " | ".join(log_msgs)}

    except Exception as e:
        logger.error(f"[DDL] Erro Crítico: {e}", exc_info=True)
        return {'estado': 'FALHOU', 'mensagem': f"Erro técnico: {str(e)}"}
    
@shared_task(bind=True)
def executar_carga_mapeada_task(self, config):
    """
    Lê dados de Staging, renomeia colunas conforme mapa e insere no Banco Novo.
    config = {
        'origem': 'ad_users_staging',
        'banco_destino': 'dq4iam_novo',
        'tabela_destino': 'ad_users',
        'mapeamento': {'cn': 'nome_completo', 'mail': 'email'}
    }
    """
    tabela_origem = config['origem']
    banco_destino = config['banco_destino']
    tabela_destino = config['tabela_destino']
    mapeamento = config['mapeamento'] 
    rename_map = {v: k for k, v in mapeamento.items() if v}
    colunas_origem_necessarias = list(rename_map.keys())

    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_host = os.getenv('DB_HOST')
    db_name_padrao = os.getenv('DB_NAME')

    logger.info(f"[ETL] Iniciando carga de {tabela_origem} para {banco_destino}.{tabela_destino}...")

    try:
        # 1. LER DADOS DA ORIGEM (Staging)
        # Conecta no banco padrão do Django
        url_origem = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name_padrao}"
        engine_origem = create_engine(url_origem)
        
        # Lê apenas as colunas que o usuário escolheu usar
        cols_sql = ", ".join([f'"{c}"' for c in colunas_origem_necessarias])
        query = f'SELECT {cols_sql} FROM "{tabela_origem}"'
        
        logger.info(f"[ETL] Lendo dados: {query}")
        df = pd.read_sql(query, engine_origem)
        
        # 2. TRANSFORMAÇÃO
        # Renomeia as colunas para os nomes da tabela de destino
        df.rename(columns=rename_map, inplace=True)
        
        # 3. CARGA NO DESTINO
        url_destino = f"postgresql://{db_user}:{db_pass}@{db_host}/{banco_destino}"
        engine_destino = create_engine(url_destino)
        
        with engine_destino.connect() as conn:
            # Usa to_sql com append. O mapeamento garante que os nomes batam.
            df.to_sql(
                tabela_destino, 
                conn, 
                if_exists='append', 
                index=False,        
                method='multi',
                chunksize=1000
            )
        total = len(df)
        msg = f"Sucesso! {total} registros migrados."
        
        # SALVA O LOG NO BANCO
        HistoricoCarga.objects.create(
            tabela_origem=tabela_origem,
            banco_destino=banco_destino,
            tabela_destino=tabela_destino,
            status='SUCESSO',
            mensagem=msg,
            total_linhas=total
        )
            
        return {'estado': 'CONCLUÍDO', 'mensagem': f"Sucesso! {len(df)} registros migrados para '{banco_destino}'."}

    except Exception as e:
        HistoricoCarga.objects.create(
            tabela_origem=tabela_origem,
            banco_destino=banco_destino,
            tabela_destino=tabela_destino,
            status='ERRO',
            mensagem=str(e),
            total_linhas=0
        )
        return {'estado': 'FALHOU', 'mensagem': str(e)}