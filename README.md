# 🍱 弁当注文管理システム

モダンなWeb技術を使用した、お客様と店舗向けの弁当注文管理システムです。

## 📋 目次

- [概要](#概要)
- [技術スタック](#技術スタック)
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

## プロジェクト構成

```
bento-order-system/
├── 📁 .devcontainer/          # VS Code開発コンテナ設定
├── 📁 routers/                # FastAPI ルーター
│   ├── auth.py               # 認証エンドポイント
│   ├── customer.py           # お客様向けAPI
│   └── store.py              # 店舗向けAPI
├── 📁 static/                # 静的ファイル
│   ├── 📁 css/               # スタイルシート（画面別）
│   │   ├── common.css        # 共通スタイル
│   │   ├── auth.css          # 認証画面
│   │   ├── customer_home.css # お客様メニュー画面
│   │   ├── customer_orders.css # お客様注文履歴
│   │   └── store.css         # 店舗画面共通
│   └── 📁 js/                # JavaScript（画面別）
│       ├── 📁 types/         # TypeScript型定義
│       │   └── api.ts        # 自動生成API型
│       ├── common.js         # 共通ロジック・APIクライアント
│       ├── auth.js           # 認証画面
│       ├── customer_home.js  # お客様メニュー画面
│       ├── customer_orders.js # お客様注文履歴
│       ├── store_dashboard.js # 店舗ダッシュボード
│       └── store_menus.js    # 店舗メニュー管理
├── 📁 templates/             # HTMLテンプレート
├── 📁 scripts/               # ユーティリティスクリプト
│   ├── generate-types.sh     # 型定義生成（Linux/Mac）
│   └── generate-types.bat    # 型定義生成（Windows）
├── 📄 schemas.py             # ⭐ API契約定義（Single Source of Truth）
├── 📄 models.py              # SQLAlchemyデータベースモデル
├── 📄 database.py            # データベース接続設定
├── 📄 auth.py                # JWT認証ロジック
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

# 4. ブラウザでアクセス
# http://localhost:8000
```

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
POST /api/auth/register  # ユーザー登録
POST /api/auth/login     # ログイン
POST /api/auth/logout    # ログアウト
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
GET  /api/store/orders             # 全注文一覧
PUT  /api/store/orders/{id}/status # 注文ステータス更新
POST /api/store/menus              # メニュー作成
PUT  /api/store/menus/{id}         # メニュー更新
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

#### インテグレーションテスト
APIエンドポイントの動作を検証するテスト:
- `tests/test_customer_orders.py` - 注文履歴API

#### セキュリティテスト
認証・認可の動作を検証するテスト:
- 未認証ユーザーのアクセス拒否
- 他ユーザーのデータへのアクセス防止
- 無効なトークンの拒否

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
2. 機能ブランチを作成してください (`git checkout -b feature/amazing-feature`)
3. 変更をコミットしてください (`git commit -m 'feat: add amazing feature'`)
4. ブランチにプッシュしてください (`git push origin feature/amazing-feature`)
5. Pull Requestを作成してください

---

📧 **サポート**: 質問がある場合は、GitHubのIssueを作成してください。

🚀 **開発チーム**: このシステムは3-5人のチーム開発を想定して設計されています。