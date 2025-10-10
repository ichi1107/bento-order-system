"""
Unit tests for authentication utilities (auth.py)
"""
import pytest
from datetime import timedelta, datetime
from jose import jwt, JWTError
from auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)


class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_get_password_hash_creates_bcrypt_hash(self):
        """Verify password is hashed using bcrypt"""
        password = "test_password123"
        hashed = get_password_hash(password)
        
        # Bcrypt hashes start with $2b$
        assert hashed.startswith("$2b$")
        # Hash should not be the same as original
        assert hashed != password
        # Hash should be consistent length (60 chars for bcrypt)
        assert len(hashed) == 60
    
    def test_get_password_hash_is_non_reversible(self):
        """Verify same password produces different hashes (salt)"""
        password = "test_password123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Each hash should be different due to random salt
        assert hash1 != hash2
    
    def test_verify_password_with_correct_password(self):
        """Verify correct password validates successfully"""
        password = "correct_password"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_with_incorrect_password(self):
        """Verify incorrect password fails validation"""
        correct_password = "correct_password"
        incorrect_password = "wrong_password"
        hashed = get_password_hash(correct_password)
        
        assert verify_password(incorrect_password, hashed) is False
    
    def test_verify_password_with_empty_password(self):
        """Verify empty password fails validation"""
        password = "test_password"
        hashed = get_password_hash(password)
        
        assert verify_password("", hashed) is False


class TestAccessTokens:
    """Test access token creation and validation"""
    
    def test_create_access_token_with_default_expiry(self):
        """Verify access token is created with default 30-minute expiry"""
        data = {"sub": "testuser@example.com"}
        token = create_access_token(data)
        
        # Decode to verify
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser@example.com"
        
        # Verify expiry is set (should be ~30 minutes from now)
        exp_timestamp = payload["exp"]
        exp_time = datetime.fromtimestamp(exp_timestamp)
        now = datetime.utcnow()
        delta = exp_time - now
        
        # Should be between 29-31 minutes (allowing 1 minute tolerance)
        assert timedelta(minutes=29) <= delta <= timedelta(minutes=31)
    
    def test_create_access_token_with_custom_expiry(self):
        """Verify access token respects custom expiry"""
        data = {"sub": "testuser@example.com"}
        custom_delta = timedelta(minutes=60)
        token = create_access_token(data, expires_delta=custom_delta)
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload["exp"]
        exp_time = datetime.fromtimestamp(exp_timestamp)
        now = datetime.utcnow()
        delta = exp_time - now
        
        # Should be between 59-61 minutes
        assert timedelta(minutes=59) <= delta <= timedelta(minutes=61)
    
    def test_create_access_token_includes_all_data(self):
        """Verify all data is included in token payload"""
        data = {
            "sub": "testuser@example.com",
            "user_id": 123,
            "role": "customer",
        }
        token = create_access_token(data)
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser@example.com"
        assert payload["user_id"] == 123
        assert payload["role"] == "customer"


class TestRefreshTokens:
    """Test refresh token creation and validation"""
    
    def test_create_refresh_token_with_default_expiry(self):
        """Verify refresh token is created with default 7-day expiry"""
        data = {"sub": "testuser@example.com"}
        token = create_refresh_token(data)
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser@example.com"
        assert payload["type"] == "refresh"
        
        # Verify expiry is set (should be ~7 days from now)
        exp_timestamp = payload["exp"]
        exp_time = datetime.fromtimestamp(exp_timestamp)
        now = datetime.utcnow()
        delta = exp_time - now
        
        # Should be between 6.9-7.1 days (allowing tolerance)
        assert timedelta(days=6, hours=23) <= delta <= timedelta(days=7, hours=1)
    
    def test_create_refresh_token_with_custom_expiry(self):
        """Verify refresh token respects custom expiry"""
        data = {"sub": "testuser@example.com"}
        custom_delta = timedelta(days=14)
        token = create_refresh_token(data, expires_delta=custom_delta)
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload["exp"]
        exp_time = datetime.fromtimestamp(exp_timestamp)
        now = datetime.utcnow()
        delta = exp_time - now
        
        # Should be between 13.9-14.1 days
        assert timedelta(days=13, hours=23) <= delta <= timedelta(days=14, hours=1)
    
    def test_create_refresh_token_includes_type_field(self):
        """Verify refresh token has 'type' field set to 'refresh'"""
        data = {"sub": "testuser@example.com"}
        token = create_refresh_token(data)
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "type" in payload
        assert payload["type"] == "refresh"
    
    def test_create_refresh_token_includes_all_data(self):
        """Verify all data is included in refresh token payload"""
        data = {
            "sub": "testuser@example.com",
            "user_id": 123,
        }
        token = create_refresh_token(data)
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser@example.com"
        assert payload["user_id"] == 123
        assert payload["type"] == "refresh"


class TestDecodeToken:
    """Test token decoding functionality"""
    
    def test_decode_token_with_valid_access_token(self):
        """Verify valid access token is decoded correctly"""
        data = {"sub": "testuser@example.com", "user_id": 123}
        token = create_access_token(data)
        
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "testuser@example.com"
        assert payload["user_id"] == 123
        assert "exp" in payload
    
    def test_decode_token_with_valid_refresh_token(self):
        """Verify valid refresh token is decoded correctly"""
        data = {"sub": "testuser@example.com"}
        token = create_refresh_token(data)
        
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "testuser@example.com"
        assert payload["type"] == "refresh"
    
    def test_decode_token_with_expired_token(self):
        """Verify expired token raises JWTError"""
        data = {"sub": "testuser@example.com"}
        # Create token that expires immediately
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        with pytest.raises(JWTError):
            decode_token(token)
    
    def test_decode_token_with_invalid_token(self):
        """Verify invalid token raises JWTError"""
        invalid_token = "invalid.token.string"
        
        with pytest.raises(JWTError):
            decode_token(invalid_token)
    
    def test_decode_token_with_tampered_token(self):
        """Verify tampered token raises JWTError"""
        data = {"sub": "testuser@example.com"}
        token = create_access_token(data)
        
        # Tamper with the token by changing a character
        tampered_token = token[:-5] + "xxxxx"
        
        with pytest.raises(JWTError):
            decode_token(tampered_token)
    
    def test_decode_token_with_wrong_secret(self):
        """Verify token signed with different secret raises JWTError"""
        data = {"sub": "testuser@example.com"}
        # Create token with different secret
        wrong_token = jwt.encode(data, "wrong_secret_key", algorithm=ALGORITHM)
        
        with pytest.raises(JWTError):
            decode_token(wrong_token)


class TestVerifyToken:
    """Test legacy verify_token function for backward compatibility"""
    
    def test_verify_token_with_valid_token(self):
        """Verify valid token returns username"""
        username = "testuser@example.com"
        token = create_access_token(data={"sub": username})
        
        result = verify_token(token)
        assert result == username
    
    def test_verify_token_with_expired_token(self):
        """Verify expired token returns None"""
        username = "testuser@example.com"
        token = create_access_token(
            data={"sub": username},
            expires_delta=timedelta(seconds=-1)
        )
        
        result = verify_token(token)
        assert result is None
    
    def test_verify_token_with_invalid_token(self):
        """Verify invalid token returns None"""
        invalid_token = "invalid.token.string"
        
        result = verify_token(invalid_token)
        assert result is None
    
    def test_verify_token_with_missing_sub(self):
        """Verify token without 'sub' field returns None"""
        token = create_access_token(data={"user_id": 123})
        
        result = verify_token(token)
        assert result is None


class TestConstants:
    """Test configuration constants"""
    
    def test_access_token_expire_minutes_is_positive(self):
        """Verify access token expiry is positive"""
        assert ACCESS_TOKEN_EXPIRE_MINUTES > 0
    
    def test_refresh_token_expire_days_is_positive(self):
        """Verify refresh token expiry is positive"""
        assert REFRESH_TOKEN_EXPIRE_DAYS > 0
    
    def test_refresh_token_longer_than_access_token(self):
        """Verify refresh token has longer expiry than access token"""
        refresh_minutes = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60
        assert refresh_minutes > ACCESS_TOKEN_EXPIRE_MINUTES
    
    def test_secret_key_is_set(self):
        """Verify SECRET_KEY is configured"""
        assert SECRET_KEY is not None
        assert len(SECRET_KEY) > 0
    
    def test_algorithm_is_hs256(self):
        """Verify algorithm is HS256"""
        assert ALGORITHM == "HS256"
