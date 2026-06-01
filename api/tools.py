import os
import re

import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import pyotp
import qrcode
from io import BytesIO
import base64

from constants import TECH_SUPPORT_FIRST_ANSWER, VERIFICATION_CODE_EMAIL_HTML

private_vars = os.environ
SENDER_EMAIL: str = private_vars["SENDER_EMAIL"]
SMTP_SERVER: int = private_vars["SMTP_SERVER"]
SMTP_PORT: int = private_vars["SMTP_PORT"]
APP_PASSWORD: str = private_vars["APP_PASSWORD"]

class Tools:
    def __init__(self):
        pass

    @staticmethod
    def simple_tokenize(text: str) -> str:
        """Лёгкая токенизация: lower + только слова"""
        if not text:
            return []

        cleaned = re.sub(r'[^\w\s]', ' ', text.lower())
        # Разбиваем и отбрасываем слишком короткие токены
        return [word for word in cleaned.split() if len(word) >= 2]
    
    @staticmethod
    def score(text: str, tokens: list[str]):
        text = text.lower()
        return sum(token in text for token in tokens)

    @staticmethod
    def send_tech_support_email(to_email: str, name: str, theme: str, message_text: str) -> bool:
        """
        Отправляет электронное письмо на передаваемый адрес
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = to_email
            msg['Subject'] = f"Ваше обращение в поддержку: {theme}"

            body = TECH_SUPPORT_FIRST_ANSWER.replace('{name}', name).replace('{theme}', theme).replace('{message_text}', message_text)
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, APP_PASSWORD)
                server.send_message(msg)

            return True

        except Exception as _ex:
            print(f"[tools.py->send_tech_support_email]. Error :: {_ex}")
            return False
        
    @staticmethod
    def send_verification_code_email(code: str, to_email: str) -> bool:
        """
        Отправляет электронное письмо на передаваемый адрес. В письме содержится код верификации
        """
        try:
            print('trying to send verification code')
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = to_email
            msg['Subject'] = f"Код верификации для подтверждения действия в Tatiana-News"

            formatted_code = f"{code[:2]} {code[2:]}"
            html_body = VERIFICATION_CODE_EMAIL_HTML.replace(
                "{verification_code_formatted}", formatted_code
            )

            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, APP_PASSWORD)
                server.send_message(msg)

            return True

        except Exception as _ex:
            print(f"[tools.py->send_verification_code_email]. Error :: {_ex}")
            return False
        
    @staticmethod
    def generate_verification_code() -> str:
        code = f"{secrets.randbelow(10000):04d}"
        return code
    
    @staticmethod
    def censor_text(text: str) -> str:
        del_point = text.find('@')
        text_pre_stars = text[:3]
        text_after_del = text[del_point:]
        return text_pre_stars + '*' * 2 + text_after_del

    @staticmethod
    def generate_2fa_qr(email: str, issuer_name: str = "T — News"):
        """Генерирует секрет и QR-код в base64 для Google Authenticator"""
        secret = pyotp.random_base32()                    # надёжный секрет
        totp = pyotp.TOTP(secret)

        provisioning_uri = totp.provisioning_uri(
            name=email,
            issuer_name=issuer_name
        )

        # Создаём QR-код
        qr = qrcode.make(provisioning_uri)
        buffered = BytesIO()
        qr.save(buffered, format="PNG")
        buffered.seek(0)

        qr_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return secret, f"data:image/png;base64,{qr_base64}"