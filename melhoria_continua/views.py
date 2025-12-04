from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required 
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
import json
import logging
from .models import AuditoriaAD, IncidenteQualidade

logger = logging.getLogger(__name__)

@csrf_exempt
def api_receber_auditoria(request):
    """
    Endpoint API para receber logs enviados pelo Agente Windows.

    **Método:** ``POST``  
    **Content-Type:** ``application/json``

    **Payload esperado (exemplo):**

    .. code-block:: json

        {
            "tecnico": "admin.joao",
            "acao": "CREATE",
            "tipo_objeto": "USER",
            "objeto": "cn=aluno.novo,ou=...",
            "detalhes": {}
        }

    **Retornos:**
    - ``201`` – Registro criado com sucesso
    - ``400`` – JSON inválido
    - ``405`` – Método não permitido
    - ``500`` – Erro interno
    """
    
    if request.method != 'POST':
        return JsonResponse({'erro': 'Método não permitido. Use POST.'}, status=405)

    try:
        # 1. Decodifica o JSON recebido
        dados = json.loads(request.body)
        
        # 2. Extrai os campos (com valores padrão para evitar erro)
        tecnico = dados.get('tecnico', 'SISTEMA')
        acao = dados.get('acao', 'UNKNOWN')
        tipo_obj = dados.get('tipo_objeto', 'UNKNOWN')
        objeto = dados.get('objeto', 'Desconhecido')
        detalhes = dados.get('detalhes', {})
        ip = request.META.get('REMOTE_ADDR') # Pega o IP de quem enviou

        # 3. Cria o registro de Auditoria
        registro = AuditoriaAD.objects.create(
            tecnico_ad_login=tecnico,
            ip_origem=ip,
            tipo_acao=acao,
            tipo_objeto=tipo_obj,
            objeto_nome=objeto,
            dados_evento=detalhes,
            timestamp=timezone.now()
        )
        
        logger.info(f"[API AUDITORIA] Novo evento recebido: {registro}")

        # 4. (GATILHO FUTURO) Aqui chamaremos o Motor de Validação em Tempo Real
        # verificar_regras_melhoria_continua(registro)

        return JsonResponse({
            'status': 'sucesso', 
            'mensagem': 'Evento registrado.', 
            'id_log': registro.id
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'erro': 'JSON inválido.'}, status=400)
    except Exception as e:
        logger.error(f"Erro na API: {e}")
        return JsonResponse({'erro': str(e)}, status=500)

@login_required
def painel_gestao_incidentes(request):
    """
    Tela onde os gerentes veem os problemas e tomam decisões.
    """
    # Busca apenas o que está pendente
    incidentes_pendentes = IncidenteQualidade.objects.filter(status='PENDENTE').order_by('-data_abertura')
    
    # Busca histórico recente de resolvidos
    incidentes_resolvidos = IncidenteQualidade.objects.exclude(status='PENDENTE').order_by('-data_fechamento')[:10]

    context = {
        'titulo': 'Central de Melhoria Contínua (Gestão de Incidentes)',
        'pendentes': incidentes_pendentes,
        'resolvidos': incidentes_resolvidos
    }
    return render(request, 'melhoria_continua/painel_gerente.html', context)

@login_required
def tratar_incidente(request, pk):
    """
    Processa a decisão do gerente (Aprovar ou Rejeitar).
    """
    if request.method != 'POST':
        return redirect('painel_gestao_incidentes')
    
    incidente = get_object_or_404(IncidenteQualidade, pk=pk)
    acao = request.POST.get('acao')
    observacao = request.POST.get('observacao', '')
    
    if acao == 'aprovar':
        incidente.status = 'APROVADO_EXCECAO'
        msg = 'Incidente aprovado como exceção.'
    elif acao == 'rejeitar':
        incidente.status = 'REJEITADO_CORRIGIR'
        msg = 'Incidente rejeitado. Técnico será notificado para corrigir.'
    elif acao == 'corrigido':
        incidente.status = 'CORRIGIDO'
        msg = 'Incidente marcado como corrigido.'
    else:
        return redirect('painel_gestao_incidentes')

    # Registra quem decidiu e quando
    incidente.gerente_decisor = request.user
    incidente.observacao_gerente = observacao
    incidente.data_fechamento = timezone.now()
    incidente.save()
    
    messages.success(request, f"Sucesso: {msg}")
    return redirect('painel_gestao_incidentes')