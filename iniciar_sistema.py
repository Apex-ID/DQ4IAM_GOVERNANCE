import subprocess
import time
import os
import sys

def abrir_terminal(titulo, comando):
    """
    Abre uma nova janela/aba do terminal GNOME e executa o comando.
    O '; exec bash' mantém a janela aberta após o comando (ou erro).
    """
    print(f"🚀 Iniciando: {titulo}...")
    try:
        # Tenta abrir no gnome-terminal (padrão do Ubuntu/WSL com GUI)
        subprocess.Popen([
            'gnome-terminal', 
            '--tab', 
            '--title', titulo, 
            '--', 
            'bash', '-c', f"{comando}; exec bash"
        ])
    except FileNotFoundError:
        print(f"❌ Erro: gnome-terminal não encontrado. Você está em um servidor sem interface?")
        print(f"   Comando manual para {titulo}: {comando}")

def main():
    print("="*50)
    print("   DQ4IAM GOVERNANCE - INICIALIZADOR DE SISTEMA")
    print("="*50)

    # 1. Verifica/Inicia Redis (precisa de sudo, pode pedir senha)
    print("🔧 Verificando Redis...")
    subprocess.run(['sudo', 'service', 'redis-server', 'start'])
    time.sleep(1)

    # Caminho do Python no ambiente virtual
    python_exec = sys.executable 

    # 2. Inicia Celery Worker
    cmd_celery = f"{python_exec} -m celery -A apex_project worker -l info"
    abrir_terminal("1. Celery Worker", cmd_celery)
    time.sleep(2)

    # 3. Inicia Django Server
    cmd_django = f"{python_exec} manage.py runserver"
    abrir_terminal("2. Django Server", cmd_django)
    time.sleep(2)

    # 4. Inicia Agente Simulador (Opcional)
    # cmd_agente = f"{python_exec} agente_simulador.py"
    # abrir_terminal("3. Agente Simulador AD", cmd_agente)

    print("\n✅ Sistema inicializado!")
    print("   - Celery: Processando tarefas em segundo plano")
    print("   - Django: http://127.0.0.1:8000/painel/")
    print("="*50)

if __name__ == "__main__":
    main()