"""
認証機能

JWT トークンベースの認証とパスワードハッシュ化機能
"""

import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# 設定値
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    平文パスワードとハッシュ化パスワードを比較
    
    Args:
        plain_password: 平文パスワード
        hashed_password: ハッシュ化されたパスワード
        
    Returns:
        bool: パスワードが一致する場合True
    """
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def get_password_hash(password: str) -> str:
    """
    パスワードをハッシュ化
    
    Args:
        password: 平文パスワード
        
    Returns:
        str: ハッシュ化されたパスワード
    """
    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWTアクセストークンを作成
    
    Args:
        data: トークンに含めるデータ
        expires_delta: 有効期限（デフォルト: ACCESS_TOKEN_EXPIRE_MINUTES）
        
    Returns:
        str: JWTトークン
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """
    JWTトークンを検証し、ユーザー名を取得
    
    Args:
        token: JWTトークン
        
    Returns:
        Optional[str]: ユーザー名（無効な場合はNone）
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None