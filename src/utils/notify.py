#!/usr/bin/env python3
"""
Módulo de notificação para alertas de anomalias
Suporta notificações por e-mail e Telegram

Uso:
    python -m src.utils.notify --type anomaly --message "Mensagem de alerta"
    python -m src.utils.notify --type info --message "Informação geral"

Variáveis de ambiente necessárias:
    # E-mail
    NOTIFY_EMAIL_ENABLED=true
    NOTIFY_EMAIL_SMTP_HOST=smtp.gmail.com
    NOTIFY_EMAIL_SMTP_PORT=587
    NOTIFY_EMAIL_USERNAME=seu_email@gmail.com
    NOTIFY_EMAIL_PASSWORD=sua_senha_app
    NOTIFY_EMAIL_FROM=seu_email@gmail.com
    NOTIFY_EMAIL_TO=destinatario@gmail.com
    
    # Telegram
    NOTIFY_TELEGRAM_ENABLED=true
    NOTIFY_TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
    NOTIFY_TELEGRAM_CHAT_ID=-1001234567890
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmailNotifier:
    """Notificador por e-mail usando SMTP"""
    
    def __init__(self):
        self.enabled = os.getenv('NOTIFY_EMAIL_ENABLED', 'false').lower() == 'true'
        self.smtp_host = os.getenv('NOTIFY_EMAIL_SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('NOTIFY_EMAIL_SMTP_PORT', '587'))
        self.username = os.getenv('NOTIFY_EMAIL_USERNAME')
        self.password = os.getenv('NOTIFY_EMAIL_PASSWORD')
        self.from_email = os.getenv('NOTIFY_EMAIL_FROM')
        self.to_email = os.getenv('NOTIFY_EMAIL_TO')
        
    def is_configured(self) -> bool:
        """Verifica se todas as configurações necessárias estão presentes"""
        required_vars = [self.username, self.password, self.from_email, self.to_email]
        return self.enabled and all(var is not None for var in required_vars)
    
    def send(self, subject: str, message: str, alert_type: str = 'info') -> bool:
        """Envia notificação por e-mail"""
        if not self.is_configured():
            logger.warning("E-mail não configurado ou desabilitado")
            return False
            
        try:
            # TODO: Implementar envio real de e-mail
            # import smtplib
            # from email.mime.text import MIMEText
            # from email.mime.multipart import MIMEMultipart
            
            logger.info(f"[PLACEHOLDER] Enviando e-mail:")
            logger.info(f"  De: {self.from_email}")
            logger.info(f"  Para: {self.to_email}")
            logger.info(f"  Assunto: {subject}")
            logger.info(f"  Mensagem: {message}")
            logger.info(f"  Tipo: {alert_type}")
            
            # Simular sucesso
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail: {e}")
            return False


class TelegramNotifier:
    """Notificador por Telegram usando Bot API"""
    
    def __init__(self):
        self.enabled = os.getenv('NOTIFY_TELEGRAM_ENABLED', 'false').lower() == 'true'
        self.bot_token = os.getenv('NOTIFY_TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('NOTIFY_TELEGRAM_CHAT_ID')
        
    def is_configured(self) -> bool:
        """Verifica se todas as configurações necessárias estão presentes"""
        return self.enabled and self.bot_token and self.chat_id
    
    def send(self, message: str, alert_type: str = 'info') -> bool:
        """Envia notificação por Telegram"""
        if not self.is_configured():
            logger.warning("Telegram não configurado ou desabilitado")
            return False
            
        try:
            # TODO: Implementar envio real via Telegram
            # import requests
            
            # Adicionar emoji baseado no tipo
            emoji_map = {
                'anomaly': '🚨',
                'error': '❌',
                'warning': '⚠️',
                'info': 'ℹ️',
                'success': '✅'
            }
            emoji = emoji_map.get(alert_type, 'ℹ️')
            
            formatted_message = f"{emoji} *Milionária AI*\n\n{message}"
            
            logger.info(f"[PLACEHOLDER] Enviando Telegram:")
            logger.info(f"  Bot Token: {self.bot_token[:10]}...")
            logger.info(f"  Chat ID: {self.chat_id}")
            logger.info(f"  Mensagem: {formatted_message}")
            logger.info(f"  Tipo: {alert_type}")
            
            # Simular sucesso
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar Telegram: {e}")
            return False


class NotificationManager:
    """Gerenciador central de notificações"""
    
    def __init__(self):
        self.email_notifier = EmailNotifier()
        self.telegram_notifier = TelegramNotifier()
        
    def send_notification(self, message: str, alert_type: str = 'info', subject: Optional[str] = None) -> bool:
        """Envia notificação através de todos os canais configurados"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Preparar assunto para e-mail
        if subject is None:
            subject_map = {
                'anomaly': 'ANOMALIA DETECTADA - Milionária AI',
                'error': 'ERRO - Milionária AI',
                'warning': 'AVISO - Milionária AI',
                'info': 'INFO - Milionária AI',
                'success': 'SUCESSO - Milionária AI'
            }
            subject = subject_map.get(alert_type, 'Milionária AI')
        
        # Adicionar timestamp à mensagem
        full_message = f"[{timestamp}] {message}"
        
        success_count = 0
        total_notifiers = 0
        
        # Tentar enviar por e-mail
        if self.email_notifier.is_configured():
            total_notifiers += 1
            if self.email_notifier.send(subject, full_message, alert_type):
                success_count += 1
                logger.info("Notificação por e-mail enviada com sucesso")
            else:
                logger.error("Falha ao enviar notificação por e-mail")
        
        # Tentar enviar por Telegram
        if self.telegram_notifier.is_configured():
            total_notifiers += 1
            if self.telegram_notifier.send(full_message, alert_type):
                success_count += 1
                logger.info("Notificação por Telegram enviada com sucesso")
            else:
                logger.error("Falha ao enviar notificação por Telegram")
        
        if total_notifiers == 0:
            logger.warning("Nenhum notificador configurado")
            return False
        
        success_rate = success_count / total_notifiers
        logger.info(f"Notificações enviadas: {success_count}/{total_notifiers} ({success_rate:.1%})")
        
        return success_count > 0


def main():
    """Função principal para uso via linha de comando"""
    parser = argparse.ArgumentParser(description='Enviar notificações de anomalias')
    parser.add_argument('--type', choices=['anomaly', 'error', 'warning', 'info', 'success'], 
                       default='info', help='Tipo de alerta')
    parser.add_argument('--message', required=True, help='Mensagem a ser enviada')
    parser.add_argument('--subject', help='Assunto personalizado para e-mail')
    
    args = parser.parse_args()
    
    # Criar gerenciador e enviar notificação
    manager = NotificationManager()
    success = manager.send_notification(
        message=args.message,
        alert_type=args.type,
        subject=args.subject
    )
    
    if success:
        logger.info("Notificação processada com sucesso")
        sys.exit(0)
    else:
        logger.error("Falha ao processar notificação")
        sys.exit(1)


if __name__ == '__main__':
    main()