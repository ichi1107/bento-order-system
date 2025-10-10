"""
依存関数

FastAPIの依存関数（Dependency Injection）を定義
認証が必要なエンドポイントで使用
"""

from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from auth import verify_token, decode_token
from models import User, Role, UserRole

# OAuth2認証スキーム（Swagger UI対応）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# カスタム例外クラス
class InvalidCredentialsException(HTTPException):
    """無効な認証情報の例外"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InactiveUserException(HTTPException):
    """非アクティブユーザーの例外"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )


class InsufficientPermissionsException(HTTPException):
    """権限不足の例外"""
    def __init__(self, required_roles: List[str]):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required roles: {', '.join(required_roles)}",
        )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    現在のユーザーを取得
    
    Args:
        token: JWTトークン
        db: データベースセッション
        
    Returns:
        User: 現在のユーザー
        
    Raises:
        InvalidCredentialsException: 認証に失敗した場合
    """
    try:
        # トークンからユーザー名を取得
        username = verify_token(token)
        if username is None:
            raise InvalidCredentialsException()
    except Exception:
        raise InvalidCredentialsException()
    
    # データベースからユーザーを取得
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise InvalidCredentialsException()
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    現在のアクティブユーザーを取得
    
    Args:
        current_user: 現在のユーザー
        
    Returns:
        User: アクティブなユーザー
        
    Raises:
        InactiveUserException: ユーザーが無効化されている場合
    """
    if not current_user.is_active:
        raise InactiveUserException()
    return current_user


def get_current_user_from_refresh_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    リフレッシュトークンから現在のユーザーを取得
    
    Args:
        token: リフレッシュトークン
        db: データベースセッション
        
    Returns:
        User: 現在のユーザー
        
    Raises:
        InvalidCredentialsException: 認証に失敗した場合
    """
    try:
        # トークンをデコードしてペイロードを取得
        payload = decode_token(token)
        
        # リフレッシュトークンであることを確認
        if payload.get("type") != "refresh":
            raise InvalidCredentialsException()
        
        username: str = payload.get("sub")
        if username is None:
            raise InvalidCredentialsException()
    except Exception:
        raise InvalidCredentialsException()
    
    # データベースからユーザーを取得
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise InvalidCredentialsException()
    
    return user


def require_role(allowed_roles: List[str]):
    """
    指定された役割を持つユーザーのみアクセス可能にする依存性を返す
    
    Args:
        allowed_roles: 許可される役割のリスト (例: ['owner', 'manager'])
        
    Returns:
        依存性関数
        
    Example:
        @app.get("/admin", dependencies=[Depends(require_role(['owner']))])
        def admin_endpoint():
            return {"message": "Admin only"}
    """
    def role_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        """
        ユーザーの役割を確認
        
        Args:
            current_user: 現在のアクティブユーザー
            db: データベースセッション
            
        Returns:
            User: 権限を持つユーザー
            
        Raises:
            InsufficientPermissionsException: 権限が不足している場合
        """
        # UserRoleテーブルから役割を取得
        user_roles = (
            db.query(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == current_user.id)
            .all()
        )
        
        # ユーザーが持つ役割名のリストを作成
        user_role_names = [role.name for role in user_roles]
        
        # 許可された役割のいずれかを持っているかチェック
        if not any(role in user_role_names for role in allowed_roles):
            raise InsufficientPermissionsException(allowed_roles)
        
        return current_user
    
    return role_checker


def get_current_customer(current_user: User = Depends(get_current_active_user)) -> User:
    """
    現在のお客様ユーザーを取得
    
    Args:
        current_user: 現在のユーザー
        
    Returns:
        User: お客様ユーザー
        
    Raises:
        HTTPException: お客様権限がない場合
    """
    if current_user.role != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer access required"
        )
    return current_user


def get_current_store_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    現在の店舗ユーザーを取得
    
    Args:
        current_user: 現在のユーザー
        
    Returns:
        User: 店舗ユーザー
        
    Raises:
        HTTPException: 店舗権限がない場合
    """
    if current_user.role != "store":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Store access required"
        )
    return current_user