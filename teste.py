from datetime import datetime

status = "Falha"
ultima_notificacao_enviada = datetime.now()
intervalor_mínimo_notificação = 60

def deve_notificar():
        """Verifica se deve enviar uma nova notificação"""
        # Só notifica se houve mudança de status para falha
        if status != "Sucesso":
            # Se é a primeira notificação ou já passou tempo suficiente desde a última
            if (not ultima_notificacao_enviada or 
                (datetime.now() - ultima_notificacao_enviada).total_seconds() >= intervalor_mínimo_notificação):  # 1 minuto
                return True
        return False
    
print(datetime.now())
deve_notificar()