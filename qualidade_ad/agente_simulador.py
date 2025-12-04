import requests
import json
import random
import time
from datetime import datetime

# Configuração
URL_API = "http://127.0.0.1:8000/api/auditoria/receber/"
TECNICOS = ["admin.joao", "admin.maria", "suporte.pedro", "automacao.script"]

def gerar_evento_simulado():
    """
    Gera um evento de AD aleatório.
    Alguns violarão as regras de negócio propositalmente.
    """
    tipo = random.choice(['USER', 'GROUP', 'COMPUTER'])
    acao = random.choice(['CREATE', 'UPDATE', 'DELETE'])
    tecnico = random.choice(TECNICOS)
    
    payload = {
        "tecnico": tecnico,
        "acao": acao,
        "tipo_objeto": tipo,
        "objeto": "",
        "detalhes": {}
    }

    # CENÁRIO 1: VIOLAÇÃO - Usuário sem Gerente (Regra de Completude)
    if tipo == 'USER' and acao == 'CREATE' and random.random() < 0.4: # 40% de chance de erro
        nome = f"aluno.teste.{random.randint(1000,9999)}"
        payload["objeto"] = f"CN={nome},OU=Alunos,DC=ufs,DC=br"
        payload["detalhes"] = {
            "sAMAccountName": nome,
            "manager": "" # <--- ERRO: Vazio!
        }
        print(f"⚠️  [SIMULADOR] Gerando ERRO: Usuário sem gerente ({nome})")

    # CENÁRIO 2: VIOLAÇÃO - Usuário no Container Errado (Regra de Consistência)
    elif tipo == 'USER' and acao == 'CREATE' and random.random() < 0.4:
        nome = f"funcionario.{random.randint(1000,9999)}"
        payload["objeto"] = f"CN={nome},CN=Users,DC=ufs,DC=br" # <--- ERRO: CN=Users
        payload["detalhes"] = {
            "sAMAccountName": nome,
            "manager": "CN=Gerente,OU=TI..."
        }
        print(f"⚠️  [SIMULADOR] Gerando ERRO: Usuário fora de padrão ({nome})")

    # CENÁRIO 3: VIOLAÇÃO - Alteração em Grupo Admin (Regra de Segurança)
    elif tipo == 'GROUP' and acao == 'UPDATE' and random.random() < 0.3:
        grupo = "Domain Admins"
        payload["objeto"] = f"CN={grupo},CN=Users,DC=ufs,DC=br"
        payload["detalhes"] = {"member": "adicionou hacker_01"}
        print(f"🚨 [SIMULADOR] Gerando ALERTA: Alteração em Grupo Crítico ({grupo})")

    # CENÁRIO 4: SUCESSO - Tudo certo
    else:
        nome = f"objeto.ok.{random.randint(1000,9999)}"
        payload["objeto"] = f"CN={nome},OU=Correto,DC=ufs,DC=br"
        payload["detalhes"] = {"manager": "CN=Chefe,OU=TI...", "description": "Tudo certo"}
        print(f"✅ [SIMULADOR] Gerando evento normal...")

    return payload

def enviar_para_api():
    evento = gerar_evento_simulado()
    try:
        response = requests.post(URL_API, json=evento)
        if response.status_code == 201:
            print(f"   -> Enviado com sucesso! ID: {response.json().get('id_log')}")
        else:
            print(f"   -> Erro no envio: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   -> Falha de conexão: {e}")

if __name__ == "__main__":
    print(f"--- INICIANDO AGENTE SIMULADOR DE AD ---")
    print(f"Alvo: {URL_API}\n")
    
    while True:
        enviar_para_api()
        # Espera entre 2 e 5 segundos para o próximo evento
        tempo_espera = random.randint(2, 5)
        time.sleep(tempo_espera)