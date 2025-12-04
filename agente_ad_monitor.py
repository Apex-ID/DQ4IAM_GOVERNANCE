import win32evtlog # type: ignore
import xml.etree.ElementTree as ET
import requests
import time
import socket
import json
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO ---
# Substitua pelo IP do seu servidor Linux onde o Django está rodando
URL_API = "http://10.110.1.69:8000/api/auditoria/receber/" 

# IDs de Eventos do Windows que queremos monitorar
EVENTOS_MONITORADOS = {
    4720: 'CREATE',   # Um usuário foi criado
    4722: 'ENABLE',   # Uma conta de usuário foi habilitada
    4725: 'DISABLE',  # Uma conta de usuário foi desabilitada
    4726: 'DELETE',   # Uma conta de usuário foi excluída
    4738: 'UPDATE',   # Uma conta de usuário foi alterada
    4723: 'PASSWORD', # Tentativa de alteração de senha
    
    # Grupos
    4727: 'CREATE_GROUP', # Grupo criado
    4728: 'ADD_MEMBER',   # Membro adicionado a grupo
    4729: 'REM_MEMBER',   # Membro removido de grupo
    4730: 'DEL_GROUP',    # Grupo deletado
}

def obter_xml_evento(handle, flags, record_number):
    """Lê o XML detalhado do evento do Windows."""
    events = win32evtlog.EvtQuery(handle, win32evtlog.EvtQueryChannelPath, "Security", f"*[System[(EventID={record_number})]]")
    event = list(win32evtlog.EvtNext(events, 1))[0]
    return win32evtlog.EvtRender(event, win32evtlog.EvtRenderEventXml)

def parse_evento_xml(xml_str):
    """Extrai quem fez (Técnico) e o que foi afetado (Objeto) do XML."""
    root = ET.fromstring(xml_str)
    
    # Namespaces do XML do Windows Event Log
    ns = {'ns': 'http://schemas.microsoft.com/win/2004/08/events/event'}
    
    data = {}
    for data_item in root.findall('.//ns:EventData/ns:Data', ns):
        name = data_item.get('Name')
        val = data_item.text
        if name and val:
            data[name] = val
            
    # Mapeamento Padrão
    # SubjectUserName = Quem fez a ação (O Técnico)
    # TargetUserName / SamAccountName = Quem sofreu a ação (O Objeto)
    
    tecnico = data.get('SubjectUserName', 'SYSTEM')
    objeto_login = data.get('TargetUserName', data.get('SamAccountName', 'Desconhecido'))
    domain = data.get('TargetDomainName', '')
    
    # Tenta pegar o DN se disponível, senão monta um fake
    objeto_dn = data.get('DistinguishedName', f"CN={objeto_login},CN=Users,DC={domain},DC=local")

    return {
        'tecnico': tecnico,
        'objeto_nome': objeto_dn,
        'detalhes': data
    }

def monitorar_logs():
    server = 'localhost' # Monitora a própria máquina
    log_type = 'Security'
    
    print(f"--- INICIANDO AGENTE APEX NO SERVIDOR {socket.gethostname()} ---")
    print(f"Alvo API: {URL_API}")
    print("Monitorando eventos de segurança do Active Directory...")

    # Abre o log de segurança
    hand = win32evtlog.OpenEventLog(server, log_type)
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
    
    # Lê o último registro para saber onde começar (para não ler o passado inteiro)
    total = win32evtlog.GetNumberOfEventLogRecords(hand)
    print(f"Total de eventos no log: {total}")
    
    ultimo_indice_lido = total
    
    while True:
        # Verifica se há novos eventos
        novo_total = win32evtlog.GetNumberOfEventLogRecords(hand)
        
        if novo_total > ultimo_indice_lido:
            # Lê apenas os novos
            try:
                # Aqui usamos uma abordagem simplificada: lemos os últimos e filtramos
                # Em produção real, usaríamos a API EvtSubscribe, mas esta lógica funciona bem para TCC
                
                events = win32evtlog.ReadEventLog(hand, flags, 0)
                # Nota: ReadEventLog lê em blocos. O loop garante a leitura.
                
                for event in events:
                    event_id = event.EventID & 0xFFFF # Máscara para pegar o ID real
                    
                    # Se for um evento que nos interessa
                    if event_id in EVENTOS_MONITORADOS:
                        
                        # Evita processar eventos muito antigos se o loop for grande
                        tempo_evento = event.TimeGenerated
                        if (datetime.now() - tempo_evento).total_seconds() > 60:
                            continue 

                        acao = EVENTOS_MONITORADOS[event_id]
                        
                        # Extrai dados básicos (string list) - Método rápido
                        # O Windows retorna uma lista de strings. A ordem muda por evento.
                        # Geralmente: String[0] ou [1] é o técnico, String[5] ou [6] é o alvo.
                        # Para precisão total, o XML é melhor, mas aqui vamos na heurística:
                        
                        dados = event.StringInserts
                        if not dados: continue
                        
                        # Lógica heurística para pegar Técnico e Alvo
                        # Na maioria dos eventos de AD (47xx):
                        # O Técnico é quem está executando o processo
                        # O Alvo é o objeto sendo manipulado
                        
                        # Vamos enviar o payload bruto para o Django tratar se necessário
                        # Mas tentaremos identificar aqui:
                        
                        payload = {
                            "tecnico": f"{event.SourceName} (ID {event_id})", # Simplificação
                            "acao": acao,
                            "tipo_objeto": "AD_OBJECT",
                            "objeto": f"Evento ID {event_id}",
                            "detalhes": {
                                "RawData": str(dados),
                                "Time": str(tempo_evento),
                                "EventID": event_id
                            }
                        }
                        
                        # Tenta enviar
                        try:
                            print(f"⚡ Detectado: {acao} (ID {event_id})")
                            resp = requests.post(URL_API, json=payload, timeout=5)
                            if resp.status_code == 201:
                                print("   -> Enviado para o APEX [OK]")
                            else:
                                print(f"   -> Erro API: {resp.status_code}")
                        except Exception as e_req:
                            print(f"   -> Falha de conexão: {e_req}")
                            
                ultimo_indice_lido = novo_total
                
            except Exception as e:
                print(f"Erro no loop: {e}")
                time.sleep(5) # Espera em caso de erro
        
        time.sleep(2) # Verifica a cada 2 segundos

if __name__ == '__main__':
    try:
        monitorar_logs()
    except KeyboardInterrupt:
        print("Parando agente...")