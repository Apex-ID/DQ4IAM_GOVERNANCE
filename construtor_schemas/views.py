from django.db import connections
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from sqlalchemy import create_engine, text
from .utils import processar_dicionario
from .tasks import executar_criacao_schema_task, executar_carga_mapeada_task
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from .models import HistoricoCarga
import os


@login_required
def upload_dicionario(request):
    """
    View responsável pelo upload e processamento de Dicionários de Dados (PDF/DOCX).
    
    Permite ao usuário:
    1. Enviar um arquivo.
    2. Visualizar os tipos de dados sugeridos.
    3. Ajustar os tipos.
    4. Solicitar a criação da tabela/banco no PostgreSQL.
    """
    context = {'titulo': 'Construtor de Schemas (Data Architect)'}
    
    # CENÁRIO 1: Upload do Arquivo
    if request.method == 'POST' and 'arquivo_dicionario' in request.FILES:
        arquivo = request.FILES['arquivo_dicionario']
        extensao = os.path.splitext(arquivo.name)[1].lower()
        
        fs = FileSystemStorage()
        filename = fs.save(f"dic_{arquivo.name}", arquivo)
        try:
            dados = processar_dicionario(fs.path(filename), extensao)
            context['dados_extraidos'] = dados
            context['nome_arquivo'] = arquivo.name
            
            # Sugere nome da tabela limpo
            nome_limpo = arquivo.name.lower().replace('dicionario', '').strip()
            nome_limpo = nome_limpo.replace('.docx', '').replace('.pdf', '').replace('.doc', '')
            sugestao_tabela = nome_limpo.replace(' ', '_').replace('.', '_')
            context['sugestao_tabela'] = sugestao_tabela

        except Exception as e:
            messages.error(request, f"Erro ao ler: {e}")
        finally:
            os.remove(fs.path(filename))

    # CENÁRIO 2: Confirmação e Criação
    elif request.method == 'POST' and 'acao_criar_tabela' in request.POST:
        try:
            nome_banco = request.POST.get('nome_banco')
            criar_db = request.POST.get('criar_db') == 'on'
            nome_tabela = request.POST.get('nome_tabela')
            
            # 1. Pega as listas completas de todos os inputs (marcados ou não)
            todos_nomes = request.POST.getlist('col_nome')
            todos_tipos = request.POST.getlist('col_tipo')
            
            # 2. Pega apenas os índices que foram marcados no checkbox
            indices_selecionados = request.POST.getlist('col_selecionada')
            
            colunas_finais = []
            
            for i in indices_selecionados:
                idx = int(i) # Converte string para inteiro
                
                # Garante que o índice existe (segurança)
                if idx < len(todos_nomes):
                    nome = todos_nomes[idx]
                    tipo = todos_tipos[idx]
                    
                    # Adiciona na lista final se tiver dados válidos
                    if nome and tipo:
                        colunas_finais.append({'nome': nome, 'tipo': tipo})
            
            if not colunas_finais:
                messages.error(request, "Nenhuma coluna selecionada!")
                return redirect('upload_dicionario')

            # Dispara a Task com a lista filtrada
            config = {
                'nome_banco': nome_banco,
                'criar_banco': criar_db,
                'nome_tabela': nome_tabela,
                'colunas': colunas_finais
            }
            
            executar_criacao_schema_task.delay(config)
            
            messages.success(request, f"Solicitação enviada! Verificando banco '{nome_banco}' e criando tabela '{nome_tabela}' com {len(colunas_finais)} colunas.")
            return redirect('upload_dicionario')
            
        except Exception as e:
            messages.error(request, f"Erro ao processar formulário: {e}")

    return render(request, 'construtor_schemas/upload.html', context)


def get_colunas_do_banco(nome_banco, nome_tabela):
    """
    Função auxiliar (não é view) que conecta ao banco e lista colunas.
    Usada pelo definidor de mapeamento.
    """
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_host = os.getenv('DB_HOST')
    
    url = f"postgresql://{db_user}:{db_pass}@{db_host}/{nome_banco}"
    engine = create_engine(url)
    
    colunas = []
    try:
        with engine.connect() as conn:
            query = text(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{nome_tabela}'
                ORDER BY ordinal_position
            """)
            result = conn.execute(query)
            colunas = [{'nome': row[0], 'tipo': row[1]} for row in result]
    except Exception as e:
        print(f"Erro ao ler colunas: {e}")
        
    return colunas


def get_lista_bancos():
    """
    Função auxiliar que lista todos os bancos de dados do servidor.
    """
    bancos = []
    try:
        # Usa a conexão padrão do Django para consultar o catálogo
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;")
            bancos = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Erro ao listar bancos: {e}")
    return bancos


def definir_mapeamento(request):
    """
    Tela para ligar Staging -> Produção Nova
    """
    context = {'titulo': 'ETL Builder: Mapeamento de Carga'}

    # 1. Listar tabelas de Staging (Origem)
    try:
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE '%_staging'")
            tabelas_staging = [row[0] for row in cursor.fetchall()]
        context['tabelas_staging'] = tabelas_staging
    except:
        context['tabelas_staging'] = []

    # 2. Listar Bases de Dados Disponíveis (Destino) 
    context['lista_bancos'] = get_lista_bancos()

    # 3. Processamento do Formulário
    if request.method == 'POST':
        # ETAPA A: Carregar Colunas
        if 'btn_carregar_colunas' in request.POST:
            origem = request.POST.get('tabela_origem')
            banco_dest = request.POST.get('banco_destino')
            tabela_dest = request.POST.get('tabela_destino')
            
            if not origem or not banco_dest or not tabela_dest:
                messages.error(request, "Por favor, selecione a Origem, o Banco e digite a Tabela de Destino.")
            else:
                try:
                    cols_origem = get_colunas_do_banco(os.getenv('DB_NAME'), origem)
                    cols_destino = get_colunas_do_banco(banco_dest, tabela_dest)
                    
                    if not cols_destino:
                        messages.warning(request, f"A tabela '{tabela_dest}' não foi encontrada no banco '{banco_dest}' ou não tem colunas.")
                    
                    context['cols_origem'] = cols_origem
                    context['cols_destino'] = cols_destino
                    
                    # Mantém as escolhas
                    context['sel_origem'] = origem
                    context['sel_banco_dest'] = banco_dest
                    context['sel_tabela_dest'] = tabela_dest
                    
                except Exception as e:
                    messages.error(request, f"Erro ao ler tabelas: {e}")

        # ETAPA B: Executar Carga
        elif 'btn_executar_carga' in request.POST:
            origem = request.POST.get('tabela_origem_final')
            banco_dest = request.POST.get('banco_destino_final')
            tabela_dest = request.POST.get('tabela_destino_final')
            
            mapeamento = {}
            for key, value in request.POST.items():
                if key.startswith("map_") and value:
                    coluna_destino = key.replace("map_", "")
                    coluna_origem = value
                    mapeamento[coluna_destino] = coluna_origem
            
            if not mapeamento:
                messages.error(request, "Nenhuma coluna foi mapeada.")
            else:
                config_carga = {
                    'origem': origem,
                    'banco_destino': banco_dest,
                    'tabela_destino': tabela_dest,
                    'mapeamento': mapeamento
                }
                
                executar_carga_mapeada_task.delay(config_carga)
                messages.success(request, f"Carga iniciada! Transferindo dados de {origem} para {banco_dest}.{tabela_dest}")
                return redirect('painel_de_controle')

    return render(request, 'construtor_schemas/mapeamento.html', context)

@login_required
def api_listar_tabelas_banco(request):
    """
    API auxiliar que retorna as tabelas públicas de um banco de dados específico.
    """
    nome_banco = request.GET.get('banco')
    
    if not nome_banco:
        return JsonResponse({'tabelas': []})

    print(f"--- API: Tentando listar tabelas do banco '{nome_banco}' ---")

    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_host = os.getenv('DB_HOST')
    
    # Conecta especificamente no banco solicitado
    url = f"postgresql://{db_user}:{db_pass}@{db_host}/{nome_banco}"
    
    tabelas = []
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            # Busca tabelas criadas pelo usuário (schema public)
            query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            result = conn.execute(query)
            tabelas = [row[0] for row in result]
            
        print(f"--- API: Sucesso! Encontradas {len(tabelas)} tabelas: {tabelas}")
        return JsonResponse({'tabelas': tabelas})

    except Exception as e:
        print(f"--- API ERRO CRÍTICO: Não foi possível conectar no banco '{nome_banco}': {e}")
        return JsonResponse({'error': str(e), 'tabelas': []}, status=500)

@login_required   
def historico_cargas(request):
    cargas = HistoricoCarga.objects.all().order_by('-data_execucao')
    return render(request, 'construtor_schemas/historico.html', {'cargas': cargas})