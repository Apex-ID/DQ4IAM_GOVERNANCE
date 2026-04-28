# qualidade_ad/views.py
    
from datetime import timezone
import os
import csv
import re
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .tasks import (
    executar_pipeline_completo_task, 
    importar_arquivos_existentes_task
)
from .models import (
    ExecucaoPipeline,
    DicionarioOrganograma, 
    HistoricoOrganograma,
    IdentidadeConsolidada,
    VinculoRH
)
from .forms import (
    OrganogramaForm, 
    UploadOrganogramaForm,
    UploadVinculosForm
)

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
        'titulo': 'DQ4IAM - Painel de Carga de Dados (ETL)',
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
    # Pega a hierarquia do pai da URL (se houver)
    parent_hier = request.GET.get('parent_hier', '')
    initial_data = {}
    
    if parent_hier:
        # Se o pai é .605.18., sugere que o filho comece com isso
        initial_data = {'hierarquia': parent_hier}

    if request.method == "POST":
        form = OrganogramaForm(request.POST)
        if form.is_valid():
            # ... (código de salvar igual ao anterior) ...
            messages.success(request, "Nova unidade criada!")
            return redirect('explorer_organograma') # Redireciona para a árvore
    else:
        form = OrganogramaForm(initial=initial_data) # Preenche o form
    
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

# --- GESTÃO DE IDENTIDADE (FONTE DA VERDADE) ---

@login_required
def upload_vinculos_rh(request):
    if request.method == 'POST' and request.FILES.get('arquivo_csv'):
        myfile = request.FILES['arquivo_csv']
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp'))
        filename = fs.save(myfile.name, myfile)
        file_path = fs.path(filename)

        try:
            # Apaga dados anteriores para ter uma foto limpa
            VinculoRH.objects.all().delete()
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, quotechar="'", delimiter=',')
                
                buffer_vinculos = []
                
                for row in reader:
                    # Limpeza de dados (Trim e Upper)
                    # Verifica se a chave existe antes de acessar para evitar KeyError
                    status_raw = row.get('status_rh', '')
                    status_limpo = status_raw.strip().upper()
                    
                    vinculo = VinculoRH(
                        samaccountname=row.get('samaccountname', '').strip(),
                        nome=row.get('nome_completo', '').strip(),
                        email=row.get('email_correto', '').strip(),
                        departamento_string=row.get('departamento_correto', '').strip(),
                        cargo=row.get('cargo_correto', '').strip(),
                        gerente_login=row.get('gerente_correto_login', '').strip(),
                        status_rh=status_limpo
                    )
                    buffer_vinculos.append(vinculo)
                
                # Bulk Create para performance
                VinculoRH.objects.bulk_create(buffer_vinculos)
                
            os.remove(file_path)
            messages.success(request, f"Sucesso! {len(buffer_vinculos)} inhas importadas. Agora clique em 'Processar Regras' para atualizar o Golden Record.")
            return redirect('listar_identidades')

        except Exception as e:
            messages.error(request, f"Erro na importação: {e}")
            return redirect('upload_vinculos_rh')

    form = UploadVinculosForm()
    return render(request, 'qualidade_ad/upload_generico.html', {'form': form, 'titulo': 'Importar Fonte da Verdade (RH)'})

@login_required
def processar_consolidacao(request):
    """
    Lê a tabela VinculoRH (bruta), aplica as regras de negócio 
    e popula a IdentidadeConsolidada (limpa).
    """
    # 1. Limpar tabela de consolidação anterior
    IdentidadeConsolidada.objects.all().delete()
    
    # 2. Pegar lista de logins únicos
    logins_unicos = VinculoRH.objects.values_list('samaccountname', flat=True).distinct()
    
    identidades_buffer = []
    
    for login in logins_unicos:
        vinculos = VinculoRH.objects.filter(samaccountname=login)
        
        # --- REGRA 1: DEFINIR STATUS ---
        vinculo_ativo = vinculos.filter(status_rh__icontains='ATIVO').first()
        
        if vinculo_ativo:
            status_final = 'ATIVO'
            vinculo_principal = vinculo_ativo
        else:
            status_final = 'INATIVO' 
            vinculo_principal = vinculos.first()
            
        # --- REGRA 2: EXTRAIR CÓDIGO DA LOTAÇÃO ---
        codigo_lotacao = None
        sigla_lotacao = None
        ggs = []

        if status_final == 'ATIVO':
            texto_depto = vinculo_principal.departamento_string
            match = re.search(r'(\d+)\s*$', texto_depto)
            
            if match:
                codigo_lotacao = match.group(1)
                try:
                    unidade = DicionarioOrganograma.objects.get(pk=codigo_lotacao)
                    sigla_lotacao = unidade.sigla
                    
                    # --- REGRA 3: DEFINIR GGs ---
                    cargo = vinculo_principal.cargo.upper()
                    
                    if 'PROFESSOR' in cargo or 'DOCENTE' in cargo:
                        ggs.append(f"GG_{sigla_lotacao}_DOCENTES")
                        ggs.append(f"GG_{sigla_lotacao}_IMPRESSAO")
                    elif 'TECNICO' in cargo:
                        ggs.append(f"GG_{sigla_lotacao}_ADMINISTRATIVO")
                        ggs.append(f"GG_{sigla_lotacao}_IMPRESSAO")
                        
                except DicionarioOrganograma.DoesNotExist:
                    sigla_lotacao = "NAO_ENCONTRADO"
            
            if 'DISCENTE' in vinculo_principal.cargo.lower():
                ggs.append("GG_ALUNOS_GENERICO") 

        identidade = IdentidadeConsolidada(
            samaccountname=login,
            nome_completo=vinculo_principal.nome,
            status_calculado=status_final,
            lotacao_codigo=codigo_lotacao,
            lotacao_sigla=sigla_lotacao,
            ggs_sugeridas=", ".join(ggs)
        )
        identidades_buffer.append(identidade)
    
    IdentidadeConsolidada.objects.bulk_create(identidades_buffer)
    
    messages.success(request, f"Processamento concluído! {len(identidades_buffer)} identidades consolidadas.")
    return redirect('listar_identidades')

@login_required
def listar_identidades(request):
    identidades = IdentidadeConsolidada.objects.all().order_by('nome_completo')
    return render(request, 'qualidade_ad/identidades_list.html', {'identidades': identidades})



@login_required
def processar_consolidacao(request):
    """
    Lê a tabela VinculoRH (bruta), aplica as regras de negócio 
    e popula a IdentidadeConsolidada (limpa).
    """
    # 1. Limpar tabela de consolidação anterior (Recomeçar do zero)
    IdentidadeConsolidada.objects.all().delete()
    
    # 2. Pegar lista de logins únicos na tabela bruta
    logins_unicos = VinculoRH.objects.values_list('samaccountname', flat=True).distinct()
    
    identidades_buffer = []
    
    for login in logins_unicos:
        # Pega todas as linhas desse usuário (Ex: as 6 linhas do aaronsena)
        vinculos = VinculoRH.objects.filter(samaccountname=login)
        
        # --- REGRA 1: DEFINIR STATUS ---
        # Se tiver PELO MENOS UMA linha contendo "ATIVO", o usuário é ATIVO.
        # Usamos icontains para ignorar maiúsculas/minúsculas
        vinculo_ativo = vinculos.filter(status_rh__icontains='ATIVO').first()
        
        if vinculo_ativo:
            status_final = 'ATIVO'
            vinculo_principal = vinculo_ativo # A linha ativa é a que manda na lotação
        else:
            status_final = 'INATIVO' 
            vinculo_principal = vinculos.first() # Pega qualquer uma só para ter o nome
            
        # --- REGRA 2: EXTRAIR CÓDIGO DA LOTAÇÃO ---
        codigo_lotacao = None
        sigla_lotacao = None
        ggs = []

        if status_final == 'ATIVO':
            texto_depto = vinculo_principal.departamento_string # "DHI ... - 112406 "
            
            # REGEX: Procura dígitos no final da string
            match = re.search(r'(\d+)\s*$', texto_depto)
            
            if match:
                codigo_lotacao = match.group(1) # "112406"
                
                # Busca no Organograma Oficial
                try:
                    unidade = DicionarioOrganograma.objects.get(pk=codigo_lotacao)
                    sigla_lotacao = unidade.sigla # "DHI"
                    
                    # --- REGRA 3: DEFINIR GGs ---
                    cargo = vinculo_principal.cargo.upper()
                    
                    if 'PROFESSOR' in cargo or 'DOCENTE' in cargo:
                        ggs.append(f"GG_{sigla_lotacao}_DOCENTES")
                        ggs.append(f"GG_{sigla_lotacao}_IMPRESSAO")
                    elif 'TECNICO' in cargo:
                        ggs.append(f"GG_{sigla_lotacao}_ADMINISTRATIVO")
                        ggs.append(f"GG_{sigla_lotacao}_IMPRESSAO")
                        
                except DicionarioOrganograma.DoesNotExist:
                    sigla_lotacao = "NAO_ENCONTRADO"
            
            # Tratamento especial para ALUNOS (que não costumam ter código numérico no final)
            if 'DISCENTE' in vinculo_principal.cargo.lower():
                ggs.append("GG_ALUNOS_GENERICO") 

        # Cria o objeto na memória
        identidade = IdentidadeConsolidada(
            samaccountname=login,
            nome_completo=vinculo_principal.nome,
            status_calculado=status_final,
            lotacao_codigo=codigo_lotacao,
            lotacao_sigla=sigla_lotacao,
            ggs_sugeridas=", ".join(ggs)
        )
        identidades_buffer.append(identidade)
    
    # Salva tudo no banco de uma vez
    IdentidadeConsolidada.objects.bulk_create(identidades_buffer)
    
    messages.success(request, f"Processamento concluído! {len(identidades_buffer)} identidades consolidadas.")
    return redirect('listar_identidades')

@login_required
def listar_identidades(request):
    """
    Mostra o resultado final.
    """
    identidades = IdentidadeConsolidada.objects.all().order_by('nome_completo')
    return render(request, 'qualidade_ad/identidades_list.html', {'identidades': identidades})


@login_required
def explorer_organograma(request):
    """
    Renderiza o Organograma em formato de Árvore Visual.
    Calcula o nível de profundidade baseado nos pontos da hierarquia.
    """
    # Ordena por hierarquia é VITAL para a árvore ser montada na ordem certa
    unidades = DicionarioOrganograma.objects.all().order_by('hierarquia')
    
    # Processamento para identificar o nível (recuo)
    arvore = []
    for u in unidades:
        #HUMBERTO SE TIVER DUVIDA ME PERGUNTE
        # Conta quantos pontos tem. 
        # Ex: .605. (2 pontos) -> Nível 0
        # Ex: .605.102. (3 pontos) -> Nível 1
        # Ex: .605.102.109. (4 pontos) -> Nível 2
        nivel = u.hierarquia.count('.') - 2 
        if nivel < 0: nivel = 0
        
        arvore.append({
            'obj': u,
            'nivel': nivel,
            'pixel_indent': nivel * 40, # 40px de recuo por nível
            'eh_pai': False # Logica futura se quiser ícone de pasta
        })

    return render(request, 'qualidade_ad/organograma_tree.html', {
        'arvore': arvore,
        'titulo': 'Explorer do Organograma Institucional'
    })

@login_required
def relatorio_organograma_pdf(request):
    """
    Gera uma versão imprimível (Print Friendly) que pode ser salva como PDF.
    """
    unidades = DicionarioOrganograma.objects.all().order_by('hierarquia')
    lista_impressao = []
    
    for u in unidades:
        nivel = u.hierarquia.count('.') - 2
        if nivel < 0: nivel = 0
        lista_impressao.append({
            'codigo': u.codigo_unidade,
            'hierarquia': u.hierarquia,
            'sigla': u.sigla,
            'nome': u.nome,
            'espacos': '&nbsp;' * (nivel * 8) # Espaços para simular recuo no texto
        })
        
    return render(request, 'qualidade_ad/relatorio_pdf_organograma.html', {
        'lista': lista_impressao,
        'data_geracao': timezone.now()
    })

