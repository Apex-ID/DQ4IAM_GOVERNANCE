from celery import shared_task
from django.utils import timezone
import traceback
import logging
from sqlalchemy import create_engine, text
import os
import pandas as pd

# Importe TODOS os models
from .models import (
    RelatorioCompletude, RelatorioCompletudeGeral, 
    RelatorioValidadeFormato, RelatorioUnicidade, RelatorioUnicidadeGeral,
    RelatorioRegraNegocio, RelatorioUnicidadePersonalizada
)
# Importe as lógicas
from .logica_de_analise.logica_validade import executar_analise_de_validade
from .logica_de_analise.logica_unicidade import (
    analisar_unicidade_coluna, 
    analisar_unicidade_tabela_inteira, 
    analisar_unicidade_multicoluna
)
from .logica_de_analise.regras_negocio import REGRAS_DE_QUALIDADE

logger = logging.getLogger(__name__)

# --- TAREFAS DE COMPLETUDE ---
@shared_task(bind=True)
def executar_analise_completude_task(self):
    logger.info("[ANÁLISE] Iniciando Análise de Completude (Usuários)...")
    try:
        db_user = os.getenv('DB_USER')
        db_pass = os.getenv('DB_PASS')
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME')
        db_url = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
        engine = create_engine(db_url)

        with engine.connect() as connection:
            sql_query = text("""
            SELECT COUNT(*),
                COUNT(*) FILTER (WHERE "manager" IS NULL OR "manager" = ''),
                COUNT(*) FILTER (WHERE "department" IS NULL OR "department" = ''),
                COUNT(*) FILTER (WHERE "title" IS NULL OR "title" = ''),
                COUNT(*) FILTER (WHERE ("mail" IS NOT NULL AND "mail" != '') AND ("telephoneNumber" IS NOT NULL AND "telephoneNumber" != ''))
            FROM ad_users;
            """)
            result = connection.execute(sql_query).fetchone()
            
            if not result or result[0] == 0:
                return {'estado': 'FALHOU', 'mensagem': 'Tabela ad_users vazia.'}

            total, s_mgr, s_dept, s_title, contato = result
            t = total if total > 0 else 1
            
            RelatorioCompletude.objects.create(
                total_usuarios=total, sem_gerente=s_mgr, sem_departamento=s_dept, sem_cargo=s_title, contato_completo=contato,
                perc_sem_gerente=(s_mgr/t)*100, perc_sem_departamento=(s_dept/t)*100,
                perc_sem_cargo=(s_title/t)*100, perc_contato_completo=(contato/t)*100
            )
            return {'estado': 'CONCLUÍDO', 'mensagem': 'Análise de usuários concluída.'}
    except Exception as e:
        return {'estado': 'FALHOU', 'mensagem': str(e)}

@shared_task(bind=True)
def executar_analise_completude_geral_task(self):
    logger.info("[ANÁLISE GERAL] Iniciando...")
    try:
        db_user = os.getenv('DB_USER')
        db_pass = os.getenv('DB_PASS')
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME')
        db_url = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
        engine = create_engine(db_url)
        
        tabelas = ['ad_users_staging', 'ad_computers_staging', 'ad_groups_staging', 'ad_ous_staging']

        with engine.connect() as connection:
            for tb in tabelas:
                df = pd.read_sql_table(tb, connection)
                if df.empty: continue
                
                df.replace('', pd.NA, inplace=True)
                total_celulas = df.size
                preenchidas = df.count().sum()
                perc = (preenchidas / total_celulas) * 100 if total_celulas > 0 else 0
                
                vazias = df.isnull().sum()
                vazias_dict = {k: int(v) for k, v in vazias[vazias > 0].to_dict().items()}

                RelatorioCompletudeGeral.objects.create(
                    tabela_analisada=tb, total_registros=len(df), total_colunas=len(df.columns),
                    total_celulas=total_celulas, total_celulas_preenchidas=preenchidas,
                    percentual_completude_geral=perc, relatorio_colunas_vazias=vazias_dict
                )
        return {'estado': 'CONCLUÍDO', 'mensagem': 'Análise Geral concluída.'}
    except Exception as e:
        return {'estado': 'FALHOU', 'mensagem': str(e)}

# --- TAREFA DE VALIDADE ---
@shared_task(bind=True)
def executar_analise_validade_formato_task(self):
    logger.info("[ANÁLISE VALIDADE] Iniciando...")
    try:
        db_user = os.getenv('DB_USER')
        db_pass = os.getenv('DB_PASS')
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME')
        db_url = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
        engine = create_engine(db_url)
        
        tabelas = ['ad_users_staging', 'ad_computers_staging', 'ad_groups_staging', 'ad_ous_staging']

        with engine.connect() as connection:
            for tb in tabelas:
                df = pd.read_sql_table(tb, connection)
                if df.empty: continue
                
                res = executar_analise_de_validade(df)
                
                RelatorioValidadeFormato.objects.create(
                    tabela_analisada=tb,
                    total_celulas_preenchidas=res['total_celulas_preenchidas'],
                    total_celulas_invalidas=res['total_celulas_invalidas'],
                    total_celulas_vazias=res['total_celulas_vazias'],
                    percentual_validade=res['percentual_validade'],
                    detalhamento_erros=res['detalhamento_erros']
                )
        return {'estado': 'CONCLUÍDO', 'mensagem': 'Análise de Validade concluída.'}
    except Exception as e:
        return {'estado': 'FALHOU', 'mensagem': str(e)}

# --- TAREFAS DE UNICIDADE GERAL ---
def _executar_unicidade_geral(tabelas_alvo):
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    db_url = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
    engine = create_engine(db_url)

    with engine.connect() as connection:
        RelatorioUnicidadeGeral.objects.filter(tabela_analisada__in=tabelas_alvo).delete()
        
        for table_name in tabelas_alvo:
            logger.info(f"[ANÁLISE UNICIDADE] Processando tabela: {table_name}")
            try:
                df = pd.read_sql_table(table_name, connection)
            except Exception as e:
                logger.warning(f"Tabela {table_name} não encontrada: {e}")
                continue
            
            if df.empty: continue
            
            resultado = analisar_unicidade_tabela_inteira(df, table_name)
            
            RelatorioUnicidadeGeral.objects.create(
                tabela_analisada=table_name,
                total_registros=resultado['total_registros'],
                total_colunas_analisadas=resultado['total_colunas_analisadas'],
                media_unicidade=resultado['media_unicidade'],
                qtd_colunas_com_duplicatas=resultado['qtd_colunas_com_duplicatas'],
                detalhe_por_coluna=resultado['detalhe_por_coluna']
            )

@shared_task(bind=True)
def executar_analise_unicidade_staging_task(self):
    try:
        _executar_unicidade_geral(['ad_users_staging', 'ad_computers_staging', 'ad_groups_staging', 'ad_ous_staging'])
        return {'estado': 'CONCLUÍDO', 'mensagem': 'Unicidade Staging concluída.'}
    except Exception as e:
        logger.error(f"Falha Unicidade Staging: {e}", exc_info=True)
        return {'estado': 'FALHOU', 'mensagem': str(e)}

@shared_task(bind=True)
def executar_analise_unicidade_producao_task(self):
    try:
        _executar_unicidade_geral(['ad_users', 'ad_computers', 'ad_groups', 'ad_ous'])
        return {'estado': 'CONCLUÍDO', 'mensagem': 'Unicidade Produção concluída.'}
    except Exception as e:
        logger.error(f"Falha Unicidade Produção: {e}", exc_info=True)
        return {'estado': 'FALHOU', 'mensagem': str(e)}

# --- TAREFA DE UNICIDADE PERSONALIZADA ---
@shared_task(bind=True)
def executar_unicidade_personalizada_task(self, tabela_nome, colunas_lista):
    try:
        db_user = os.getenv('DB_USER')
        db_pass = os.getenv('DB_PASS')
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME')
        db_url = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
        engine = create_engine(db_url)

        with engine.connect() as connection:
            cols_sql = ", ".join([f'"{c}"' for c in colunas_lista])
            query = text(f'SELECT {cols_sql} FROM {tabela_nome}')
            
            df = pd.read_sql_query(query, connection)
            resultado = analisar_unicidade_multicoluna(df, colunas_lista)
            
            relatorio = RelatorioUnicidadePersonalizada.objects.create(
                tabela_analisada=tabela_nome,
                colunas_combinadas=", ".join(colunas_lista),
                total_registros=resultado['total_registros'],
                registros_unicos=resultado['registros_unicos'],
                registros_duplicados=resultado['registros_duplicados'],
                percentual_unicidade=resultado['percentual_unicidade'],
                exemplos_duplicatas=resultado['exemplos']
            )
            return {'estado': 'CONCLUÍDO', 'mensagem': f'Análise personalizada salva: Relatório #{relatorio.id}'}
    except Exception as e:
        logger.error(f"Falha na análise personalizada: {e}", exc_info=True)
        return {'estado': 'FALHOU', 'mensagem': str(e)}


# --- TAREFAS DE REGRAS DE NEGÓCIO (AS QUE FALTAVAM!) ---
def _executar_regras_generica(filtro_tipo):
    tipo_str = "STAGING" if filtro_tipo == 'staging' else "PRODUÇÃO"
    logger.info(f"[REGRAS {tipo_str}] Iniciando bateria de testes...")
    
    try:
        db_user = os.getenv('DB_USER')
        db_pass = os.getenv('DB_PASS')
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME')
        db_url = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
        engine = create_engine(db_url)

        with engine.connect() as connection:
            for regra in REGRAS_DE_QUALIDADE:
                tabelas_alvo = regra['tabelas_alvo']
                if filtro_tipo == 'staging':
                    tabelas_processar = [t for t in tabelas_alvo if t.endswith('_staging')]
                else:
                    tabelas_processar = [t for t in tabelas_alvo if not t.endswith('_staging')]

                for tabela in tabelas_processar:
                    logger.info(f"  -> Regra '{regra['nome']}' em '{tabela}'")
                    try:
                        # 1. Contar Total
                        total = connection.execute(text(f'SELECT COUNT(*) FROM {tabela}')).scalar()
                        if total == 0: continue

                        # 2. Contar Falhas
                        sql_falhas = text(f"SELECT COUNT(*) FROM {tabela} WHERE {regra['sql_filtro_falha']}")
                        falhas = connection.execute(sql_falhas).scalar()
                        
                        percentual = (falhas / total) * 100
                        
                        # --- NOVA LÓGICA: Buscar Exemplos ---
                        exemplos_json = []
                        if falhas > 0:
                            condicao = regra['sql_filtro_falha']
                            sql_exemplos = text(f'SELECT * FROM {tabela} WHERE {condicao} LIMIT 20')
                            df_exemplos = pd.read_sql_query(sql_exemplos, connection)
                            df_exemplos = df_exemplos.where(pd.notnull(df_exemplos), None)
                            
                            cols_desejadas = ['cn', 'sAMAccountName', 'distinguishedName', 'id', 'name', 'ou', 'description']
                            cols_existentes = [c for c in cols_desejadas if c in df_exemplos.columns]
                            if cols_existentes:
                                df_exemplos = df_exemplos[cols_existentes]
                            
                            exemplos_json = df_exemplos.to_dict(orient='records')
                        # ------------------------------------

                        RelatorioRegraNegocio.objects.create(
                            nome_regra=regra['nome'],
                            dimensao=regra['dimensao'],
                            tabela_analisada=tabela,
                            tipo_tabela=filtro_tipo.upper(),
                            qtd_total_registros=total,
                            qtd_falhas=falhas,
                            percentual_falha=percentual,
                            descricao_impacto=regra['impacto'],
                            exemplos_falhas=exemplos_json
                        )
                    except Exception as sql_err:
                        logger.error(f"Erro regra {regra['nome']}: {sql_err}")
                        continue

        return {'estado': 'CONCLUÍDO', 'mensagem': f'Regras de Negócio ({tipo_str}) concluídas.'}
    except Exception as e:
        logger.error(f"FALHA GERAL REGRAS: {e}", exc_info=True)
        return {'estado': 'FALHOU', 'mensagem': str(e)}

@shared_task(bind=True)
def executar_regras_staging_task(self):
    return _executar_regras_generica('staging')

@shared_task(bind=True)
def executar_regras_producao_task(self):
    return _executar_regras_generica('producao')