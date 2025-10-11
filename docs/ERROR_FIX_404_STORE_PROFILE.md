# 404エラー修正まとめ

## 問題

`/api/store/profile` エンドポイントにアクセスすると404エラーが発生

## 原因

1. **`Store`モデルが存在しなかった**
   - `models.py`に`Store`クラスが定義されていなかった

2. **`Store`スキーマが存在しなかった**
   - `schemas.py`に`StoreResponse`, `StoreUpdate`が定義されていなかった

3. **店舗プロフィールAPIエンドポイントが実装されていなかった**
   - `routers/store.py`に`/profile`エンドポイントが存在しなかった

## 修正内容

### 1. models.pyの修正

#### Storeモデルの追加:
```python
class Store(Base):
    """店舗テーブル"""
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    opening_time = Column(Time, nullable=False)
    closing_time = Column(Time, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # リレーションシップ
    users = relationship("User", back_populates="store")
```

#### Userモデルの修正:
```python
class User(Base):
    # ... 既存のフィールド ...
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # リレーションシップ
    store = relationship("Store", back_populates="users")
```

### 2. schemas.pyの修正

```python
class StoreBase(BaseModel):
    """店舗情報の基底スキーマ"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    opening_time: Optional[time] = None
    closing_time: Optional[time] = None
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class StoreCreate(StoreBase):
    """店舗作成時のリクエスト"""
    name: str = Field(..., min_length=1, max_length=255)
    opening_time: time = Field(..., description="開店時間")
    closing_time: time = Field(..., description="閉店時間")


class StoreUpdate(StoreBase):
    """店舗更新時のリクエスト"""
    pass


class StoreResponse(StoreBase):
    """店舗情報のレスポンス"""
    id: int
    name: str
    opening_time: time
    closing_time: time
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### 3. routers/store.pyの修正

#### インポート追加:
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
import os
import uuid
from models import User, Menu, Order, Store
from schemas import (
    # ... 既存のインポート ...
    StoreResponse, StoreUpdate
)
```

#### エンドポイント追加:

1. **GET /store/profile** - 店舗情報取得
2. **PUT /store/profile** - 店舗情報更新(owner権限のみ)
3. **POST /store/profile/image** - 店舗画像アップロード(owner権限のみ)
4. **DELETE /store/profile/image** - 店舗画像削除(owner権限のみ)

### 4. データベースセットアップ

#### テーブル作成:
```bash
docker-compose exec web python -c "from database import engine, Base; from models import Store; Base.metadata.create_all(bind=engine)"
```

#### テストデータ作成:
`setup_store_data.py`を作成・実行:
- テスト弁当屋を作成
- owner/manager/staffロールを作成
- store1, store2, adminユーザーに店舗とロールを割り当て

## 動作確認

### 1. ログイン
```
ユーザー名: store1
パスワード: password123
```

または

```
ユーザー名: admin
パスワード: admin@123
```

### 2. 店舗情報ページにアクセス
http://localhost:8000/store/profile

### 3. 期待される動作
- ✅ 店舗情報が表示される
- ✅ ownerユーザー(store1, admin)は編集可能
- ✅ managerユーザー(store2)は読み取り専用

## テストユーザー情報

| ユーザー名 | パスワード | ロール | 権限 |
|----------|----------|-------|------|
| admin | admin@123 | store + owner | 編集可能 |
| store1 | password123 | store + owner | 編集可能 |
| store2 | password123 | store + manager | 読み取り専用 |

## トラブルシューティング

### まだ404エラーが出る場合

1. **Dockerコンテナを再起動**:
   ```bash
   docker-compose restart web
   ```

2. **ブラウザのキャッシュをクリア**:
   Ctrl + Shift + Delete

3. **ローカルストレージをクリア**:
   F12 → Application → Local Storage → `currentUser`を削除

### ユーザーに店舗が割り当てられていない場合

```bash
docker-compose exec web python setup_store_data.py
```

### データベースをリセットしたい場合

```bash
docker-compose exec db psql -U postgres -d bento_db -c "DROP TABLE IF EXISTS stores CASCADE;"
docker-compose exec web python -c "from database import engine, Base; from models import Store; Base.metadata.create_all(bind=engine)"
docker-compose exec web python setup_store_data.py
```
