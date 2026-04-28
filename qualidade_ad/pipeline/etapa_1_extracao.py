#qualidade_ad/pipeline/etapa_1_extracao.py


import ldap3
import csv
import os
from dotenv import load_dotenv
from datetime import datetime
import traceback
from django.utils import timezone
from qualidade_ad.models import LogEtapa
import logging

logger = logging.getLogger(__name__)

def executar_extracao_ad(execucao_id):
    etapa_nome = 'ETAPA_1_EXTRACAO'
    timestamp_inicio = timezone.now()
    resumo_da_etapa = ""
    status_final = "SUCESSO"
    conn = None
    
    try:
        logger.info(f"  [Etapa 1] Iniciando extração do AD (Execução ID: {execucao_id})...")
        
        load_dotenv()
        server_uri = os.getenv("AD_SERVER")
        bind_user = os.getenv("AD_USER")
        bind_password = os.getenv("AD_PASSWORD")
        search_base = os.getenv("AD_SEARCH_BASE")

        # --- INÍCIO DA CORREÇÃO ---
        # Corrigido: Usando 3 'dirname' para chegar na raiz do projeto (DQ4IAM_GOVERNANCE)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # --- FIM DA CORREÇÃO ---

        save_path = os.path.join(base_dir, 'temp_data')
        os.makedirs(save_path, exist_ok=True)
        
        if not all([server_uri, bind_user, bind_password, search_base]):
            logger.error("  [Etapa 1] ERRO: Credenciais do AD não encontradas no .env.")
            raise ValueError("Credenciais do AD ausentes no .env")

        TARGET_OBJECTS = {
            "users": "(&(objectClass=user)(objectCategory=person))",
            "computers": "(objectClass=computer)",
            "groups": "(objectClass=group)",
            "ous": "(objectClass=organizationalUnit)"
        }
        
        report_data = {}
        server = ldap3.Server(server_uri, use_ssl=True, get_info=ldap3.ALL)
        
        conn = ldap3.Connection(server, user=bind_user, password=bind_password, auto_bind=True)
        logger.info("  [Etapa 1] Conexão com o AD estabelecida.")

        for category, ldap_filter in TARGET_OBJECTS.items():
            logger.info(f"    -> Processando categoria: {category.upper()}")
            search_generator = conn.extend.standard.paged_search(
                search_base=search_base, search_filter=ldap_filter,
                attributes=ldap3.ALL_ATTRIBUTES, paged_size=500, generator=True
            )
            entries = list(search_generator)
            object_count = len(entries)
            report_data[category] = object_count
            
            if not entries:
                logger.warning(f"    AVISO: Nenhum objeto do tipo '{category}' encontrado.")
                continue

            logger.info(f"    -> {object_count} objetos encontrados.")
            all_attribute_names = set()
            for entry in entries:
                if 'attributes' in entry and entry['attributes']:
                    all_attribute_names.update(entry['attributes'].keys())
            
            sorted_attributes = sorted(list(all_attribute_names))
            
            output_file_path = os.path.join(save_path, f"ad_{category}.csv")
            logger.info(f"    -> Gravando dados em: '{output_file_path}'")
            
            with open(output_file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted_attributes)
                writer.writeheader()
                for entry in entries:
                    row_data = entry.get('attributes', {})
                    cleaned_row = {}
                    for attr in sorted_attributes:
                        value = row_data.get(attr)
                        if value is None: cleaned_row[attr] = ''
                        elif isinstance(value, list): cleaned_row[attr] = '; '.join(map(str, value))
                        else: cleaned_row[attr] = str(value)
                    writer.writerow(cleaned_row)
            
            logger.info(f"    -> Arquivo para '{category}' gerado.")

        end_time_legacy = datetime.now()
        report_file_path = os.path.join(save_path, "extraction_report.txt")
        
        with open(report_file_path, 'w', encoding='utf-8') as f:
            f.write("RELATÓRIO DE EXTRAÇÃO DE DADOS DO ACTIVE DIRECTORY\n")
            f.write(f"Início: {timestamp_inicio} | Fim: {end_time_legacy}\n")
            f.write(f"Duração Total: {end_time_legacy - timestamp_inicio.replace(tzinfo=None)}\n\n")
            for category, count in report_data.items():
                f.write(f"- {category.capitalize()}: {count} objetos\n")
        
        logger.info(f"  [Etapa 1] Relatório de extração salvo em '{report_file_path}'.")
        total_objetos = sum(report_data.values())
        resumo_da_etapa = f"Extração concluída. {total_objetos} objetos totais processados."
        
    except Exception as e:
        status_final = "FALHOU"
        resumo_da_etapa = f"ERRO CRÍTICO: {e}\n{traceback.format_exc()}"
        logger.error(f"  [Etapa 1] ERRO: {resumo_da_etapa}")
        raise e
    
    finally:
        if conn and conn.bound:
            conn.unbind()
            logger.info("  [Etapa 1] Conexão com o AD foi encerrada.")
        
        timestamp_fim = timezone.now()
        try:
            LogEtapa.objects.create(
                execucao_id=execucao_id, etapa_nome=etapa_nome, status=status_final,
                timestamp_inicio=timestamp_inicio, timestamp_fim=timestamp_fim,
                resumo_execucao=resumo_da_etapa
            )
            logger.info(f"  [Etapa 1] Log de execução salvo no banco de dados.")
        except Exception as db_error:
            logger.critical(f"  [Etapa 1] ERRO CRÍTICO AO SALVAR LOG: {db_error}")
            
    return resumo_da_etapa