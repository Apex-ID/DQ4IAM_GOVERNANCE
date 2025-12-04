from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .dicionario_dados import obter_info_coluna
from .catalogo_formulas import FORMULAS_QUALIDADE

# 1. Importa models de Análises Simples
from analises_simples.models import (
    RelatorioCompletudeGeral, 
    RelatorioValidadeFormato, 
    RelatorioUnicidadeGeral,
    RelatorioRegraNegocio
)

# 2. Importa models de Análises Relacionais
from analises_relacionais.models import RelatorioAnaliseRelacional

@login_required
def central_relatorios(request):
    """
    Tela principal que lista todos os relatórios para impressão.
    """
    ctx = {
        'titulo': 'Central de Relatórios e Auditoria',
        
        # Buscando os últimos 10 de cada categoria
        'lista_regras_simples': RelatorioRegraNegocio.objects.all().order_by('-timestamp_inicio')[:10],
        'lista_regras_complexas': RelatorioAnaliseRelacional.objects.all().order_by('-timestamp_inicio')[:10],
        
        'lista_completude': RelatorioCompletudeGeral.objects.all().order_by('-timestamp_inicio')[:10],
        'lista_validade': RelatorioValidadeFormato.objects.all().order_by('-timestamp_inicio')[:10],
        'lista_unicidade': RelatorioUnicidadeGeral.objects.all().order_by('-timestamp_inicio')[:10],
    }
    return render(request, 'relatorios_gerenciais/index.html', ctx)

@login_required
def relatorio_oficial_impressao(request, tipo_metrica, pk):
    """
    Gera o PDF oficial.
    """
    contexto = {
        'data_geracao': timezone.now(),
        'sistema': 'APEX GOVERNANCE',
        'versao': '1.0.0',
    }

    # Lógica de seleção do objeto baseada no tipo
    if tipo_metrica == 'completude_geral':
        obj = get_object_or_404(RelatorioCompletudeGeral, pk=pk)
        contexto.update({'titulo': f"Completude: {obj.tabela_analisada}", 'obj': obj, 'formula': FORMULAS_QUALIDADE['completude'], 'tipo': 'completude'})
        # Enriquecimento de colunas
        detalhes = []
        if obj.relatorio_colunas_vazias:
            for col, count in obj.relatorio_colunas_vazias.items():
                info = obter_info_coluna(obj.tabela_analisada, col)
                detalhes.append({'coluna_negocio': info['nome'], 'coluna_tecnica': col, 'descricao': info['desc'], 'falhas': count})
        contexto['detalhes_enrich'] = detalhes

    elif tipo_metrica == 'validade':
        obj = get_object_or_404(RelatorioValidadeFormato, pk=pk)
        contexto.update({'titulo': f"Validade: {obj.tabela_analisada}", 'obj': obj, 'formula': FORMULAS_QUALIDADE['validade'], 'tipo': 'validade'})
        detalhes = []
        if obj.detalhamento_erros:
            for col, count in obj.detalhamento_erros.items():
                info = obter_info_coluna(obj.tabela_analisada, col)
                detalhes.append({'coluna_negocio': info['nome'], 'coluna_tecnica': col, 'descricao': info['desc'], 'falhas': count})
        contexto['detalhes_enrich'] = detalhes

    elif tipo_metrica == 'unicidade_geral':
        obj = get_object_or_404(RelatorioUnicidadeGeral, pk=pk)
        contexto.update({'titulo': f"Unicidade: {obj.tabela_analisada}", 'obj': obj, 'formula': FORMULAS_QUALIDADE['unicidade'], 'tipo': 'unicidade'})
        detalhes = []
        if obj.detalhe_por_coluna:
            for col, stats in obj.detalhe_por_coluna.items():
                if stats['duplicatas'] > 0: 
                    info = obter_info_coluna(obj.tabela_analisada, col)
                    detalhes.append({'coluna_negocio': info['nome'], 'coluna_tecnica': col, 'descricao': info['desc'], 'duplicatas': stats['duplicatas']})
        contexto['detalhes_enrich'] = detalhes

    # --- CORREÇÃO AQUI: Padronização das Variáveis ---
    elif tipo_metrica == 'regra_simples':
        obj = get_object_or_404(RelatorioRegraNegocio, pk=pk)
        contexto.update({'titulo': f"Regra: {obj.nome_regra}", 'obj': obj, 'formula': FORMULAS_QUALIDADE['consistencia'], 'tipo': 'regra'})
        
        # Padroniza nomes para o template
        contexto['total_analisado'] = obj.qtd_total_registros
        contexto['total_falhas'] = obj.qtd_falhas
        contexto['lista_exemplos'] = obj.exemplos_falhas

    elif tipo_metrica == 'regra_complexa':
        obj = get_object_or_404(RelatorioAnaliseRelacional, pk=pk)
        contexto.update({'titulo': f"Regra Cruzada: {obj.nome_analise}", 'obj': obj, 'formula': FORMULAS_QUALIDADE['consistencia'], 'tipo': 'regra'})
        
        # Padroniza nomes para o template
        contexto['total_analisado'] = obj.total_registros_analisados
        contexto['total_falhas'] = obj.total_inconsistencias
        contexto['lista_exemplos'] = obj.exemplos_inconsistencias
    # -------------------------------------------------

    return render(request, 'relatorios_gerenciais/relatorio_oficial.html', contexto)