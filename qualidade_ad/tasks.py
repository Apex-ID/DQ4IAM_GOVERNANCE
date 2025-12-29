#qualidade_ad/tasks.py

import re
from celery import shared_task
from django.utils import timezone
import traceback
import logging
from django.db.models import Q

logger = logging.getLogger(__name__)

from .models import ExecucaoPipeline, LogEtapa, VinculoRH, IdentidadeConsolidada, DicionarioOrganograma
from .pipeline.etapa_1_extracao import executar_extracao_ad
from .pipeline.etapa_2_limpeza import executar_limpeza_csvs
from .pipeline.etapa_3_preparacao_banco import executar_preparacao_banco
from .pipeline.etapa_4_carga_staging import executar_carga_staging
from .pipeline.etapa_5_transformacao import executar_transformacao_e_carga

@shared_task(bind=True)
def executar_pipeline_completo_task(self):
    execucao = ExecucaoPipeline.objects.create(status='INICIADO')
    try:
        execucao.status = 'EM_PROGRESSO'
        execucao.save()
        
        logger.info(f"[Execução #{execucao.id}] INICIANDO ETAPA 1: Extração...")
        self.update_state(state='PROGRESS', meta={'passo_atual': 20, 'mensagem_status': 'Iniciando Etapa 1: Extração...'})
        executar_extracao_ad(execucao.id)

        logger.info(f"[Execução #{execucao.id}] INICIANDO ETAPA 2: Limpeza...")
        self.update_state(state='PROGRESS', meta={'passo_atual': 40, 'mensagem_status': 'Iniciando Etapa 2: Limpeza...'})
        executar_limpeza_csvs(execucao.id)

        logger.info(f"[Execução #{execucao.id}] INICIANDO ETAPA 3: Preparação do Banco...")
        self.update_state(state='PROGRESS', meta={'passo_atual': 60, 'mensagem_status': 'Iniciando Etapa 3: Preparação do Banco...'})
        executar_preparacao_banco(execucao.id)

        logger.info(f"[Execução #{execucao.id}] INICIANDO ETAPA 4: Carga Staging...")
        self.update_state(state='PROGRESS', meta={'passo_atual': 80, 'mensagem_status': 'Iniciando Etapa 4: Carga Staging...'})
        executar_carga_staging(execucao.id)

        logger.info(f"[Execução #{execucao.id}] INICIANDO ETAPA 5: Transformação...")
        self.update_state(state='PROGRESS', meta={'passo_atual': 100, 'mensagem_status': 'Iniciando Etapa 5: Transformação...'})
        executar_transformacao_e_carga(execucao.id)

        execucao.status = 'CONCLUIDO'
        execucao.timestamp_fim = timezone.now()
        execucao.save()
        
        logger.info(f"[Execução #{execucao.id}] Pipeline concluído com SUCESSO.")
        return {'estado': 'CONCLUÍDO', 'mensagem': f'Pipeline (Execução #{execucao.id}) concluído com sucesso!'}

    except Exception as e:
        logger.error(f"[Execução #{execucao.id}] FALHA CRÍTICA NO PIPELINE: {e}", exc_info=True)
        execucao.status = 'FALHOU'
        execucao.timestamp_fim = timezone.now()
        execucao.save()
        self.update_state(state='FAILURE', meta={'tipo_erro': type(e).__name__, 'mensagem_erro': str(e)})
        
        
        return {'estado': 'FALHOU', 'mensagem': f"Falha no pipeline: {e}"}
        # -------------------------------


@shared_task(bind=True)
def importar_arquivos_existentes_task(self):
    execucao = ExecucaoPipeline.objects.create(status='INICIADO')
    try:
        execucao.status = 'EM_PROGRESSO'
        execucao.save()

        logger.info(f"[Execução #{execucao.id}] INICIANDO ETAPA 2: Limpeza...")
        self.update_state(state='PROGRESS', meta={'passo_atual': 25, 'mensagem_status': 'Iniciando Etapa 2: Limpeza...'})
        executar_limpeza_csvs(execucao.id)

        logger.info(f"[Execução #{execucao.id}] INICIANDO ETAPA 3: Preparação do Banco...")
        self.update_state(state='PROGRESS', meta={'passo_atual': 50, 'mensagem_status': 'Iniciando Etapa 3: Preparação do Banco...'})
        executar_preparacao_banco(execucao.id)

        logger.info(f"[Execução #{execucao.id}] INICIANDO ETAPA 4: Carga Staging...")
        self.update_state(state='PROGRESS', meta={'passo_atual': 75, 'mensagem_status': 'Iniciando Etapa 4: Carga Staging...'})
        executar_carga_staging(execucao.id)

        logger.info(f"[Execução #{execucao.id}] INICIANDO ETAPA 5: Transformação...")
        self.update_state(state='PROGRESS', meta={'passo_atual': 100, 'mensagem_status': 'Iniciando Etapa 5: Transformação...'})
        executar_transformacao_e_carga(execucao.id)

        execucao.status = 'CONCLUIDO'
        execucao.timestamp_fim = timezone.now()
        execucao.save()
        logger.info(f"[Execução #{execucao.id}] Importação concluída com SUCESSO.")
        return {'estado': 'CONCLUÍDO', 'mensagem': f'Importação (Execução #{execucao.id}) concluída com sucesso!'}

    except Exception as e:
        logger.error(f"[Execução #{execucao.id}] FALHA CRÍTICA NA IMPORTAÇÃO: {e}", exc_info=True)
        execucao.status = 'FALHOU'
        execucao.timestamp_fim = timezone.now()
        execucao.save()
        self.update_state(state='FAILURE', meta={'tipo_erro': type(e).__name__, 'mensagem_erro': str(e)})
        
        
        return {'estado': 'FALHOU', 'mensagem': f"Falha na importação: {e}"}
        # -------------------------------

def consolidar_identidades():
    # 1. Limpar tabela de consolidação anterior
    IdentidadeConsolidada.objects.all().delete()
    
    # 2. Pegar todos os logins únicos
    logins_unicos = VinculoRH.objects.values_list('samaccountname', flat=True).distinct()
    
    identidades_para_criar = []
    
    for login in logins_unicos:
        # Pega todas as linhas desse usuário (Ex: as 6 linhas do aaronsena)
        vinculos = VinculoRH.objects.filter(samaccountname=login)
        
        # --- REGRA DE STATUS ---
        # Se tiver QUALQUER linha contendo "Ativo", ele é Ativo.
        vinculo_ativo = vinculos.filter(status_rh__icontains='ATIVO').first()
        
        if vinculo_ativo:
            status_final = 'ATIVO'
            vinculo_principal = vinculo_ativo # O vínculo ativo dita as regras
        else:
            status_final = 'INATIVO' # Aposentado, Concluído, etc.
            vinculo_principal = vinculos.first() # Pega o primeiro só para ter nome/dados
            
        # --- EXTRAÇÃO DO CÓDIGO DA LOTAÇÃO ---
        # Tenta extrair número do final da string: "DHI ... HISTÓRIA - 112406 " -> 112406
        codigo_lotacao = None
        sigla_lotacao = None
        ggs = []

        if status_final == 'ATIVO':
            texto_depto = vinculo_principal.departamento_string
            # Regex: Procura dígitos (\d+) no final da string ($), ignorando espaços (\s*)
            match = re.search(r'(\d+)\s*$', texto_depto)
            
            if match:
                codigo_lotacao = match.group(1)
                # Busca no nosso Organograma importado anteriormente
                try:
                    unidade = DicionarioOrganograma.objects.get(pk=codigo_lotacao)
                    sigla_lotacao = unidade.sigla # Ex: DHI
                except DicionarioOrganograma.DoesNotExist:
                    sigla_lotacao = f"COD_{codigo_lotacao}" # Fallback se não achar no organograma
            
            # --- CÁLCULO DE GGs (SUGESTÃO) ---
            cargo = vinculo_principal.cargo.upper()
            
            if sigla_lotacao:
                if 'PROFESSOR' in cargo or 'DOCENTE' in cargo:
                    ggs.append(f"GG_{sigla_lotacao}_DOCENTES")
                    ggs.append(f"GG_{sigla_lotacao}_IMPRESSAO")
                elif 'TECNICO' in cargo:
                    ggs.append(f"GG_{sigla_lotacao}_ADMINISTRATIVO")
                    ggs.append(f"GG_{sigla_lotacao}_IMPRESSAO")
            
            # Tratamento para Alunos (Geralmente não têm código 112406, e sim texto do curso)
            if 'DISCENTE' in cargo or 'ALUNO' in cargo:
                # Ex: G - ARTES VISUAIS - 08
                # Lógica simples: pegar o nome do curso entre os hifens
                partes = texto_depto.split('-')
                if len(partes) >= 2:
                    nome_curso = partes[1].strip().replace(' ', '_').upper()
                    ggs.append(f"GG_{nome_curso}_ALUNOS")

        # --- CRIA O OBJETO CONSOLIDADO ---
        identidade = IdentidadeConsolidada(
            samaccountname=login,
            nome_completo=vinculo_principal.nome,
            status_calculado=status_final,
            lotacao_codigo=codigo_lotacao,
            lotacao_sigla=sigla_lotacao,
            tipo_vinculo_principal=vinculo_principal.cargo,
            ggs_sugeridas=", ".join(ggs)
        )
        identidades_para_criar.append(identidade)
    
    # Salva tudo no banco
    IdentidadeConsolidada.objects.bulk_create(identidades_para_criar)
    return len(identidades_para_criar)