# 店舗プロフィールAPI仕様書

## 概要

店舗オーナーが自店舗の基本情報を管理するためのAPIエンドポイント群です。役割ベースのアクセス制御（RBAC）により、適切な権限を持つユーザーのみが操作できます。

## エンドポイント一覧

### 1. 店舗プロフィール取得

**GET** `/api/store/profile`

ログイン中のユーザーが所属する店舗の情報を取得します。

#### 必要な権限
- **store** (owner, manager, staff)

#### レスポンス
```json
{
  "id": 1,
  "name": "本店 - 弁当屋さん",
  "address": "東京都渋谷区1-2-3",
  "phone_number": "03-1234-5678",
  "email": "honten@bento.com",
  "opening_time": "09:00:00",
  "closing_time": "20:00:00",
  "description": "美味しい弁当をお届けする本店です。",
  "image_url": "https://via.placeholder.com/600x400?text=Main+Store",
  "is_active": true,
  "created_at": "2025-10-11T06:40:02.793811Z",
  "updated_at": "2025-10-11T06:40:02.793811Z"
}
```

#### エラー
- **400 Bad Request**: ユーザーが店舗に所属していない
- **401 Unauthorized**: 認証トークンが無効
- **403 Forbidden**: 店舗権限がない
- **404 Not Found**: 店舗が見つからない

---

### 2. 店舗プロフィール更新

**PUT** `/api/store/profile`

店舗情報を更新します（オーナー専用）。

#### 必要な権限
- **owner**

#### リクエストボディ
```json
{
  "name": "更新後の店舗名",
  "address": "東京都新宿区4-5-6",
  "phone_number": "03-9876-5432",
  "email": "updated@bento.com",
  "opening_time": "08:00:00",
  "closing_time": "21:00:00",
  "description": "新しい説明文です。",
  "is_active": true
}
```

**注意**: すべてのフィールドはオプショナルです。提供されたフィールドのみが更新されます。

#### バリデーションルール
- **name**: 1〜100文字
- **address**: 1〜255文字
- **phone_number**: 10〜20文字、日本の電話番号形式（0から始まる10桁または11桁）
- **email**: 有効なメールアドレス形式
- **opening_time**: HH:MM:SS形式
- **closing_time**: HH:MM:SS形式（opening_timeより後である必要があります）
- **description**: 最大1000文字
- **is_active**: boolean

#### レスポンス
更新後の店舗情報（GET /api/store/profileと同じ形式）

#### エラー
- **400 Bad Request**: ユーザーが店舗に所属していない、またはバリデーションエラー
- **401 Unauthorized**: 認証トークンが無効
- **403 Forbidden**: owner権限がない
- **404 Not Found**: 店舗が見つからない

---

### 3. 店舗画像アップロード

**POST** `/api/store/profile/image`

店舗画像をアップロードします（オーナー専用）。

#### 必要な権限
- **owner**

#### リクエスト
- **Content-Type**: `multipart/form-data`
- **file**: 画像ファイル（JPEG, PNG, GIF, WebP対応）

#### 対応ファイル形式
- `.jpg`, `.jpeg`
- `.png`
- `.gif`
- `.webp`

#### 処理フロー
1. ファイル形式を検証
2. 一意のファイル名を生成（UUID + 拡張子）
3. `static/uploads/stores/` に保存
4. 古い画像ファイルを削除（存在する場合）
5. データベースの`image_url`を更新

#### レスポンス
更新後の店舗情報（`image_url`が新しいパスに更新される）

```json
{
  "id": 1,
  "name": "本店 - 弁当屋さん",
  ...
  "image_url": "/static/uploads/stores/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg",
  ...
}
```

#### エラー
- **400 Bad Request**: ユーザーが店舗に所属していない、または不正なファイル形式
- **401 Unauthorized**: 認証トークンが無効
- **403 Forbidden**: owner権限がない
- **404 Not Found**: 店舗が見つからない
- **500 Internal Server Error**: ファイル保存に失敗

---

### 4. 店舗画像削除

**DELETE** `/api/store/profile/image`

店舗画像を削除します（オーナー専用）。

#### 必要な権限
- **owner**

#### 処理フロー
1. 現在の画像ファイルを削除（存在する場合）
2. データベースの`image_url`をNULLに設定

#### レスポンス
更新後の店舗情報（`image_url`がnullになる）

```json
{
  "id": 1,
  "name": "本店 - 弁当屋さん",
  ...
  "image_url": null,
  ...
}
```

#### エラー
- **400 Bad Request**: ユーザーが店舗に所属していない
- **401 Unauthorized**: 認証トークンが無効
- **403 Forbidden**: owner権限がない
- **404 Not Found**: 店舗が見つからない

---

## セキュリティ

### 1. 認証
すべてのエンドポイントはJWT認証が必要です。リクエストヘッダーに以下を含める必要があります：

```
Authorization: Bearer <access_token>
```

### 2. 役割ベースのアクセス制御（RBAC）

#### 店舗ユーザーの役割
- **owner**: すべての操作が可能（閲覧、更新、画像管理）
- **manager**: 閲覧のみ可能
- **staff**: 閲覧のみ可能

#### 店舗分離
- 各ユーザーは自分が所属する店舗の情報のみアクセス可能
- `store_id`による自動的なフィルタリング
- 他店舗の情報には一切アクセスできない

### 3. データバリデーション
- Pydanticスキーマによる厳密なバリデーション
- 不正なデータは400 Bad Requestエラーを返す
- ファイルアップロード時の拡張子チェック

---

## テスト方法

### Swagger UIでのテスト
1. ブラウザで http://localhost:8000/docs にアクセス
2. `/api/auth/login` エンドポイントでログイン
3. レスポンスから `access_token` を取得
4. 右上の「Authorize」ボタンをクリック
5. `Bearer <access_token>` 形式でトークンを入力
6. 店舗プロフィールAPIエンドポイントをテスト

### curlでのテスト例

```bash
# 1. ログイン（owner権限）
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin@123"}' \
  | jq -r '.access_token')

# 2. 店舗プロフィール取得
curl -X GET http://localhost:8000/api/store/profile \
  -H "Authorization: Bearer $TOKEN"

# 3. 店舗プロフィール更新
curl -X PUT http://localhost:8000/api/store/profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "更新後の店舗名",
    "description": "新しい説明文"
  }'

# 4. 画像アップロード
curl -X POST http://localhost:8000/api/store/profile/image \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/image.jpg"

# 5. 画像削除
curl -X DELETE http://localhost:8000/api/store/profile/image \
  -H "Authorization: Bearer $TOKEN"
```

### 権限テスト

```bash
# manager権限でログイン
MANAGER_TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"store1","password":"password123"}' \
  | jq -r '.access_token')

# 閲覧は成功
curl -X GET http://localhost:8000/api/store/profile \
  -H "Authorization: Bearer $MANAGER_TOKEN"

# 更新は失敗（403 Forbidden）
curl -X PUT http://localhost:8000/api/store/profile \
  -H "Authorization: Bearer $MANAGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "更新試行"}'
```

---

## 初期データ

### デフォルト店舗
- **ID**: 1
- **名前**: 本店 - 弁当屋さん
- **住所**: 東京都渋谷区1-2-3
- **電話**: 03-1234-5678

### デフォルトユーザー

| ユーザー名 | パスワード | 役割 | 権限 |
|-----------|-----------|------|------|
| admin | admin@123 | owner | 全ての操作可能 |
| store1 | password123 | manager | 閲覧のみ |
| store2 | password123 | staff | 閲覧のみ |

---

## エラーハンドリング

### 一般的なエラーコード
- **400 Bad Request**: リクエストデータが不正
- **401 Unauthorized**: 認証失敗またはトークンが無効
- **403 Forbidden**: 権限不足
- **404 Not Found**: リソースが見つからない
- **500 Internal Server Error**: サーバーエラー

### エラーレスポンス形式
```json
{
  "detail": "Insufficient permissions. Required roles: owner"
}
```

---

## 実装ファイル

### バックエンド
- **routers/store.py**: APIエンドポイント実装
- **models.py**: Storeモデル定義
- **schemas.py**: StoreResponse, StoreUpdateスキーマ
- **dependencies.py**: 認証・認可依存関数

### データベース
- **alembic/versions/82c749cdf529_*.py**: マイグレーションスクリプト
- **init_data.py**: 初期データ投入スクリプト

### ドキュメント
- **docs/ER_DIAGRAM.md**: データベースER図
- **docs/STORE_PROFILE_API.md**: このドキュメント
