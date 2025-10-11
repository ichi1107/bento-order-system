"""
データベースモデル定義

SQLAlchemyを使用したデータベーステーブルの定義
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Time, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """ユーザーテーブル"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # 'customer' or 'store'
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーションシップ
    orders = relationship("Order", back_populates="user")
    user_roles = relationship("UserRole", back_populates="user")


class Role(Base):
    """役割テーブル（店舗スタッフの職位管理）"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)  # 'owner', 'manager', 'staff'
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーションシップ
    user_roles = relationship("UserRole", back_populates="role")


class UserRole(Base):
    """ユーザー役割紐付けテーブル"""
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    # リレーションシップ
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")


class Menu(Base):
    """メニューテーブル"""
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    price = Column(Integer, nullable=False)
    description = Column(Text)
    image_url = Column(String(512))
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # リレーションシップ
    orders = relationship("Order", back_populates="menu")


class Order(Base):
    """注文テーブル"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Integer, nullable=False)
    status = Column(String(50), default="pending")  # pending, confirmed, preparing, ready, completed, cancelled
    delivery_time = Column(Time)
    notes = Column(Text)
    ordered_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # リレーションシップ
    user = relationship("User", back_populates="orders")
    menu = relationship("Menu", back_populates="orders")


class PasswordResetToken(Base):
    """パスワードリセットトークンテーブル"""
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
