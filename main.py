import threading
import platform
import subprocess
import time
from datetime import datetime
import os
import json
from notificação import configurar_notificacoes
from log import GerenciadorLog
from logo_alefe import apresentação

HISTORICO_FILE = 'historico_endereço_ping.json'
CONFIG_FILE = 'config.json'
# Classe para gerenciar o monitoramento de múltiplos hosts
class MonitorHost:
    def __init__(self, host):
        self.host = host
        self.ultimo_ping = None
        self.status = "Iniciando..."
        self.historico = []
        self.falhas = 0
        self.ultima_falha = None
        self.tempo_total_falhas = 0
        self.ultima_notificacao_enviada = None  # Novo atributo para controlar notificações
        
    def adicionar_resultado(self, ping, status):
        """Adiciona um novo resultado de ping e atualiza as estatísticas"""
        self.ultimo_ping = ping
        self.status = status
        tempo_atual = datetime.now()
        
        # Registra o resultado no histórico
        self.historico.append({
            'timestamp': tempo_atual.strftime("%Y-%m-%d %H:%M:%S"),
            'ping': ping,
            'status': status
        })
        
        # Atualiza contagem de falhas e tempo
        if status != "Sucesso":
            self.falhas += 1
            if self.ultima_falha:
                delta = (tempo_atual - self.ultima_falha).total_seconds()
                self.tempo_total_falhas += delta
            self.ultima_falha = tempo_atual
        else:
            self.ultima_falha = None
            
    def deve_notificar(self):
        """Verifica se deve enviar uma nova notificação"""
        return True if self.status != "Sucesso" else False


class MonitorMultiplosHosts:
    def __init__(self):
        self.hosts = {}  # Dicionário para armazenar os monitores de cada host
        self.running = False
        self.threads = []
        self.lock = threading.Lock()
        self.gerenciador_log = GerenciadorLog()  # Nova instância
        self.historico = self.carregar_historico()  # Carrega o histórico ao iniciar
        
        # Carrega configurações do arquivo
        self.carregar_configuracoes()
        self.notificador = configurar_notificacoes(self.carregar_configuracoes())

    def carregar_configuracoes(self):
        """Carrega as configurações do arquivo JSON ou cria um novo com configurações padrão"""
        # Dicionário com as configurações padrão
        configuracoes_padrao = {
            'intervalo_ping': 1,
            'max_hosts': 9,
            'tipos_notificacao': ['desktop'],
            # Configurar envio de email
            'email_remetente': 'seu_email@gmail.com',
            'senha_remetente': 'sua_senha',
            'email_destinatario': 'destinatario@gmail.com',
            # Configurar envio no Telegram
            'token_bot_telegram': 'seu_token_bot',
            'chat_id_telegram': 'seu_chat_id',
            # Configurar envio no SMS
            'account_sid_twilio': 'seu_account_sid',
            'auth_token_twilio': 'seu_auth_token',
            'numero_remetente_twilio': '+1234567890',
            'numero_destinatario_twilio': '+0987654321',
            # Configurar envio no WhatsApp
            'url_whatsapp': 'https://graph.facebook.com/v13.0/YOUR_PHONE_NUMBER_ID/messages',
            'token_whatsapp': 'YOUR_ACCESS_TOKEN',
            'numero_destinatario_whatsapp': '5599993451333'
        }

        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Atualiza as configurações com os valores do arquivo, mantendo os padrões se não existirem
                for chave, valor in configuracoes_padrao.items():
                    setattr(self, chave, config.get(chave, valor))
                return config  # Retorna o dicionário de configurações
        else:
            # Salva as configurações padrão
            self.salvar_configuracoes(configuracoes_padrao)
            # Define as configurações padrão na instância
            for chave, valor in configuracoes_padrao.items():
                setattr(self, chave, valor)
            return configuracoes_padrao  # Retorna as configurações padrão

    def salvar_configuracoes(self, configuracoes):
        """Salva as configurações atuais no arquivo JSON"""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(configuracoes, f, indent=4)  # Salva o dicionário de configurações no arquivo

    def carregar_historico(self):
        """Carrega o histórico de hosts monitorados"""
        if os.path.exists(HISTORICO_FILE):
            try:
                with open(HISTORICO_FILE, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def adicionar_ao_historico(self, host):
        """Adiciona um host ao histórico, evitando duplicatas"""
        if host not in self.historico:
            self.historico.insert(0, host)  # Adiciona no início da lista
            if len(self.historico) > 9:  # Mantém apenas os 9 últimos
                self.historico.pop()
        elif host in self.historico:  # Se já existe, move para o topo
            self.historico.remove(host)
            self.historico.insert(0, host)
        self.salvar_historico()  # Salva o histórico

    def salvar_historico(self):
        """Salva o histórico de hosts monitorados"""
        with open(HISTORICO_FILE, 'w') as f:
            json.dump(self.historico, f)

    def adicionar_host(self, hosts):
        """Adiciona um ou mais hosts ao monitoramento"""
        for host in hosts:
            if host not in self.hosts:
                self.hosts[host] = MonitorHost(host)  # Supondo que MonitorHost é a classe que você usa para monitorar um host
                print(f"Host {host} adicionado para monitoramento.")
            else:
                print(f"Host {host} já está sendo monitorado.")

    def remover_host(self, host):
        """Remove um host do monitoramento e do histórico"""
        with self.lock:
            if host in self.hosts:
                del self.hosts[host]
                self.historico.remove(host)  # Remove do histórico
                self.salvar_historico()  # Salva o histórico

    def verificar_ping(self, host):
        """Verifica o ping para um host específico"""
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        
        try:
            comando = ['ping', param, '1', host]
            encoding = 'cp1252' if platform.system().lower() == 'windows' else 'utf-8'
            resultado = subprocess.check_output(comando, timeout=5).decode(encoding)
            
            if platform.system().lower() == 'windows':
                if 'tempo=' in resultado:
                    ms = float(resultado.split('tempo=')[1].split('ms')[0].strip())
                    return ms, "Sucesso"
            else:
                if 'time=' in resultado:
                    ms = float(resultado.split('time=')[1].split('ms')[0].strip())
                    return ms, "Sucesso"
                    
            return None, "Timeout"
        except subprocess.TimeoutExpired:
            return None, "Timeout"
        except subprocess.CalledProcessError:
            return None, "Falha na conexão"
        except Exception as e:
            return None, f"Erro: {str(e)}"

    def monitor_thread(self, host):
        """Thread para monitorar um host específico"""
        while self.running:
            ms, status = self.verificar_ping(host)
            
            with self.lock:
                monitor: MonitorHost = self.hosts[host]
                monitor.adicionar_resultado(ms, status)
                
                # Adiciona log
                self.gerenciador_log.registrar_log({
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'host': host,
                    'ping': ms,
                    'status': status
                })
                
                # Verifica se deve enviar notificação
                if monitor.deve_notificar():
                    mensagem = f"Falha detectada no host {host}\nStatus: {status}"
                    titulo = f"Alerta de Conexão - {host}"
                    
                    # Envia notificações e registra resultados
                    resultados = self.notificador.enviar_notificacao(
                        mensagem=mensagem,
                        titulo=titulo,
                        tipos=self.tipos_notificacao,  # Usa os tipos de notificação configurados
                        host=host
                    )
                    
                    # Registra os resultados das tentativas de notificaço no log
                    self.gerenciador_log.registrar_log_notificacao(host, resultados)
            
            time.sleep(self.intervalo_ping)  # Usa o intervalo configurado
            
    def iniciar_monitoramento(self):
        """Inicia o monitoramento de todos os hosts"""
        self.running = True
        
        # Inicia uma thread para cada host, respeitando o número máximo de hosts
        for host in list(self.hosts.keys())[:self.max_hosts]:
            thread = threading.Thread(target=self.monitor_thread, args=(host,))
            thread.daemon = True
            self.threads.append(thread)
            thread.start()
        
        # Inicia thread para salvar logs
        log_thread = threading.Thread(target=self.gerenciador_log.salvar_logs)
        log_thread.daemon = True
        log_thread.start()
        
    def parar_monitoramento(self):
        """Para o monitoramento de todos os hosts"""
        self.running = False
        for thread in self.threads:
            thread.join()
        self.threads.clear()
        
    def obter_estatisticas(self):
        """Retorna estatísticas de todos os hosts monitorados"""
        estatisticas = {}
        with self.lock:
            for host, monitor in self.hosts.items():
                pings = [h['ping'] for h in monitor.historico if h['ping'] is not None]
                estatisticas[host] = {
                    'último_ping': monitor.ultimo_ping,
                    'status': monitor.status,
                    'média_ping': sum(pings) / len(pings) if pings else 0,
                    'min_ping': min(pings) if pings else 0,
                    'max_ping': max(pings) if pings else 0,
                    'total_falhas': monitor.falhas,
                    'tempo_total_falhas': monitor.tempo_total_falhas,
                    'última_falha': monitor.ultima_falha.strftime("%Y-%m-%d %H:%M:%S") if monitor.ultima_falha else None
                }
        return estatisticas

    def configurar_monitoramento(self):
        """Configura o monitoramento de hosts"""
        print("Configuração do Monitoramento:")
        try:
            # Configura o intervalo de ping
            intervalo_input = input(f"Digite o intervalo de ping em segundos (padrão {self.intervalo_ping}s): ")
            self.intervalo_ping = int(intervalo_input) if intervalo_input else self.intervalo_ping
            
            # Configura o número máximo de hosts
            max_hosts_input = input(f"Digite o número máximo de hosts a serem monitorados (padrão {self.max_hosts}): ")
            self.max_hosts = int(max_hosts_input) if max_hosts_input else self.max_hosts
            
            # Configura os tipos de notificação
            print("Escolha os tipos de notificação (separados por vírgula):")
            print("1. desktop")
            print("2. sms")
            print("3. email")
            print("4. telegram")
            print("5. whatsapp")
            
            opcoes_notificacao = input("Digite os números das opções desejadas (padrão: 1): ") or '1'
            
            tipos_notificacao = {
                '1': 'desktop',
                '2': 'sms',
                '3': 'email',
                '4': 'telegram',
                '5': 'whatsapp'
            }
            
            # Armazena as opções selecionadas
            self.tipos_notificacao = [tipos_notificacao[numero] for numero in opcoes_notificacao.split(',') if numero in tipos_notificacao]
            
            # Se nenhuma opção foi selecionada, usa o padrão
            if not self.tipos_notificacao:
                self.tipos_notificacao = ['desktop']
            
            # Salva as novas configurações
            configuracoes_atualizadas = {
                'intervalo_ping': self.intervalo_ping,
                'max_hosts': self.max_hosts,
                'tipos_notificacao': self.tipos_notificacao
            }
            
            print("Novas configurações:")
            print(configuracoes_atualizadas)
            
            self.salvar_configuracoes(configuracoes_atualizadas)  # Salva as novas configurações
        except ValueError:
            print("Entrada inválida. Usando configurações padrão.")

    def selecionar_host(self):
        """Permite ao usuário selecionar um ou mais hosts do histórico ou digitar novos"""
        historico = self.carregar_historico()
        hosts_selecionados = []  # Lista para armazenar os hosts selecionados

        while True:
            try:
                if historico:
                    print("\nÚltimos endereços pesquisados:")
                    for i, host in enumerate(historico, 1):
                        print(f"{i}. {host}")
                    print("D. Digitar novo endereço")
                    print("C. Configurar o monitor")
                
                    opcao = input("\nEscolha uma opção ou digite os números separados por vírgula): ")

                else:
                    
                    print("D. Digitar novo endereço")
                    print("C. Configurar o monitor")
                
                    opcao = input("\nEscolha uma opçãoa: ")
                    
                if opcao.upper() == "C":
                    self.configurar_monitoramento()  # Chama a nova função de configuração
                elif opcao.upper() == 'D':
                    # Permite ao usuário digitar um novo endereço
                    host = input("\nDigite o endereço para monitorar: ").strip()
                    if host:  # Verifica se o usuário digitou algo
                        self.adicionar_ao_historico(host)  # Adiciona ao histórico
                        hosts_selecionados.append(host)
                    else:
                        print("Você deve digitar um endereço válido.")
                else:
                    # Permite selecionar múltiplos hosts
                    numeros_selecionados = [int(num) for num in opcao.replace(' ', '').split(',') if num.isdigit()]
                    for numero in numeros_selecionados:
                        if 1 <= numero <= len(historico):
                            hosts_selecionados.append(historico[numero - 1])
                        else:
                            print(f"Opção {numero} é inválida!")

                # Se o usuário escolheu hosts, retorna a lista de hosts selecionados
                if hosts_selecionados:
                    return hosts_selecionados

                print("Nenhum host selecionado. Tente novamente.")
            except ValueError:
                print("Entrada inválida. Por favor, digite números válidos.")
        
        # Se não há histórico ou usuário escolheu digitar novo endereço
        host = input("\nDigite o endereço para monitorar (ou pressione Enter para usar 8.8.8.8): ").strip() or "8.8.8.8"
        self.adicionar_ao_historico(host)  # Adiciona ao histórico
        return [host]  # Retorna uma lista com o host

# Exemplo de uso
def main():
    
    print(" By: ".center(120, "—"))
    print(apresentação())
    print(" Versão: ".center(120, "—"))
    print("Seja Bem-vindo ao Monitor de Redes!")
    print("Este programa monitora a conectividade de múltiplos hosts.")
    print("Você pode adicionar, remover e monitorar hosts de sua escolha.")
    print("Também é possível configurar notificações para alertá-lo em caso de falha.")
    print("Pressione Enter para continuar...")
    input()
    
    MonitorMultiplo = MonitorMultiplosHosts()
    # Solicita ao usuário para adicionar hosts para monitoramento
    while True:
        hosts = MonitorMultiplo.selecionar_host()  # Agora retorna uma lista de hosts
        if hosts:
            MonitorMultiplo.adicionar_host(hosts)  # Passa a lista de hosts
            iniciar = input("\nDeseja iniciar o monitoramento? (s/n): ").strip().lower()
            if iniciar.upper() == 'S':
                break
        
    if not MonitorMultiplo.hosts:
        print("Nenhum host foi adicionado para monitoramento. Encerrando.")
        return  # Sai se não houver hosts para monitorar

    print("Hosts selecionados para monitoramento:")
    for host in MonitorMultiplo.hosts.keys():
        print(f"- {host}")

    
    print("Iniciando monitoramento de múltiplos hosts...")
    print("Pressione Ctrl+C para parar")
    
    try:
        MonitorMultiplo.iniciar_monitoramento()
        
        while True:
            # Exibe estatísticas a cada 5 segundos
            estatisticas = MonitorMultiplo.obter_estatisticas()
            os.system('cls' if platform.system().lower() == 'windows' else 'clear')
            print("\nEstatísticas de Monitoramento:")
            print("-" * 50)
            
            for host, stats in estatisticas.items():
                print(f"\nHost: {host}")
                print(f"Status: {stats['status']}")
                print(f"Último ping: {stats['último_ping']}ms")
                print(f"Média: {stats['média_ping']:.1f}ms")
                print(f"Mín/Máx: {stats['min_ping']:.1f}ms / {stats['max_ping']:.1f}ms")
                print(f"Total de falhas: {stats['total_falhas']}")
                print(f"Tempo total em falha: {stats['tempo_total_falhas']:.1f}s")
                if stats['última_falha']:
                    print(f"Última falha: {stats['última_falha']}")
                print("-" * 30)
                
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nParando monitoramento...")
        MonitorMultiplo.parar_monitoramento()
        print("Monitoramento finalizado!")

if __name__ == "__main__":
    main()
