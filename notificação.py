from datetime import datetime
from plyer import notification
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import queue
from log import GerenciadorLog

class NotificadorBase:
    """Classe base para todos os tipos de notificadores"""
    def __init__(self):
        self.ultima_notificacao = None
        self.intervalo_minimo = 60  # 1 minuto entre notificações
        self.log_queue = queue.Queue()  # Fila para logs
        self.host = None  # Novo atributo para identificar o host

    def pode_notificar(self):
        if not self.ultima_notificacao:
            return True
        """Verifica se já passou tempo suficiente desde a última notificação"""
        tempo_passado = (datetime.now() - self.ultima_notificacao).total_seconds()
        if tempo_passado < self.intervalo_minimo:
            # Registra que está aguardando o intervalo
            log_entry = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'tipo': 'aguardando_intervalo',
                'servico': self.__class__.__name__.replace('Notificador', '').lower(),
                'tempo_restante': self.intervalo_minimo - tempo_passado,
                'host': self.host,
                'tipo_notificacao': self.__class__.__name__.replace('Notificador', '').lower()
            }
            self.log_queue.put(log_entry)
            return False
        return True

    def atualizar_tempo_notificacao(self):
        """Atualiza o timestamp da última notificação"""
        self.ultima_notificacao = datetime.now()

    def registrar_erro(self, tipo_notificacao, erro):
        """Registra erro no log"""
        log_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'tipo': 'erro_notificacao',
            'servico': tipo_notificacao,
            'mensagem': str(erro)
        }
        self.log_queue.put(log_entry)

# Notificar por meio do Email
class NotificadorEmail(NotificadorBase):
    """Classe para enviar notificações por e-mail"""
    def __init__(self, email_remetente, senha_remetente, email_destinatario):
        super().__init__()
        self.email_remetente = email_remetente
        self.senha_remetente = senha_remetente
        self.email_destinatario = email_destinatario
        self.servidor_smtp = "smtp.gmail.com"
        self.porta_smtp = 587

    def enviar_notificacao(self, assunto, mensagem):
        """Envia uma notificação por e-mail"""
        if not self.pode_notificar():
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_remetente
            msg['To'] = self.email_destinatario
            msg['Subject'] = assunto

            msg.attach(MIMEText(mensagem, 'plain'))

            servidor = smtplib.SMTP(self.servidor_smtp, self.porta_smtp)
            servidor.starttls()
            servidor.login(self.email_remetente, self.senha_remetente)
            
            texto = msg.as_string()
            servidor.sendmail(self.email_remetente, self.email_destinatario, texto)
            servidor.quit()

            self.atualizar_tempo_notificacao()
            return True
        except Exception as e:
            self.registrar_erro('email', e)
            return False

# Notificar por meio do Telegram
class NotificadorTelegram(NotificadorBase):
    """Classe para enviar notificações via Telegram"""
    def __init__(self, token_bot, chat_id):
        super().__init__()
        self.token_bot = token_bot
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{token_bot}"

    def enviar_notificacao(self, mensagem):
        """Envia uma notificação via Telegram"""
        if not self.pode_notificar():
            return False

        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": mensagem,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, data=data)
            if response.status_code == 200:
                self.atualizar_tempo_notificacao()
                return True
            
            self.registrar_erro('telegram', f"Status code: {response.status_code}")
            return False
        except Exception as e:
            self.registrar_erro('telegram', e)
            return False

# Notificar por meio de SMS
class NotificadorSMS(NotificadorBase):
    """Classe para enviar notificações via SMS usando Twilio"""
    def __init__(self, account_sid, auth_token, numero_remetente, numero_destinatario):
        super().__init__()
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.numero_remetente = numero_remetente
        self.numero_destinatario = numero_destinatario
        
        # Importa Twilio apenas se for necessário
        try:
            from twilio.rest import Client
            self.client = Client(account_sid, auth_token)
        except ImportError:
            print("Twilio não está instalado. Use: pip install twilio")
            self.client = None

    def enviar_notificacao(self, mensagem):
        """Envia uma notificação via SMS"""
        if not self.pode_notificar() or not self.client:
            return False

        try:
            message = self.client.messages.create(
                body=mensagem,
                from_=self.numero_remetente,
                to=self.numero_destinatario
            )
            if message.sid:
                self.atualizar_tempo_notificacao()
                return True
                
            self.registrar_erro('sms', "Falha ao obter SID da mensagem")
            return False
        except Exception as e:
            self.registrar_erro('sms', e)
            return False

# Notificar pelo Desktop
class NotificadorDesktop(NotificadorBase):
    """Classe para enviar notificações desktop usando plyer"""
    def __init__(self, app_name="Monitor de Ping"):
        super().__init__()
        self.app_name = app_name
        self.intervalo_minimo = 10  # Reduzido para 10 segundos para notificações desktop

    def enviar_notificacao(self, mensagem, titulo=None):
        """Envia uma notificação desktop"""
        if not self.pode_notificar():
            return False

        try:
            notification.notify(
                title=titulo or self.app_name,
                message=mensagem,
                app_icon=None,  # Pode especificar o caminho para um ícone
                timeout=10,     # Notificação desaparece após 10 segundos
            )
            self.atualizar_tempo_notificacao()
            return True
        except Exception as e:
            self.registrar_erro('desktop', e)
            return False

# Notificar por meio do WhatsApp Business API
class NotificadorWhatsApp(NotificadorBase):
    """Classe para enviar notificações via WhatsApp usando a API do WhatsApp Business"""
    def __init__(self, url, token, numero_destinatario):
        super().__init__()
        self.url = url
        self.token = token
        self.numero_destinatario = numero_destinatario

    def enviar_notificacao(self, mensagem):
        """Envia uma notificação via WhatsApp"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": self.numero_destinatario,
            "text": {
                "body": mensagem
            }
        }
        response = requests.post(self.url, headers=headers, json=data)
        if response.status_code == 200:
            self.atualizar_tempo_notificacao()
            return True
        else:
            self.registrar_erro('whatsapp', response.json())
            return False

# Classe para gerenciar todas as notificações
class GerenciadorNotificacoes:
    """Classe para gerenciar todos os tipos de notificações"""
    def __init__(self):
        self.notificadores = {}
        self.gerenciador_log = GerenciadorLog()  # Nova instância

    def adicionar_notificador(self, tipo, notificador):
        """Adiciona um novo notificador"""
        self.notificadores[tipo] = notificador

    def processar_logs_notificadores(self):
        """Processa os logs de todos os notificadores"""
        for notificador in self.notificadores.values():
            try:
                while True:
                    log_entry = notificador.log_queue.get_nowait()
                    self.gerenciador_log.registrar_log(log_entry)
            except queue.Empty:
                continue

    def enviar_notificacao(self, mensagem, titulo=None, tipos=None, host=None):
        """Envia notificação para todos os tipos especificados"""
        if tipos is None:
            tipos = self.notificadores.keys()

        resultados = {}
        for tipo in tipos:
            if tipo in self.notificadores:
                notificador:GerenciadorNotificacoes = self.notificadores[tipo]
                notificador.host = host  # Define o host atual
                
                # Verifica se pode notificar (isso já vai gerar o log de aguardando se necessário)
                pode_notificar = notificador.pode_notificar()
                
                if pode_notificar:
                    # Tenta enviar a notificação
                    if tipo == 'email':
                        resultados[tipo] = notificador.enviar_notificacao(
                            titulo or "Alerta de Monitoramento", 
                            mensagem
                        )
                    elif tipo == 'desktop':
                        resultados[tipo] = notificador.enviar_notificacao(
                            mensagem,
                            titulo
                        )
                    else:
                        resultados[tipo] = notificador.enviar_notificacao(mensagem)
                    
                    if resultados[tipo]:
                        notificador.ultima_notificacao = datetime.now()
                else:
                    resultados[tipo] = False

        # Processa os logs após todas as tentativas
        self.processar_logs_notificadores()
        
        return resultados


# Função para configurar notificações a partir do arquivo de configuração
def configurar_notificacoes(config):
    """Configura e retorna um gerenciador de notificações"""
    gerenciador = GerenciadorNotificacoes()

    # Configurar Notificação Desktop
    desktop_notificador = NotificadorDesktop()
    gerenciador.adicionar_notificador('desktop', desktop_notificador)

    # Configurar Email
    email_notificador = NotificadorEmail(
        email_remetente=config.get('email_remetente', 'seu_email@gmail.com'),
        senha_remetente=config.get('senha_remetente', 'sua_senha'),
        email_destinatario=config.get('email_destinatario', 'destinatario@gmail.com')
    )
    gerenciador.adicionar_notificador('email', email_notificador)

    # Configurar Telegram
    telegram_notificador = NotificadorTelegram(
        token_bot=config.get('token_bot_telegram', 'seu_token_bot'),
        chat_id=config.get('chat_id_telegram', 'seu_chat_id')
    )
    gerenciador.adicionar_notificador('telegram', telegram_notificador)

    # Configurar SMS (Twilio)
    sms_notificador = NotificadorSMS(
        account_sid=config.get('account_sid_twilio', 'seu_account_sid'),
        auth_token=config.get('auth_token_twilio', 'seu_auth_token'),
        numero_remetente=config.get('numero_remetente_twilio', '+1234567890'),
        numero_destinatario=config.get('numero_destinatario_twilio', '+0987654321')
    )
    gerenciador.adicionar_notificador('sms', sms_notificador)

    # Configurar WhatsApp Business API
    whatsapp_notificador = NotificadorWhatsApp(
        url=config.get('url_whatsapp', 'https://graph.facebook.com/v13.0/YOUR_PHONE_NUMBER_ID/messages'),
        token=config.get('token_whatsapp', 'YOUR_ACCESS_TOKEN'),
        numero_destinatario=config.get('numero_destinatario_whatsapp', '5599993451333')
    )
    gerenciador.adicionar_notificador('whatsapp', whatsapp_notificador)

    return gerenciador