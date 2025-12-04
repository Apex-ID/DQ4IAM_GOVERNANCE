from django.db import models

class RelatorioAnaliseRelacional(models.Model):
    """
    Armazena resultados de análises que cruzam múltiplas tabelas
    (Consistência de Integridade e Acurácia).
    """
    timestamp_inicio = models.DateTimeField(auto_now_add=True)
    nome_analise = models.CharField(max_length=200)
    tabelas_envolvidas = models.CharField(max_length=200)
    total_registros_analisados = models.BigIntegerField()
    total_inconsistencias = models.BigIntegerField()
    percentual_consistencia = models.FloatField()
    descricao_impacto = models.TextField()
    exemplos_inconsistencias = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.nome_analise} ({self.timestamp_inicio.strftime('%Y-%m-%d %H:%M')})"


class RelatorioDQI(models.Model):
    """
    Data Quality Index - O Score Final.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Define se o DQI é da carga (Staging) ou do ambiente real (Produção)
    tipo_ambiente = models.CharField(max_length=20, default='PRODUCAO') 
    
    score_total = models.FloatField()
    score_completude = models.FloatField()
    score_validade = models.FloatField()
    score_unicidade = models.FloatField()
    score_consistencia = models.FloatField()

    def __str__(self):
        return f"DQI {self.tipo_ambiente}: {self.score_total:.1f} ({self.timestamp})"

    @property
    def cor_status(self):
        if self.score_total > 80: return '#28a745' # Verde
        elif self.score_total > 60: return '#ffc107' # Amarelo
        else: return '#dc3545' # Vermelho


class RelatorioRiscoSenha(models.Model):
    """
    Histograma de idade da senha (Password Age).
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    total_contas = models.IntegerField()
    faixa_verde_90dias = models.IntegerField()
    faixa_amarela_180dias = models.IntegerField()
    faixa_vermelha_1ano = models.IntegerField()
    faixa_critica_velha = models.IntegerField()

    def __str__(self):
        return f"Risco Senha ({self.timestamp})"

    # Métodos auxiliares para o Template (evita lógica no HTML)
    def _calc_pct(self, valor):
        return (valor / self.total_contas * 100) if self.total_contas > 0 else 0

    @property
    def perc_verde(self): return self._calc_pct(self.faixa_verde_90dias)
    @property
    def perc_amarela(self): return self._calc_pct(self.faixa_amarela_180dias)
    @property
    def perc_vermelha(self): return self._calc_pct(self.faixa_vermelha_1ano)
    @property
    def perc_critica(self): return self._calc_pct(self.faixa_critica_velha)


class RelatorioScorecard(models.Model):
    """
    Armazena o resumo da análise de qualidade POR LINHA (Scorecard).
    Gera um CSV completo e guarda os 'Top Ofensores' em JSON.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Caminho para o arquivo CSV gerado
    arquivo_csv = models.CharField(max_length=500, null=True, blank=True)
    
    # Resumo Quantitativo
    total_objetos_analisados = models.IntegerField(default=0)
    total_objetos_com_falha = models.IntegerField(default=0)
    media_falhas_por_objeto = models.FloatField(default=0.0)
    
    # JSON com os top 50 piores registros
    top_ofensores = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Scorecard Geral ({self.timestamp.strftime('%d/%m/%Y %H:%M')})"