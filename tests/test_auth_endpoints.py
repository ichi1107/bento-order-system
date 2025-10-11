"""
Integration tests for authentication endpoints (routers/auth.py)
"""
import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from database import SessionLocal
from models import User
from auth import get_password_hash, create_access_token, create_refresh_token


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
    """テスト用ユーザー（customer1）"""
    user = db.query(User).filter(User.username == "customer1").first()
    return user


@pytest.fixture
def inactive_user(db: Session):
    """テスト用非アクティブユーザー"""
    existing_user = db.query(User).filter(User.username == "inactive_test_user").first()
    if existing_user:
        db.delete(existing_user)
        db.commit()
    
    user = User(
        username="inactive_test_user",
        email="inactive_test@example.com",
        hashed_password=get_password_hash("password123"),
        role="customer",
        full_name="Inactive User",
        is_active=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    
    # クリーンアップ
    db.delete(user)
    db.commit()


class TestRegisterEndpoint:
    """ユーザー登録エンドポイントのテスト"""
    
    def test_register_new_user(self, db: Session):
        """新規ユーザー登録が成功する"""
        # 既存ユーザーを削除（クリーンアップ）
        existing_user = db.query(User).filter(User.username == "newuser").first()
        if existing_user:
            db.delete(existing_user)
            db.commit()
        
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User",
            "role": "customer"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "customer"
        assert "hashed_password" not in data
        
        # クリーンアップ
        db.delete(db.query(User).filter(User.username == "newuser").first())
        db.commit()
    
    def test_register_duplicate_username(self, db: Session, test_user: User):
        """重複したユーザー名で登録できない"""
        user_data = {
            "username": test_user.username,
            "email": "different@example.com",
            "password": "password123",
            "full_name": "Duplicate User",
            "role": "customer"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_duplicate_email(self, db: Session, test_user: User):
        """重複したメールアドレスで登録できない"""
        user_data = {
            "username": "differentuser",
            "email": test_user.email,
            "password": "password123",
            "full_name": "Duplicate Email User",
            "role": "customer"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()


class TestLoginEndpoint:
    """ログインエンドポイントのテスト"""
    
    def test_login_success(self, test_user: User):
        """正しい認証情報でログインできる"""
        login_data = {
            "username": test_user.username,
            "password": "password123"  # init_data.pyで設定されたパスワード
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == test_user.username
        assert data["user"]["email"] == test_user.email
    
    def test_login_wrong_password(self, test_user: User):
        """誤ったパスワードでログインできない"""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self):
        """存在しないユーザーでログインできない"""
        login_data = {
            "username": "nonexistent",
            "password": "password"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_login_inactive_user(self, inactive_user: User):
        """非アクティブユーザーでログインできない"""
        login_data = {
            "username": inactive_user.username,
            "password": "password123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 403
        assert "inactive" in response.json()["detail"].lower()


class TestRefreshEndpoint:
    """トークンリフレッシュエンドポイントのテスト"""
    
    def test_refresh_with_valid_refresh_token(self, test_user: User):
        """有効なリフレッシュトークンで新しいアクセストークンを取得できる"""
        refresh_token = create_refresh_token(data={"sub": test_user.username})
        
        response = client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == test_user.username
    
    def test_refresh_with_access_token_fails(self, test_user: User):
        """アクセストークンではリフレッシュできない（type="refresh"が必要）"""
        access_token = create_access_token(data={"sub": test_user.username})
        
        response = client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 401
    
    def test_refresh_with_expired_token(self, test_user: User):
        """期限切れリフレッシュトークンではリフレッシュできない"""
        expired_token = create_refresh_token(
            data={"sub": test_user.username},
            expires_delta=timedelta(seconds=-1)
        )
        
        response = client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401
    
    def test_refresh_without_token(self):
        """トークンなしではリフレッシュできない"""
        response = client.post("/api/auth/refresh")
        
        assert response.status_code == 401


class TestMeEndpoint:
    """現在のユーザー情報取得エンドポイントのテスト"""
    
    def test_get_current_user_info(self, test_user: User):
        """有効なアクセストークンで現在のユーザー情報を取得できる"""
        access_token = create_access_token(data={"sub": test_user.username})
        
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert data["role"] == test_user.role
        assert data["is_active"] == test_user.is_active
        assert "hashed_password" not in data
    
    def test_get_current_user_without_token(self):
        """トークンなしではユーザー情報を取得できない"""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 401
    
    def test_get_current_user_with_invalid_token(self):
        """無効なトークンではユーザー情報を取得できない"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
    
    def test_get_current_user_with_expired_token(self, test_user: User):
        """期限切れトークンではユーザー情報を取得できない"""
        expired_token = create_access_token(
            data={"sub": test_user.username},
            expires_delta=timedelta(seconds=-1)
        )
        
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401


class TestLogoutEndpoint:
    """ログアウトエンドポイントのテスト"""
    
    def test_logout_success(self):
        """ログアウトが成功する"""
        response = client.post("/api/auth/logout")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data


class TestAuthenticationFlow:
    """認証フロー全体のテスト"""
    
    def test_complete_auth_flow(self, test_user: User):
        """ログイン→me→リフレッシュ→me→ログアウトの一連の流れ"""
        # 1. ログイン
        login_response = client.post(
            "/api/auth/login",
            json={"username": test_user.username, "password": "password123"}
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]
        
        # 2. ユーザー情報取得（アクセストークン使用）
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["username"] == test_user.username
        
        # 3. トークンリフレッシュ
        refresh_response = client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.json()["access_token"]
        
        # 4. 新しいアクセストークンでユーザー情報取得
        me_response2 = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert me_response2.status_code == 200
        assert me_response2.json()["username"] == test_user.username
        
        # 5. ログアウト
        logout_response = client.post("/api/auth/logout")
        assert logout_response.status_code == 200
        assert logout_response.json()["success"] is True
