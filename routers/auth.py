"""
認証ルーター

ユーザー認証関連のAPIエンドポイント
"""

from datetime import datetime, timedelta, timezone
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import User, PasswordResetToken, UserRole
from schemas import (
    UserCreate, 
    UserLogin, 
    TokenResponse, 
    UserResponse, 
    SuccessResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetResponse
)
from auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from dependencies import get_current_active_user, get_current_user_from_refresh_token
from mail import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["認証"])

# パスワードリセットのレート制限（メールアドレスごとに5分間に1回まで）
password_reset_rate_limit: dict[str, datetime] = {}


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
def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    現在ログイン中のユーザー情報を取得
    
    Authorization: Bearer <access_token>
    
    認証されたユーザーのプロファイル情報を返します。
    """
    # user_rolesリレーションシップをロード
    user = db.query(User).options(
        joinedload(User.user_roles).joinedload(UserRole.role)
    ).filter(User.id == current_user.id).first()
    
    return user


@router.post("/password-reset-request", response_model=PasswordResetResponse, summary="パスワードリセット要求")
async def request_password_reset(
    request_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    パスワードリセットのリクエストを送信
    
    - **email**: パスワードリセットを要求するメールアドレス
    
    メールアドレスが登録されている場合、リセット用のリンクを含むメールを送信します。
    セキュリティのため、メールアドレスの存在有無に関わらず同じレスポンスを返します。
    
    レート制限: 同一メールアドレスにつき5分間に1回まで
    """
    email = request_data.email
    
    # レート制限チェック
    now = datetime.now(timezone.utc)
    if email in password_reset_rate_limit:
        last_request = password_reset_rate_limit[email]
        time_since_last_request = now - last_request
        
        if time_since_last_request < timedelta(minutes=5):
            remaining_seconds = int((timedelta(minutes=5) - time_since_last_request).total_seconds())
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Please try again in {remaining_seconds} seconds."
            )
    
    # レート制限の古いエントリを削除（5分以上前のもの）
    expired_emails = [
        email_key for email_key, timestamp in password_reset_rate_limit.items()
        if now - timestamp > timedelta(minutes=5)
    ]
    for email_key in expired_emails:
        del password_reset_rate_limit[email_key]
    
    # ユーザーを検索
    user = db.query(User).filter(User.email == email).first()
    
    # セキュリティのため、ユーザーの存在有無に関わらず同じ処理を行う
    if user:
        # トークンを生成
        reset_token = secrets.token_urlsafe(32)
        
        # トークンの有効期限を設定（1時間後）
        expires_at = now + timedelta(hours=1)
        
        # トークンをデータベースに保存
        db_token = PasswordResetToken(
            token=reset_token,
            email=email,
            expires_at=expires_at
        )
        db.add(db_token)
        db.commit()
        
        # パスワードリセットメールを送信
        try:
            await send_password_reset_email(email, reset_token)
        except Exception as e:
            # メール送信エラーはログに記録するが、ユーザーには成功レスポンスを返す
            print(f"Failed to send password reset email: {str(e)}")
    
    # レート制限を更新
    password_reset_rate_limit[email] = now
    
    # セキュリティのため、常に同じメッセージを返す
    return PasswordResetResponse(
        message="If the email address is registered, a password reset link has been sent."
    )


@router.post("/password-reset-confirm", response_model=PasswordResetResponse, summary="パスワードリセット実行")
def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    パスワードリセットトークンを使用してパスワードを変更
    
    - **token**: パスワードリセットトークン
    - **new_password**: 新しいパスワード（6文字以上）
    
    トークンが有効な場合、パスワードを変更します。
    """
    # トークンを検索
    db_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == reset_data.token
    ).first()
    
    # トークンが存在しない場合
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid password reset token"
        )
    
    # トークンの有効期限をチェック
    now = datetime.now(timezone.utc)
    if now > db_token.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired"
        )
    
    # トークンが既に使用されているかチェック
    if db_token.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has already been used"
        )
    
    # ユーザーを検索
    user = db.query(User).filter(User.email == db_token.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # パスワードを更新
    user.hashed_password = get_password_hash(reset_data.new_password)
    
    # トークンを使用済みにマーク
    db_token.used_at = now
    
    db.commit()
    
    return PasswordResetResponse(
        message="Password has been successfully reset"
    )
