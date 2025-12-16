# Dentro de: qualidade_ad/views.py
    
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .tasks import (
    executar_pipeline_completo_task, 
    importar_arquivos_existentes_task
)
from .models import (
    ExecucaoPipeline,
    DicionarioOrganograma, 
    HistoricoOrganograma
)
from .forms import OrganogramaForm

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

@login_required
def listar_organograma(request):
    unidades = DicionarioOrganograma.objects.all().order_by('nome')
    return render(request, 'qualidade_ad/organograma_list.html', {'unidades': unidades})

@login_required
def editar_unidade(request, pk):
    unidade = get_object_or_404(DicionarioOrganograma, pk=pk)
    nome_antigo = unidade.nome
    sigla_antiga = unidade.sigla
    
    if request.method == "POST":
        form = OrganogramaForm(request.POST, instance=unidade)
        if form.is_valid():
            nova_unidade = form.save()
            
            #  LÓGICA DE VERSIONAMENTO 
            detalhes = []
            if nome_antigo != nova_unidade.nome:
                detalhes.append(f"Nome mudou de '{nome_antigo}' para '{nova_unidade.nome}'")
            if sigla_antiga != nova_unidade.sigla:
                detalhes.append(f"Sigla mudou de '{sigla_antiga}' para '{nova_unidade.sigla}'")
            
            if detalhes:
                HistoricoOrganograma.objects.create(
                    unidade_afetada=nova_unidade,
                    acao='EDICAO',
                    detalhes="; ".join(detalhes),
                    responsavel=request.user
                )
                
                # TODO: AQUI ENTRARÁ A CHAMADA PARA ATUALIZAR O AD (CELERY TASK)
                # atualizar_ad_task.delay(nova_unidade.codigo_unidade, acao='RENOMEAR')
                
                messages.success(request, "Unidade atualizada com sucesso! Alterações registradas.")
            else:
                messages.info(request, "Nenhuma alteração detectada.")
                
            return redirect('listar_organograma')
    else:
        form = OrganogramaForm(instance=unidade)
    
    return render(request, 'qualidade_ad/organograma_form.html', {'form': form, 'titulo': 'Editar Unidade'})

@login_required
def criar_unidade(request):
    if request.method == "POST":
        form = OrganogramaForm(request.POST)
        if form.is_valid():
            nova_unidade = form.save()
            
            # Histórico
            HistoricoOrganograma.objects.create(
                unidade_afetada=nova_unidade,
                acao='CRIACAO',
                detalhes=f"Unidade criada manualmente: {nova_unidade.nome}",
                responsavel=request.user
            )
            
            # TODO: AQUI ENTRARÁ A CHAMADA PARA CRIAR NO AD
            # atualizar_ad_task.delay(nova_unidade.codigo_unidade, acao='CRIAR')

            messages.success(request, "Nova unidade criada!")
            return redirect('listar_organograma')
    else:
        form = OrganogramaForm()
    
    return render(request, 'qualidade_ad/organograma_form.html', {'form': form, 'titulo': 'Nova Unidade'})