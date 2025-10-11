"""
認証ルーター

ユーザー認証関連のAPIエンドポイント
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import UserCreate, UserLogin, TokenResponse, UserResponse, SuccessResponse
from auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from dependencies import get_current_active_user, get_current_user_from_refresh_token

router = APIRouter(prefix="/auth", tags=["認証"])


@router.post("/register", response_model=UserResponse, summary="ユーザー登録")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    新しいユーザーを登録
    
    - **username**: ユーザー名（3-50文字、一意）
    - **email**: メールアドレス（一意）
    - **password**: パスワード（6文字以上）
    - **full_name**: 氏名
    - **role**: ロール（customer または store）
    """
    # ユーザー名の重複チェック
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # メールアドレスの重複チェック
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # パスワードをハッシュ化
    hashed_password = get_password_hash(user.password)
    
    # ユーザーを作成
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=TokenResponse, summary="ログイン")
def login_for_access_token(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    ユーザーログインしてアクセストークンとリフレッシュトークンを取得
    
    - **username**: ユーザー名
    - **password**: パスワード
    
    成功時は、アクセストークン、リフレッシュトークン、ユーザー情報を返します。
    """
    # ユーザーを検索
    user = db.query(User).filter(User.username == user_credentials.username).first()
    
    # ユーザー存在確認とパスワード検証
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # ユーザーがアクティブか確認
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    # アクセストークンを作成
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # リフレッシュトークンを作成
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/logout", response_model=SuccessResponse, summary="ログアウト")
def logout():
    """
    ログアウト
    
    注意: JWTはステートレスなため、サーバー側では特別な処理は行いません。
    クライアント側でトークンを削除してください。
    
    将来的にトークン無効化リスト（ブラックリスト）を実装する場合は、
    ここでリフレッシュトークンを無効化リストに追加します。
    """
    return {"success": True, "message": "Successfully logged out"}


@router.post("/refresh", response_model=TokenResponse, summary="トークンリフレッシュ")
def refresh_access_token(
    current_user: User = Depends(get_current_user_from_refresh_token),
    db: Session = Depends(get_db)
):
    """
    リフレッシュトークンを使用して新しいアクセストークンを取得
    
    Authorization: Bearer <refresh_token>
    
    成功時は、新しいアクセストークン、リフレッシュトークン、ユーザー情報を返します。
    """
    # 新しいアクセストークンを作成
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username}, 
        expires_delta=access_token_expires
    )
    
    # 新しいリフレッシュトークンも作成（セキュリティのため）
    refresh_token = create_refresh_token(data={"sub": current_user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": current_user
    }


@router.get("/me", response_model=UserResponse, summary="現在のユーザー情報取得")
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    現在ログイン中のユーザー情報を取得
    
    Authorization: Bearer <access_token>
    
    認証されたユーザーのプロファイル情報を返します。
    """
    return current_user