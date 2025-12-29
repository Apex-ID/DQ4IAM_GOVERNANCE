import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import traceback
from django.utils import timezone
from django.conf import settings  
from qualidade_ad.models import LogEtapa

def executar_carga_staging(execucao_id):
    """
    Executa a Etapa 4 (Carga para Staging) e registra um LogEtapa
    no banco de dados com o resultado.
    """

    etapa_nome = 'ETAPA_4_CARGA_STAGING'
    timestamp_inicio = timezone.now()
    resumo_da_etapa = ""
    status_final = "SUCESSO"
    
    try:
        print(f"  [Etapa 4] Iniciando carga para Staging (Execução ID: {execucao_id})...")
        
        load_dotenv()
        
        
        # Usa o BASE_DIR do Django para garantir que pegamos a pasta temp_data dentro do projeto
        data_path = os.path.join(settings.BASE_DIR, 'temp_data')
        # ---------------------------

        # Mapeamento dos arquivos limpos para as tabelas de staging
        csv_to_table_map = {
            'ad_users_cleaned.csv': 'ad_users_staging',
            'ad_computers_cleaned.csv': 'ad_computers_staging',
            'ad_groups_cleaned.csv': 'ad_groups_staging',
            'ad_ous_cleaned.csv': 'ad_ous_staging'
        }

        # Carrega as credenciais do banco (já devem estar no .env)
        db_user, db_pass, db_host, db_name = (os.getenv('DB_USER'), os.getenv('DB_PASS'), os.getenv('DB_HOST'), os.getenv('DB_NAME'))
        
        if not all([db_user, db_pass, db_host, db_name]):
            raise ValueError("Credenciais do DB ausentes no .env")

        db_url = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
        engine = create_engine(db_url)

        total_linhas_carregadas = 0
        erros = []

        with engine.connect() as connection:
            for csv_file, table_name in csv_to_table_map.items():
                print(f"    -> Processando: {csv_file} -> {table_name}")
                
                file_path = os.path.join(data_path, csv_file)
                
                # Verifica se o arquivo existe antes de tentar ler
                if not os.path.exists(file_path):
                    msg_erro = f"Arquivo não encontrado no caminho esperado: {file_path}"
                    print(f"      ERRO: {msg_erro}")
                    # Não vamos parar tudo por um arquivo, mas vamos registrar o erro
                    erros.append(msg_erro)
                    continue 

                print(f"      -> Lendo o arquivo '{file_path}'...")
                df = pd.read_csv(file_path, dtype=str)

                # Limpeza final (Pandas lê 'None' como string, então padronizamos para NULL)
                df.dropna(how='all', inplace=True)
                df = df.where(pd.notnull(df), None) # Substitui NaN por None

                print(f"      -> {len(df)} linhas válidas lidas.")
                if df.empty:
                    print("      AVISO: Nenhum dado para carregar.")
                    continue

                trans = connection.begin()
                try:
                    print(f"      -> Limpando a tabela '{table_name}' (TRUNCATE)...")
                    truncate_command = text(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE;')
                    connection.execute(truncate_command)

                    print(f"      -> Inserindo {len(df)} linhas em lotes...")
                    df.to_sql(
                        table_name,
                        con=connection,
                        if_exists='append',
                        index=False,
                        method='multi',
                        chunksize=1000 # Usamos lotes de 1000 para evitar timeouts
                    )
                    
                    trans.commit()
                    print(f"      SUCESSO: {len(df)} linhas carregadas na tabela '{table_name}'.")
                    total_linhas_carregadas += len(df)
                except Exception as e:
                    print(f"      ERRO CRÍTICO ao carregar dados para '{table_name}': {e}")
                    trans.rollback()
                    erros.append(f"Falha ao carregar {table_name}: {e}")
                    raise e # Levanta o erro para o try/except principal
        
        if erros:
             resumo_da_etapa = f"Carga concluída parcialmente. {total_linhas_carregadas} linhas importadas. Erros: {'; '.join(erros)}"
             # Se houve erros de arquivo, podemos considerar FALHOU ou SUCESSO PARCIAL.
             # Aqui vou deixar passar se carregou algo, mas alertando.
        else:
            resumo_da_etapa = f"Carga para Staging concluída. {total_linhas_carregadas} linhas totais carregadas nas 4 tabelas."
            
        print(f"  [Etapa 4] {resumo_da_etapa}")

    except Exception as e:
        status_final = "FALHOU"
        resumo_da_etapa = f"ERRO CRÍTICO: {e}\n{traceback.format_exc()}"
        print(f"  [Etapa 4] ERRO: {resumo_da_etapa}")
        raise e
    
    finally:
        if 'engine' in locals() and engine is not None:
            engine.dispose()
            
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
            print(f"  [Etapa 4] Log de execução salvo no banco de dados.")
        except Exception as db_error:
            print(f"  [Etapa 4] ERRO CRÍTICO AO SALVAR LOG: {db_error}")

    return resumo_da_etapa