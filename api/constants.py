TECH_SUPPORT_FIRST_ANSWER: str = '''Здравствуйте, {name}!

Мы получили Ваше обращение по теме: {theme}.

Ваше сообщение:
{message_text}

Мы свяжемся с вами в ближайшее время.

С уважением,
Команда поддержки Tatiana-News'''


VERIFICATION_CODE_EMAIL: str = '''Здравствуйте! Отправили Вам код верификации. Если Вы не взаимодействовали с сервисом Tatiana-News в настоящий момент, никому не сообщайте код верификации. 
Код верификации: {verification_code}

С уважением,
Команда сервиса Tatiana-News'''


VERIFICATION_CODE_EMAIL_HTML: str = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Код подтверждения</title>
</head>
<body style="margin:0; padding:0; background-color:#f4f4f4; font-family: Arial, Helvetica, sans-serif;">
    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color:#f4f4f4;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table width="100%" max-width="600px" border="0" cellspacing="0" cellpadding="0" style="background-color:#ffffff; border-radius:8px; overflow:hidden; box-shadow:0 4px 12px rgba(0,0,0,0.1);">
                    
                    <!-- Основной контент -->
                    <tr>
                        <td style="padding: 40px 40px 30px 40px; text-align:center; color:#222222;">
                            <h2 style="margin:0 0 20px 0; font-size:20px; font-weight:600;">
                                Код для подтверждения регистрации на портале Tatiana.News:
                            </h2>
                            
                            <!-- Код -->
                            <div style="margin: 30px 0;">
                                <div style="background-color:#4285f4; color:white; font-size:32px; font-weight:700; 
                                            padding:14px 30px; border-radius:10px; display:inline-block; 
                                            letter-spacing:5px; box-shadow:0 4px 15px rgba(66,133,244,0.3);">
                                    {verification_code_formatted}
                                </div>
                            </div>
                            
                            <p style="margin:25px 0 0 0; font-size:16px; line-height:1.5; color:#444444;">
                                Если вы не пытались войти в Tatiana.News,<br>
                                просто проигнорируйте это письмо.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Чёрная полоса внизу -->
                    <tr>
                        <td style="background-color:#000000; padding:20px 40px; text-align:center;">
                            <a href="http://127.0.0.1:8000/user_agreement/" 
                               style="color:#ffffff; text-decoration:underline; font-size:14px;">
                                Пользовательское соглашение
                            </a>
                            <span style="color:#555555; margin:0 12px;">•</span>
                            <a href="http://127.0.0.1:8000/privacy/" 
                               style="color:#ffffff; text-decoration:underline; font-size:14px;">
                                Политика конфиденциальности
                            </a>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
'''
