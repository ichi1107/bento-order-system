"""
API契約定義 - Single Source of Truth

このファイルは、バックエンドAPI（FastAPI）とフロントエンドの間の
すべてのデータ構造を定義する唯一の信頼できる情報源です。

編集時のルール:
1. 頻繁にgit pullを実行してコンフリクトを避ける
2. 小さな変更単位でPull Requestを作成する
3. 変更前にチームメンバーに事前連絡する
4. 変更後は必ずTypeScript型定義を再生成する
"""

from datetime import datetime, time
from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


# ===== 共通型定義 =====

class SuccessResponse(BaseModel):
    """成功時の共通レスポンス"""
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    """エラー時の共通レスポンス"""
    success: bool = False
    message: str
    detail: Optional[str] = None


# ===== 認証関連 =====

class UserCreate(BaseModel):
    """ユーザー作成時のリクエスト"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., pattern="^(customer|store)$")


class UserLogin(BaseModel):
    """ログイン時のリクエスト"""
    username: str
    password: str


class UserResponse(BaseModel):
    """ユーザー情報のレスポンス"""
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    store_id: Optional[int] = None
    created_at: datetime
    
    # 店舗情報も含める（オプショナル）
    store: Optional['StoreResponse'] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """認証トークンのレスポンス"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


# ===== パスワードリセット関連 =====

class PasswordResetRequest(BaseModel):
    """パスワードリセット要求"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """パスワードリセット確認"""
    token: str
    new_password: str = Field(..., min_length=6)


class PasswordResetResponse(BaseModel):
    """パスワードリセットレスポンス"""
    message: str


# ===== 役割（Role）関連 =====

class RoleResponse(BaseModel):
    """役割情報のレスポンス"""
    id: int
    name: Literal['owner', 'manager', 'staff']
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RoleAssignRequest(BaseModel):
    """ユーザーへ役割を割り当てるリクエスト"""
    user_id: int = Field(..., ge=1, description="割り当て対象のユーザーID")
    role_id: int = Field(..., ge=1, description="割り当てる役割ID")


class UserRoleResponse(BaseModel):
    """ユーザー役割割り当て情報のレスポンス"""
    id: int
    user_id: int
    role_id: int
    assigned_at: datetime
    # 役割の詳細情報も含める
    role: RoleResponse

    class Config:
        from_attributes = True


class UserWithRolesResponse(BaseModel):
    """ユーザー情報＋割り当てられた役割一覧"""
    id: int
    username: str
    email: str
    full_name: str
    role: str  # 'customer' or 'store'
    is_active: bool
    created_at: datetime
    # 店舗ユーザーの場合、割り当てられた役割一覧
    user_roles: List[UserRoleResponse] = []

    class Config:
        from_attributes = True


# ===== 店舗（Store）関連 =====

class StoreBase(BaseModel):
    """店舗の基本情報"""
    name: str = Field(..., min_length=1, max_length=100, description="店舗名")
    address: str = Field(..., min_length=1, max_length=255, description="住所")
    phone_number: str = Field(..., min_length=10, max_length=20, description="電話番号（ハイフンあり/なし両対応）")
    email: EmailStr = Field(..., description="店舗のメールアドレス")
    opening_time: time = Field(..., description="開店時刻")
    closing_time: time = Field(..., description="閉店時刻")
    description: Optional[str] = Field(None, max_length=1000, description="店舗説明")
    image_url: Optional[str] = Field(None, max_length=500, description="店舗画像URL")
    is_active: bool = Field(True, description="店舗の有効/無効状態")

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """電話番号の形式を検証（日本の電話番号形式）"""
        # ハイフンを除去して数字のみにする
        digits_only = re.sub(r'[^0-9]', '', v)
        
        # 10桁または11桁の数字であることを確認
        if not re.match(r'^0\d{9,10}$', digits_only):
            raise ValueError('電話番号は0から始まる10桁または11桁の数字である必要があります（例: 03-1234-5678, 090-1234-5678）')
        
        return v

    @field_validator('closing_time')
    @classmethod
    def validate_closing_time(cls, v: time, info) -> time:
        """閉店時刻が開店時刻より後であることを検証"""
        # info.data から opening_time を取得
        if 'opening_time' in info.data:
            opening_time = info.data['opening_time']
            if v <= opening_time:
                raise ValueError('閉店時刻は開店時刻より後である必要があります')
        return v


class StoreCreate(StoreBase):
    """店舗作成時のリクエスト"""
    pass


class StoreUpdate(BaseModel):
    """店舗更新時のリクエスト（すべてオプショナル）"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="店舗名")
    address: Optional[str] = Field(None, min_length=1, max_length=255, description="住所")
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20, description="電話番号")
    email: Optional[EmailStr] = Field(None, description="店舗のメールアドレス")
    opening_time: Optional[time] = Field(None, description="開店時刻")
    closing_time: Optional[time] = Field(None, description="閉店時刻")
    description: Optional[str] = Field(None, max_length=1000, description="店舗説明")
    image_url: Optional[str] = Field(None, max_length=500, description="店舗画像URL")
    is_active: Optional[bool] = Field(None, description="店舗の有効/無効状態")

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        """電話番号の形式を検証（日本の電話番号形式）"""
        if v is None:
            return v
        
        # ハイフンを除去して数字のみにする
        digits_only = re.sub(r'[^0-9]', '', v)
        
        # 10桁または11桁の数字であることを確認
        if not re.match(r'^0\d{9,10}$', digits_only):
            raise ValueError('電話番号は0から始まる10桁または11桁の数字である必要があります（例: 03-1234-5678, 090-1234-5678）')
        
        return v


class StoreResponse(StoreBase):
    """店舗情報のレスポンス"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StoreListResponse(BaseModel):
    """店舗一覧のレスポンス"""
    stores: List[StoreResponse]
    total: int


# ===== メニュー関連 =====

class MenuBase(BaseModel):
    """メニューの基本情報"""
    name: str = Field(..., min_length=1, max_length=255)
    price: int = Field(..., ge=1)
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_available: bool = True


class MenuCreate(MenuBase):
    """メニュー作成時のリクエスト"""
    store_id: int = Field(..., ge=1, description="所属店舗ID")


class MenuUpdate(BaseModel):
    """メニュー更新時のリクエスト"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    price: Optional[int] = Field(None, ge=1)
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None


class MenuResponse(MenuBase):
    """メニュー情報のレスポンス"""
    id: int
    store_id: int
    created_at: datetime
    updated_at: datetime
    
    # 店舗情報も含める（オプショナル）
    store: Optional['StoreResponse'] = None

    class Config:
        from_attributes = True


class MenuListResponse(BaseModel):
    """メニュー一覧のレスポンス"""
    menus: List[MenuResponse]
    total: int


# ===== 注文関連 =====

class OrderBase(BaseModel):
    """注文の基本情報"""
    menu_id: int = Field(..., ge=1)
    quantity: int = Field(..., ge=1, le=10)
    delivery_time: Optional[time] = None
    notes: Optional[str] = Field(None, max_length=500)


class OrderCreate(OrderBase):
    """注文作成時のリクエスト"""
    store_id: int = Field(..., ge=1, description="注文先店舗ID")


class OrderStatusUpdate(BaseModel):
    """注文ステータス更新時のリクエスト"""
    status: str = Field(..., pattern="^(pending|confirmed|preparing|ready|completed|cancelled)$")


class OrderResponse(BaseModel):
    """注文情報のレスポンス"""
    id: int
    user_id: int
    menu_id: int
    store_id: int
    quantity: int
    total_price: int
    status: str
    delivery_time: Optional[time]
    notes: Optional[str]
    ordered_at: datetime
    updated_at: datetime
    
    # メニュー情報も含める
    menu: MenuResponse
    
    # 店舗情報も含める（オプショナル）
    store: Optional['StoreResponse'] = None
    
    # お客様情報（店舗向けのみ）
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """注文一覧のレスポンス"""
    orders: List[OrderResponse]
    total: int


class OrderHistoryItem(BaseModel):
    """注文履歴の項目（メニュー情報を含む）"""
    id: int
    quantity: int
    total_price: int
    status: str
    delivery_time: Optional[time]
    notes: Optional[str]
    ordered_at: datetime
    updated_at: datetime
    
    # メニュー情報（商品名、画像URL）
    menu_id: int
    menu_name: str
    menu_image_url: Optional[str]
    menu_price: int

    class Config:
        from_attributes = True


class OrderHistoryResponse(BaseModel):
    """注文履歴のレスポンス"""
    orders: List[OrderHistoryItem]
    total: int


class OrderSummary(BaseModel):
    """注文サマリー（ダッシュボード用）"""
    total_orders: int
    pending_orders: int
    confirmed_orders: int
    preparing_orders: int
    ready_orders: int
    completed_orders: int
    cancelled_orders: int
    total_sales: int


# ===== レポート関連 =====

class DailySalesReport(BaseModel):
    """日別売上レポート"""
    date: str  # YYYY-MM-DD format
    total_orders: int
    total_sales: int
    popular_menu: Optional[str] = None


class MenuSalesReport(BaseModel):
    """メニュー別売上レポート"""
    menu_id: int
    menu_name: str
    total_quantity: int
    total_sales: int


class SalesReportResponse(BaseModel):
    """売上レポートのレスポンス"""
    period: str  # "daily", "weekly", "monthly"
    start_date: str
    end_date: str
    daily_reports: List[DailySalesReport]
    menu_reports: List[MenuSalesReport]
    total_sales: int
    total_orders: int


# ===== 検索・フィルタ関連 =====

class OrderFilter(BaseModel):
    """注文一覧フィルタ"""
    status: Optional[str] = None
    user_id: Optional[int] = None
    menu_id: Optional[int] = None
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None    # YYYY-MM-DD
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class MenuFilter(BaseModel):
    """メニュー一覧フィルタ"""
    is_available: Optional[bool] = None
    price_min: Optional[int] = Field(None, ge=0)
    price_max: Optional[int] = Field(None, ge=0)
    search: Optional[str] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


# ===== ページネーション =====

class PaginationInfo(BaseModel):
    """ページネーション情報"""
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel):
    """ページネーション付きレスポンスの基底クラス"""
    pagination: PaginationInfo


# ===== 前方参照の解決 =====
# StoreResponse の前方参照を解決
UserResponse.model_rebuild()
MenuResponse.model_rebuild()
OrderResponse.model_rebuild()
