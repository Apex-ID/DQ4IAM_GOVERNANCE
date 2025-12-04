from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AuditoriaAD, IncidenteQualidade

@receiver(post_save, sender=AuditoriaAD)
def validar_evento_ad(sender, instance, created, **kwargs):
    """
    Gatilho disparado toda vez que um novo log de auditoria chega.
    Verifica regras de negócio e abre incidentes se necessário.
    """
    if not created:
        return  # Só analisa registros novos

    dados = instance.dados_evento or {}
    violation_found = False
    
    # --- REGRA 1: CRIAÇÃO DE USUÁRIO SEM GERENTE ---
    # Se a ação for CREATE e o tipo for USER
    if instance.tipo_acao == 'CREATE' and instance.tipo_objeto == 'USER':
        gerente = dados.get('manager', '')
        
        if not gerente:
            violation_found = True
            IncidenteQualidade.objects.create(
                evento_auditoria=instance,
                regra_violada="Criação de Usuário sem Gerente",
                descricao_incidente=f"O técnico {instance.tecnico_ad_login} criou o usuário {instance.objeto_nome} sem definir o campo 'manager'.",
                responsavel_resolucao='AD_ADMIN', # Define quem resolve
                status='PENDENTE'
            )

    # --- REGRA 2: USUÁRIO CRIADO FORA DO PADRÃO (OU ERRADA) ---
    # Exemplo: Criou na raiz "CN=Users" em vez de uma OU específica
    if instance.tipo_acao == 'CREATE' and instance.tipo_objeto == 'USER':
        dn = instance.objeto_nome.upper() # DistinguishedName
        if "CN=USERS," in dn:
            violation_found = True
            IncidenteQualidade.objects.create(
                evento_auditoria=instance,
                regra_violada="Usuário criado em Container Padrão",
                descricao_incidente=f"O objeto {instance.objeto_nome} foi criado na pasta padrão 'CN=Users'. Deveria estar em uma OU departamental.",
                responsavel_resolucao='AD_ADMIN',
                status='PENDENTE'
            )

    # --- REGRA 3: ALTERAÇÃO EM GRUPO CRÍTICO (ADMINS) ---
    if instance.tipo_objeto == 'GROUP' and 'ADMIN' in instance.objeto_nome.upper():
        # Qualquer mexida em grupo de admin gera um alerta preventivo
        violation_found = True
        IncidenteQualidade.objects.create(
            evento_auditoria=instance,
            regra_violada="Alteração em Grupo Crítico",
            descricao_incidente=f"O grupo administrativo {instance.objeto_nome} foi modificado por {instance.tecnico_ad_login}. Requer validação imediata.",
            responsavel_resolucao='AD_ADMIN',
            status='PENDENTE'
        )

    # Se houve violação, marca o log original como "Violou Regras"
    if violation_found:
        instance.violou_regras = True
        instance.save()