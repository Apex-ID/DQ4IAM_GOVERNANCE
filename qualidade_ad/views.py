# qualidade_ad/views.py
    
import os
import csv
from django.conf import settings
from django.core.files.storage import FileSystemStorage
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
from .forms import OrganogramaForm, UploadOrganogramaForm

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

            messages.success(request, "Nova unidade criada!")
            return redirect('listar_organograma')
    else:
        form = OrganogramaForm()
    
    return render(request, 'qualidade_ad/organograma_form.html', {'form': form, 'titulo': 'Nova Unidade'})

@login_required
def deletar_unidade(request, pk):
    unidade = get_object_or_404(DicionarioOrganograma, pk=pk)
    if request.method == "POST":
        nome = unidade.nome
        unidade.delete()
        HistoricoOrganograma.objects.create(
            unidade_afetada=None, 
            acao='EXCLUSAO',
            detalhes=f"Unidade excluída: {nome}",
            responsavel=request.user
        )
        messages.success(request, f"Unidade {nome} excluída.")
        return redirect('listar_organograma')
    return render(request, 'qualidade_ad/organograma_confirm_delete.html', {'unidade': unidade})

@login_required
def upload_organograma(request):
    if request.method == 'POST' and request.FILES['arquivo_csv']:
        myfile = request.FILES['arquivo_csv']
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp'))
        filename = fs.save(myfile.name, myfile)
        file_path = fs.path(filename)

        # Salva o caminho na sessão para usar na confirmação
        request.session['csv_temp_path'] = file_path

        # -- ANÁLISE DO ARQUIVO (PREVIEW) --
        novos = []
        alterados = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, quotechar="'", delimiter=',')
                
                for row in reader:
                    codigo = row['codigo_unidade'].strip()
                    sigla = row['sigla'].strip()
                    nome = row['nome'].strip()
                    
                    try:
                        existente = DicionarioOrganograma.objects.get(pk=codigo)
                        # Verifica se mudou algo
                        if existente.nome != nome or existente.sigla != sigla:
                            alterados.append({
                                'codigo': codigo,
                                'antes': f"{existente.sigla} - {existente.nome}",
                                'depois': f"{sigla} - {nome}"
                            })
                    except DicionarioOrganograma.DoesNotExist:
                        novos.append({'codigo': codigo, 'sigla': sigla, 'nome': nome})
            
            return render(request, 'qualidade_ad/organograma_preview.html', {
                'novos': novos,
                'alterados': alterados,
                'total_novos': len(novos),
                'total_alterados': len(alterados)
            })

        except Exception as e:
            messages.error(request, f"Erro ao ler CSV: {e}")
            return redirect('listar_organograma')

    form = UploadOrganogramaForm()
    return render(request, 'qualidade_ad/organograma_upload.html', {'form': form})

@login_required
def confirmar_importacao(request):
    file_path = request.session.get('csv_temp_path')
    
    if not file_path or not os.path.exists(file_path):
        messages.error(request, "Arquivo temporário expirou. Faça upload novamente.")
        return redirect('upload_organograma')

    # Executa a gravação real
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, quotechar="'", delimiter=',')
            count = 0
            for row in reader:
                obj, created = DicionarioOrganograma.objects.update_or_create(
                    codigo_unidade=row['codigo_unidade'].strip(),
                    defaults={
                        'sigla': row['sigla'].strip(),
                        'nome': row['nome'].strip(),
                        'hierarquia': row['hierarquia'].strip()
                    }
                )
                if created:
                     HistoricoOrganograma.objects.create(
                        unidade_afetada=obj, acao='CRIACAO', detalhes="Importação CSV", responsavel=request.user
                    )
                count += 1
        
        # Limpa arquivo temp
        os.remove(file_path)
        del request.session['csv_temp_path']
        
        messages.success(request, f"Importação concluída! {count} registros processados.")
        return redirect('listar_organograma')

    except Exception as e:
        messages.error(request, f"Erro na gravação: {e}")
        return redirect('upload_organograma')