import platform
import subprocess
import time
from datetime import datetime
import os
import json

HISTORICO_FILE = 'historico_ping.json'

def carregar_historico():
    """Carrega o histórico de hosts pesquisados"""
    if os.path.exists(HISTORICO_FILE):
        try:
            with open(HISTORICO_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def salvar_historico(historico):
    """Salva o histórico de hosts pesquisados"""
    with open(HISTORICO_FILE, 'w') as f:
        json.dump(historico, f)

def adicionar_ao_historico(host, historico):
    """Adiciona um host ao histórico, evitando duplicatas"""
    if host not in historico:
        historico.insert(0, host)  # Adiciona no início da lista
        if len(historico) > 5:  # Mantém apenas os 5 últimos
            historico.pop()
    elif host in historico:  # Se já existe, move para o topo
        historico.remove(host)
        historico.insert(0, host)
    salvar_historico(historico)

def selecionar_host():
    """Permite ao usuário selecionar um host do histórico ou digitar um novo"""
    historico = carregar_historico()
    
    if historico:
        print("\nÚltimos endereços pesquisados:")
        for i, host in enumerate(historico, 1):
            print(f"{i}. {host}")
        print("0. Digitar novo endereço")
        
        while True:
            try:
                opcao = input("\nEscolha uma opção (0-{}): ".format(len(historico)))
                if opcao.strip() == "":
                    return "8.8.8.8"
                
                opcao = int(opcao)
                if opcao == 0:
                    break
                elif 1 <= opcao <= len(historico):
                    return historico[opcao-1]
                else:
                    print("Opção inválida!")
            except ValueError:
                print("Por favor, digite um número válido!")
    
    # Se não há histórico ou usuário escolheu digitar novo endereço
    host = input("\nDigite o endereço para monitorar (ou pressione Enter para usar 8.8.8.8): ").strip() or "8.8.8.8"
    adicionar_ao_historico(host, historico)
    return host

def verificar_ping(host="8.8.8.8"):
    """
    Verifica o ping para um host específico e retorna os resultados
    Por padrão usa o DNS do Google (8.8.8.8)
    """
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    
    try:
        # Executa o comando ping
        comando = ['ping', param, '1', host]
        encoding = 'cp1252' if platform.system().lower() == 'windows' else 'utf-8'
        resultado = subprocess.check_output(comando).decode(encoding)
        
        # Extrai o tempo de resposta
        if platform.system().lower() == 'windows':
            if 'tempo=' in resultado:
                ms = resultado.split('tempo=')[1].split('ms')[0].strip()
            else:
                return None, "Timeout"
        else:
            if 'time=' in resultado:
                ms = resultado.split('time=')[1].split('ms')[0].strip()
            else:
                return None, "Timeout"
                
        return float(ms), "Sucesso"
    
    except subprocess.CalledProcessError:
        return None, "Falha na conexão"
    except Exception as e:
        return None, f"Erro: {str(e)}"

def configurar_console():
    """Configura o console do Windows para uma melhor experiência"""
    if platform.system().lower() == 'windows':
        os.system('title Monitor de Ping')  # Define o título da janela
        os.system('color 0A')  # Define cores (0=preto, A=verde claro)
        os.system('mode con: cols=100 lines=30')  # Define tamanho da janela

def main():
    configurar_console()  # Configura o console
    
    print("=" * 50)
    print("           MONITOR DE PING - v0.0.1 - By: Alefe")
    print("=" * 50)
    print("\nIniciando monitoramento...\n")
    
    # Cria pasta logs se não existir
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Gera nome do arquivo com data e hora atual
    inicio = datetime.now()
    nome_arquivo = f"logs/ping_log_{inicio.strftime('%Y%m%d_%H%M%S')}.txt"
    
    # Usa a nova função de seleção de host
    host = selecionar_host()
    
    print(f"\nMonitorando ping para {host}")
    print(f"Logs sendo salvos em: {nome_arquivo}")
    print("Pressione Ctrl+C para parar\n")
    
    with open(nome_arquivo, 'w', encoding='utf-8') as arquivo:
        # Escreve cabeçalho no arquivo
        arquivo.write(f"Monitoramento de ping para {host}\n")
        arquivo.write(f"Início: {inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")
        arquivo.write("-" * 50 + "\n")
        
        while True:
            tempo_atual = datetime.now().strftime("%H:%M:%S")
            ms, status = verificar_ping(host)
            
            if ms is not None:
                log_line = f"[{tempo_atual}] Status: {status} - Ping: {ms}ms"
            else:
                log_line = f"[{tempo_atual}] Status: {status}"
            
            # Exibe no console e salva no arquivo
            print(log_line)
            arquivo.write(log_line + "\n")
            arquivo.flush()  # Força a escrita no arquivo
            
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nMonitoramento finalizado!")
        
        
