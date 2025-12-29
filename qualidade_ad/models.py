# qualidade_ad/models.py

from django.db import models
from django.contrib.auth.models import User

class ExecucaoPipeline(models.Model):
    """
    Representa uma única execução completa do pipeline.
    """
    STATUS_CHOICES = [
        ('INICIADO', 'Iniciado'),
        ('EM_PROGRESSO', 'Em Progresso'),
        ('CONCLUIDO', 'Concluído'),
        ('FALHOU', 'Falhou'),
    ]
    
    timestamp_inicio = models.DateTimeField(auto_now_add=True)
    timestamp_fim = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INICIADO')
    
    def __str__(self):
        return f"Execução #{self.id} - {self.get_status_display()}"

class LogEtapa(models.Model):
    """
    Registra o resultado de uma etapa específica.
    """
    ETAPAS_CHOICES = [
        ('ETAPA_1_EXTRACAO', 'Etapa 1: Extração AD'),
        ('ETAPA_2_LIMPEZA', 'Etapa 2: Limpeza de CSVs'),
        ('ETAPA_3_PREPARACAO_BANCO', 'Etapa 3: Preparação do Banco'),
        ('ETAPA_4_CARGA_STAGING', 'Etapa 4: Carga para Staging'),
        ('ETAPA_5_TRANSFORMACAO', 'Etapa 5: Transformação (Produção)'),
        ('ETAPA_DESCONHECIDA', 'Etapa Desconhecida'),
    ]
    
    STATUS_CHOICES = [
        ('SUCESSO', 'Sucesso'),
        ('FALHOU', 'Falhou'),
    ]

    execucao = models.ForeignKey(ExecucaoPipeline, related_name='logs_etapas', on_delete=models.CASCADE)
    etapa_nome = models.CharField(max_length=50, choices=ETAPAS_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    timestamp_inicio = models.DateTimeField()
    timestamp_fim = models.DateTimeField()
    resumo_execucao = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Log {self.etapa_nome} (Execução #{self.execucao.id}) - {self.status}"
    
class BaseConhecimentoRH(models.Model):
    """
    Tabela que armazena a Cópia Dourada (Source of Truth) importada do sistema acadêmico/RH.
    """
    samaccountname = models.CharField(max_length=255, primary_key=True) # Chave de cruzamento
    status_rh = models.CharField(max_length=100) # Ativo, Cancelado, Concluído
    departamento_correto = models.CharField(max_length=255, null=True, blank=True)
    cargo_correto = models.CharField(max_length=255, null=True, blank=True)
    gerente_correto_login = models.CharField(max_length=255, null=True, blank=True)
    nome_completo = models.CharField(max_length=255, null=True, blank=True)
    email_correto = models.CharField(max_length=255, null=True, blank=True)
    
    data_importacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.samaccountname} ({self.status_rh})"

class MapeamentoDepartamentoGrupo(models.Model):
    """
    Traduz o nome do setor no CSV para o nome do Grupo no AD.
    Ex: 'DCOMP - DEPARTAMENTO DE COMPUTAÇÃO' -> 'GG_DCOMP'
    """
    departamento_rh = models.CharField(max_length=255, unique=True) # Como vem no CSV
    prefixo_grupo_ad = models.CharField(max_length=100) # Ex: GG_DCOMP
    
    # Se quiser separar por tipo (Admin/Impressão), pode ter sufixos
    # Mas o básico é saber qual a sigla da unidade.

class UsuarioUnificado(models.Model):
    """
    O 'Golden Record'. Representa o estado DESEJADO do usuário no AD
    após processar todas as suas linhas do CSV.
    """
    samaccountname = models.CharField(max_length=255, primary_key=True)
    nome_completo = models.CharField(max_length=255)
    email_oficial = models.CharField(max_length=255)
    
    # Status calculado: Se tiver pelo menos 1 vínculo ativo, é TRUE.
    deve_estar_ativo = models.BooleanField(default=False)
    
    # Lista calculada de grupos que ele DEVE ter (JSON)
    # Ex: ['GG_CP_ADMINISTRATIVO', 'GG_MEIOAMB_DISCENTES']
    grupos_calculados = models.JSONField(default=list)
    
    # Log de quais linhas do CSV geraram esse registro
    perfis_origem = models.JSONField(default=list)
    
    data_processamento = models.DateTimeField(auto_now=True)   


class DicionarioOrganograma(models.Model):
    """
    Representa a estrutura oficial (Setores/Unidades).
    Dados importados do CSV e gerenciáveis pelos técnicos.
    """
    codigo_unidade = models.CharField(max_length=50, primary_key=True, help_text="Código único (ex: 112406)")
    sigla = models.CharField(max_length=50, null=True, blank=True)
    nome = models.CharField(max_length=255)
    hierarquia = models.CharField(max_length=100, help_text="Ex: .605.102.109.")
    
    # Controle de sistema
    data_criacao = models.DateTimeField(auto_now_add=True)
    ultima_atualizacao = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.sigla} - {self.nome} ({self.codigo_unidade})"

class HistoricoOrganograma(models.Model):
    """
    Guarda as versões e alterações feitas no Organograma.
    """
    Acoes = [
        ('CRIACAO', 'Criação'),
        ('EDICAO', 'Edição/Renomeação'),
        ('IMPORTACAO', 'Importação CSV'),
    ]

    unidade_afetada = models.ForeignKey(DicionarioOrganograma, on_delete=models.CASCADE)
    acao = models.CharField(max_length=20, choices=Acoes)
    
    # O que mudou?
    detalhes = models.TextField(help_text="Ex: Nome alterado de 'DHI' para 'DHIST'")
    
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    data_evento = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.acao} em {self.unidade_afetada} - {self.data_evento}"
    
class VinculoRH(models.Model):
    """
    Fonte da Verdade Bruta (Importada do CSV).
    """
    # Identificação
    samaccountname = models.CharField(max_length=100, db_index=True)
    nome = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    
    # Dados Organizacionais
    departamento_string = models.CharField(max_length=255) 
    cargo = models.CharField(max_length=255)
    gerente_login = models.CharField(max_length=100, null=True, blank=True)
    
    # Status
    status_rh = models.CharField(max_length=100)
    
    data_importacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vínculo de RH"
        verbose_name_plural = "Vínculos de RH"

    def __str__(self):
        return f"{self.samaccountname} - {self.status_rh}"

class IdentidadeConsolidada(models.Model):
    """
    Tabela Final: Um registro único por pessoa (Login), 
    com o status calculado e as GGs definidas.
    """
    samaccountname = models.CharField(max_length=100, primary_key=True)
    nome_completo = models.CharField(max_length=255)
    
    # Status Final (ATIVO ou INATIVO)
    status_calculado = models.CharField(max_length=50) 
    
    # Dados Organizacionais (Limpos)
    lotacao_codigo = models.CharField(max_length=50, null=True, blank=True)
    lotacao_sigla = models.CharField(max_length=50, null=True, blank=True)
    
    # Grupos Calculados
    ggs_sugeridas = models.TextField(blank=True, help_text="Grupos separados por vírgula")
    
    data_processamento = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.samaccountname} ({self.status_calculado})"
    
class IdentidadeConsolidada(models.Model):
    """
    O 'Golden Record'. Resultado do processamento de múltiplos vínculos.
    Aqui decidimos quem o usuário É, baseados em todas as suas linhas do CSV.
    """
    samaccountname = models.CharField(max_length=100, primary_key=True)
    nome_completo = models.CharField(max_length=255)
    
    # Status Calculado (Se tiver 1 ativo, vira ATIVO)
    status_calculado = models.CharField(max_length=50) 
    
    # O Vínculo "Vencedor" (Aquele que está ativo e definiu a lotação)
    lotacao_codigo = models.CharField(max_length=50, null=True, blank=True) # Ex: 112406
    lotacao_sigla = models.CharField(max_length=50, null=True, blank=True) # Ex: DHI (Vem do Organograma)
    tipo_vinculo_principal = models.CharField(max_length=100, null=True, blank=True) # Ex: DOCENTE
    
    # GGs Sugeridas (Lista separada por vírgula para visualização)
    ggs_sugeridas = models.TextField(help_text="Lista de GGs calculadas baseadas na regra", blank=True)
    
    data_processamento = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.samaccountname} - {self.status_calculado}"