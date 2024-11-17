import platform
import subprocess
import time
from datetime import datetime
import os
import json
from plyer import notification  # Importa a biblioteca plyer para notificações
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import socket  # Para obter o IP da máquina local
import psutil  # Para obter informações da conexão de rede
import requests  # Adicione esta importação no início do seu arquivo

HISTORICO_FILE = 'historico_endereço_ping.json'

# Definindo um limite de tempo de resposta em milissegundos
LIMITE_PING = 1000  # Exemplo: 100ms

# tempo limite de falha para enviar um email com o erro. Em segundos.
TEMPO_LIMITE_ENVIO_EMAIL = 10

# Configurações do e-mail
EMAIL_REMETENTE = "alefsander.pvh14@gmail.com"  # Substitua pelo seu e-mail
SENHA_REMETENTE = "kgqg zwyn vkad gpho"  # Substitua pela sua senha ou token de aplicativo
EMAIL_DESTINATARIO = "alefsander.pvh_14@hotmail.com"  # E-mail para onde enviar a notificação

# Variável para rastrear o tempo da última falha
ultimo_tempo_falha = None

# Variáveis para armazenar informações do ping
ultimo_tempo_resposta = None
numero_tentativas = 0
data_hora_ultimo_ping = None

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
                
        global ultimo_tempo_resposta, numero_tentativas, data_hora_ultimo_ping
        ultimo_tempo_resposta = float(ms)
        numero_tentativas += 1
        data_hora_ultimo_ping = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return ultimo_tempo_resposta, "Sucesso"
    
    except subprocess.CalledProcessError:
        return None, "Falha na conexão"
    except Exception as e:
        return None, f"Erro: {str(e)}"

def configurar_console():
    """Configura o console do Windows para uma melhor experiência"""
    if platform.system().lower() == 'windows':
        os.system('title Monitor de Ping')  # Define o título da janela
        os.system('mode con: cols=100 lines=30')  # Define tamanho da janela

def obter_informacoes_conexao():
    """Obtém informações sobre a conexão de rede"""
    conexao = psutil.net_if_addrs()
    tipo_conexao = "Desconhecido"
    
    for interface, enderecos in conexao.items():
        for endereco in enderecos:
            if endereco.family == socket.AF_INET:  # IPv4
                tipo_conexao = interface  # Nome da interface
                break
    
    return tipo_conexao

def notificar_falha(host, tempo_falha):
    """Notifica o usuário sobre a falha no ping e envia um e-mail se a falha persistir por um tempo significativo"""
    global ultimo_tempo_falha
    mensagem = f"ALERTA: Falha no ping para {host} por {tempo_falha} segundos!"
    print(mensagem)
    notification.notify(
        title="Falha no Ping",
        message=mensagem,
        app_name="Monitor de Ping",
        timeout=1  # Tempo em segundos para a notificação desaparecer
    )
    
    # Envia e-mail quando a conexão é restaurada
    if ultimo_tempo_falha is None or (datetime.now() - ultimo_tempo_falha).total_seconds() > 10:
        ultimo_tempo_falha = datetime.now()  # Atualiza o tempo da última falha

def notificar_lentidao(host, ms):
    """Notifica o usuário sobre a lentidão no ping"""
    mensagem = f"ALERTA: Tempo de resposta elevado para {host}: {ms}ms!"
    print(mensagem)
    notification.notify(
        title="Lentidão no Ping",
        message=mensagem,
        app_name="Monitor de Ping",
        timeout=10  # Tempo em segundos para a notificação desaparecer
    )

def verificar_conexao_email():
    """Verifica se a conexão com a internet está disponível."""

    ms, status = verificar_ping('8.8.8.8')
    if ms is not None and status == "Sucesso":
        return True  # Se o ping for bem-sucedido, a conexão está ativa
    else:
        return False


def enviar_email_falha(host, tempo_falha):
    """Envia um e-mail quando há uma falha no ping"""
    ip_local = socket.gethostbyname(socket.gethostname())  # Obtém o IP local
    hora_inicio_erro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hora_fim_erro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Hora em que a conexão foi restaurada
    sistema_info = platform.uname()  # Obtém informações do sistema
    tipo_conexao = obter_informacoes_conexao()  # Obtém informações da conexão de rede

    # Cria o corpo HTML do e-mail
    corpo_html = f"""
    <html>
    <body>
        <h2>ALERTA: Falha no Ping para {host} por {tempo_falha} segundos</h2>
        <p>Não foi possível conectar ao host: <strong>{host}</strong>.</p>
        <p><strong>Informações Adicionais:</strong></p>
        <ul>
            <li>IP Local: {ip_local}</li>
            <li>IP do Host de Destino: {host}</li>
            <li>Hora do Início do Erro: {hora_inicio_erro}</li>
            <li>Hora do Fim do Erro: {hora_fim_erro}</li>
            <li>Tempo de Falha: {tempo_falha} segundos</li>
            <li>Tipo de Conexão: {tipo_conexao}</li>
            <li>Sistema: {sistema_info.system} {sistema_info.release} ({sistema_info.version})</li>
            <li>Nome do Computador: {sistema_info.node}</li>
            <li>Processador: {sistema_info.machine}</li>
            <li>Arquitetura: {sistema_info.processor}</li>
        </ul>
    </body>
    </html>
    """

    # Cria o assunto do e-mail
    assunto = f"ALERTA: Falha no Ping para {host} por {tempo_falha} segundos"

    # Cria a mensagem
    msg = MIMEMultipart('alternative')
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo_html, 'html'))

    try:
        # Verifica a conexão antes de enviar o e-mail
        if verificar_conexao_email():
            # Conecta ao servidor SMTP e envia o e-mail
            with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
                servidor.starttls()  # Inicia a conexão segura
                servidor.login(EMAIL_REMETENTE, SENHA_REMETENTE)
                servidor.send_message(msg)
                print(f"E-mail enviado para {EMAIL_DESTINATARIO} sobre a falha no ping para {host}.")
        else:
            print("Conexão com a internet não disponível. E-mail não enviado.")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {str(e)}")

def teste_envio_email():
    """Teste de envio de e-mail"""
    host_teste = "test@example.com"  # Substitua por um endereço de e-mail válido para teste
    enviar_email_falha(host_teste)

def obter_ip_externo():
    """Obtém o IP externo da máquina usando um serviço online"""
    try:
        response = requests.get('https://api.ipify.org?format=json')
        return response.json().get('ip')
    except Exception as e:
        print(f"Erro ao obter IP externo: {str(e)}")
        return None

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
    
    # Obtém informações do sistema e da conexão para o cabeçalho do log
    ip_local_anterior = socket.gethostbyname(socket.gethostname())  # Obtém o IP local
    ip_externo = obter_ip_externo()  # Obtém o IP externo
    tipo_conexao = obter_informacoes_conexao()  # Obtém informações da conexão de rede
    sistema_info = platform.uname()  # Obtém informações do sistema

    tempo_falha = 0  # Variável para rastrear o tempo de falha
    falha_conexao = False  # Flag para indicar se a conexão está falhando

    with open(nome_arquivo, 'w', encoding='utf-8') as arquivo:
        # Escreve cabeçalho no arquivo
        arquivo.write(f"Monitoramento de ping para {host}\n")
        arquivo.write(f"Início: {inicio.strftime('%Y-%m-%d %H:%M:%S')}\n")
        arquivo.write(f"IP Local: {ip_local_anterior}\n")
        arquivo.write(f"IP Externo: {ip_externo}\n")  # Adiciona o IP externo ao log
        arquivo.write(f"Tipo de Conexão: {tipo_conexao}\n")
        arquivo.write(f"Sistema: {sistema_info.system} {sistema_info.release} ({sistema_info.version})\n")
        arquivo.write(f"Nome do Computador: {sistema_info.node}\n")
        arquivo.write(f"Processador: {sistema_info.machine}\n")
        arquivo.write(f"Arquitetura: {sistema_info.processor}\n")
        arquivo.write("-" * 50 + "\n")
        
        while True:
            tempo_atual = datetime.now().strftime("%H:%M:%S")
            ms, status = verificar_ping(host)
            
            # Verifica se o IP local mudou
            ip_local_atual = socket.gethostbyname(socket.gethostname())
            if ip_local_atual != ip_local_anterior:
                log_line = f"[{tempo_atual}] Mudança de IP local detectada: {ip_local_anterior} -> {ip_local_atual}"
                print(log_line)
                arquivo.write(log_line + "\n")
                arquivo.flush()  # Força a escrita no arquivo
                ip_local_anterior = ip_local_atual  # Atualiza o IP anterior
            
            if ms is not None:
                log_line = f"[{tempo_atual}] Ping: {ms}ms"
                # Se a conexão estava falhando e excedeu o tempo limite para ser enviado o email
                if falha_conexao and tempo_falha >= TEMPO_LIMITE_ENVIO_EMAIL:  
                    # Envia o e-mail apenas uma vez quando a conexão é restaurada
                    if verificar_conexao_email():
                        enviar_email_falha(host, tempo_falha)  # Envia e-mail quando a conexão é restaurada
                        falha_conexao = False  # Reseta a flag de falha
                        tempo_falha = 0  # Reseta o tempo de falha
                else:
                    tempo_falha = 0  # Reseta o tempo de falha
            else:
                log_line = f"[{tempo_atual}] Status: {status}"
                tempo_falha += 1  # Incrementa o tempo de falha
                falha_conexao = True  # Marca que a conexão está falhando
                notificar_falha(host, tempo_falha)
            
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
        
        
