"""
Unit tests for authentication dependencies (dependencies.py)
"""
import pytest
from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session

from auth import create_access_token, create_refresh_token, get_password_hash
from dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_user_from_refresh_token,
    require_role,
    InvalidCredentialsException,
    InactiveUserException,
    InsufficientPermissionsException,
    oauth2_scheme,
)
from models import User, Role, UserRole
from database import SessionLocal


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
    """テスト用アクティブユーザー"""
    user = db.query(User).filter(User.username == "customer1").first()
    return user


@pytest.fixture
def inactive_user(db: Session):
    """テスト用非アクティブユーザー（作成）"""
    # 一時的に非アクティブユーザーを作成
    existing_user = db.query(User).filter(User.username == "inactive_test").first()
    if existing_user:
        db.delete(existing_user)
        db.commit()
    
    user = User(
        username="inactive_test",
        email="inactive@test.com",
        hashed_password=get_password_hash("password123"),
        role="customer",
        is_active=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    
    # クリーンアップ
    db.delete(user)
    db.commit()


@pytest.fixture
def owner_user(db: Session):
    """オーナー役割を持つユーザー（admin）"""
    user = db.query(User).filter(User.username == "admin").first()
    return user


@pytest.fixture
def manager_user(db: Session):
    """マネージャー役割を持つユーザー（store1）"""
    user = db.query(User).filter(User.username == "store1").first()
    return user


@pytest.fixture
def staff_user(db: Session):
    """スタッフ役割を持つユーザー（store2）"""
    user = db.query(User).filter(User.username == "store2").first()
    return user


class TestGetCurrentUser:
    """get_current_user関数のテスト"""
    
    def test_valid_token_returns_user(self, db: Session, test_user: User):
        """有効なトークンでユーザーが取得できる"""
        token = create_access_token(data={"sub": test_user.username})
        
        user = get_current_user(token=token, db=db)
        
        assert user.id == test_user.id
        assert user.username == test_user.username
        assert user.email == test_user.email
    
    def test_invalid_token_raises_exception(self, db: Session):
        """無効なトークンで例外が発生する"""
        invalid_token = "invalid.token.string"
        
        with pytest.raises(InvalidCredentialsException):
            get_current_user(token=invalid_token, db=db)
    
    def test_expired_token_raises_exception(self, db: Session, test_user: User):
        """期限切れトークンで例外が発生する"""
        token = create_access_token(
            data={"sub": test_user.username},
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(InvalidCredentialsException):
            get_current_user(token=token, db=db)
    
    def test_token_with_nonexistent_user_raises_exception(self, db: Session):
        """存在しないユーザーのトークンで例外が発生する"""
        token = create_access_token(data={"sub": "nonexistent_user"})
        
        with pytest.raises(InvalidCredentialsException):
            get_current_user(token=token, db=db)


class TestGetCurrentActiveUser:
    """get_current_active_user関数のテスト"""
    
    def test_active_user_returns_successfully(self, test_user: User):
        """アクティブユーザーは正常に返される"""
        user = get_current_active_user(current_user=test_user)
        
        assert user.id == test_user.id
        assert user.is_active is True
    
    def test_inactive_user_raises_exception(self, inactive_user: User):
        """非アクティブユーザーで例外が発生する"""
        with pytest.raises(InactiveUserException):
            get_current_active_user(current_user=inactive_user)


class TestGetCurrentUserFromRefreshToken:
    """get_current_user_from_refresh_token関数のテスト"""
    
    def test_valid_refresh_token_returns_user(self, db: Session, test_user: User):
        """有効なリフレッシュトークンでユーザーが取得できる"""
        token = create_refresh_token(data={"sub": test_user.username})
        
        user = get_current_user_from_refresh_token(token=token, db=db)
        
        assert user.id == test_user.id
        assert user.username == test_user.username
    
    def test_access_token_raises_exception(self, db: Session, test_user: User):
        """アクセストークンではエラーになる（type!=refresh）"""
        # アクセストークンにはtype="refresh"が含まれない
        token = create_access_token(data={"sub": test_user.username})
        
        with pytest.raises(InvalidCredentialsException):
            get_current_user_from_refresh_token(token=token, db=db)
    
    def test_expired_refresh_token_raises_exception(self, db: Session, test_user: User):
        """期限切れリフレッシュトークンで例外が発生する"""
        token = create_refresh_token(
            data={"sub": test_user.username},
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(InvalidCredentialsException):
            get_current_user_from_refresh_token(token=token, db=db)
    
    def test_invalid_refresh_token_raises_exception(self, db: Session):
        """無効なリフレッシュトークンで例外が発生する"""
        invalid_token = "invalid.refresh.token"
        
        with pytest.raises(InvalidCredentialsException):
            get_current_user_from_refresh_token(token=invalid_token, db=db)


class TestRequireRole:
    """require_role関数のテスト"""
    
    def test_owner_has_owner_role(self, db: Session, owner_user: User):
        """オーナーユーザーはowner役割を持つ"""
        role_checker = require_role(['owner'])
        
        user = role_checker(current_user=owner_user, db=db)
        
        assert user.id == owner_user.id
    
    def test_manager_has_manager_role(self, db: Session, manager_user: User):
        """マネージャーユーザーはmanager役割を持つ"""
        role_checker = require_role(['manager'])
        
        user = role_checker(current_user=manager_user, db=db)
        
        assert user.id == manager_user.id
    
    def test_staff_has_staff_role(self, db: Session, staff_user: User):
        """スタッフユーザーはstaff役割を持つ"""
        role_checker = require_role(['staff'])
        
        user = role_checker(current_user=staff_user, db=db)
        
        assert user.id == staff_user.id
    
    def test_owner_can_access_manager_endpoint(self, db: Session, owner_user: User):
        """オーナーは複数役割の中でアクセス可能"""
        role_checker = require_role(['owner', 'manager'])
        
        user = role_checker(current_user=owner_user, db=db)
        
        assert user.id == owner_user.id
    
    def test_staff_cannot_access_owner_endpoint(self, db: Session, staff_user: User):
        """スタッフはオーナー専用エンドポイントにアクセスできない"""
        role_checker = require_role(['owner'])
        
        with pytest.raises(InsufficientPermissionsException) as exc_info:
            role_checker(current_user=staff_user, db=db)
        
        assert exc_info.value.status_code == 403
        assert "owner" in exc_info.value.detail
    
    def test_customer_has_no_staff_roles(self, db: Session, test_user: User):
        """顧客ユーザーはスタッフ役割を持たない"""
        role_checker = require_role(['owner', 'manager', 'staff'])
        
        with pytest.raises(InsufficientPermissionsException) as exc_info:
            role_checker(current_user=test_user, db=db)
        
        assert exc_info.value.status_code == 403
    
    def test_multiple_roles_allowed(self, db: Session, manager_user: User):
        """複数の役割のいずれかを持つユーザーがアクセスできる"""
        role_checker = require_role(['owner', 'manager', 'staff'])
        
        user = role_checker(current_user=manager_user, db=db)
        
        assert user.id == manager_user.id


class TestCustomExceptions:
    """カスタム例外クラスのテスト"""
    
    def test_invalid_credentials_exception_has_401_status(self):
        """InvalidCredentialsExceptionは401ステータスを持つ"""
        exc = InvalidCredentialsException()
        
        assert exc.status_code == 401
        assert "validate credentials" in exc.detail
        assert "WWW-Authenticate" in exc.headers
    
    def test_inactive_user_exception_has_403_status(self):
        """InactiveUserExceptionは403ステータスを持つ"""
        exc = InactiveUserException()
        
        assert exc.status_code == 403
        assert "Inactive" in exc.detail
    
    def test_insufficient_permissions_exception_includes_roles(self):
        """InsufficientPermissionsExceptionは必要な役割を含む"""
        exc = InsufficientPermissionsException(['owner', 'manager'])
        
        assert exc.status_code == 403
        assert "owner" in exc.detail
        assert "manager" in exc.detail


class TestOAuth2Scheme:
    """OAuth2PasswordBearerスキームのテスト"""
    
    def test_oauth2_scheme_has_correct_token_url(self):
        """OAuth2スキームが正しいtokenUrlを持つ"""
        assert oauth2_scheme.model.flows.password.tokenUrl == "/api/v1/auth/login"


class TestGetCurrentCustomer:
    """get_current_customer関数のテスト"""
    
    def test_customer_user_returns_successfully(self, test_user: User):
        """顧客ユーザーは正常に返される"""
        from dependencies import get_current_customer
        
        user = get_current_customer(current_user=test_user)
        
        assert user.id == test_user.id
        assert user.role == "customer"
    
    def test_store_user_raises_exception(self, owner_user: User):
        """店舗ユーザーで例外が発生する"""
        from dependencies import get_current_customer
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_customer(current_user=owner_user)
        
        assert exc_info.value.status_code == 403
        assert "Customer access required" in exc_info.value.detail


class TestGetCurrentStoreUser:
    """get_current_store_user関数のテスト"""
    
    def test_store_user_returns_successfully(self, owner_user: User):
        """店舗ユーザーは正常に返される"""
        from dependencies import get_current_store_user
        
        user = get_current_store_user(current_user=owner_user)
        
        assert user.id == owner_user.id
        assert user.role == "store"
    
    def test_customer_user_raises_exception(self, test_user: User):
        """顧客ユーザーで例外が発生する"""
        from dependencies import get_current_store_user
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_store_user(current_user=test_user)
        
        assert exc_info.value.status_code == 403
        assert "Store access required" in exc_info.value.detail
