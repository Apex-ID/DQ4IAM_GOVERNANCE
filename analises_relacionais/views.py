from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import FileResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
import os

from .models import (
    RelatorioAnaliseRelacional, 
    RelatorioDQI, 
    RelatorioRiscoSenha,
    RelatorioScorecard
)
from .tasks import (
    executar_analises_relacionais_task, 
    executar_metricas_avancadas_task,
    executar_scorecard_completo_task,
    # --- NOVAS TAREFAS IMPORTADAS ---
    executar_regras_staging_task,
    executar_regras_producao_task
)

# -----------------------------------

@login_required
def dashboard_relacional(request):
    """
    View principal do painel relacional (Dashboard).
    Separada em Staging e Produção.
    """
    if request.method == 'POST':
        
        # 1. AUDITORIA DE PRODUÇÃO (Botão Roxo)
        if 'acao_auditoria_producao' in request.POST:
            executar_regras_producao_task.delay() # Roda as regras limpas
            executar_metricas_avancadas_task.delay(tipo_analise='producao') 
            messages.success(request, 'Auditoria de PRODUÇÃO iniciada!')

        # 2. AUDITORIA DE STAGING (Botão Laranja)
        elif 'acao_auditoria_staging' in request.POST:
            executar_regras_staging_task.delay() # Roda as regras blindadas (regex)
            executar_metricas_avancadas_task.delay(tipo_analise='staging') 
            messages.success(request, 'Auditoria de STAGING iniciada!')

        # 3. SCORECARDS (CSV)
        elif 'acao_scorecard_producao' in request.POST:
            executar_scorecard_completo_task.delay(tipo_analise='producao')
            messages.success(request, 'Geração de Scorecard (Produção) iniciada!')
            return redirect('dashboard_scorecard')
            
        elif 'acao_scorecard_staging' in request.POST:
            executar_scorecard_completo_task.delay(tipo_analise='staging')
            messages.success(request, 'Geração de Scorecard (Staging) iniciada!')
            return redirect('dashboard_scorecard')

        # Botão Legado (Compatibilidade)
        elif 'acao_analise_consistencia' in request.POST:
            executar_analises_relacionais_task.delay()
            executar_metricas_avancadas_task.delay()
            messages.success(request, 'Auditoria Padrão Iniciada!')
            
        return redirect('dashboard_relacional')
    
    # SEPARAÇÃO DO HISTÓRICO PARA O TEMPLATE 
    
    # Staging: Tabelas que TERMINAM com "_staging" ou contém "_staging" na string de join
    historico_staging = RelatorioAnaliseRelacional.objects.filter(
        tabelas_envolvidas__contains='_staging'
    ).order_by('-timestamp_inicio', 'nome_analise')[:100]

    # Produção: Tabelas que NÃO contêm "_staging"
    historico_producao = RelatorioAnaliseRelacional.objects.exclude(
        tabelas_envolvidas__contains='_staging'
    ).order_by('-timestamp_inicio', 'nome_analise')[:100]
    
    # KPIs (DQI e Risco)
    dqi_producao = RelatorioDQI.objects.filter(tipo_ambiente='PRODUÇÃO').last()
    dqi_staging = RelatorioDQI.objects.filter(tipo_ambiente='STAGING').last()
    ultimo_risco = RelatorioRiscoSenha.objects.last()

    context = {
        'titulo': 'APEX - Governança Avançada (DQI & Riscos)',
        'historico_producao': historico_producao, 
        'historico_staging': historico_staging,   
        'dqi_producao': dqi_producao,
        'dqi_staging': dqi_staging,
        'risco_senha': ultimo_risco
    }
    return render(request, 'analises_relacionais/dashboard_relacional.html', context)


@login_required
def detalhe_relatorio_relacional(request, pk):
    """
    View de detalhe para um relatório específico.
    """
    relatorio = get_object_or_404(RelatorioAnaliseRelacional, pk=pk)
    
    status_classe = "status-sucesso" if relatorio.total_inconsistencias == 0 else "status-falhou"
    
    context = {
        'titulo': f"Detalhe: {relatorio.nome_analise}",
        'relatorio': relatorio,
        'status_classe': status_classe
    }
    return render(request, 'analises_relacionais/detalhe_relatorio_relacional.html', context)
    
# -----------------------------------

@login_required
def dashboard_scorecard(request):
    """
    Tela que mostra os Top 50 ofensores e o botão de download.
    """
    ultimo_scorecard = RelatorioScorecard.objects.last()
    
    if request.method == 'POST':
        executar_scorecard_completo_task.delay(tipo_analise='producao')
        messages.success(request, 'Novo Scorecard solicitado!')
        return redirect('dashboard_scorecard')
        
    return render(request, 'analises_relacionais/dashboard_scorecard.html', {
        'titulo': 'Scorecard Individual (Detalhe por Objeto)',
        'scorecard': ultimo_scorecard
    })

@login_required
def baixar_csv_scorecard(request, pk):
    """
    Serve o arquivo CSV gerado para download.
    """
    scorecard = get_object_or_404(RelatorioScorecard, pk=pk)
    
    # Caminho completo do arquivo
    file_path = os.path.join(settings.BASE_DIR, 'media', 'scorecards', scorecard.arquivo_csv)
    
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=scorecard.arquivo_csv)
    else:
        messages.error(request, "Arquivo CSV não encontrado no servidor (pode ter sido excluído).")
        return redirect('dashboard_scorecard')