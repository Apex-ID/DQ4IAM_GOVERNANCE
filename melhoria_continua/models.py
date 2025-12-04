from django.db import models
from django.contrib.auth.models import User

# 1. Definição das Responsabilidades (Áreas de Gestão)
RESPONSABILIDADES_CHOICES = [
    ('GRADUACAO', 'Gerente de Acadêmicos - Graduação'),
    ('POS_GRADUACAO', 'Gerente de Acadêmicos - Pós-Graduação'),
    ('EFETIVOS', 'Gerente de Funcionários Efetivos'),
    ('TERCEIRIZADOS', 'Gerente de Terceirizados'),
    ('COMPUTADORES', 'Gerente de Computadores e Infra'),
    ('AD_ADMIN', 'Gerente do Active Directory (Super Admin)'),
]

class PerfilGerente(models.Model):
    """
    Estende o usuário do Django para atribuir uma responsabilidade de governança.
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_governanca')
    responsabilidade = models.CharField(max_length=50, choices=RESPONSABILIDADES_CHOICES)
    
    def __str__(self):
        return f"{self.usuario.username} - {self.get_responsabilidade_display()}"

class AuditoriaAD(models.Model):
    """
    Tabela de Rastreabilidade Total (Audit Log).
    Recebe dados brutos do Agente no Servidor Windows.
    Registra TUDO que os técnicos fazem, certo ou errado.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Quem fez? (O técnico logado no Windows Server)
    tecnico_ad_login = models.CharField(max_length=100) 
    ip_origem = models.GenericIPAddressField(null=True, blank=True)
    
    # O que fez?
    tipo_acao = models.CharField(max_length=50) # Ex: CREATE, UPDATE, DELETE, MOVE
    tipo_objeto = models.CharField(max_length=50) # Ex: USER, GROUP, COMPUTER, GPO
    
    # Em quem?
    objeto_nome = models.CharField(max_length=200) # Ex: cn=joao.silva...
    objeto_guid = models.CharField(max_length=100, null=True, blank=True)
    
    # Detalhes técnicos (JSON com o antes e depois, se houver)
    dados_evento = models.JSONField(default=dict)
    
    # Flag de Violação (O sistema marca isso automaticamente após validar regras)
    violou_regras = models.BooleanField(default=False)

    def __str__(self):
        return f"LOG #{self.id}: {self.tipo_acao} em {self.objeto_nome} por {self.tecnico_ad_login}"

class IncidenteQualidade(models.Model):
    """
    O 'Ticket' gerado quando uma ação viola a Melhoria Contínua.
    Requer intervenção do Gerente.
    """
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente de Análise'),
        ('APROVADO_EXCECAO', 'Aprovado (Exceção Permitida)'),
        ('REJEITADO_CORRIGIR', 'Rejeitado (Necessita Correção)'),
        ('CORRIGIDO', 'Corrigido pelo Técnico'),
    ]

    # Vínculo com o evento original
    evento_auditoria = models.ForeignKey(AuditoriaAD, on_delete=models.CASCADE)
    
    data_abertura = models.DateTimeField(auto_now_add=True)
    
    # Qual regra foi quebrada? (Ex: "Usuário criado fora da OU padrão")
    regra_violada = models.CharField(max_length=200)
    descricao_incidente = models.TextField()
    
    # Quem deve resolver?
    responsavel_resolucao = models.CharField(max_length=50, choices=RESPONSABILIDADES_CHOICES)
    
    # Decisão do Gerente
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    gerente_decisor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    observacao_gerente = models.TextField(blank=True, null=True)
    data_fechamento = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Incidente #{self.id} ({self.status}): {self.regra_violada}"