from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
import pandas as pd
import os
import datetime
from .forms import UploadCSVForm
from .tasks import executar_importacao_dinamica_task
from django.contrib.auth.decorators import login_required


@login_required
def upload_csv_view(request):
    """
    Passo 1 da Importação Dinâmica: Upload do arquivo CSV.
    Salva o arquivo temporariamente para processamento.
    """
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            arquivo = request.FILES['arquivo_csv']
            
            # Salva o arquivo temporariamente
            fs = FileSystemStorage(location='temp_data/')
            filename = fs.save(arquivo.name, arquivo)
            file_path = fs.path(filename)
            
            # Guarda o caminho na sessão para o próximo passo
            request.session['csv_path'] = file_path
            return redirect('configurar_importacao')
    else:
        form = UploadCSVForm()
    
    return render(request, 'importador_dinamico/passo1_upload.html', {'form': form})


@login_required
def configurar_importacao_view(request):
    """
    Passo 2: Configuração de colunas e banco de destino.
    Dispara a tarefa Celery para criar o banco e importar os dados.
    """
    file_path = request.session.get('csv_path')
    
    if not file_path or not os.path.exists(file_path):
        messages.error(request, "Arquivo não encontrado. Faça o upload novamente.")
        return redirect('upload_csv')

    # Lê apenas o cabeçalho e as primeiras 5 linhas para prévia
    try:
        df_preview = pd.read_csv(file_path, nrows=5)
        colunas = df_preview.columns.tolist()
        # Converte para dicionário para exibir no HTML
        dados_preview = df_preview.to_dict(orient='records')
    except Exception as e:
        messages.error(request, f"Erro ao ler CSV: {e}")
        return redirect('upload_csv')

    if request.method == 'POST':
        # 1. Pega o nome do banco (ou gera automático)
        nome_banco = request.POST.get('nome_banco')
        if not nome_banco:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_banco = f"db_importado_{timestamp}"
        
        # Limpa nome do banco (segurança básica)
        nome_banco = "".join(c for c in nome_banco if c.isalnum() or c == '_').lower()

        # 2. Pega as colunas selecionadas
        cols_selecionadas = request.POST.getlist('colunas')
        
        if not cols_selecionadas:
            messages.error(request, "Selecione pelo menos uma coluna.")
            return redirect('configurar_importacao')
        
        # 3. Define nome da tabela (baseado no nome do arquivo)
        nome_arquivo = os.path.basename(file_path).split('.')[0]
        nome_tabela = f"{nome_arquivo}_staging"
        nome_tabela = "".join(c for c in nome_tabela if c.isalnum() or c == '_').lower()

        # 4. Dispara a Task
        executar_importacao_dinamica_task.delay(file_path, nome_banco, cols_selecionadas, nome_tabela)
        
        messages.success(request, f"Processo iniciado! Criando banco '{nome_banco}' e importando dados...")
        return redirect('painel_de_controle') # Ou uma tela de status

    context = {
        'colunas': colunas,
        'dados_preview': dados_preview,
        'filename': os.path.basename(file_path)
    }
    return render(request, 'importador_dinamico/passo2_config.html', context)