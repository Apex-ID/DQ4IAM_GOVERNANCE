import pandas as pd
from sqlalchemy import text
import logging

# --- CORREÇÃO: Importar as listas separadas e específicas ---
from .regras_staging import REGRAS_STAGING
from .regras_producao import REGRAS_PRODUCAO
# ----------------------------------------------------------

logger = logging.getLogger(__name__)

def gerar_scorecard_detalhado(engine, tipo_analise='producao'):
    """
    Executa TODAS as regras, coleta os IDs de quem falhou e 
    agrupa os erros por objeto.
    
    tipo_analise: 'staging' ou 'producao'
    """
    mapa_falhas = {} 

    # 1. Seleciona a lista de regras correta
    # Isso garante que usamos o SQL blindado para Staging e o otimizado para Produção
    if tipo_analise == 'staging':
        lista_regras = REGRAS_STAGING
    else:
        lista_regras = REGRAS_PRODUCAO

    with engine.connect() as connection:
        for regra in lista_regras:
            
            # 2. Identifica a tabela analisada (para agrupar no relatório)
            if 'tabelas_alvo' in regra:
                tabela_analisada = regra['tabelas_alvo'][0]
            else:
                # Fallback para garantir compatibilidade
                tabela_analisada = regra.get('tabelas', 'desconhecida').split(' ')[0]

            # Inicializa o grupo da tabela se não existir
            if tabela_analisada not in mapa_falhas:
                mapa_falhas[tabela_analisada] = {}

            try:
                # 3. Executa a query
                # O SQL já vem pronto do arquivo correto, não precisa de .replace()
                sql_execucao = regra['sql']
                
                df = pd.read_sql_query(text(sql_execucao), connection)
                
                if not df.empty:
                    for _, row in df.iterrows():
                        # Assume que a query sempre retorna a coluna 'origem' (o ID do objeto)
                        objeto = str(row['origem'])
                        
                        if objeto not in mapa_falhas[tabela_analisada]:
                            mapa_falhas[tabela_analisada][objeto] = []
                        
                        # Adiciona a falha à lista desse objeto
                        mapa_falhas[tabela_analisada][objeto].append(regra['nome'])
                        
            except Exception as e:
                logger.error(f"Erro Scorecard na regra '{regra['nome']}': {e}")
                continue

    # 4. Transforma o Dicionário em Lista Plana (para o CSV e JSON)
    lista_final = []
    for tabela, objetos in mapa_falhas.items():
        for nome_objeto, lista_regras_violadas in objetos.items():
            lista_final.append({
                'tabela': tabela,
                'objeto': nome_objeto,
                'qtd_erros': len(lista_regras_violadas),
                'regras_violadas': "; ".join(lista_regras_violadas)
            })

    df_scorecard = pd.DataFrame(lista_final)
    
    if df_scorecard.empty:
         return pd.DataFrame() # Retorna vazio se não houver erros

    # Ordena pelos piores casos (quem tem mais erros primeiro)
    df_scorecard.sort_values(by='qtd_erros', ascending=False, inplace=True)

    return df_scorecard