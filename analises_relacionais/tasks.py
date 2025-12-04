from celery import shared_task
from sqlalchemy import create_engine, text
import os
import pandas as pd
import logging
from django.conf import settings
from django.utils import timezone

# 1. Importa as listas de regras separadas (Staging vs Produção)
from .regras_staging import REGRAS_STAGING
from .regras_producao import REGRAS_PRODUCAO

# 2. Importa os models do próprio app
from .models import (
    RelatorioAnaliseRelacional, 
    RelatorioDQI, 
    RelatorioRiscoSenha,
    RelatorioScorecard
)

# 3. Importa a lógica do scorecard
from .logica_scorecard import gerar_scorecard_detalhado

# 4. Importa models de outros apps para o cálculo do DQI
from analises_simples.models import (
    RelatorioCompletudeGeral, 
    RelatorioValidadeFormato, 
    RelatorioUnicidadeGeral,
    RelatorioCompletude
)

logger = logging.getLogger(__name__)

# FUNÇÃO INTERNA (HELPER) - Executa uma lista de regras
def _executar_lista_regras(lista_regras, tipo_execucao):
    """
    Função genérica que recebe uma lista PRONTA de regras e executa.
    """
    logger.info(f"[RELACIONAL] Iniciando bateria: {tipo_execucao}")
    
    try:
        db_user = os.getenv('DB_USER')
        db_pass = os.getenv('DB_PASS')
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME')
        db_url = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
        engine = create_engine(db_url)

        with engine.connect() as connection:
            for regra in lista_regras:
                logger.info(f"  -> Regra: {regra['nome']}")
                
                # Transação isolada para cada regra
                trans = connection.begin()
                try:
                    # 1. Executa SQL de falhas
                    df_falhas = pd.read_sql_query(text(regra['sql']), connection)
                    qtd_falhas = len(df_falhas)
                    
                    # 2. Conta total (Tenta extrair tabela do SQL ou usa metadado)
                    if 'tabelas_alvo' in regra:
                        tabela_base = regra['tabelas_alvo'][0]
                    else:
                        tabela_base = regra.get('tabelas', '').split(' ')[0]
                    
                    try:
                        # Remove aliases se houver
                        tabela_limpa = tabela_base.split(' ')[0]
                        total = connection.execute(text(f'SELECT COUNT(*) FROM {tabela_limpa}')).scalar()
                    except: 
                        total = 0
                    
                    # 3. Calcula Percentual
                    pct = ((total - qtd_falhas) / total) * 100 if total > 0 else 100.0
                    
                    # 4. Prepara exemplos (Top 20)
                    exemplos = df_falhas.head(20).to_dict(orient='records')

                    # 5. Salva
                    RelatorioAnaliseRelacional.objects.create(
                        nome_analise=regra['nome'],
                        tabelas_envolvidas=tabela_base,
                        total_registros_analisados=total,
                        total_inconsistencias=qtd_falhas,
                        percentual_consistencia=pct,
                        descricao_impacto=regra['impacto'],
                        exemplos_inconsistencias=exemplos
                    )
                    trans.commit()
                except Exception as erro_regra:
                    trans.rollback()
                    logger.error(f"Erro regra {regra['nome']}: {erro_regra}")
                    continue

        return {'estado': 'CONCLUÍDO', 'mensagem': f'Análises ({tipo_execucao}) finalizadas.'}
    except Exception as e:
        return {'estado': 'FALHOU', 'mensagem': str(e)}


# TAREFAS PÚBLICAS (Auditoria de Regras)

@shared_task(bind=True)
def executar_analises_relacionais_task(self):
    """Compatibilidade: Roda regras de PRODUÇÃO por padrão."""
    return _executar_lista_regras(REGRAS_PRODUCAO, "PADRÃO (PRODUÇÃO)")

@shared_task(bind=True)
def executar_regras_staging_task(self):
    """Executa regras específicas de STAGING (SQL Blindado)."""
    return _executar_lista_regras(REGRAS_STAGING, "STAGING")

@shared_task(bind=True)
def executar_regras_producao_task(self):
    """Executa regras específicas de PRODUÇÃO (SQL Tipado)."""
    return _executar_lista_regras(REGRAS_PRODUCAO, "PRODUÇÃO")


# TAREFA DE MÉTRICAS AVANÇADAS (DQI e RISCO)
@shared_task(bind=True)
def executar_metricas_avancadas_task(self, tipo_analise='producao'):
    """
    Calcula o DQI (Data Quality Index) separado por ambiente.
    tipo_analise: 'staging' ou 'producao'
    """
    tipo_analise = tipo_analise.lower()
    ambiente_str = "STAGING" if tipo_analise == 'staging' else "PRODUÇÃO"
    
    logger.info(f"[DQI] Iniciando cálculo para {ambiente_str}...")
    
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    db_url = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
    engine = create_engine(db_url)

    try:
        # 1. ANÁLISE DE RISCO DE SENHA (Apenas em Produção)
        if tipo_analise == 'producao':
            try:
                with engine.connect() as connection:
                    sql_senha = text("""
                        SELECT 
                            COUNT(*) FILTER (WHERE "pwdLastSet" >= NOW() - INTERVAL '90 days') as verde,
                            COUNT(*) FILTER (WHERE "pwdLastSet" < NOW() - INTERVAL '90 days' AND "pwdLastSet" >= NOW() - INTERVAL '180 days') as amarela,
                            COUNT(*) FILTER (WHERE "pwdLastSet" < NOW() - INTERVAL '180 days' AND "pwdLastSet" >= NOW() - INTERVAL '1 year') as vermelha,
                            COUNT(*) FILTER (WHERE "pwdLastSet" < NOW() - INTERVAL '1 year') as critica,
                            COUNT(*) as total
                        FROM ad_users
                        WHERE "userAccountControl" IS NOT NULL AND (CAST("userAccountControl" AS INTEGER) & 2) = 0 
                    """)
                    result = connection.execute(sql_senha).fetchone()
                    
                    RelatorioRiscoSenha.objects.create(
                        faixa_verde_90dias=result[0], faixa_amarela_180dias=result[1],
                        faixa_vermelha_1ano=result[2], faixa_critica_velha=result[3], total_contas=result[4]
                    )
            except Exception as e_senha:
                logger.error(f"Erro Risco Senha: {e_senha}")

        # 2. CÁLCULO DO DQI (Separado por Ambiente)
        
        # A. COMPLETUDE
        if tipo_analise == 'staging':
            # Staging: Baseado em Células Vazias
            last_comp = RelatorioCompletudeGeral.objects.last()
            nota_completude = last_comp.percentual_completude_geral if last_comp else 0.0
        else:
            # Produção: Baseado no relatório de Negócio (Usuários)
            last_comp = RelatorioCompletude.objects.last()
            if last_comp:
                media_erros = (last_comp.perc_sem_gerente + last_comp.perc_sem_departamento) / 2
                nota_completude = 100 - media_erros
            else:
                nota_completude = 0.0

        # B. VALIDADE
        if tipo_analise == 'staging':
            last_val = RelatorioValidadeFormato.objects.last()
            nota_validade = last_val.percentual_validade if last_val else 0.0
        else:
            # Produção assume validade alta ou usa média de regras de validade
            nota_validade = 100.0 
        
        # C. UNICIDADE (Filtra pela tabela correta no nome)
        if tipo_analise == 'staging':
            last_uni = RelatorioUnicidadeGeral.objects.filter(tabela_analisada__endswith='_staging').order_by('id').last()
        else:
            last_uni = RelatorioUnicidadeGeral.objects.exclude(tabela_analisada__endswith='_staging').order_by('id').last()
        
        nota_unicidade = last_uni.media_unicidade if last_uni else 100.0
        
        # D. CONSISTÊNCIA (Filtra as regras executadas recentemente neste ambiente)
        if tipo_analise == 'staging':
            regras = RelatorioAnaliseRelacional.objects.filter(tabelas_envolvidas__contains='_staging').order_by('-timestamp_inicio')[:20]
        else:
            regras = RelatorioAnaliseRelacional.objects.exclude(tabelas_envolvidas__contains='_staging').order_by('-timestamp_inicio')[:20]

        if regras:
            soma = sum([r.percentual_consistencia for r in regras])
            nota_consistencia = soma / len(regras)
        else:
            nota_consistencia = 0.0

        # Fórmula Final Ponderada
        dqi_final = (0.3 * nota_completude) + (0.3 * nota_consistencia) + (0.2 * nota_validade) + (0.2 * nota_unicidade)

        RelatorioDQI.objects.create(
            tipo_ambiente=ambiente_str,
            score_total=dqi_final,
            score_completude=nota_completude,
            score_consistencia=nota_consistencia,
            score_validade=nota_validade,
            score_unicidade=nota_unicidade
        )

        return {'estado': 'CONCLUÍDO', 'mensagem': f'DQI ({ambiente_str}) calculado: {dqi_final:.1f}'}

    except Exception as e:
        return {'estado': 'FALHOU', 'mensagem': str(e)}


@shared_task(bind=True)
def executar_scorecard_completo_task(self, tipo_analise='producao'):
    """
    Gera o Scorecard (Relatório detalhado linha a linha) e salva CSV.
    """
    logger.info(f"[SCORECARD] Iniciando ({tipo_analise})...")
    
    try:
        db_user = os.getenv('DB_USER')
        db_pass = os.getenv('DB_PASS')
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME')
        db_url = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
        engine = create_engine(db_url)

        # 1. Contagem Real de Objetos
        total_real_objetos = 0
        tabelas_contagem = ['ad_users', 'ad_computers', 'ad_groups', 'ad_ous']
        if tipo_analise == 'staging':
            tabelas_contagem = [t + '_staging' for t in tabelas_contagem]
            
        with engine.connect() as connection:
            for t in tabelas_contagem:
                try:
                    c = connection.execute(text(f'SELECT COUNT(*) FROM {t}')).scalar()
                    total_real_objetos += c
                except: pass

        # 2. Gera o DataFrame com falhas
        df_resultado = gerar_scorecard_detalhado(engine, tipo_analise)
        
        # Variáveis padrão se vazio
        qtd_falhas = 0
        media_falhas = 0.0
        top_50 = []
        nome_arquivo = None

        if df_resultado is not None and not df_resultado.empty:
            qtd_falhas = len(df_resultado)
            media_falhas = df_resultado['qtd_erros'].mean()
            top_50 = df_resultado.head(50).to_dict(orient='records')

            # Salva CSV
            media_path = os.path.join(settings.BASE_DIR, 'media', 'scorecards')
            os.makedirs(media_path, exist_ok=True)
            timestamp_str = timezone.now().strftime('%Y%m%d_%H%M%S')
            nome_arquivo = f"scorecard_{tipo_analise}_{timestamp_str}.csv"
            caminho_completo = os.path.join(media_path, nome_arquivo)
            
            df_resultado.to_csv(caminho_completo, index=False, sep=';', encoding='utf-8-sig')

        # 3. Salva no Banco
        RelatorioScorecard.objects.create(
            arquivo_csv=nome_arquivo,
            total_objetos_analisados=total_real_objetos,
            total_objetos_com_falha=qtd_falhas,
            media_falhas_por_objeto=media_falhas,
            top_ofensores=top_50
        )

        return {'estado': 'CONCLUÍDO', 'mensagem': f'Scorecard ({tipo_analise}) gerado.'}

    except Exception as e:
        logger.error(f"Erro Scorecard: {e}", exc_info=True)
        return {'estado': 'FALHOU', 'mensagem': str(e)}