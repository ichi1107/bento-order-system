"""
ダッシュボードAPI統合テスト

ダッシュボード機能の包括的なテストを提供:
- 認証・認可のテスト
- データ集計ロジックのテスト
- マルチテナント分離のテスト
- エッジケース(データなし、ゼロ除算など)のテスト
"""

import pytest
from datetime import datetime, date, timedelta, time as datetime_time
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models import Order, Menu, User, Store


class TestDashboardAuthentication:
    """ダッシュボードAPI認証・認可テスト"""
    
    def test_dashboard_requires_authentication(self, client: TestClient):
        """認証なしでアクセスすると401を返す"""
        response = client.get("/api/store/dashboard")
        assert response.status_code == 401
        assert "detail" in response.json()
    
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
    
    def test_dashboard_owner_can_access(self, client: TestClient, owner_user_store_a: User):
        """オーナーロールはアクセス可能"""
        # オーナーでログイン
        login_response = client.post("/api/auth/login", json={
            "username": "owner_store_a",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # ダッシュボードにアクセス
        response = client.get("/api/store/dashboard", headers=headers)
        assert response.status_code == 200
    
    def test_dashboard_manager_can_access(self, client: TestClient, manager_user_store_a: User):
        """マネージャーロールはアクセス可能"""
        login_response = client.post("/api/auth/login", json={
            "username": "manager_store_a",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/store/dashboard", headers=headers)
        assert response.status_code == 200
    
    def test_dashboard_staff_can_access(self, client: TestClient, staff_user_store_a: User):
        """スタッフロールはアクセス可能"""
        login_response = client.post("/api/auth/login", json={
            "username": "staff_store_a",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/store/dashboard", headers=headers)
        assert response.status_code == 200


class TestDashboardDataStructure:
    """ダッシュボードAPIレスポンス構造テスト"""
    
    def test_dashboard_returns_correct_structure(self, client: TestClient, owner_user_store_a: User):
        """正しいデータ構造を返す"""
        login_response = client.post("/api/auth/login", json={
            "username": "owner_store_a",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/store/dashboard", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # 必須フィールドの存在確認
        assert "total_orders" in data
        assert "pending_orders" in data
        assert "confirmed_orders" in data
        assert "preparing_orders" in data
        assert "ready_orders" in data
        assert "completed_orders" in data
        assert "cancelled_orders" in data
        assert "total_sales" in data
        assert "today_revenue" in data
        assert "average_order_value" in data
        assert "yesterday_comparison" in data
        assert "popular_menus" in data
        assert "hourly_orders" in data
        
        # データ型の確認
        assert isinstance(data["total_orders"], int)
        assert isinstance(data["total_sales"], (int, float))
        assert isinstance(data["yesterday_comparison"], dict)
        assert isinstance(data["popular_menus"], list)
        assert isinstance(data["hourly_orders"], list)
        
        # yesterday_comparisonの構造
        assert "orders_change" in data["yesterday_comparison"]
        assert "orders_change_percent" in data["yesterday_comparison"]
        assert "revenue_change" in data["yesterday_comparison"]
        assert "revenue_change_percent" in data["yesterday_comparison"]
        
        # hourly_ordersの長さは24時間分
        assert len(data["hourly_orders"]) == 24
        
        # hourly_ordersの各要素の構造
        for hour_data in data["hourly_orders"]:
            assert "hour" in hour_data
            assert "order_count" in hour_data
            assert 0 <= hour_data["hour"] <= 23


class TestDashboardEmptyData:
    """データが存在しない場合のテスト"""
    
    def test_dashboard_with_no_orders(self, client: TestClient, owner_user_store_a: User):
        """注文がない場合でもエラーにならない"""
        login_response = client.post("/api/auth/login", json={
            "username": "owner_store_a",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/store/dashboard", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_orders"] == 0
        assert data["pending_orders"] == 0
        assert data["total_sales"] == 0
        assert data["average_order_value"] == 0.0  # ゼロ除算エラーが発生しない
        assert len(data["popular_menus"]) == 0
    
    def test_dashboard_with_all_cancelled_orders(
        self, 
        client: TestClient, 
        db_session: Session,
        owner_user_store_a: User,
        store_a: Store,
        customer_user_a: User
    ):
        """全てキャンセルされた注文の場合"""
        # メニュー作成
        menu = Menu(
            name="テスト弁当",
            price=500,
            store_id=store_a.id,
            is_available=True
        )
        db_session.add(menu)
        db_session.commit()
        db_session.refresh(menu)
        
        # キャンセルされた注文を作成
        order = Order(
            user_id=customer_user_a.id,
            menu_id=menu.id,
            store_id=store_a.id,
            quantity=2,
            total_price=1000,
            status="cancelled",
            ordered_at=datetime.now()
        )
        db_session.add(order)
        db_session.commit()
        
        # ダッシュボード取得
        login_response = client.post("/api/auth/login", json={
            "username": "owner_store_a",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/store/dashboard", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_orders"] == 1
        assert data["cancelled_orders"] == 1
        assert data["total_sales"] == 0  # キャンセルは売上に含まれない
        assert data["average_order_value"] == 0.0  # ゼロ除算エラーなし


class TestDashboardDataAggregation:
    """データ集計ロジックのテスト"""
    
    def test_dashboard_aggregates_today_orders_correctly(
        self,
        client: TestClient,
        db_session: Session,
        owner_user_store_a: User,
        store_a: Store,
        customer_user_a: User
    ):
        """本日の注文を正しく集計する"""
        # メニュー作成
        menu = Menu(
            name="から揚げ弁当",
            price=600,
            store_id=store_a.id,
            is_available=True
        )
        db_session.add(menu)
        db_session.commit()
        db_session.refresh(menu)
        
        # 各ステータスの注文を作成
        today = datetime.now()
        
        orders_data = [
            {"status": "pending", "quantity": 1, "price": 600},
            {"status": "pending", "quantity": 2, "price": 1200},
            {"status": "confirmed", "quantity": 1, "price": 600},
            {"status": "preparing", "quantity": 1, "price": 600},
            {"status": "ready", "quantity": 1, "price": 600},
            {"status": "completed", "quantity": 3, "price": 1800},
            {"status": "completed", "quantity": 2, "price": 1200},
            {"status": "cancelled", "quantity": 1, "price": 600},
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
        
        # ダッシュボード取得
        login_response = client.post("/api/auth/login", json={
            "username": "owner_store_a",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/store/dashboard", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # ステータス別の注文数
        assert data["total_orders"] == 8
        assert data["pending_orders"] == 2
        assert data["confirmed_orders"] == 1
        assert data["preparing_orders"] == 1
        assert data["ready_orders"] == 1
        assert data["completed_orders"] == 2
        assert data["cancelled_orders"] == 1
        
        # 売上（キャンセル除く）
        expected_sales = 600 + 1200 + 600 + 600 + 600 + 1800 + 1200  # 6600円
        assert data["total_sales"] == expected_sales
        assert data["today_revenue"] == expected_sales
        
        # 平均注文単価（キャンセル除く7件）
        expected_avg = expected_sales / 7
        assert abs(data["average_order_value"] - expected_avg) < 0.01
    
    def test_dashboard_excludes_other_days_orders(
        self,
        client: TestClient,
        db_session: Session,
        owner_user_store_a: User,
        store_a: Store,
        customer_user_a: User
    ):
        """他の日の注文は含まれない"""
        menu = Menu(
            name="幕の内弁当",
            price=800,
            store_id=store_a.id,
            is_available=True
        )
        db_session.add(menu)
        db_session.commit()
        db_session.refresh(menu)
        
        # 今日の注文
        today_order = Order(
            user_id=customer_user_a.id,
            menu_id=menu.id,
            store_id=store_a.id,
            quantity=1,
            total_price=800,
            status="completed",
            ordered_at=datetime.now()
        )
        db_session.add(today_order)
        
        # 昨日の注文
        yesterday_order = Order(
            user_id=customer_user_a.id,
            menu_id=menu.id,
            store_id=store_a.id,
            quantity=2,
            total_price=1600,
            status="completed",
            ordered_at=datetime.now() - timedelta(days=1)
        )
        db_session.add(yesterday_order)
        
        # 1週間前の注文
        old_order = Order(
            user_id=customer_user_a.id,
            menu_id=menu.id,
            store_id=store_a.id,
            quantity=3,
            total_price=2400,
            status="completed",
            ordered_at=datetime.now() - timedelta(days=7)
        )
        db_session.add(old_order)
        
        db_session.commit()
        
        # ダッシュボード取得
        login_response = client.post("/api/auth/login", json={
            "username": "owner_store_a",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/store/dashboard", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # 今日の注文のみ
        assert data["total_orders"] == 1
        assert data["total_sales"] == 800
    
    def test_dashboard_calculates_yesterday_comparison(
        self,
        client: TestClient,
        db_session: Session,
        owner_user_store_a: User,
        store_a: Store,
        customer_user_a: User
    ):
        """前日比較を正しく計算する"""
        menu = Menu(
            name="サーモン弁当",
            price=1000,
            store_id=store_a.id,
            is_available=True
        )
        db_session.add(menu)
        db_session.commit()
        db_session.refresh(menu)
        
        # 今日: 3件、3000円
        for i in range(3):
            order = Order(
                user_id=customer_user_a.id,
                menu_id=menu.id,
                store_id=store_a.id,
                quantity=1,
                total_price=1000,
                status="completed",
                ordered_at=datetime.now()
            )
            db_session.add(order)
        
        # 昨日: 2件、2000円
        for i in range(2):
            order = Order(
                user_id=customer_user_a.id,
                menu_id=menu.id,
                store_id=store_a.id,
                quantity=1,
                total_price=1000,
                status="completed",
                ordered_at=datetime.now() - timedelta(days=1)
            )
            db_session.add(order)
        
        db_session.commit()
        
        # ダッシュボード取得
        login_response = client.post("/api/auth/login", json={
            "username": "owner_store_a",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/store/dashboard", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        comparison = data["yesterday_comparison"]
        
        # 注文数の変化: +1件 (+50%)
        assert comparison["orders_change"] == 1
        assert abs(comparison["orders_change_percent"] - 50.0) < 0.01
        
        # 売上の変化: +1000円 (+50%)
        assert comparison["revenue_change"] == 1000
        assert abs(comparison["revenue_change_percent"] - 50.0) < 0.01


class TestDashboardPopularMenus:
    """人気メニュー機能のテスト"""
    
    def test_dashboard_returns_popular_menus(
        self,
        client: TestClient,
        db_session: Session,
        owner_user_store_a: User,
        store_a: Store,
        customer_user_a: User
    ):
        """人気メニュートップ3を返す"""
        # 3つのメニューを作成
        menus = []
        for i, (name, price) in enumerate([
            ("人気1位", 500),
            ("人気2位", 600),
            ("人気3位", 700)
        ]):
            menu = Menu(
                name=name,
                price=price,
                store_id=store_a.id,
                is_available=True
            )
            db_session.add(menu)
            menus.append(menu)
        
        db_session.commit()
        for menu in menus:
            db_session.refresh(menu)
        
        # 注文を作成（人気順）
        # 人気1位: 5件
        for i in range(5):
            order = Order(
                user_id=customer_user_a.id,
                menu_id=menus[0].id,
                store_id=store_a.id,
                quantity=1,
                total_price=500,
                status="completed",
                ordered_at=datetime.now()
            )
            db_session.add(order)
        
        # 人気2位: 3件
        for i in range(3):
            order = Order(
                user_id=customer_user_a.id,
                menu_id=menus[1].id,
                store_id=store_a.id,
                quantity=1,
                total_price=600,
                status="completed",
                ordered_at=datetime.now()
            )
            db_session.add(order)
        
        # 人気3位: 1件
        order = Order(
            user_id=customer_user_a.id,
            menu_id=menus[2].id,
            store_id=store_a.id,
            quantity=1,
            total_price=700,
            status="completed",
            ordered_at=datetime.now()
        )
        db_session.add(order)
        
        db_session.commit()
        
        # ダッシュボード取得
        login_response = client.post("/api/auth/login", json={
            "username": "owner_store_a",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/store/dashboard", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        popular_menus = data["popular_menus"]
        
        # 3件返される
        assert len(popular_menus) == 3
        
        # 順序が正しい
        assert popular_menus[0]["menu_name"] == "人気1位"
        assert popular_menus[0]["order_count"] == 5
        assert popular_menus[0]["total_revenue"] == 2500
        
        assert popular_menus[1]["menu_name"] == "人気2位"
        assert popular_menus[1]["order_count"] == 3
        assert popular_menus[1]["total_revenue"] == 1800
        
        assert popular_menus[2]["menu_name"] == "人気3位"
        assert popular_menus[2]["order_count"] == 1
        assert popular_menus[2]["total_revenue"] == 700
    
    def test_dashboard_popular_menus_excludes_cancelled(
        self,
        client: TestClient,
        db_session: Session,
        owner_user_store_a: User,
        store_a: Store,
        customer_user_a: User
    ):
        """人気メニューにキャンセルされた注文は含まれない"""
        menu = Menu(
            name="テスト弁当",
            price=500,
            store_id=store_a.id,
            is_available=True
        )
        db_session.add(menu)
        db_session.commit()
        db_session.refresh(menu)
        
        # 完了した注文: 2件
        for i in range(2):
            order = Order(
                user_id=customer_user_a.id,
                menu_id=menu.id,
                store_id=store_a.id,
                quantity=1,
                total_price=500,
                status="completed",
                ordered_at=datetime.now()
            )
            db_session.add(order)
        
        # キャンセルされた注文: 3件
        for i in range(3):
            order = Order(
                user_id=customer_user_a.id,
                menu_id=menu.id,
                store_id=store_a.id,
                quantity=1,
                total_price=500,
                status="cancelled",
                ordered_at=datetime.now()
            )
            db_session.add(order)
        
        db_session.commit()
        
        # ダッシュボード取得
        login_response = client.post("/api/auth/login", json={
            "username": "owner_store_a",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/store/dashboard", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        popular_menus = data["popular_menus"]
        
        # キャンセルを除いた2件のみ
        assert len(popular_menus) == 1
        assert popular_menus[0]["order_count"] == 2
        assert popular_menus[0]["total_revenue"] == 1000


class TestDashboardHourlyOrders:
    """時間帯別注文数のテスト"""
    
    def test_dashboard_returns_24_hours_data(
        self,
        client: TestClient,
        db_session: Session,
        owner_user_store_a: User,
        store_a: Store,
        customer_user_a: User
    ):
        """0-23時の24時間分のデータを返す"""
        menu = Menu(
            name="テスト弁当",
            price=500,
            store_id=store_a.id,
            is_available=True
        )
        db_session.add(menu)
        db_session.commit()
        db_session.refresh(menu)
        
        # 9時、12時、18時に注文
        today = date.today()
        for hour in [9, 12, 18]:
            order_time = datetime.combine(today, datetime_time(hour, 30))
            order = Order(
                user_id=customer_user_a.id,
                menu_id=menu.id,
                store_id=store_a.id,
                quantity=1,
                total_price=500,
                status="completed",
                ordered_at=order_time
            )
            db_session.add(order)
        
        db_session.commit()
        
        # ダッシュボード取得
        login_response = client.post("/api/auth/login", json={
            "username": "owner_store_a",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/store/dashboard", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        hourly_orders = data["hourly_orders"]
        
        # 24時間分
        assert len(hourly_orders) == 24
        
        # 注文がある時間帯
        hour_9 = next(h for h in hourly_orders if h["hour"] == 9)
        hour_12 = next(h for h in hourly_orders if h["hour"] == 12)
        hour_18 = next(h for h in hourly_orders if h["hour"] == 18)
        
        assert hour_9["order_count"] == 1
        assert hour_12["order_count"] == 1
        assert hour_18["order_count"] == 1
        
        # 注文がない時間帯は0
        hour_0 = next(h for h in hourly_orders if h["hour"] == 0)
        assert hour_0["order_count"] == 0


class TestDashboardMultiTenantIsolation:
    """マルチテナント分離のテスト"""
    
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
        # 店舗Aのメニュー
        menu_a = Menu(
            name="店舗Aの弁当",
            price=500,
            store_id=store_a.id,
            is_available=True
        )
        db_session.add(menu_a)
        
        # 店舗Bのメニュー
        menu_b = Menu(
            name="店舗Bの弁当",
            price=600,
            store_id=store_b.id,
            is_available=True
        )
        db_session.add(menu_b)
        
        db_session.commit()
        db_session.refresh(menu_a)
        db_session.refresh(menu_b)
        
        # 店舗Aの注文: 3件
        for i in range(3):
            order = Order(
                user_id=customer_user_a.id,
                menu_id=menu_a.id,
                store_id=store_a.id,
                quantity=1,
                total_price=500,
                status="completed",
                ordered_at=datetime.now()
            )
            db_session.add(order)
        
        # 店舗Bの注文: 5件
        for i in range(5):
            order = Order(
                user_id=customer_user_a.id,
                menu_id=menu_b.id,
                store_id=store_b.id,
                quantity=1,
                total_price=600,
                status="completed",
                ordered_at=datetime.now()
            )
            db_session.add(order)
        
        db_session.commit()
        
        # 店舗Aのダッシュボード
        login_response_a = client.post("/api/auth/login", json={
            "username": "owner_store_a",
            "password": "password123"
        })
        token_a = login_response_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}
        
        response_a = client.get("/api/store/dashboard", headers=headers_a)
        assert response_a.status_code == 200
        data_a = response_a.json()
        
        # 店舗Aのデータのみ
        assert data_a["total_orders"] == 3
        assert data_a["total_sales"] == 1500
        
        # 店舗Bのダッシュボード
        login_response_b = client.post("/api/auth/login", json={
            "username": "owner_store_b",
            "password": "password123"
        })
        token_b = login_response_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}
        
        response_b = client.get("/api/store/dashboard", headers=headers_b)
        assert response_b.status_code == 200
        data_b = response_b.json()
        
        # 店舗Bのデータのみ
        assert data_b["total_orders"] == 5
        assert data_b["total_sales"] == 3000
    
    def test_dashboard_user_without_store_gets_error(
        self,
        client: TestClient,
        db_session: Session,
        roles
    ):
        """店舗に所属していないユーザーはエラー"""
        # 店舗に所属していない店舗ユーザーを作成
        user = User(
            username="orphan_store_user",
            email="orphan@test.com",
            full_name="孤立店舗ユーザー",
            hashed_password=get_password_hash("password123"),
            role="store",
            store_id=None,  # 店舗なし
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # オーナーロールを付与
        from models import UserRole
        user_role = UserRole(user_id=user.id, role_id=roles["owner"].id)
        db_session.add(user_role)
        db_session.commit()
        
        # ログイン
        login_response = client.post("/api/auth/login", json={
            "username": "orphan_store_user",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # ダッシュボードにアクセス
        response = client.get("/api/store/dashboard", headers=headers)
        assert response.status_code == 400
        assert "not associated with any store" in response.json()["detail"]


class TestWeeklySalesAPI:
    """週間売上APIのテスト"""
    
    def test_weekly_sales_requires_authentication(self, client: TestClient):
        """認証が必要"""
        response = client.get("/api/store/dashboard/weekly-sales")
        assert response.status_code == 401
    
    def test_weekly_sales_returns_7_days_data(
        self,
        client: TestClient,
        db_session: Session,
        owner_user_store_a: User,
        store_a: Store,
        customer_user_a: User
    ):
        """7日分のデータを返す"""
        menu = Menu(
            name="テスト弁当",
            price=1000,
            store_id=store_a.id,
            is_available=True
        )
        db_session.add(menu)
        db_session.commit()
        db_session.refresh(menu)
        
        # 過去7日間、毎日1件ずつ注文
        today = date.today()
        for days_ago in range(7):
            order_date = today - timedelta(days=days_ago)
            order_time = datetime.combine(order_date, datetime_time(12, 0))
            order = Order(
                user_id=customer_user_a.id,
                menu_id=menu.id,
                store_id=store_a.id,
                quantity=1,
                total_price=1000,
                status="completed",
                ordered_at=order_time
            )
            db_session.add(order)
        
        db_session.commit()
        
        # 週間売上取得
        login_response = client.post("/api/auth/login", json={
            "username": "owner_store_a",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/store/dashboard/weekly-sales", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # 7日分のデータ
        assert "labels" in data
        assert "data" in data
        assert len(data["labels"]) == 7
        assert len(data["data"]) == 7
        
        # 各日1000円
        for revenue in data["data"]:
            assert revenue == 1000
    
    def test_weekly_sales_excludes_cancelled_orders(
        self,
        client: TestClient,
        db_session: Session,
        owner_user_store_a: User,
        store_a: Store,
        customer_user_a: User
    ):
        """キャンセルされた注文は売上に含まれない"""
        menu = Menu(
            name="テスト弁当",
            price=1000,
            store_id=store_a.id,
            is_available=True
        )
        db_session.add(menu)
        db_session.commit()
        db_session.refresh(menu)
        
        today = date.today()
        order_time = datetime.combine(today, datetime_time(12, 0))
        
        # 完了した注文
        order1 = Order(
            user_id=customer_user_a.id,
            menu_id=menu.id,
            store_id=store_a.id,
            quantity=1,
            total_price=1000,
            status="completed",
            ordered_at=order_time
        )
        db_session.add(order1)
        
        # キャンセルされた注文
        order2 = Order(
            user_id=customer_user_a.id,
            menu_id=menu.id,
            store_id=store_a.id,
            quantity=1,
            total_price=1000,
            status="cancelled",
            ordered_at=order_time
        )
        db_session.add(order2)
        
        db_session.commit()
        
        # 週間売上取得
        login_response = client.post("/api/auth/login", json={
            "username": "owner_store_a",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/store/dashboard/weekly-sales", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # 今日の売上は完了分のみ
        today_index = 6  # 最後の要素が今日
        assert data["data"][today_index] == 1000
    
    def test_weekly_sales_isolates_stores(
        self,
        client: TestClient,
        db_session: Session,
        owner_user_store_a: User,
        owner_user_store_b: User,
        store_a: Store,
        store_b: Store,
        customer_user_a: User
    ):
        """店舗間でデータが分離されている"""
        # 店舗Aのメニュー
        menu_a = Menu(
            name="店舗Aの弁当",
            price=500,
            store_id=store_a.id,
            is_available=True
        )
        db_session.add(menu_a)
        
        # 店舗Bのメニュー
        menu_b = Menu(
            name="店舗Bの弁当",
            price=1000,
            store_id=store_b.id,
            is_available=True
        )
        db_session.add(menu_b)
        
        db_session.commit()
        db_session.refresh(menu_a)
        db_session.refresh(menu_b)
        
        today = date.today()
        order_time = datetime.combine(today, datetime_time(12, 0))
        
        # 店舗Aの注文: 500円
        order_a = Order(
            user_id=customer_user_a.id,
            menu_id=menu_a.id,
            store_id=store_a.id,
            quantity=1,
            total_price=500,
            status="completed",
            ordered_at=order_time
        )
        db_session.add(order_a)
        
        # 店舗Bの注文: 1000円
        order_b = Order(
            user_id=customer_user_a.id,
            menu_id=menu_b.id,
            store_id=store_b.id,
            quantity=1,
            total_price=1000,
            status="completed",
            ordered_at=order_time
        )
        db_session.add(order_b)
        
        db_session.commit()
        
        # 店舗Aの週間売上
        login_response_a = client.post("/api/auth/login", json={
            "username": "owner_store_a",
            "password": "password123"
        })
        token_a = login_response_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}
        
        response_a = client.get("/api/store/dashboard/weekly-sales", headers=headers_a)
        data_a = response_a.json()
        
        # 今日の売上は500円
        assert data_a["data"][6] == 500
        
        # 店舗Bの週間売上
        login_response_b = client.post("/api/auth/login", json={
            "username": "owner_store_b",
            "password": "password123"
        })
        token_b = login_response_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}
        
        response_b = client.get("/api/store/dashboard/weekly-sales", headers=headers_b)
        data_b = response_b.json()
        
        # 今日の売上は1000円
        assert data_b["data"][6] == 1000


# 必要なインポート追加
from auth import get_password_hash
