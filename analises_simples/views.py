from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import connection
from django.contrib.auth.decorators import login_required

# Importe TODOS os models
from .models import (
    RelatorioCompletude, 
    RelatorioCompletudeGeral, 
    RelatorioValidadeFormato, 
    RelatorioUnicidadeGeral, 
    RelatorioRegraNegocio, 
    RelatorioUnicidadePersonalizada
)
# Importe TODAS as tasks
from .tasks import (
    executar_analise_completude_task, 
    executar_analise_completude_geral_task,
    executar_analise_validade_formato_task,
    executar_analise_unicidade_staging_task,
    executar_analise_unicidade_producao_task,
    executar_regras_staging_task,
    executar_regras_producao_task,
    executar_unicidade_personalizada_task
)

@login_required
def dashboard_analises(request):
    """
    View principal do Dashboard de Análises.
    """
    if request.method == 'POST':
        if 'acao_analise_completude_usuarios' in request.POST:
            executar_analise_completude_task.delay()
            messages.success(request, 'A ANÁLISE DE COMPLETUDE (Usuários) foi iniciada!')
        elif 'acao_analise_completude_geral' in request.POST:
            executar_analise_completude_geral_task.delay()
            messages.success(request, 'A ANÁLISE GERAL DE COMPLETUDE (Staging) foi iniciada!')
        elif 'acao_analise_validade' in request.POST:
            executar_analise_validade_formato_task.delay()
            messages.success(request, 'A ANÁLISE DE VALIDADE DE FORMATO foi iniciada!')
        elif 'acao_analise_unicidade_staging' in request.POST:
            executar_analise_unicidade_staging_task.delay()
            messages.success(request, 'A ANÁLISE DE UNICIDADE (Staging) foi iniciada!')
        elif 'acao_analise_unicidade_producao' in request.POST:
            executar_analise_unicidade_producao_task.delay()
            messages.success(request, 'A ANÁLISE DE UNICIDADE (Produção) foi iniciada!')
        elif 'acao_regras_staging' in request.POST:
            executar_regras_staging_task.delay()
            messages.success(request, 'Análise de Regras de Negócio (Staging) iniciada!')            
        elif 'acao_regras_producao' in request.POST:
            executar_regras_producao_task.delay()
            messages.success(request, 'Análise de Regras de Negócio (Produção) iniciada!')
        return redirect('dashboard_analises')

    # Queries de Histórico (Ordenados por Data Descrescente)
    ultimos_relatorios_usuarios = RelatorioCompletude.objects.all().order_by('-timestamp_inicio')[:5]
    ultimos_relatorios_gerais = RelatorioCompletudeGeral.objects.all().order_by('-timestamp_inicio')[:5]
    ultimos_relatorios_validade = RelatorioValidadeFormato.objects.all().order_by('-timestamp_inicio')[:5]
    
    ultimos_relatorios_unicidade_staging = RelatorioUnicidadeGeral.objects.filter(
        tabela_analisada__endswith='_staging'
    ).order_by('-timestamp_inicio')[:5]
    
    ultimos_relatorios_unicidade_producao = RelatorioUnicidadeGeral.objects.exclude(
        tabela_analisada__endswith='_staging'
    ).order_by('-timestamp_inicio')[:5]

    ultimas_regras_staging = RelatorioRegraNegocio.objects.filter(
        tipo_tabela='STAGING'
    ).order_by('-timestamp_inicio')[:50]
    
    ultimas_regras_producao = RelatorioRegraNegocio.objects.filter(
        tipo_tabela='PRODUÇÃO'
    ).order_by('-timestamp_inicio')[:50]

    ultimos_relatorios_personalizados = RelatorioUnicidadePersonalizada.objects.all().order_by('-timestamp_inicio')[:5]

    context = {
        'titulo': 'APEX - Dashboard de Análises Simples',
        'ultimos_relatorios_usuarios': ultimos_relatorios_usuarios, 
        'ultimos_relatorios_gerais': ultimos_relatorios_gerais,
        'ultimos_relatorios_validade': ultimos_relatorios_validade,
        'ultimos_relatorios_unicidade_staging': ultimos_relatorios_unicidade_staging,
        'ultimos_relatorios_unicidade_producao': ultimos_relatorios_unicidade_producao,
        'ultimas_regras_staging': ultimas_regras_staging,
        'ultimas_regras_producao': ultimas_regras_producao,
        'ultimos_relatorios_personalizados': ultimos_relatorios_personalizados,
    }
    return render(request, 'analises_simples/dashboard_analises.html', context)

# --- Views de Detalhe ---

@login_required
def detalhe_relatorio_geral(request, pk):
    relatorio = get_object_or_404(RelatorioCompletudeGeral, pk=pk)
    colunas_vazias = []
    if relatorio.relatorio_colunas_vazias:
        for col, count in relatorio.relatorio_colunas_vazias.items():
            perc = (count / relatorio.total_registros) * 100 if relatorio.total_registros > 0 else 0
            colunas_vazias.append({'nome': col, 'contagem': count, 'percentual': perc})
    
    context = {
        'titulo': 'Detalhe Geral', 
        'relatorio': relatorio, 
        'colunas_vazias': colunas_vazias
    }
    return render(request, 'analises_simples/detalhe_relatorio.html', context)

@login_required
def detalhe_relatorio_validade(request, pk):
    relatorio = get_object_or_404(RelatorioValidadeFormato, pk=pk)
    erros = relatorio.detalhamento_erros.items() if relatorio.detalhamento_erros else []
    
    context = {
        'titulo': 'Detalhe Validade', 
        'relatorio': relatorio, 
        'colunas_com_erros': erros
    }
    return render(request, 'analises_simples/detalhe_relatorio_validade.html', context)

@login_required
def detalhe_relatorio_unicidade(request, pk):
    relatorio = get_object_or_404(RelatorioUnicidadeGeral, pk=pk)
    
    detalhes_colunas = []
    if relatorio.detalhe_por_coluna:
        for col_nome, stats in relatorio.detalhe_por_coluna.items():
            stats['nome'] = col_nome
            detalhes_colunas.append(stats)
            
    detalhes_colunas.sort(key=lambda x: x['duplicatas'], reverse=True)

    context = {
        'titulo': f"Detalhe Unicidade: {relatorio.tabela_analisada}",
        'relatorio': relatorio,
        'detalhes_colunas': detalhes_colunas
    }
    return render(request, 'analises_simples/detalhe_relatorio_unicidade.html', context)

def detalhe_relatorio_regras(request, pk):
    relatorio = get_object_or_404(RelatorioRegraNegocio, pk=pk)
    status_classe = "status-sucesso" if relatorio.qtd_falhas == 0 else "status-falhou"
    
    context = {
        'titulo': f"Detalhe Regra: {relatorio.nome_regra}",
        'relatorio': relatorio,
        'status_classe': status_classe
    }
    return render(request, 'analises_simples/detalhe_relatorio_regras.html', context)

# --- View de Configuração Personalizada ---

@login_required
def configuracao_unicidade(request):
    tabelas_disponiveis = [
        'ad_users_staging', 'ad_computers_staging', 
        'ad_groups_staging', 'ad_ous_staging',
        'ad_users', 'ad_computers', 'ad_groups'
    ]
    
    colunas_encontradas = []
    tabela_selecionada = None

    if request.method == 'POST':
        if 'btn_buscar_colunas' in request.POST:
            tabela_selecionada = request.POST.get('tabela_selecionada')
            if tabela_selecionada in tabelas_disponiveis:
                with connection.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = '{tabela_selecionada}'
                        ORDER BY column_name
                    """)
                    colunas_encontradas = [row[0] for row in cursor.fetchall() if row[0] != 'id']

        elif 'btn_executar_analise' in request.POST:
            tabela_final = request.POST.get('tabela_final')
            colunas_escolhidas = request.POST.getlist('colunas_escolhidas')
            
            if len(colunas_escolhidas) > 0 and len(colunas_escolhidas) <= 5:
                executar_unicidade_personalizada_task.delay(tabela_final, colunas_escolhidas)
                messages.success(request, f"Análise Personalizada iniciada para a tabela '{tabela_final}'!")
                return redirect('dashboard_analises')
            else:
                messages.error(request, "Erro: Selecione entre 1 e 5 colunas.")
                return redirect('configuracao_unicidade')

    context = {
        'titulo': 'Nova Análise de Unicidade',
        'tabelas': tabelas_disponiveis,
        'tabela_selecionada': tabela_selecionada,
        'colunas': colunas_encontradas
    }
    return render(request, 'analises_simples/configuracao_unicidade.html', context)

@login_required
def detalhe_relatorio_personalizado(request, pk):
    relatorio = get_object_or_404(RelatorioUnicidadePersonalizada, pk=pk)
    
    context = {
        'titulo': f"Resultado: Unicidade Personalizada",
        'relatorio': relatorio,
        'exemplos': relatorio.exemplos_duplicatas 
    }
    return render(request, 'analises_simples/detalhe_relatorio_personalizado.html', context)