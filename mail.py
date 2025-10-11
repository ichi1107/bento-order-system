"""
メール送信機能

パスワードリセット等のメール送信を管理
"""

import os
from typing import List
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr


class EmailConfig:
    """メール設定"""
    
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM = os.getenv("MAIL_FROM", "noreply@bento-system.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "Bento Order System")
    MAIL_STARTTLS = os.getenv("MAIL_STARTTLS", "True").lower() == "true"
    MAIL_SSL_TLS = os.getenv("MAIL_SSL_TLS", "False").lower() == "true"
    MAIL_USE_CREDENTIALS = os.getenv("MAIL_USE_CREDENTIALS", "True").lower() == "true"
    MAIL_VALIDATE_CERTS = os.getenv("MAIL_VALIDATE_CERTS", "True").lower() == "true"


# メール設定の初期化
conf = ConnectionConfig(
    MAIL_USERNAME=EmailConfig.MAIL_USERNAME,
    MAIL_PASSWORD=EmailConfig.MAIL_PASSWORD,
    MAIL_FROM=EmailConfig.MAIL_FROM,
    MAIL_PORT=EmailConfig.MAIL_PORT,
    MAIL_SERVER=EmailConfig.MAIL_SERVER,
    MAIL_FROM_NAME=EmailConfig.MAIL_FROM_NAME,
    MAIL_STARTTLS=EmailConfig.MAIL_STARTTLS,
    MAIL_SSL_TLS=EmailConfig.MAIL_SSL_TLS,
    USE_CREDENTIALS=EmailConfig.MAIL_USE_CREDENTIALS,
    VALIDATE_CERTS=EmailConfig.MAIL_VALIDATE_CERTS
)

fast_mail = FastMail(conf)


async def send_password_reset_email(email: EmailStr, reset_token: str, base_url: str = "http://localhost:8000"):
    """
    パスワードリセットメールを送信
    
    Args:
        email: 送信先メールアドレス
        reset_token: パスワードリセットトークン
        base_url: アプリケーションのベースURL
    """
    reset_link = f"{base_url}/reset-password?token={reset_token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>パスワードリセット</title>
        <style>
            body {{
                font-family: 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .container {{
                background-color: #f9f9f9;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                padding-bottom: 20px;
                border-bottom: 2px solid #4CAF50;
            }}
            h1 {{
                color: #4CAF50;
                margin: 0;
            }}
            .content {{
                padding: 20px 0;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                margin: 20px 0;
                background-color: #4CAF50;
                color: white !important;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
            }}
            .button:hover {{
                background-color: #45a049;
            }}
            .info-box {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                color: #777;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🍱 Bento Order System</h1>
            </div>
            
            <div class="content">
                <h2>パスワードリセットのご案内</h2>
                <p>パスワードリセットのリクエストを受け付けました。</p>
                <p>以下のボタンをクリックして、新しいパスワードを設定してください。</p>
                
                <div style="text-align: center;">
                    <a href="{reset_link}" class="button">パスワードをリセット</a>
                </div>
                
                <div class="info-box">
                    <strong>⚠️ 重要な注意事項:</strong>
                    <ul>
                        <li>このリンクの有効期限は <strong>1時間</strong> です</li>
                        <li>リンクは <strong>1回のみ</strong> 使用可能です</li>
                        <li>心当たりがない場合は、このメールを無視してください</li>
                    </ul>
                </div>
                
                <p style="color: #777; font-size: 14px;">
                    ボタンが機能しない場合は、以下のURLをコピーしてブラウザに貼り付けてください:<br>
                    <code style="background-color: #f0f0f0; padding: 5px; display: block; margin-top: 10px; word-break: break-all;">
                        {reset_link}
                    </code>
                </p>
            </div>
            
            <div class="footer">
                <p>© 2025 Bento Order System. All rights reserved.</p>
                <p>このメールに心当たりがない場合は、無視してください。</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject="【Bento Order System】パスワードリセットのご案内",
        recipients=[email],
        body=html_content,
        subtype=MessageType.html
    )
    
    await fast_mail.send_message(message)
