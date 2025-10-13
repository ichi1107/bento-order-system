# 🍱 弁当注文管理システム

モダンなWeb技術を使用した、お客様と店舗向けの弁当注文管理システムです。

## 📋 目次

- [概要](#概要)
- [技術スタック](#技術スタック)
- [データベーススキーマ](#データベーススキーマ)
- [プロジェクト構成](#プロジェクト構成)
- [セットアップ](#セットアップ)
- [開発ワークフロー](#開発ワークフロー)
- [API仕様](#api仕様)
- [デプロイ](#デプロイ)
- [チーム開発ガイド](#チーム開発ガイド)

## 概要

### システムの特徴

- **ユーザーロールベースアクセス制御（RBAC）**
  - お客様: メニュー閲覧・注文作成・履歴確認
  - 店舗スタッフ: 注文管理・メニュー管理・売上分析

- **型安全性を重視した設計**
  - `schemas.py`を唯一の信頼できる情報源（Single Source of Truth）
  - Pydanticスキーマから自動生成されるTypeScript型定義

- **チーム開発に最適化**
  - 画面・機能ごとに分割されたCSS/JavaScriptファイル
  - Gitコンフリクトを最小限に抑えるファイル構成

## 技術スタック

### バックエンド
- **FastAPI** - 高速なPython Webフレームワーク
- **SQLAlchemy** - ORM（Object-Relational Mapping）
- **PostgreSQL** - リレーショナルデータベース
- **JWT** - JSON Web Token認証
- **Pydantic** - データ検証とシリアライゼーション

### フロントエンド
- **HTML5/CSS3/JavaScript (ES6+)** - モダンWeb標準
- **Jinja2** - Pythonテンプレートエンジン

### 開発・運用
- **Docker & Docker Compose** - コンテナ化
- **VS Code Dev Containers** - 一貫した開発環境
- **pip-tools** - Python依存関係管理
- **pydantic-to-typescript** - 型定義自動生成
- **Alembic** - データベースマイグレーション管理

## マルチテナント対応について

### 🏪 概要

本システムは**複数の店舗が独立してサービスを提供できるマルチテナント設計**を採用しています。

#### 主な特徴

- **完全なデータ分離**: 各店舗のメニュー・注文・売上データが物理的に分離
- **店舗独立運用**: 各店舗が独自のメニュー管理・注文管理を実施
- **お客様の自由選択**: お客様は全店舗から自由にメニューを選択・注文可能
- **セキュアなアクセス制御**: 店舗スタッフは自店舗データのみアクセス可能

### 🎯 マルチテナントアーキテクチャ

#### データ分離モデル

```
┌─────────────────────────────────────────────┐
│         Bento Order System                  │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ 店舗A    │  │ 店舗B    │  │ 店舗C    │ │
│  ├──────────┤  ├──────────┤  ├──────────┤ │
│  │メニュー  │  │メニュー  │  │メニュー  │ │
│  │注文      │  │注文      │  │注文      │ │
│  │売上      │  │売上      │  │売上      │ │
│  │スタッフ  │  │スタッフ  │  │スタッフ  │ │
│  └──────────┘  └──────────┘  └──────────┘ │
│       ↑            ↑            ↑         │
│       └────────────┼────────────┘         │
│                    │                      │
│            ┌───────┴───────┐              │
│            │  お客様        │              │
│            │  (全店舗利用可) │              │
│            └───────────────┘              │
└─────────────────────────────────────────────┘
```

#### セキュリティモデル

**店舗スタッフのアクセス制御:**
- ✅ 自店舗のメニュー・注文・売上のみ閲覧・編集可能
- ❌ 他店舗のデータには一切アクセス不可
- 🔒 APIレベルで`store_id`による厳格なフィルタリング

**お客様のアクセス:**
- ✅ 全店舗のメニューを閲覧可能
- ✅ 複数店舗から自由に注文可能
- 🔒 自分の注文履歴のみ閲覧可能

### 📊 店舗管理機能

#### 店舗スタッフの役割（RBAC）

本システムでは、店舗スタッフに以下の3つの役割を割り当てることができます：

| 役割 | 権限 | 主な用途 |
|-----|------|---------|
| **Owner（オーナー）** | 全権限 | 店舗の最高責任者。すべての操作が可能 |
| **Manager（マネージャー）** | メニュー管理、売上レポート閲覧 | 店舗運営の管理者 |
| **Staff（スタッフ）** | 注文確認・ステータス更新のみ | 調理・配達担当者 |

#### 店舗ごとに利用できる機能

**ダッシュボード（全ロール）**
- 本日の注文件数・売上
- 注文ステータス別の件数（注文受付・準備完了）
- リアルタイム注文状況

**注文管理（全ロール）**
- 注文一覧の閲覧・フィルタリング・検索
- 注文ステータスの更新（注文受付 → 準備完了 → 受取完了）
- ステータス遷移ルール:
  - `pending`（注文受付）→ `ready`（準備完了）または `cancelled`（キャンセル）
  - `ready`（準備完了）→ `completed`（受取完了）
  - `completed`/`cancelled` → 変更不可（最終状態）

**メニュー管理（Owner / Manager）**
- メニューの作成・編集
- 価格・在庫状況の更新
- メニュー画像のアップロード

**メニュー削除（Ownerのみ）**
- 不要になったメニューの削除

**売上レポート（Owner / Manager）**
- 期間別売上集計
- 人気メニューランキング
- メニュー別売上分析

## データベーススキーマ

### ER図

詳細なER図とテーブル説明は [docs/ER_DIAGRAM.md](docs/ER_DIAGRAM.md) を参照してください。

**主要なテーブル:**

| テーブル | 説明 | マルチテナント対応 |
|---------|------|------------------|
| **stores** | 店舗情報（名前、住所、営業時間など） | テナントの中核テーブル |
| **users** | ユーザー情報（お客様と店舗スタッフ） | `store_id`で店舗スタッフを識別 |
| **menus** | メニュー情報 | `store_id`で店舗ごとに分離 ✅ |
| **orders** | 注文情報 | `store_id`で店舗ごとに分離 ✅ |
| **roles** | 職位定義（owner, manager, staff） | 全店舗共通 |
| **user_roles** | ユーザーと職位の紐付け | - |

**データ分離の実装:**

```python
# すべての店舗向けAPIで自動的にstore_idフィルタリング
@router.get("/menus")
def get_menus(current_user: User = Depends(require_role(['owner', 'manager', 'staff']))):
    # 現在のユーザーの店舗IDで自動フィルタ
    menus = db.query(Menu).filter(Menu.store_id == current_user.store_id).all()
    return menus
```

### マイグレーション管理

データベーススキーマの変更はAlembicで管理されています。

```bash
# マイグレーションを実行（最新スキーマに更新）
docker-compose run --rm web alembic upgrade head

# マイグレーションを1つ戻す
docker-compose run --rm web alembic downgrade -1

# 新しいマイグレーションを生成（models.py変更後）
docker-compose run --rm web alembic revision --autogenerate -m "description"

# マイグレーション履歴を確認
docker-compose run --rm web alembic history
```

## プロジェクト構成

```
bento-order-system/
├── 📁 .devcontainer/          # VS Code開発コンテナ設定
├── 📁 alembic/                # データベースマイグレーション
│   └── 📁 versions/          # マイグレーションスクリプト
├── 📁 docs/                   # ドキュメント
│   └── ER_DIAGRAM.md         # データベースER図
├── 📁 routers/                # FastAPI ルーター
│   ├── auth.py               # 認証エンドポイント
│   ├── customer.py           # お客様向けAPI
│   └── store.py              # 店舗向けAPI
├── 📁 static/                # 静的ファイル
│   ├── 📁 css/               # スタイルシート（画面別）
│   │   ├── common.css        # 共通スタイル
│   │   ├── auth.css          # 認証画面
│   │   ├── password_reset.css # パスワードリセット画面
│   │   ├── customer_home.css # お客様メニュー画面
│   │   ├── customer_orders.css # お客様注文履歴
│   │   └── store.css         # 店舗画面共通
│   └── 📁 js/                # JavaScript（画面別）
│       ├── 📁 types/         # TypeScript型定義
│       │   └── api.ts        # 自動生成API型
│       ├── common.js         # 共通ロジック・APIクライアント
│       ├── auth.js           # 認証画面
│       ├── password_reset_request.js  # パスワードリセットリクエスト
│       ├── password_reset_confirm.js  # パスワードリセット確認
│       ├── customer_home.js  # お客様メニュー画面
│       ├── customer_orders.js # お客様注文履歴
│       ├── store_dashboard.js # 店舗ダッシュボード
│       └── store_menus.js    # 店舗メニュー管理
├── 📁 templates/             # HTMLテンプレート
│   ├── login.html            # ログイン画面
│   ├── register.html         # ユーザー登録画面
│   ├── password_reset_request.html  # パスワードリセットリクエスト
│   ├── password_reset_confirm.html  # パスワードリセット確認
│   ├── customer_home.html    # お客様メニュー画面
│   └── ...                   # その他テンプレート
├── 📁 tests/                 # テストコード
│   ├── 📁 e2e/               # E2Eテスト（Playwright）
│   │   ├── conftest.py       # E2Eテスト用フィクスチャ
│   │   └── test_password_reset_flow.py  # パスワードリセットE2Eテスト
│   ├── conftest.py           # 共通テストフィクスチャ
│   └── test_*.py             # ユニット・統合テスト
├── 📁 scripts/               # ユーティリティスクリプト
│   ├── generate-types.sh     # 型定義生成（Linux/Mac）
│   └── generate-types.bat    # 型定義生成（Windows）
├── 📄 schemas.py             # ⭐ API契約定義（Single Source of Truth）
├── 📄 models.py              # SQLAlchemyデータベースモデル
├── 📄 database.py            # データベース接続設定
├── 📄 auth.py                # JWT認証ロジック
├── 📄 mail.py                # メール送信機能
├── 📄 dependencies.py        # FastAPI依存関数
├── 📄 main.py                # FastAPIメインアプリケーション
├── 📄 init_data.py           # 初期データ投入スクリプト
├── 📄 requirements.in        # ⭐ 手動編集する依存関係
├── 📄 requirements.txt       # ⭐ 自動生成される依存関係
├── 📄 docker-compose.yml     # Docker Compose設定
├── 📄 Dockerfile             # Dockerイメージ定義
└── 📄 README.md              # このファイル
```

## セットアップ

### 方法1: Docker Compose（推奨）

```bash
# 1. リポジトリをクローン
git clone <repository-url>
cd bento-order-system

# 2. 環境変数ファイルを作成
cp .env.example .env

# 3. Docker Composeでサービスを起動
docker-compose up --build

# 4. データベースマイグレーションを実行（初回のみ）
docker-compose run --rm web alembic upgrade head

# 5. 初期データを投入
docker-compose exec web python init_data.py

# 6. 店舗データと店舗スタッフの紐付け（初回のみ）
docker-compose exec web python setup_store_data.py

# 7. アクセスURL
# - アプリケーション: http://localhost:8000
# - MailHog (メールテスト): http://localhost:8025
# - Swagger API ドキュメント: http://localhost:8000/docs
```

**初期データの内容:**

| データ種類 | 詳細 |
|-----------|------|
| デモ店舗 | 「テスト弁当屋」が自動作成されます |
| デモユーザー | お客様用・店舗スタッフ用アカウントが作成されます |
| デモメニュー | サンプルメニューが数種類登録されます |
| 職位 | owner, manager, staffの3つの職位が作成されます |

**作成されるデモアカウント:**

| ロール | ユーザー名 | パスワード | 店舗 | 職位 |
|--------|-----------|-----------|------|------|
| お客様 | customer1 | password123 | - | - |
| 店舗オーナー | admin | admin@123 | テスト弁当屋 | owner |
| 店舗スタッフ | store1 | password123 | テスト弁当屋 | staff |
```

**起動されるサービス:**
- `web`: FastAPIアプリケーション（ポート8000）
- `db`: PostgreSQLデータベース（ポート5432）
- `mailhog`: メールテスト用SMTPサーバー（ポート1025, Web UI: 8025）

### 方法2: VS Code Dev Containers

```bash
# 1. リポジトリをクローン
git clone <repository-url>
cd bento-order-system

# 2. VS Codeで開く
code .

# 3. Command Palette (Ctrl+Shift+P) で
#    "Dev Containers: Reopen in Container" を実行

# 4. コンテナ内でアプリケーションが自動起動
```

### 方法3: ローカル環境

```bash
# 1. Python仮想環境を作成
python -m venv venv

# 2. 仮想環境をアクティベート
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. 依存関係をインストール
pip install -r requirements.txt

# 4. PostgreSQLデータベースを準備
# （事前にPostgreSQLをインストール・設定）

# 5. 環境変数を設定
cp .env.example .env
# .envファイルを編集してデータベース接続情報を設定

# 6. データベースを初期化
python init_data.py

# 7. アプリケーションを起動
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 開発ワークフロー

### マルチテナント機能の開発ガイドライン

新しいAPIエンドポイントを開発する際は、以下の**マルチテナント対応チェックリスト**を必ず確認してください：

#### 店舗向けAPIの開発チェックリスト

- [ ] **store_id存在確認を実装**
  ```python
  if not current_user.store_id:
      raise HTTPException(status_code=400, detail="User is not associated with any store")
  ```

- [ ] **すべてのDBクエリにstore_idフィルタを追加**
  ```python
  # ❌ 悪い例（他店舗データが漏洩）
  menus = db.query(Menu).all()
  
  # ✅ 良い例（自店舗データのみ）
  menus = db.query(Menu).filter(Menu.store_id == current_user.store_id).all()
  ```

- [ ] **データ作成時はcurrent_user.store_idを自動設定**
  ```python
  # ❌ 悪い例（クライアントがstore_idを指定可能）
  db_menu = Menu(**menu.dict())
  
  # ✅ 良い例（サーバー側で自動設定）
  db_menu = Menu(**menu.dict(), store_id=current_user.store_id)
  ```

- [ ] **存在しないリソースは404を返す**
  ```python
  # 他店舗のデータの場合も404で統一（403ではなく）
  menu = db.query(Menu).filter(
      Menu.id == menu_id,
      Menu.store_id == current_user.store_id
  ).first()
  if not menu:
      raise HTTPException(status_code=404, detail="Menu not found")
  ```

- [ ] **データ分離のテストを追加**
  ```python
  # tests/test_my_feature.py
  def test_store_a_cannot_access_store_b_data(client, auth_headers_store_a):
      # 店舗Aが店舗Bのデータにアクセスできないことを検証
      response = client.get("/api/store/resource/999", headers=auth_headers_store_a)
      assert response.status_code == 404
  ```

#### 推奨される開発パターン

**パターン1: リソース一覧取得**
```python
@router.get("/resources")
def get_resources(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager', 'staff']))
):
    """リソース一覧取得（自店舗のみ）"""
    if not current_user.store_id:
        raise HTTPException(status_code=400, detail="User is not associated with any store")
    
    resources = db.query(Resource).filter(
        Resource.store_id == current_user.store_id
    ).all()
    return resources
```

**パターン2: リソース作成**
```python
@router.post("/resources")
def create_resource(
    resource: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager']))
):
    """リソース作成（自動的に自店舗に紐付け）"""
    if not current_user.store_id:
        raise HTTPException(status_code=400, detail="User is not associated with any store")
    
    db_resource = Resource(
        **resource.dict(),
        store_id=current_user.store_id  # サーバー側で自動設定
    )
    db.add(db_resource)
    db.commit()
    return db_resource
```

**パターン3: リソース更新・削除**
```python
@router.put("/resources/{resource_id}")
def update_resource(
    resource_id: int,
    resource: ResourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager']))
):
    """リソース更新（自店舗データのみ）"""
    if not current_user.store_id:
        raise HTTPException(status_code=400, detail="User is not associated with any store")
    
    db_resource = db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.store_id == current_user.store_id  # 必須フィルタ
    ).first()
    
    if not db_resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    for key, value in resource.dict(exclude_unset=True).items():
        setattr(db_resource, key, value)
    
    db.commit()
    return db_resource
```

### API仕様変更時の手順

1. **schemas.pyを編集**
   ```python
   # schemas.pyに新しいPydanticモデルを追加
   class NewFeatureRequest(BaseModel):
       name: str
       description: Optional[str] = None
   ```

2. **TypeScript型定義を再生成**
   ```bash
   # Windows
   scripts\generate-types.bat
   
   # Linux/Mac
   bash scripts/generate-types.sh
   ```

3. **フロントエンドで型定義を使用**
   ```javascript
   // static/js/some-feature.js
   // 生成された型定義を参照
   // static/js/types/api.ts の型が利用可能
   ```

### ライブラリの追加・更新方法

1. **requirements.inに依存関係を追記**
   ```
   # 新しいライブラリを追加
   requests==2.31.0
   ```

2. **requirements.txtを更新**
   ```bash
   # Docker環境の場合
   docker-compose exec web pip-compile requirements.in
   
   # ローカル環境の場合
   pip-compile requirements.in
   ```

3. **両ファイルをコミット**
   ```bash
   git add requirements.in requirements.txt
   git commit -m "feat: add requests library"
   ```

### CSS/JavaScript ファイルの構成原則

**コンフリクト回避のため、以下の原則に従ってください:**

- **1機能1ファイル**: 画面や機能ごとにファイルを分割
- **共通機能の分離**: `common.css`、`common.js`に共通部分を記述
- **命名規則**: `{画面名}_{機能}.{拡張子}` (例: `customer_home.css`)

## API仕様

### 自動生成ドキュメント

アプリケーション起動後、以下のURLでAPI仕様を確認できます：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要エンドポイント

#### 認証
```
POST /api/auth/register                # ユーザー登録
POST /api/auth/login                   # ログイン
POST /api/auth/logout                  # ログアウト
POST /api/auth/password-reset-request  # パスワードリセットリクエスト
POST /api/auth/password-reset-confirm  # パスワードリセット確認
```

#### パスワードリセット機能

**お客様向けの使い方:**

1. ログイン画面で「パスワードをお忘れですか?」リンクをクリック
2. 登録済みのメールアドレスを入力して送信
3. メールに記載されたリンクをクリック
4. 新しいパスワードを入力（6文字以上）
5. パスワードがリセットされ、新しいパスワードでログイン可能

**開発者向け情報:**

- **メールテスト**: 開発環境では[MailHog](https://github.com/mailhog/MailHog)を使用
  - Web UI: http://localhost:8025
  - 送信されたメールをブラウザで確認可能
  - SMTP: localhost:1025

- **セキュリティ機能**:
  - トークンの有効期限: 1時間
  - レート制限: 同一メールアドレスへのリクエストは5分間に1回まで
  - トークンの使い捨て: 一度使用したトークンは再利用不可

- **E2Eテスト実行**:
  ```bash
  # Docker環境でE2Eテストを実行
  docker-compose exec web pytest tests/e2e/ -v
  
  # カバレッジ付きで実行
  docker-compose exec web pytest tests/e2e/ --cov=. --cov-report=html
  ```

#### お客様向け
```
GET  /api/customer/menus           # メニュー一覧取得
GET  /api/customer/menus/{id}      # メニュー詳細取得
POST /api/customer/orders          # 注文作成
GET  /api/customer/orders          # 注文履歴取得
PUT  /api/customer/orders/{id}/cancel # 注文キャンセル
```

#### 店舗向け
```
GET  /api/store/dashboard          # ダッシュボード情報
GET  /api/store/orders             # 全注文一覧（フィルタリング対応）
PUT  /api/store/orders/{id}/status # 注文ステータス更新（遷移バリデーション付き）
POST /api/store/menus              # メニュー作成
PUT  /api/store/menus/{id}         # メニュー更新
DELETE /api/store/menus/{id}       # メニュー削除
GET  /api/store/reports/sales      # 売上レポート
```

**注文ステータス仕様 (4ステータスシステム):**

| ステータス | 値 | 説明 | 次の状態 |
|-----------|-----|------|----------|
| 注文受付 | `pending` | 新規注文を受付けた状態 | `ready`, `cancelled` |
| 準備完了 | `ready` | 商品の準備が完了し受取可能 | `completed` |
| 受取完了 | `completed` | お客様が商品を受け取った（最終状態） | - |
| キャンセル | `cancelled` | 注文がキャンセルされた（最終状態） | - |

**ステータス遷移ルール:**
- ✅ `pending` → `ready`: 商品準備完了時
- ✅ `pending` → `cancelled`: 注文キャンセル時
- ✅ `ready` → `completed`: お客様受取時
- ❌ `completed` → 他の状態: 変更不可
- ❌ `cancelled` → 他の状態: 変更不可

**店舗エンドポイントの権限マトリックス:**

| エンドポイント | owner | manager | staff | 説明 |
|---------------|:-----:|:-------:|:-----:|------|
| **ダッシュボード** |
| GET /dashboard | ✅ | ✅ | ✅ | 本日の注文状況サマリー |
| **注文管理** |
| GET /orders | ✅ | ✅ | ✅ | 全注文一覧取得（フィルタ・検索対応） |
| PUT /orders/{id}/status | ✅ | ✅ | ✅ | 注文ステータス更新（遷移検証付き） |
| **メニュー管理** |
| GET /menus | ✅ | ✅ | ✅ | メニュー一覧取得 |
| POST /menus | ✅ | ✅ | ❌ | メニュー作成 |
| PUT /menus/{id} | ✅ | ✅ | ❌ | メニュー更新 |
| DELETE /menus/{id} | ✅ | ❌ | ❌ | メニュー削除 (オーナーのみ) |
| **レポート** |
| GET /reports/sales | ✅ | ✅ | ❌ | 売上レポート取得 |

> **注意**: 店舗スタッフユーザーには `owner`, `manager`, `staff` のいずれかのロールが割り当てられます。各エンドポイントは割り当てられたロールに基づいてアクセス制御されます。
DELETE /api/store/menus/{id}       # メニュー削除
GET  /api/store/reports/sales      # 売上レポート
```

### 店舗向けAPI権限マトリックス

店舗スタッフには `owner`（オーナー）、`manager`（マネージャー）、`staff`（スタッフ）の3つの役割があり、各エンドポイントで必要な権限が異なります。

| エンドポイント | owner | manager | staff | 説明 |
|---------------|:-----:|:-------:|:-----:|------|
| **ダッシュボード** |
| GET /dashboard | ✅ | ✅ | ✅ | 本日の注文状況を確認 |
| **注文管理** |
| GET /orders | ✅ | ✅ | ✅ | 全注文一覧を閲覧（フィルタ・ソート対応） |
| PUT /orders/{id}/status | ✅ | ✅ | ✅ | 注文ステータスを更新（遷移検証付き） |
| **メニュー管理** |
| GET /menus | ✅ | ✅ | ✅ | メニュー一覧を閲覧 |
| POST /menus | ✅ | ✅ | ❌ | メニューを作成 |
| PUT /menus/{id} | ✅ | ✅ | ❌ | メニューを更新 |
| DELETE /menus/{id} | ✅ | ❌ | ❌ | メニューを削除（オーナーのみ） |
| **レポート** |
| GET /reports/sales | ✅ | ✅ | ❌ | 売上レポートを閲覧 |

**権限による制限:**
- **スタッフ**: 注文確認・ステータス更新（4ステータス）、メニュー閲覧のみ可能
- **マネージャー**: スタッフ権限 + メニュー作成・更新、売上レポート閲覧
- **オーナー**: 全権限（メニュー削除を含む）

GET  /api/store/reports/sales      # 売上レポート
```

## デプロイ

### 本番環境の準備

1. **環境変数の設定**
   ```bash
   # 本番用の安全な値に変更
   DATABASE_URL=postgresql://user:password@host:5432/bento_db
   SECRET_KEY=本番用の強力なシークレットキー
   ```

2. **データベースマイグレーション**
   ```bash
   python init_data.py
   ```

3. **静的ファイルの配信**
   ```bash
   # Nginxなどのリバースプロキシで静的ファイルを配信
   ```

### Docker本番デプロイ

```bash
# 本番用イメージをビルド
docker build -t bento-order-system:latest .

# 本番環境で起動
docker run -d \
  --name bento-system \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e SECRET_KEY="..." \
  bento-order-system:latest
```

## チーム開発ガイド

### Gitブランチ戦略（GitHub Flow）

```bash
# 新機能開発
git checkout -b feature/add-menu-management
git add .
git commit -m "feat: add menu management functionality"
git push origin feature/add-menu-management

# Pull Request作成 → レビュー → main にマージ
```

### コミットメッセージ規約（Conventional Commits）

```
feat: 新機能追加
fix: バグ修正
docs: ドキュメント更新
style: コードフォーマット（機能変更なし）
refactor: リファクタリング
test: テスト追加・修正
chore: ビルド・補助ツール変更
```

### コンフリクト回避ルール

1. **schemas.py編集時の注意**
   - 作業前に `git pull origin main` を実行
   - 小さな変更単位でPull Requestを作成
   - 変更前にSlack等でチームに連絡

2. **CSS/JavaScriptファイル**
   - 新機能は新ファイルを作成
   - 既存ファイルの大幅変更は事前相談

### コードレビューガイドライン

- **必須チェック項目**
  - [ ] schemas.py変更時は型生成スクリプトが実行されているか
  - [ ] 新しい依存関係はrequirements.inに追加されているか
  - [ ] APIエンドポイントにはSwagger説明が含まれているか
  - [ ] エラーハンドリングが適切に実装されているか

## マルチテナント機能の使い方

### 店舗の作成

#### 方法1: init_data.pyスクリプトを使用（開発環境）

```bash
# デモ店舗「テスト弁当屋」が自動的に作成されます
docker-compose exec web python init_data.py
docker-compose exec web python setup_store_data.py
```

#### 方法2: Pythonスクリプトで手動作成

```python
# create_store.py
from database import SessionLocal
from models import Store
from datetime import time

db = SessionLocal()

store = Store(
    name="新しい弁当屋",
    email="new@bento.com",
    phone="03-9876-5432",
    address="東京都新宿区新規1-2-3",
    opening_time=time(10, 0),
    closing_time=time(22, 0),
    description="新しくオープンした弁当屋です。",
    is_active=True
)
db.add(store)
db.commit()
print(f"✅ 店舗作成完了: {store.name} (ID: {store.id})")
```

実行:
```bash
docker-compose exec web python create_store.py
```

#### 方法3: API経由で作成（本番環境）

```bash
# 管理者用エンドポイント（実装が必要な場合）
curl -X POST "http://localhost:8000/api/admin/stores" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新しい弁当屋",
    "email": "new@bento.com",
    "phone": "03-9876-5432",
    "address": "東京都新宿区新規1-2-3",
    "opening_time": "10:00:00",
    "closing_time": "22:00:00",
    "description": "新しくオープンした弁当屋です。"
  }'
```

### 店舗スタッフの追加

#### 新規ユーザーを店舗スタッフとして登録

```python
# add_store_staff.py
from database import SessionLocal
from models import User, Role, UserRole
from auth import get_password_hash

db = SessionLocal()

# ユーザーを作成
user = User(
    username="new_manager",
    email="manager@newstore.com",
    hashed_password=get_password_hash("secure_password"),
    role="store",
    full_name="田中 太郎",
    store_id=1,  # 店舗ID（先に店舗を作成しておく）
    is_active=True
)
db.add(user)
db.commit()
db.refresh(user)

# マネージャーロールを割り当て
manager_role = db.query(Role).filter(Role.name == "manager").first()
user_role = UserRole(user_id=user.id, role_id=manager_role.id)
db.add(user_role)
db.commit()

print(f"✅ スタッフ追加完了: {user.username} (店舗ID: {user.store_id}, 職位: manager)")
```

#### 既存ユーザーを店舗に紐付け

```python
# assign_user_to_store.py
from database import SessionLocal
from models import User

db = SessionLocal()

# 既存ユーザーを取得
user = db.query(User).filter(User.username == "existing_user").first()

# 店舗を割り当て
user.store_id = 1  # 店舗ID
user.role = "store"  # ロールを変更
db.commit()

print(f"✅ ユーザー {user.username} を店舗ID {user.store_id} に紐付けました")
```

### 店舗情報の更新

#### 店舗プロフィールAPIを使用

```bash
# 店舗情報を更新（オーナーまたはマネージャー権限が必要）
curl -X PUT "http://localhost:8000/api/store/profile" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "リニューアルした弁当屋",
    "phone": "03-1111-2222",
    "address": "東京都渋谷区新住所1-2-3",
    "opening_time": "09:00:00",
    "closing_time": "21:00:00",
    "description": "リニューアルオープンしました！",
    "image_url": "https://example.com/new-image.jpg"
  }'
```

### 店舗の確認

#### 登録されている店舗の一覧を確認

```python
# list_stores.py
from database import SessionLocal
from models import Store

db = SessionLocal()
stores = db.query(Store).all()

print(f"登録店舗数: {len(stores)}\n")
for store in stores:
    print(f"店舗ID: {store.id}")
    print(f"店舗名: {store.name}")
    print(f"住所: {store.address}")
    print(f"電話: {store.phone_number}")
    print(f"営業時間: {store.opening_time} - {store.closing_time}")
    print(f"状態: {'営業中' if store.is_active else '休業中'}")
    print("-" * 50)
```

実行:
```bash
docker-compose exec web python list_stores.py
```

### マルチテナント動作の確認

#### 店舗ごとのデータ分離を確認

```bash
# 店舗Aのスタッフでログイン
TOKEN_A=$(curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=store_a_staff&password=password" \
  | jq -r '.access_token')

# 店舗Aのメニュー一覧を取得（店舗Aのメニューのみ表示される）
curl -X GET "http://localhost:8000/api/store/menus" \
  -H "Authorization: Bearer $TOKEN_A"

# 店舗Bのスタッフでログイン
TOKEN_B=$(curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=store_b_staff&password=password" \
  | jq -r '.access_token')

# 店舗Bのメニュー一覧を取得（店舗Bのメニューのみ表示される）
curl -X GET "http://localhost:8000/api/store/menus" \
  -H "Authorization: Bearer $TOKEN_B"

# 結果: 店舗A、Bそれぞれが自店舗のデータのみを閲覧できることを確認
```

### トラブルシューティング

**Q: 店舗スタッフがログインできるがAPIがエラーを返す**

```bash
# ユーザーのstore_idが正しく設定されているか確認
docker-compose exec db psql -U postgres -d bento_db -c \
  "SELECT id, username, role, store_id FROM users WHERE username='your_username';"

# store_idがNULLの場合は設定
docker-compose exec web python -c "
from database import SessionLocal
from models import User
db = SessionLocal()
user = db.query(User).filter(User.username == 'your_username').first()
user.store_id = 1  # 店舗ID
db.commit()
print(f'✅ {user.username} を店舗ID {user.store_id} に紐付けました')
"
```

**Q: 店舗スタッフに職位（role）が割り当てられていない**

```bash
# ユーザーの職位を確認
docker-compose exec web python -c "
from database import SessionLocal
from models import User, Role, UserRole
db = SessionLocal()
user = db.query(User).filter(User.username == 'your_username').first()
roles = db.query(Role).join(UserRole).filter(UserRole.user_id == user.id).all()
print(f'ユーザー: {user.username}')
print(f'職位: {[r.name for r in roles]}')
"

# 職位を割り当て
docker-compose exec web python -c "
from database import SessionLocal
from models import User, Role, UserRole
db = SessionLocal()
user = db.query(User).filter(User.username == 'your_username').first()
role = db.query(Role).filter(Role.name == 'staff').first()  # または 'manager', 'owner'
user_role = UserRole(user_id=user.id, role_id=role.id)
db.add(user_role)
db.commit()
print(f'✅ {user.username} に {role.name} を割り当てました')
"
```

**Q: 他店舗のデータにアクセスできてしまう**

セキュリティテストを実行して問題箇所を特定:
```bash
docker-compose exec web pytest tests/test_store_isolation.py -v

# 失敗したテストがある場合、該当するエンドポイントのコードを確認
# store_idフィルタが正しく実装されているか確認
```

## デモアカウント

以下のアカウントでログインしてシステムを体験できます：

| ロール | ユーザー名 | パスワード | 用途 |
|--------|------------|------------|------|
| お客様 | customer1 | password123 | 注文体験 |
| 店舗スタッフ | admin | admin@123 | 管理機能体験 |
| 店舗スタッフ | store1 | password123 | 通常スタッフ体験 |

## トラブルシューティング

### よくある問題

**Q: データベース接続エラーが発生する**
```bash
# PostgreSQLサービスの状態確認
docker-compose ps db

# ログの確認
docker-compose logs db
```

**Q: 型定義生成スクリプトが動かない**
```bash
# 仮想環境がアクティベートされているか確認
which python

# pydantic-to-typescriptがインストールされているか確認
pip list | grep pydantic-to-typescript
```

**Q: フロントエンドでAPIエラーが発生する**
```javascript
// ブラウザの開発者ツールでネットワークタブを確認
// 認証トークンが正しく送信されているか確認
console.log(localStorage.getItem('authToken'));
```

## テスト

### テスト環境のセットアップ

```bash
# 依存関係の更新（pytestを含む）
pip-compile requirements.in
pip install -r requirements.txt
```

### テストの実行

```bash
# 全テストを実行
pytest

# 詳細な出力で実行
pytest -v

# 特定のテストファイルのみ実行
pytest tests/test_customer_orders.py

# 特定のテストクラスのみ実行
pytest tests/test_customer_orders.py::TestGetCustomerOrders

# 特定のテストケースのみ実行
pytest tests/test_customer_orders.py::TestGetCustomerOrders::test_get_own_orders_success

# カバレッジレポート付きで実行（オプション）
pytest --cov=. --cov-report=html
```

### テストの種類

#### ユニットテスト
個々の関数やクラスの動作を検証:
- スキーマのバリデーション
- ビジネスロジックの正確性

#### インテグレーションテスト
APIエンドポイントの動作を検証:
- `tests/test_customer_orders.py` - 顧客注文履歴API
- `tests/test_store_profile.py` - 店舗プロフィール管理API
- `tests/test_password_reset.py` - パスワードリセットAPI

**店舗プロフィールAPI統合テスト:**
```bash
# 店舗プロフィールAPIのすべてのテストを実行
docker-compose exec web pytest tests/test_store_profile.py -v

# 特定のテストクラスを実行
docker-compose exec web pytest tests/test_store_profile.py::TestRBACEnforcement -v
docker-compose exec web pytest tests/test_store_profile.py::TestTenantIsolation -v

# カバレッジレポート付きで実行
docker-compose exec web pytest tests/test_store_profile.py --cov=routers.store --cov-report=term-missing
```

テスト結果の詳細は [店舗プロフィールAPIテストレポート](docs/STORE_PROFILE_API_TEST_REPORT.md) を参照してください。

#### E2Eテスト（End-to-End）
ブラウザを使った実際のユーザー操作を検証:
- `tests/e2e/test_password_reset_flow.py` - パスワードリセット完全フロー
- Playwrightを使用したヘッドレスブラウザテスト
- MailHog APIと連携したメール検証

**E2Eテストの実行:**
```bash
# Docker環境でE2Eテストのみ実行
docker-compose exec web pytest tests/e2e/ -v

# 特定のE2Eテストクラスを実行
docker-compose exec web pytest tests/e2e/test_password_reset_flow.py::TestPasswordResetFlow -v

# すべてのテスト（ユニット + 統合 + E2E）を実行
docker-compose exec web pytest -v
```

#### セキュリティテスト
認証・認可の動作を検証:
- 未認証ユーザーのアクセス拒否
- 他ユーザーのデータへのアクセス防止
- 無効なトークンの拒否
- レート制限の動作確認

#### マルチテナントセキュリティテスト
店舗間のデータ分離を検証:
- `tests/test_store_isolation.py` - マルチテナントデータ分離の包括的テスト
- 店舗Aが店舗Bのデータにアクセスできないことを検証
- 注文、メニュー、売上レポートのデータ分離
- エラーメッセージからの情報漏洩防止

**マルチテナントセキュリティテストの実行:**
```bash
# Docker環境でマルチテナントセキュリティテストを実行
docker-compose exec web pytest tests/test_store_isolation.py -v

# 詳細な出力で実行
docker-compose exec web pytest tests/test_store_isolation.py -v --tb=short

# カバレッジレポート付きで実行
docker-compose exec web pytest tests/test_store_isolation.py --cov=routers.store --cov-report=term-missing
```

**テスト結果レポート:**
- マルチテナント脆弱性発見レポート: [docs/SECURITY_TEST_REPORT_MULTI_TENANT.md](docs/SECURITY_TEST_REPORT_MULTI_TENANT.md)
- セキュリティ修正完了レポート: [docs/SECURITY_FIX_COMPLETE_REPORT.md](docs/SECURITY_FIX_COMPLETE_REPORT.md)

**テスト内容:**
- ✅ 注文データの分離（4テスト）
- ✅ メニューデータの分離（4テスト）
- ✅ ダッシュボードの分離（1テスト）
- ✅ 売上レポートの分離（1テスト）
- ✅ クロスストアアクセス拒否（3テスト）

合計13テストですべてのマルチテナントデータ分離を検証しています。

### Dockerコンテナ内でのテスト実行

```bash
# コンテナ内でテストを実行
docker-compose exec web pytest

# または、新しいコンテナでテストを実行
docker-compose run --rm web pytest
```

### CI/CDでの実行

GitHubActionsなどのCI環境では、以下のコマンドを使用:

```yaml
# .github/workflows/test.yml の例
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest -v --tb=short
```

## ライセンス

MIT License

## 貢献

このプロジェクトへの貢献を歓迎します！

1. Forkしてください
2. 機能ブランチを作成してください (`git switch -c feature/amazing-feature`)
3. 変更をコミットしてください (`git commit -m 'feat: add amazing feature'`)
4. ブランチにプッシュしてください (`git push origin feature/amazing-feature`)
5. Pull Requestを作成してください

---

📧 **サポート**: 質問がある場合は、GitHubのIssueを作成してください。

🚀 **開発チーム**: このシステムは4-5人のチーム開発を想定して設計されています。