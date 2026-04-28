from django.db import models

class MapeamentoCarga(models.Model):
    """
    Define a regra de transformação de Staging para Produção.
    Ex: Tabela A (Staging) -> Tabela B (Produção)
    """
    nome_mapeamento = models.CharField(max_length=100)
    
    # Origem (Staging - Geralmente no banco padrão do Django)
    tabela_origem = models.CharField(max_length=100) # ex: ad_users_staging
    
    # Destino (Produção - Pode ser em outro banco que acabamos de criar)
    banco_destino = models.CharField(max_length=100) # ex: DQ4IAM_producao
    tabela_destino = models.CharField(max_length=100) # ex: ad_users_final
    
    # O Mapa em si: JSON
    # Ex: {"cn": "nome_completo", "mail": "email_corp", "sAMAccountName": "login"}
    mapa_colunas = models.JSONField()
    
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome_mapeamento} ({self.tabela_origem} -> {self.tabela_destino})"
    
class HistoricoCarga(models.Model):
    data_execucao = models.DateTimeField(auto_now_add=True)
    tabela_origem = models.CharField(max_length=100)
    banco_destino = models.CharField(max_length=100)
    tabela_destino = models.CharField(max_length=100)
    status = models.CharField(max_length=20)
    mensagem = models.TextField()
    total_linhas = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.tabela_origem} -> {self.tabela_destino} ({self.status})"