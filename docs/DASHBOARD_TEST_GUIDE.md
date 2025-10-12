# ダッシュボードAPIテスト実装ガイド

## 📚 目次

1. [概要](#概要)
2. [テストアーキテクチャ](#テストアーキテクチャ)
3. [テストクラス設計](#テストクラス設計)
4. [主要なテストパターン](#主要なテストパターン)
5. [フィクスチャの活用](#フィクスチャの活用)
6. [ベストプラクティス](#ベストプラクティス)
7. [トラブルシューティング](#トラブルシューティング)

---

## 概要

### テストファイル
- **ファイル名:** `tests/test_dashboard_api.py`
- **テスト数:** 20件
- **テストクラス:** 7クラス
- **対象API:** ダッシュボード関連エンドポイント

### テスト対象エンドポイント
1. `GET /api/store/dashboard` - ダッシュボード情報取得
2. `GET /api/store/dashboard/weekly-sales` - 週間売上データ取得

### テストフレームワーク
- **pytest:** テスト実行フレームワーク
- **FastAPI TestClient:** APIテスト用クライアント
- **SQLite:** インメモリテストデータベース
- **pytest-cov:** カバレッジ測定

---

## テストアーキテクチャ

### テスト構造

```
tests/
├── conftest.py                    # 共通フィクスチャ定義
│   ├── db_session                 # データベースセッション
│   ├── client                     # FastAPI TestClient
│   ├── store_a, store_b          # テスト用店舗
│   ├── owner_user_store_a        # 店舗Aのオーナー
│   ├── manager_user_store_a      # 店舗Aのマネージャー
│   ├── staff_user_store_a        # 店舗Aのスタッフ
│   └── customer_user_a, b        # 顧客ユーザー
│
└── test_dashboard_api.py          # ダッシュボードAPIテスト
    ├── TestDashboardAuthentication      # 認証・認可
    ├── TestDashboardDataStructure       # データ構造
    ├── TestDashboardEmptyData           # 空データ処理
    ├── TestDashboardDataAggregation     # データ集計
    ├── TestDashboardPopularMenus        # 人気メニュー
    ├── TestDashboardHourlyOrders        # 時間帯別注文
    ├── TestDashboardMultiTenantIsolation # マルチテナント分離
    └── TestWeeklySalesAPI               # 週間売上API
```

### データフロー

```
テスト実行
    ↓
フィクスチャ初期化（conftest.py）
    ↓
SQLite インメモリDB作成
    ↓
テストデータ作成（店舗、ユーザー、メニュー、注文）
    ↓
API リクエスト（TestClient）
    ↓
レスポンス検証
    ↓
データベースロールバック（次のテストのため）
```

---

## テストクラス設計

### クラス分割の原則

各テストクラスは単一の責任を持つように設計されています:

#### 1. TestDashboardAuthentication
**責任:** 認証・認可のテスト

```python
class TestDashboardAuthentication:
    """ダッシュボードAPI認証・認可テスト"""
    
    # 未認証のテスト
    def test_dashboard_requires_authentication(self, client):
        pass
    
    # ロールベースアクセス制御のテスト
    def test_dashboard_requires_store_role(self, client, customer_user_a):
        pass
    
    # 各ロールのアクセステスト
    def test_dashboard_owner_can_access(self, client, owner_user_store_a):
        pass
```

**設計ポイント:**
- 認証エラー（401）と認可エラー（403）を区別
- 各ロール（owner, manager, staff, customer）のアクセス権限を個別にテスト
- 実際のログインフローを使用

#### 2. TestDashboardDataStructure
**責任:** レスポンスのデータ構造検証

```python
class TestDashboardDataStructure:
    """ダッシュボードAPIレスポンス構造テスト"""
    
    def test_dashboard_returns_correct_structure(self, client, owner_user_store_a):
        # 必須フィールドの存在確認
        assert "total_orders" in data
        assert "yesterday_comparison" in data
        
        # データ型の確認
        assert isinstance(data["total_orders"], int)
        assert isinstance(data["yesterday_comparison"], dict)
        
        # ネストされた構造の確認
        assert "orders_change" in data["yesterday_comparison"]
```

**設計ポイント:**
- APIレスポンスの型安全性を保証
- ネストされたオブジェクトの構造を詳細に検証
- 配列の長さ（hourly_ordersは24要素）も確認

#### 3. TestDashboardEmptyData
**責任:** 空データ時のエッジケース処理

```python
class TestDashboardEmptyData:
    """データが存在しない場合のテスト"""
    
    def test_dashboard_with_no_orders(self, client, owner_user_store_a):
        # ゼロ除算エラーが発生しないことを確認
        assert data["average_order_value"] == 0.0
    
    def test_dashboard_with_all_cancelled_orders(self, ...):
        # キャンセルのみの場合も正常動作
        assert data["total_sales"] == 0
```

**設計ポイント:**
- ゼロ除算エラーの防止
- 空配列の適切な処理
- nullやundefinedを返さない

#### 4. TestDashboardDataAggregation
**責任:** データ集計ロジックの正確性

```python
class TestDashboardDataAggregation:
    """データ集計ロジックのテスト"""
    
    def test_dashboard_aggregates_today_orders_correctly(self, ...):
        # 複数ステータスの注文を作成
        # 各集計値が正確であることを確認
        assert data["total_orders"] == 8
        assert data["total_sales"] == 6600
```

**設計ポイント:**
- 実際のビジネスロジックに即したテストデータ
- 手計算で検証可能な明確な数値
- 境界値テスト（日付の境界、ステータスの境界）

#### 5. TestDashboardPopularMenus
**責任:** 人気メニュー機能の検証

```python
class TestDashboardPopularMenus:
    """人気メニュー機能のテスト"""
    
    def test_dashboard_returns_popular_menus(self, ...):
        # トップ3が正しい順序で返されることを確認
        assert popular_menus[0]["menu_name"] == "人気1位"
        assert popular_menus[0]["order_count"] == 5
```

**設計ポイント:**
- ソート順序の正確性
- キャンセル注文の除外
- トップN（現在は3）の制限

#### 6. TestDashboardMultiTenantIsolation
**責任:** マルチテナントデータ分離の検証

```python
class TestDashboardMultiTenantIsolation:
    """マルチテナント分離のテスト"""
    
    def test_dashboard_shows_only_own_store_data(self, ...):
        # 店舗Aと店舗Bに異なるデータを作成
        # 各店舗のユーザーが自店舗のデータのみ取得することを確認
```

**設計ポイント:**
- セキュリティ上最も重要なテスト
- 他店舗のデータが絶対に漏れないことを保証
- 実際の攻撃シナリオを想定

---

## 主要なテストパターン

### パターン1: 認証テスト

```python
def test_dashboard_requires_authentication(self, client: TestClient):
    """認証なしでアクセスすると401を返す"""
    response = client.get("/api/store/dashboard")
    assert response.status_code == 401
    assert "detail" in response.json()
```

**ポイント:**
- Authorization ヘッダーなしでリクエスト
- 401ステータスコードを期待
- エラーメッセージの存在確認

### パターン2: ロールベースアクセス制御テスト

```python
def test_dashboard_requires_store_role(self, client: TestClient, customer_user_a: User):
    """顧客ロールではアクセスできない(403)"""
    # 顧客ユーザーでログイン
    login_response = client.post("/api/auth/login", json={
        "username": "customer_a",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # ダッシュボードにアクセス
    response = client.get("/api/store/dashboard", headers=headers)
    assert response.status_code == 403
```

**ポイント:**
- 実際のログインフローを使用
- JWTトークンを取得
- 適切なロールでないことを確認（403）

### パターン3: データ集計テスト

```python
def test_dashboard_aggregates_today_orders_correctly(
    self,
    client: TestClient,
    db_session: Session,
    owner_user_store_a: User,
    store_a: Store,
    customer_user_a: User
):
    """本日の注文を正しく集計する"""
    # 1. メニュー作成
    menu = Menu(
        name="から揚げ弁当",
        price=600,
        store_id=store_a.id,
        is_available=True
    )
    db_session.add(menu)
    db_session.commit()
    db_session.refresh(menu)
    
    # 2. 各ステータスの注文を作成
    today = datetime.now()
    orders_data = [
        {"status": "pending", "quantity": 1, "price": 600},
        {"status": "confirmed", "quantity": 1, "price": 600},
        # ... 他のステータス
    ]
    
    for order_data in orders_data:
        order = Order(
            user_id=customer_user_a.id,
            menu_id=menu.id,
            store_id=store_a.id,
            quantity=order_data["quantity"],
            total_price=order_data["price"],
            status=order_data["status"],
            ordered_at=today
        )
        db_session.add(order)
    
    db_session.commit()
    
    # 3. APIリクエスト
    login_response = client.post("/api/auth/login", json={
        "username": "owner_store_a",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/store/dashboard", headers=headers)
    assert response.status_code == 200
    
    # 4. 集計結果の検証
    data = response.json()
    assert data["total_orders"] == 8
    assert data["pending_orders"] == 2
    assert data["total_sales"] == 6600  # キャンセル除く
```

**ポイント:**
- テストデータを明示的に作成
- 期待値を手計算で確認可能
- 各ステップを明確に分離

### パターン4: 日付フィルタリングテスト

```python
def test_dashboard_excludes_other_days_orders(
    self,
    client: TestClient,
    db_session: Session,
    owner_user_store_a: User,
    store_a: Store,
    customer_user_a: User
):
    """他の日の注文は含まれない"""
    # 今日の注文
    today_order = Order(
        ...,
        ordered_at=datetime.now()
    )
    db_session.add(today_order)
    
    # 昨日の注文
    yesterday_order = Order(
        ...,
        ordered_at=datetime.now() - timedelta(days=1)
    )
    db_session.add(yesterday_order)
    
    db_session.commit()
    
    # ダッシュボードは今日の注文のみ表示
    response = client.get("/api/store/dashboard", headers=headers)
    data = response.json()
    assert data["total_orders"] == 1  # 今日の分のみ
```

**ポイント:**
- `datetime.now()` で現在時刻を使用
- `timedelta` で相対的な日付を指定
- 境界値（00:00:00, 23:59:59）を意識

### パターン5: マルチテナント分離テスト

```python
def test_dashboard_shows_only_own_store_data(
    self,
    client: TestClient,
    db_session: Session,
    owner_user_store_a: User,
    owner_user_store_b: User,
    store_a: Store,
    store_b: Store,
    customer_user_a: User
):
    """自分の店舗のデータのみ表示される"""
    # 店舗Aのメニューと注文
    menu_a = Menu(..., store_id=store_a.id)
    order_a = Order(..., store_id=store_a.id)
    
    # 店舗Bのメニューと注文
    menu_b = Menu(..., store_id=store_b.id)
    order_b = Order(..., store_id=store_b.id)
    
    db_session.add_all([menu_a, menu_b, order_a, order_b])
    db_session.commit()
    
    # 店舗Aのオーナーでアクセス
    response_a = client.get("/api/store/dashboard", headers=headers_a)
    data_a = response_a.json()
    assert data_a["total_orders"] == 3  # 店舗Aのデータのみ
    
    # 店舗Bのオーナーでアクセス
    response_b = client.get("/api/store/dashboard", headers=headers_b)
    data_b = response_b.json()
    assert data_b["total_orders"] == 5  # 店舗Bのデータのみ
```

**ポイント:**
- 同じテスト内で複数の店舗を作成
- 各店舗のユーザーで個別にアクセス
- データが完全に分離されていることを確認

---

## フィクスチャの活用

### 基本フィクスチャ

#### db_session
```python
@pytest.fixture
def db_session():
    """SQLite インメモリDBセッション"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()
```

**用途:** 各テストで独立したDBセッションを提供

#### client
```python
@pytest.fixture
def client(db_session):
    """FastAPI TestClient"""
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)
```

**用途:** APIエンドポイントのテスト

### ユーザーフィクスチャ

#### owner_user_store_a
```python
@pytest.fixture
def owner_user_store_a(db_session, roles, store_a):
    """店舗Aのオーナーユーザー"""
    user = User(
        username="owner_store_a",
        store_id=store_a.id,
        ...
    )
    db_session.add(user)
    db_session.commit()
    
    # オーナーロールを付与
    user_role = UserRole(user_id=user.id, role_id=roles["owner"].id)
    db_session.add(user_role)
    db_session.commit()
    
    return user
```

**用途:** オーナーロールでのテスト

### 店舗フィクスチャ

#### store_a, store_b
```python
@pytest.fixture
def store_a(db_session):
    """テスト用店舗A"""
    store = Store(
        name="テスト店舗A",
        description="テスト用の店舗A",
        ...
    )
    db_session.add(store)
    db_session.commit()
    db_session.refresh(store)
    return store
```

**用途:** マルチテナントテスト

### フィクスチャ依存関係

```
db_session
    ↓
roles, store_a, store_b
    ↓
owner_user_store_a, manager_user_store_a, customer_user_a
    ↓
client (db_session をオーバーライド)
```

---

## ベストプラクティス

### 1. テストの独立性

```python
# ✅ 良い例: 各テストでデータを作成
def test_dashboard_with_data(self, client, db_session, owner_user_store_a, store_a):
    # このテスト専用のデータを作成
    menu = Menu(...)
    order = Order(...)
    db_session.add_all([menu, order])
    db_session.commit()
    
    # テスト実行

# ❌ 悪い例: グローバル変数に依存
global_menu = None

def test_create_menu(...):
    global global_menu
    global_menu = Menu(...)

def test_use_menu(...):
    # global_menu に依存（テストの順序に依存）
    assert global_menu is not None
```

### 2. 明確なテスト名

```python
# ✅ 良い例: 何をテストするか明確
def test_dashboard_requires_authentication(self, client):
    pass

def test_dashboard_excludes_cancelled_orders_from_sales(self, ...):
    pass

# ❌ 悪い例: 曖昧なテスト名
def test_dashboard_1(self, client):
    pass

def test_orders(self, ...):
    pass
```

### 3. Arrange-Act-Assert パターン

```python
def test_dashboard_aggregates_today_orders_correctly(self, ...):
    # Arrange: テストデータの準備
    menu = Menu(...)
    order1 = Order(...)
    order2 = Order(...)
    db_session.add_all([menu, order1, order2])
    db_session.commit()
    
    # Act: 実際のアクション
    response = client.get("/api/store/dashboard", headers=headers)
    
    # Assert: 結果の検証
    data = response.json()
    assert data["total_orders"] == 2
    assert data["total_sales"] == 1000
```

### 4. エッジケースの網羅

```python
# 正常系
def test_dashboard_with_orders(self, ...):
    pass

# エッジケース
def test_dashboard_with_no_orders(self, ...):
    pass

def test_dashboard_with_all_cancelled_orders(self, ...):
    pass

def test_dashboard_with_zero_revenue(self, ...):
    pass

# 境界値
def test_dashboard_at_midnight(self, ...):
    pass

def test_dashboard_with_max_orders(self, ...):
    pass
```

### 5. テストデータの明確性

```python
# ✅ 良い例: 計算しやすい数値
menu_price = 1000  # 1000円
quantity = 3
expected_total = 3000  # 一目で計算できる

# ❌ 悪い例: 複雑な数値
menu_price = 987  # 計算しにくい
quantity = 7
expected_total = ???  # 暗算できない
```

---

## トラブルシューティング

### 問題1: テストが失敗する

#### 症状
```
AssertionError: assert 401 == 200
```

#### 原因
- 認証トークンが正しく設定されていない
- フィクスチャの依存関係が壊れている

#### 解決方法
```python
# ログインレスポンスを確認
login_response = client.post("/api/auth/login", json={...})
print(login_response.json())  # デバッグ出力

# トークンを確認
assert "access_token" in login_response.json()
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
```

### 問題2: データが見つからない

#### 症状
```
sqlalchemy.orm.exc.NoResultFound
```

#### 原因
- フィクスチャで作成したデータがコミットされていない
- 別のセッションでデータを作成している

#### 解決方法
```python
# データ作成後に必ずcommit
db_session.add(menu)
db_session.commit()
db_session.refresh(menu)  # IDを取得

# または
db_session.add_all([menu, order])
db_session.commit()
```

### 問題3: 日付関連のテストが不安定

#### 症状
```
AssertionError: assert 0 == 1  # 日によって結果が変わる
```

#### 原因
- `date.today()` を使用すると、日付の境界でテストが失敗する可能性

#### 解決方法
```python
# 明示的に日付を指定
today = date.today()
today_start = datetime.combine(today, datetime.min.time())  # 00:00:00
today_end = datetime.combine(today, datetime.max.time())    # 23:59:59

# または固定日付を使用（非推奨、現在の実装では使っていない）
from unittest.mock import patch
with patch('datetime.date') as mock_date:
    mock_date.today.return_value = date(2025, 10, 12)
    # テスト実行
```

### 問題4: マルチテナントテストが失敗する

#### 症状
```
AssertionError: assert 8 == 3  # 他店舗のデータが含まれている
```

#### 原因
- `store_id` フィルタが正しく適用されていない

#### 解決方法
```python
# 注文作成時に必ず store_id を設定
order = Order(
    ...,
    store_id=store_a.id,  # 必須!
    ...
)

# メニュー作成時も同様
menu = Menu(
    ...,
    store_id=store_a.id,  # 必須!
    ...
)
```

---

## まとめ

### テスト設計の7つの原則

1. **独立性:** 各テストは独立して実行可能
2. **明確性:** テスト名と内容が一致
3. **網羅性:** 正常系、異常系、エッジケースをカバー
4. **保守性:** フィクスチャで重複を排除
5. **再現性:** 同じ条件で同じ結果
6. **速度:** インメモリDBで高速実行
7. **セキュリティ:** マルチテナント分離を厳密にテスト

### 次のステップ

1. 他のエンドポイント（注文管理、メニュー管理等）のテスト作成
2. E2Eテスト（Playwright）の追加
3. パフォーマンステストの追加
4. CI/CD統合
5. カバレッジ90%以上を目標

---

**作成日:** 2025年10月12日  
**最終更新:** 2025年10月12日  
**担当:** GitHub Copilot
