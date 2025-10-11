"""
パスワードリセット機能のテスト (routers/auth.py)
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from database import SessionLocal
from models import User, PasswordResetToken
from auth import get_password_hash


client = TestClient(app)


@pytest.fixture
def db():
    """データベースセッションフィクスチャ"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db: Session):
    """テスト用ユーザー"""
    # 既存のユーザーを削除
    existing_user = db.query(User).filter(User.email == "reset_test@example.com").first()
    if existing_user:
        db.delete(existing_user)
        db.commit()
    
    user = User(
        username="reset_test_user",
        email="reset_test@example.com",
        hashed_password=get_password_hash("old_password123"),
        role="customer",
        full_name="Reset Test User",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    
    # クリーンアップ
    db.delete(user)
    db.commit()


@pytest.fixture
def cleanup_tokens(db: Session):
    """テスト後にトークンをクリーンアップ"""
    yield
    # テスト後に作成されたトークンを削除
    db.query(PasswordResetToken).filter(
        PasswordResetToken.email == "reset_test@example.com"
    ).delete()
    db.commit()


@pytest.fixture
def cleanup_rate_limit():
    """レート制限辞書をクリーンアップ"""
    from routers.auth import password_reset_rate_limit
    yield
    # テスト後にレート制限をクリア
    if "reset_test@example.com" in password_reset_rate_limit:
        del password_reset_rate_limit["reset_test@example.com"]
    if "nonexistent@example.com" in password_reset_rate_limit:
        del password_reset_rate_limit["nonexistent@example.com"]


class TestPasswordResetRequest:
    """パスワードリセット要求のテスト"""
    
    @patch("routers.auth.send_password_reset_email", new_callable=AsyncMock)
    def test_request_password_reset_success(self, mock_send_email, test_user, db, cleanup_tokens, cleanup_rate_limit):
        """有効なメールアドレスでパスワードリセット要求が成功する"""
        response = client.post(
            "/api/auth/password-reset-request",
            json={"email": "reset_test@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "password reset link has been sent" in data["message"].lower()
        
        # メール送信が呼ばれたことを確認
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        assert call_args[0][0] == "reset_test@example.com"
        
        # トークンがデータベースに保存されたことを確認
        token_in_db = db.query(PasswordResetToken).filter(
            PasswordResetToken.email == "reset_test@example.com"
        ).first()
        assert token_in_db is not None
        assert token_in_db.used_at is None
        assert token_in_db.expires_at > datetime.now(timezone.utc)
    
    @patch("routers.auth.send_password_reset_email", new_callable=AsyncMock)
    def test_request_password_reset_nonexistent_email(self, mock_send_email, cleanup_rate_limit):
        """存在しないメールアドレスでも同じレスポンスを返す(セキュリティ)"""
        response = client.post(
            "/api/auth/password-reset-request",
            json={"email": "nonexistent@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # セキュリティのため、同じメッセージを返す
        assert "password reset link has been sent" in data["message"].lower()
        
        # メール送信は呼ばれない
        mock_send_email.assert_not_called()
    
    def test_request_password_reset_invalid_email(self, cleanup_rate_limit):
        """無効なメールアドレス形式でエラーが返る"""
        response = client.post(
            "/api/auth/password-reset-request",
            json={"email": "invalid-email"}
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch("routers.auth.send_password_reset_email", new_callable=AsyncMock)
    def test_request_password_reset_rate_limit(self, mock_send_email, test_user, cleanup_tokens, cleanup_rate_limit):
        """5分以内の2回目のリクエストがレート制限される"""
        # 1回目のリクエスト
        response1 = client.post(
            "/api/auth/password-reset-request",
            json={"email": "reset_test@example.com"}
        )
        assert response1.status_code == 200
        
        # 2回目のリクエスト(5分以内)
        response2 = client.post(
            "/api/auth/password-reset-request",
            json={"email": "reset_test@example.com"}
        )
        
        assert response2.status_code == 429  # Too Many Requests
        data = response2.json()
        assert "too many requests" in data["detail"].lower()
        assert "seconds" in data["detail"].lower()
    
    @patch("routers.auth.send_password_reset_email", new_callable=AsyncMock)
    def test_request_password_reset_email_send_failure(self, mock_send_email, test_user, db, cleanup_tokens, cleanup_rate_limit):
        """メール送信失敗時でも成功レスポンスを返す"""
        # メール送信を失敗させる
        mock_send_email.side_effect = Exception("SMTP error")
        
        response = client.post(
            "/api/auth/password-reset-request",
            json={"email": "reset_test@example.com"}
        )
        
        # エラーを隠蔽して成功レスポンスを返す
        assert response.status_code == 200
        
        # トークンは保存されている
        token_in_db = db.query(PasswordResetToken).filter(
            PasswordResetToken.email == "reset_test@example.com"
        ).first()
        assert token_in_db is not None


class TestPasswordResetConfirm:
    """パスワードリセット確認のテスト"""
    
    def test_confirm_password_reset_success(self, test_user, db, cleanup_tokens):
        """有効なトークンでパスワードリセットが成功する"""
        # トークンを作成
        token_value = "valid_test_token_123"
        reset_token = PasswordResetToken(
            token=token_value,
            email="reset_test@example.com",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        db.add(reset_token)
        db.commit()
        
        # パスワードリセット
        new_password = "new_password456"
        response = client.post(
            "/api/auth/password-reset-confirm",
            json={"token": token_value, "new_password": new_password}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "successfully reset" in data["message"].lower()
        
        # トークンが使用済みになっていることを確認
        db.refresh(reset_token)
        assert reset_token.used_at is not None
        
        # パスワードが変更されたことを確認
        db.refresh(test_user)
        from auth import verify_password
        assert verify_password(new_password, test_user.hashed_password)
    
    def test_confirm_password_reset_invalid_token(self):
        """無効なトークンでエラーが返る"""
        response = client.post(
            "/api/auth/password-reset-confirm",
            json={"token": "invalid_token_xyz", "new_password": "new_password456"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "invalid" in data["detail"].lower()
    
    def test_confirm_password_reset_expired_token(self, test_user, db, cleanup_tokens):
        """期限切れのトークンでエラーが返る"""
        # 期限切れのトークンを作成
        token_value = "expired_token_123"
        reset_token = PasswordResetToken(
            token=token_value,
            email="reset_test@example.com",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)  # 1時間前に期限切れ
        )
        db.add(reset_token)
        db.commit()
        
        response = client.post(
            "/api/auth/password-reset-confirm",
            json={"token": token_value, "new_password": "new_password456"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "expired" in data["detail"].lower()
    
    def test_confirm_password_reset_already_used_token(self, test_user, db, cleanup_tokens):
        """既に使用済みのトークンでエラーが返る"""
        # 使用済みのトークンを作成
        token_value = "used_token_123"
        reset_token = PasswordResetToken(
            token=token_value,
            email="reset_test@example.com",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            used_at=datetime.now(timezone.utc) - timedelta(minutes=10)  # 10分前に使用済み
        )
        db.add(reset_token)
        db.commit()
        
        response = client.post(
            "/api/auth/password-reset-confirm",
            json={"token": token_value, "new_password": "new_password456"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already been used" in data["detail"].lower()
    
    def test_confirm_password_reset_weak_password(self, test_user, db, cleanup_tokens):
        """6文字未満のパスワードでバリデーションエラーが返る"""
        # トークンを作成
        token_value = "valid_token_123"
        reset_token = PasswordResetToken(
            token=token_value,
            email="reset_test@example.com",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        db.add(reset_token)
        db.commit()
        
        response = client.post(
            "/api/auth/password-reset-confirm",
            json={"token": token_value, "new_password": "12345"}  # 5文字
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_confirm_password_reset_empty_password(self, test_user, db, cleanup_tokens):
        """空のパスワードでバリデーションエラーが返る"""
        # トークンを作成
        token_value = "valid_token_123"
        reset_token = PasswordResetToken(
            token=token_value,
            email="reset_test@example.com",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        db.add(reset_token)
        db.commit()
        
        response = client.post(
            "/api/auth/password-reset-confirm",
            json={"token": token_value, "new_password": ""}
        )
        
        assert response.status_code == 422  # Validation error


class TestPasswordResetEdgeCases:
    """エッジケースのテスト"""
    
    def test_request_with_empty_email(self, cleanup_rate_limit):
        """空のメールアドレスでバリデーションエラーが返る"""
        response = client.post(
            "/api/auth/password-reset-request",
            json={"email": ""}
        )
        
        assert response.status_code == 422
    
    def test_confirm_with_empty_token(self):
        """空のトークンでエラーが返る"""
        response = client.post(
            "/api/auth/password-reset-confirm",
            json={"token": "", "new_password": "new_password123"}
        )
        
        # 空のトークンは存在しないトークンとして扱われる
        assert response.status_code == 404
    
    @patch("routers.auth.send_password_reset_email", new_callable=AsyncMock)
    def test_token_uniqueness(self, mock_send_email, test_user, db, cleanup_tokens, cleanup_rate_limit):
        """複数のリクエストで異なるトークンが生成される"""
        from routers.auth import password_reset_rate_limit
        
        # 1回目のリクエスト
        response1 = client.post(
            "/api/auth/password-reset-request",
            json={"email": "reset_test@example.com"}
        )
        assert response1.status_code == 200
        
        # レート制限を手動でクリア
        del password_reset_rate_limit["reset_test@example.com"]
        
        # 2回目のリクエスト
        response2 = client.post(
            "/api/auth/password-reset-request",
            json={"email": "reset_test@example.com"}
        )
        assert response2.status_code == 200
        
        # 2つの異なるトークンが生成されていることを確認
        tokens = db.query(PasswordResetToken).filter(
            PasswordResetToken.email == "reset_test@example.com"
        ).all()
        assert len(tokens) >= 2
        assert tokens[0].token != tokens[1].token
    
    def test_token_format_validation(self, test_user, db, cleanup_tokens):
        """トークンの形式が適切かを確認"""
        # トークンを作成
        token_value = "a" * 43  # secrets.token_urlsafe(32) は通常43文字程度
        reset_token = PasswordResetToken(
            token=token_value,
            email="reset_test@example.com",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        db.add(reset_token)
        db.commit()
        
        # トークンでパスワードリセット
        response = client.post(
            "/api/auth/password-reset-confirm",
            json={"token": token_value, "new_password": "new_password456"}
        )
        
        assert response.status_code == 200
