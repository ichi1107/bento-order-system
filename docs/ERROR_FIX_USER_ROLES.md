# エラー修正まとめ

## 問題

`store_profile.js:49 Error loading store profile: TypeError: Cannot read properties of undefined (reading 'map')`

### 原因

1. **`UserResponse`スキーマに`user_roles`フィールドがなかった**
   - `/api/auth/me`エンドポイントが`user_roles`を返していなかった

2. **`common.js`の`getCurrentUser()`が間違ったエンドポイントを呼んでいた**
   - `/auth/me`ではなく`/api/auth/me`が正しい

3. **`routers/auth.py`の`/auth/me`エンドポイントで`user_roles`リレーションシップをロードしていなかった**

## 修正内容

### 1. スキーマの修正 (`schemas.py`)

新しいスキーマクラスを追加:

```python
class RoleResponse(BaseModel):
    """ロール情報のレスポンス"""
    id: int
    name: str
    
    class Config:
        from_attributes = True


class UserRoleResponse(BaseModel):
    """ユーザーロール情報のレスポンス"""
    id: int
    role: RoleResponse
    
    class Config:
        from_attributes = True
```

`UserResponse`クラスに`user_roles`フィールドを追加:

```python
class UserResponse(BaseModel):
    """ユーザー情報のレスポンス"""
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    user_roles: List[UserRoleResponse] = []  # 追加

    class Config:
        from_attributes = True
```

### 2. common.jsの修正

`getCurrentUser()`メソッドのエンドポイントを修正:

```javascript
static async getCurrentUser() {
    if (!authToken) {
        throw new Error('Not authenticated');
    }
    // ローカルストレージから取得するか、APIから取得
    if (currentUser) {
        return currentUser;
    }
    const user = await this.get('/api/auth/me');  // /auth/me → /api/auth/me
    currentUser = user;
    localStorage.setItem('currentUser', JSON.stringify(user));
    return user;
}
```

### 3. routers/auth.pyの修正

必要なインポートを追加:

```python
from sqlalchemy.orm import Session, joinedload
from models import User, PasswordResetToken, UserRole
```

`/auth/me`エンドポイントで`user_roles`をロード:

```python
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
```

## 動作確認方法

1. **ブラウザのローカルストレージをクリア**:
   - F12 → Application → Local Storage → http://localhost:8000
   - `currentUser`キーを削除

2. **再ログイン**:
   - http://localhost:8000/login にアクセス
   - 店舗スタッフとしてログイン

3. **店舗情報ページにアクセス**:
   - http://localhost:8000/store/profile にアクセス
   - エラーなく表示されることを確認

## 期待される動作

- `/api/auth/me`が以下のようなJSONを返す:
  ```json
  {
    "id": 1,
    "username": "store1",
    "email": "store1@bento.com",
    "full_name": "佐藤花子",
    "role": "store",
    "is_active": true,
    "created_at": "2025-10-11T...",
    "user_roles": [
      {
        "id": 1,
        "role": {
          "id": 1,
          "name": "owner"
        }
      }
    ]
  }
  ```

- `store_profile.js`の以下のコードが正常に動作:
  ```javascript
  const currentUser = await apiClient.getCurrentUser();
  userRoles = currentUser.user_roles.map(ur => ur.role.name);
  isOwner = userRoles.includes('owner');
  ```

## トラブルシューティング

もし引き続きエラーが発生する場合:

1. **Dockerコンテナを再起動**:
   ```bash
   docker-compose restart web
   ```

2. **ブラウザのキャッシュをクリア**:
   - Ctrl + Shift + Delete
   - キャッシュとCookieをクリア

3. **コンソールでAPIレスポンスを確認**:
   ```javascript
   // ブラウザのコンソールで実行
   const response = await fetch('/api/auth/me', {
     headers: {
       'Authorization': `Bearer ${localStorage.getItem('authToken')}`
     }
   });
   const data = await response.json();
   console.log(data);
   ```

4. **user_rolesが空の場合**:
   - データベースに`user_roles`レコードが存在するか確認
   - テストデータに`UserRole`レコードを追加する必要があるかもしれません
