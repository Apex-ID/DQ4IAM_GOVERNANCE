# Dentro de: qualidade_ad/views.py
    
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .tasks import (
    executar_pipeline_completo_task, 
    importar_arquivos_existentes_task
)
from .models import ExecucaoPipeline

@login_required
def painel_de_controle(request):
    """
    View do painel de controle do pipeline (ETL).
    """
    
    if request.method == 'POST':
        if 'acao_pipeline_completo' in request.POST:
            executar_pipeline_completo_task.delay()
            messages.success(request, 'O pipeline COMPLETO (com extração do AD) foi iniciado!')
        
        elif 'acao_importar_arquivos' in request.POST:
            importar_arquivos_existentes_task.delay()
            messages.success(request, 'A IMPORTAÇÃO de arquivos locais foi iniciada!')

        return redirect('painel_de_controle')

    # Busca o histórico de execuções do PIPELINE
    ultimas_execucoes = ExecucaoPipeline.objects.all().prefetch_related('logs_etapas').order_by('-timestamp_inicio')[:5]
    
    context = {
        'titulo': 'APEX - Painel de Carga de Dados (ETL)',
        'ultimas_execucoes': ultimas_execucoes,
    }
    return render(request, 'qualidade_ad/painel.html', context)