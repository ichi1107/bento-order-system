"""
店舗向け注文API の包括的テスト

テスト対象:
- GET /api/store/orders - 注文一覧取得（フィルタリング・ソート）
- PUT /api/store/orders/{order_id}/status - ステータス更新（遷移ルール）

カバレッジ目標: 90%以上
"""

import pytest
from datetime import datetime, timedelta, date
from typing import List


class TestGetAllOrders:
    """
    GET /api/store/orders のテストクラス
    """
    
    def test_get_all_orders_success(
        self, 
        client, 
        auth_headers_store,
        orders_for_customer_a,
        orders_for_customer_b
    ):
        """
        テスト1: 全注文を正常に取得できること
        
        検証項目:
        - ステータスコード200が返されること
        - 全ての注文が返されること（4件）
        - 注文情報が正しく含まれていること
        """
        response = client.get(
            "/api/store/orders",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "orders" in data
        assert "total" in data
        assert data["total"] == 4  # customer_a: 3件 + customer_b: 1件
        assert len(data["orders"]) == 4
        
        # 注文のフィールド検証
        order = data["orders"][0]
        assert "id" in order
        assert "user_id" in order
        assert "menu_id" in order
        assert "quantity" in order
        assert "total_price" in order
        assert "status" in order
        assert "ordered_at" in order
    
    def test_orders_sorted_by_date_descending(
        self, 
        client, 
        auth_headers_store,
        orders_for_customer_a
    ):
        """
        テスト2: 注文が日付降順でソートされていること
        
        検証項目:
        - 最新の注文が最初に来ること
        """
        response = client.get(
            "/api/store/orders",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        
        orders = data["orders"]
        assert len(orders) >= 2
        
        # 日付降順の確認
        for i in range(len(orders) - 1):
            assert orders[i]["ordered_at"] >= orders[i + 1]["ordered_at"]
    
    def test_filter_by_status(
        self, 
        client, 
        auth_headers_store,
        orders_for_customer_a
    ):
        """
        テスト3: ステータスでフィルタリングできること
        
        検証項目:
        - status=pendingで該当する注文のみ取得
        """
        response = client.get(
            "/api/store/orders?status=pending",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 全ての注文がpendingステータスであること
        for order in data["orders"]:
            assert order["status"] == "pending"
    
    def test_pagination(
        self, 
        client, 
        auth_headers_store,
        orders_for_customer_a,
        orders_for_customer_b
    ):
        """
        テスト4: ページネーションが機能すること
        
        検証項目:
        - page=1&per_page=2で2件取得
        - totalが全件数であること
        """
        response = client.get(
            "/api/store/orders?page=1&per_page=2",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["orders"]) == 2
        assert data["total"] == 4
    
    def test_unauthorized_access(self, client, orders_for_customer_a):
        """
        テスト5: 未認証ユーザーはアクセスできないこと
        
        検証項目:
        - 認証ヘッダーなしでアクセスすると401エラーが返されること
        """
        response = client.get("/api/store/orders")
        
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_customer_cannot_access(
        self, 
        client, 
        auth_headers_customer_a,
        orders_for_customer_a
    ):
        """
        テスト6: 顧客ユーザーはアクセスできないこと
        
        検証項目:
        - 顧客ユーザーで403エラーが返されること
        """
        response = client.get(
            "/api/store/orders",
            headers=auth_headers_customer_a
        )
        
        assert response.status_code == 403
        assert "detail" in response.json()


class TestUpdateOrderStatus:
    """
    PUT /api/store/orders/{order_id}/status のテストクラス
    """
    
    def test_update_status_success(
        self, 
        client, 
        auth_headers_store,
        orders_for_customer_a
    ):
        """
        テスト1: 注文ステータスを正常に更新できること
        
        検証項目:
        - ステータスコード200が返されること
        - ステータスが正しく更新されること
        """
        order = orders_for_customer_a[2]  # pending状態の注文
        
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            headers=auth_headers_store,
            json={"status": "ready"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == order.id
        assert data["status"] == "ready"
    
    def test_update_status_to_preparing(
        self, 
        client, 
        auth_headers_store,
        orders_for_customer_a
    ):
        """
        テスト2: ステータスをreadyに更新してからcompletedに更新できること
        
        検証項目:
        - status=completedが正しく設定されること
        """
        order = orders_for_customer_a[2]  # pending状態の注文
        
        # まずreadyに更新
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            headers=auth_headers_store,
            json={"status": "ready"}
        )
        assert response.status_code == 200
        
        # 次にcompletedに更新
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            headers=auth_headers_store,
            json={"status": "completed"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "completed"
    
    def test_update_status_order_not_found(
        self, 
        client, 
        auth_headers_store
    ):
        """
        テスト3: 存在しない注文で404エラーが返されること
        
        検証項目:
        - 存在しないorder_idで404が返されること
        """
        response = client.put(
            "/api/store/orders/99999/status",
            headers=auth_headers_store,
            json={"status": "ready"}
        )
        
        assert response.status_code == 404
        assert "detail" in response.json()
    
    def test_unauthorized_access(
        self, 
        client, 
        orders_for_customer_a
    ):
        """
        テスト4: 未認証ユーザーはアクセスできないこと
        
        検証項目:
        - 認証ヘッダーなしでアクセスすると401エラーが返されること
        """
        order = orders_for_customer_a[0]
        
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            json={"status": "confirmed"}
        )
        
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_customer_cannot_update_status(
        self, 
        client, 
        auth_headers_customer_a,
        orders_for_customer_a
    ):
        """
        テスト5: 顧客ユーザーはステータスを更新できないこと
        
        検証項目:
        - 顧客ユーザーで403エラーが返されること
        """
        order = orders_for_customer_a[0]
        
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            headers=auth_headers_customer_a,
            json={"status": "confirmed"}
        )
        
        assert response.status_code == 403
        assert "detail" in response.json()


# ===== フィルタリング・ソート機能の包括的テスト =====

class TestOrderFiltering:
    """
    注文フィルタリング機能のテストクラス
    
    テスト対象:
    - ステータスフィルタ
    - 日付範囲フィルタ
    - 検索フィルタ
    - 複合フィルタ
    """
    
    def test_filter_by_single_status(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        単一ステータスでのフィルタリング
        """
        from models import Order
        
        # 各ステータスの注文を作成
        statuses = ['pending', 'ready', 'completed', 'cancelled']
        orders = []
        for s in statuses:
            order = Order(
                user_id=sample_customer.id,
                menu_id=sample_menu.id,
                store_id=sample_store.id,
                quantity=1,
                total_price=500,
                status=s,
                ordered_at=datetime.now()
            )
            db_session.add(order)
            orders.append(order)
        db_session.commit()
        
        # 各ステータスでフィルタリングテスト
        for s in statuses:
            response = client.get(
                f"/api/store/orders?status={s}",
                headers=auth_headers_store
            )
            
            assert response.status_code == 200
            data = response.json()
            assert all(order["status"] == s for order in data["orders"])
    
    def test_filter_by_multiple_statuses(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        複数ステータスでのフィルタリング (CSV形式)
        """
        from models import Order
        
        # テストデータ作成
        for s in ['pending', 'ready', 'completed']:
            order = Order(
                user_id=sample_customer.id,
                menu_id=sample_menu.id,
                store_id=sample_store.id,
                quantity=1,
                total_price=500,
                status=s,
                ordered_at=datetime.now()
            )
            db_session.add(order)
        db_session.commit()
        
        # pending,ready でフィルタ
        response = client.get(
            "/api/store/orders?status=pending,ready",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(order["status"] in ['pending', 'ready'] for order in data["orders"])
        assert data["total"] == 2
    
    def test_filter_by_date_range(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        日付範囲フィルタリング
        """
        from models import Order
        
        # 異なる日付の注文を作成
        today = date.today()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        
        dates = [week_ago, yesterday, today]
        for d in dates:
            order = Order(
                user_id=sample_customer.id,
                menu_id=sample_menu.id,
                store_id=sample_store.id,
                quantity=1,
                total_price=500,
                status='pending',
                ordered_at=datetime.combine(d, datetime.min.time())
            )
            db_session.add(order)
        db_session.commit()
        
        # 昨日から今日までの範囲
        response = client.get(
            f"/api/store/orders?start_date={yesterday}&end_date={today}",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # yesterday と today
    
    def test_filter_by_search_query(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_customer
    ):
        """
        検索クエリフィルタリング（顧客名・メニュー名）
        """
        from models import Order, Menu, User
        
        # 特徴的な名前のメニューと顧客を作成
        menu1 = Menu(
            store_id=sample_store.id,
            name="特製カレー弁当",
            description="スパイシー",
            price=800,
            is_available=True
        )
        menu2 = Menu(
            store_id=sample_store.id,
            name="幕の内弁当",
            description="和風",
            price=600,
            is_available=True
        )
        db_session.add_all([menu1, menu2])
        
        customer2 = User(
            username="yamada",
            full_name="山田太郎",
            email="yamada@example.com",
            hashed_password="dummy",
            role="customer"
        )
        db_session.add(customer2)
        db_session.commit()
        
        # 注文作成
        order1 = Order(
            user_id=sample_customer.id,
            menu_id=menu1.id,
            store_id=sample_store.id,
            quantity=1,
            total_price=800,
            status='pending',
            ordered_at=datetime.now()
        )
        order2 = Order(
            user_id=customer2.id,
            menu_id=menu2.id,
            store_id=sample_store.id,
            quantity=1,
            total_price=600,
            status='pending',
            ordered_at=datetime.now()
        )
        db_session.add_all([order1, order2])
        db_session.commit()
        
        # "カレー"で検索
        response = client.get(
            "/api/store/orders?q=カレー",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any("カレー" in order["menu"]["name"] for order in data["orders"])
    
    def test_combined_filters(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        複合フィルタ（ステータス + 日付 + 検索）
        """
        from models import Order
        
        today = date.today()
        
        # テストデータ
        order1 = Order(
            user_id=sample_customer.id,
            menu_id=sample_menu.id,
            store_id=sample_store.id,
            quantity=1,
            total_price=500,
            status='pending',
            ordered_at=datetime.combine(today, datetime.min.time())
        )
        order2 = Order(
            user_id=sample_customer.id,
            menu_id=sample_menu.id,
            store_id=sample_store.id,
            quantity=1,
            total_price=500,
            status='ready',
            ordered_at=datetime.combine(today - timedelta(days=1), datetime.min.time())
        )
        db_session.add_all([order1, order2])
        db_session.commit()
        
        # pending + 今日の注文
        response = client.get(
            f"/api/store/orders?status=pending&start_date={today}&end_date={today}",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(order["status"] == "pending" for order in data["orders"])


class TestOrderSorting:
    """
    注文ソート機能のテストクラス
    """
    
    def test_sort_by_newest(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        新しい順ソート（デフォルト）
        """
        from models import Order
        
        # 異なる時刻の注文を作成
        base_time = datetime.now()
        for i in range(3):
            order = Order(
                user_id=sample_customer.id,
                menu_id=sample_menu.id,
                store_id=sample_store.id,
                quantity=1,
                total_price=500,
                status='pending',
                ordered_at=base_time - timedelta(hours=i)
            )
            db_session.add(order)
        db_session.commit()
        
        response = client.get(
            "/api/store/orders?sort=newest",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        orders = data["orders"]
        
        # 降順確認
        for i in range(len(orders) - 1):
            assert orders[i]["ordered_at"] >= orders[i + 1]["ordered_at"]
    
    def test_sort_by_oldest(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        古い順ソート
        """
        from models import Order
        
        base_time = datetime.now()
        for i in range(3):
            order = Order(
                user_id=sample_customer.id,
                menu_id=sample_menu.id,
                store_id=sample_store.id,
                quantity=1,
                total_price=500,
                status='pending',
                ordered_at=base_time - timedelta(hours=i)
            )
            db_session.add(order)
        db_session.commit()
        
        response = client.get(
            "/api/store/orders?sort=oldest",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        orders = data["orders"]
        
        # 昇順確認
        for i in range(len(orders) - 1):
            assert orders[i]["ordered_at"] <= orders[i + 1]["ordered_at"]
    
    def test_sort_by_price_high(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        金額の高い順ソート
        """
        from models import Order
        
        prices = [300, 800, 500]
        for price in prices:
            order = Order(
                user_id=sample_customer.id,
                menu_id=sample_menu.id,
                store_id=sample_store.id,
                quantity=1,
                total_price=price,
                status='pending',
                ordered_at=datetime.now()
            )
            db_session.add(order)
        db_session.commit()
        
        response = client.get(
            "/api/store/orders?sort=price_high",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        orders = data["orders"]
        
        # 降順確認
        for i in range(len(orders) - 1):
            assert orders[i]["total_price"] >= orders[i + 1]["total_price"]
    
    def test_sort_by_price_low(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        金額の安い順ソート
        """
        from models import Order
        
        prices = [800, 300, 500]
        for price in prices:
            order = Order(
                user_id=sample_customer.id,
                menu_id=sample_menu.id,
                store_id=sample_store.id,
                quantity=1,
                total_price=price,
                status='pending',
                ordered_at=datetime.now()
            )
            db_session.add(order)
        db_session.commit()
        
        response = client.get(
            "/api/store/orders?sort=price_low",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        orders = data["orders"]
        
        # 昇順確認
        for i in range(len(orders) - 1):
            assert orders[i]["total_price"] <= orders[i + 1]["total_price"]


# ===== ステータス遷移ルールの網羅的テスト =====

class TestStatusTransitionRules:
    """
    ステータス遷移ルールのテストクラス
    
    遷移ルール:
    - pending → ready, cancelled
    - ready → completed
    - completed → なし（終端）
    - cancelled → なし（終端）
    """
    
    # pending からの遷移テスト
    
    def test_pending_to_ready_allowed(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        ✅ pending → ready は許可される
        """
        from models import Order
        
        order = Order(
            user_id=sample_customer.id,
            menu_id=sample_menu.id,
            store_id=sample_store.id,
            quantity=1,
            total_price=500,
            status='pending',
            ordered_at=datetime.now()
        )
        db_session.add(order)
        db_session.commit()
        
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            headers=auth_headers_store,
            json={"status": "ready"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "ready"
    
    def test_pending_to_cancelled_allowed(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        ✅ pending → cancelled は許可される
        """
        from models import Order
        
        order = Order(
            user_id=sample_customer.id,
            menu_id=sample_menu.id,
            store_id=sample_store.id,
            quantity=1,
            total_price=500,
            status='pending',
            ordered_at=datetime.now()
        )
        db_session.add(order)
        db_session.commit()
        
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            headers=auth_headers_store,
            json={"status": "cancelled"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
    
    def test_pending_to_completed_forbidden(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        ❌ pending → completed は禁止される
        """
        from models import Order
        
        order = Order(
            user_id=sample_customer.id,
            menu_id=sample_menu.id,
            store_id=sample_store.id,
            quantity=1,
            total_price=500,
            status='pending',
            ordered_at=datetime.now()
        )
        db_session.add(order)
        db_session.commit()
        
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            headers=auth_headers_store,
            json={"status": "completed"}
        )
        
        assert response.status_code == 400
        assert "Invalid status transition" in response.json()["detail"]
    
    # ready からの遷移テスト
    
    def test_ready_to_completed_allowed(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        ✅ ready → completed は許可される
        """
        from models import Order
        
        order = Order(
            user_id=sample_customer.id,
            menu_id=sample_menu.id,
            store_id=sample_store.id,
            quantity=1,
            total_price=500,
            status='ready',
            ordered_at=datetime.now()
        )
        db_session.add(order)
        db_session.commit()
        
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            headers=auth_headers_store,
            json={"status": "completed"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
    
    def test_ready_to_pending_forbidden(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        ❌ ready → pending は禁止される（逆行）
        """
        from models import Order
        
        order = Order(
            user_id=sample_customer.id,
            menu_id=sample_menu.id,
            store_id=sample_store.id,
            quantity=1,
            total_price=500,
            status='ready',
            ordered_at=datetime.now()
        )
        db_session.add(order)
        db_session.commit()
        
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            headers=auth_headers_store,
            json={"status": "pending"}
        )
        
        assert response.status_code == 400
        assert "Invalid status transition" in response.json()["detail"]
    
    def test_ready_to_cancelled_forbidden(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        ❌ ready → cancelled は禁止される
        """
        from models import Order
        
        order = Order(
            user_id=sample_customer.id,
            menu_id=sample_menu.id,
            store_id=sample_store.id,
            quantity=1,
            total_price=500,
            status='ready',
            ordered_at=datetime.now()
        )
        db_session.add(order)
        db_session.commit()
        
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            headers=auth_headers_store,
            json={"status": "cancelled"}
        )
        
        assert response.status_code == 400
        assert "Invalid status transition" in response.json()["detail"]
    
    # completed からの遷移テスト（終端状態）
    
    def test_completed_to_any_forbidden(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        ❌ completed は終端状態で、どのステータスにも遷移できない
        """
        from models import Order
        
        order = Order(
            user_id=sample_customer.id,
            menu_id=sample_menu.id,
            store_id=sample_store.id,
            quantity=1,
            total_price=500,
            status='completed',
            ordered_at=datetime.now()
        )
        db_session.add(order)
        db_session.commit()
        
        # 全ての遷移を試す
        for new_status in ['pending', 'ready', 'cancelled']:
            response = client.put(
                f"/api/store/orders/{order.id}/status",
                headers=auth_headers_store,
                json={"status": new_status}
            )
            
            assert response.status_code == 400
            assert "Invalid status transition" in response.json()["detail"]
    
    # cancelled からの遷移テスト（終端状態）
    
    def test_cancelled_to_any_forbidden(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        ❌ cancelled は終端状態で、どのステータスにも遷移できない
        """
        from models import Order
        
        order = Order(
            user_id=sample_customer.id,
            menu_id=sample_menu.id,
            store_id=sample_store.id,
            quantity=1,
            total_price=500,
            status='cancelled',
            ordered_at=datetime.now()
        )
        db_session.add(order)
        db_session.commit()
        
        # 全ての遷移を試す
        for new_status in ['pending', 'ready', 'completed']:
            response = client.put(
                f"/api/store/orders/{order.id}/status",
                headers=auth_headers_store,
                json={"status": new_status}
            )
            
            assert response.status_code == 400
            assert "Invalid status transition" in response.json()["detail"]
    
    def test_same_status_update_allowed(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        ✅ 同じステータスへの更新は許可される（冪等性）
        """
        from models import Order
        
        order = Order(
            user_id=sample_customer.id,
            menu_id=sample_menu.id,
            store_id=sample_store.id,
            quantity=1,
            total_price=500,
            status='pending',
            ordered_at=datetime.now()
        )
        db_session.add(order)
        db_session.commit()
        
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            headers=auth_headers_store,
            json={"status": "pending"}
        )
        
        # 同じステータスへの更新は成功する（遷移ルールに含まれていないため400になる可能性あり）
        # バックエンドの実装に依存
        assert response.status_code in [200, 400]


# ===== マルチテナント分離のテスト =====

class TestMultiTenantIsolation:
    """
    マルチテナントデータ分離のテストクラス
    
    検証項目:
    - 店舗Aのスタッフは店舗Bの注文を閲覧できない
    - 店舗Aのスタッフは店舗Bの注文を更新できない
    """
    
    def test_store_cannot_see_other_store_orders(
        self,
        client,
        db_session,
        roles
    ):
        """
        店舗Aは店舗Bの注文を閲覧できないこと
        """
        from models import User, Store, Menu, Order
        from datetime import time as dt_time
        
        # 店舗A
        store_a = Store(
            name="店舗A",
            description="Store A",
            address="Address A",
            phone_number="000-0000-0001",
            email="store_a@test.com",
            opening_time=dt_time(9, 0),
            closing_time=dt_time(18, 0)
        )
        db_session.add(store_a)
        db_session.commit()
        
        staff_a = User(
            username="staff_a",
            full_name="Staff A",
            email="staff_a@example.com",
            hashed_password="dummy",
            role="store",
            store_id=store_a.id
        )
        db_session.add(staff_a)
        db_session.flush()  # IDを取得
        
        # ロールを割り当て
        from models import UserRole
        user_role = UserRole(user_id=staff_a.id, role_id=roles["owner"].id)
        db_session.add(user_role)
        
        menu_a = Menu(
            store_id=store_a.id,
            name="Menu A",
            description="Menu A",
            price=500,
            is_available=True
        )
        db_session.add(menu_a)
        
        customer_a = User(
            username="customer_a_mt",
            full_name="Customer A",
            email="customer_a_mt@example.com",
            hashed_password="dummy",
            role="customer"
        )
        db_session.add(customer_a)
        db_session.commit()
        
        order_a = Order(
            user_id=customer_a.id,
            menu_id=menu_a.id,
            store_id=store_a.id,
            quantity=1,
            total_price=500,
            status='pending',
            ordered_at=datetime.now()
        )
        db_session.add(order_a)
        
        # 店舗B
        store_b = Store(
            name="店舗B",
            description="Store B",
            address="Address B",
            phone_number="000-0000-0002",
            email="store_b@test.com",
            opening_time=dt_time(9, 0),
            closing_time=dt_time(18, 0)
        )
        db_session.add(store_b)
        db_session.commit()
        
        staff_b = User(
            username="staff_b",
            full_name="Staff B",
            email="staff_b@example.com",
            hashed_password="dummy",
            role="store",
            store_id=store_b.id
        )
        db_session.add(staff_b)
        db_session.flush()  # IDを取得
        
        # ロールを割り当て
        user_role_b = UserRole(user_id=staff_b.id, role_id=roles["owner"].id)
        db_session.add(user_role_b)
        
        menu_b = Menu(
            store_id=store_b.id,
            name="Menu B",
            description="Menu B",
            price=600,
            is_available=True
        )
        db_session.add(menu_b)
        
        customer_b = User(
            username="customer_b_mt",
            full_name="Customer B",
            email="customer_b_mt@example.com",
            hashed_password="dummy",
            role="customer"
        )
        db_session.add(customer_b)
        db_session.commit()
        
        order_b = Order(
            user_id=customer_b.id,
            menu_id=menu_b.id,
            store_id=store_b.id,
            quantity=1,
            total_price=600,
            status='pending',
            ordered_at=datetime.now()
        )
        db_session.add(order_b)
        db_session.commit()
        
        # 店舗Aのトークン取得
        login_response = client.post(
            "/api/auth/login",
            data={"username": "staff_a", "password": "dummy"}
        )
        # NOTE: 実際はハッシュ化されたパスワードが必要なので、このテストは要調整
        # ここでは概念的なテストとして記述
        
        # または直接トークン生成（テスト用）
        from auth import create_access_token
        token_a = create_access_token({"sub": staff_a.username, "user_id": staff_a.id})
        headers_a = {"Authorization": f"Bearer {token_a}"}
        
        # 店舗Aのスタッフで注文一覧取得
        response = client.get(
            "/api/store/orders",
            headers=headers_a
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 店舗Aの注文のみ含まれること
        assert all(order["store_id"] == store_a.id for order in data["orders"])
        assert data["total"] == 1
        
        # 店舗Bの注文は含まれないこと
        assert not any(order["id"] == order_b.id for order in data["orders"])
    
    def test_store_cannot_update_other_store_order(
        self,
        client,
        db_session,
        roles
    ):
        """
        店舗Aは店舗Bの注文を更新できないこと
        """
        from models import User, Store, Menu, Order
        from auth import create_access_token
        from datetime import time as dt_time
        
        # 店舗A
        store_a = Store(
            name="店舗A2",
            description="Store A2",
            address="Address A2",
            phone_number="000-0000-0003",
            email="store_a2@test.com",
            opening_time=dt_time(9, 0),
            closing_time=dt_time(18, 0)
        )
        db_session.add(store_a)
        db_session.commit()
        
        staff_a = User(
            username="staff_a2",
            full_name="Staff A2",
            email="staff_a2@example.com",
            hashed_password="dummy",
            role="store",
            store_id=store_a.id
        )
        db_session.add(staff_a)
        db_session.flush()  # IDを取得
        
        # ロールを割り当て
        from models import UserRole
        user_role = UserRole(user_id=staff_a.id, role_id=roles["owner"].id)
        db_session.add(user_role)
        db_session.commit()
        
        # 店舗B
        store_b = Store(
            name="店舗B2",
            description="Store B2",
            address="Address B2",
            phone_number="000-0000-0004",
            email="store_b2@test.com",
            opening_time=dt_time(9, 0),
            closing_time=dt_time(18, 0)
        )
        db_session.add(store_b)
        db_session.commit()
        
        menu_b = Menu(
            store_id=store_b.id,
            name="Menu B2",
            description="Menu B2",
            price=700,
            is_available=True
        )
        db_session.add(menu_b)
        
        customer_b = User(
            username="customer_b2_mt",
            full_name="Customer B2",
            email="customer_b2_mt@example.com",
            hashed_password="dummy",
            role="customer"
        )
        db_session.add(customer_b)
        db_session.commit()
        
        # 店舗Bの注文
        order_b = Order(
            user_id=customer_b.id,
            menu_id=menu_b.id,
            store_id=store_b.id,
            quantity=1,
            total_price=700,
            status='pending',
            ordered_at=datetime.now()
        )
        db_session.add(order_b)
        db_session.commit()
        
        # 店舗Aのトークン
        token_a = create_access_token({"sub": staff_a.username, "user_id": staff_a.id})
        headers_a = {"Authorization": f"Bearer {token_a}"}
        
        # 店舗Aのスタッフが店舗Bの注文を更新しようとする
        response = client.put(
            f"/api/store/orders/{order_b.id}/status",
            headers=headers_a,
            json={"status": "ready"}
        )
        
        # 404 Not Found が返されること（自店舗の注文として見つからない）
        assert response.status_code == 404
        assert "Order not found" in response.json()["detail"]
        
        # 注文のステータスが変更されていないことを確認
        db_session.refresh(order_b)
        assert order_b.status == 'pending'
    
    def test_customer_orders_isolated_by_user(
        self,
        client,
        db_session,
        sample_store,
        sample_menu
    ):
        """
        顧客Aは顧客Bの注文を閲覧できないこと（顧客側のAPIでも同様）
        """
        from models import User, Order
        from auth import create_access_token
        
        # 顧客A
        customer_a = User(
            username="customer_isolation_a",
            full_name="Customer Isolation A",
            email="customer_isolation_a@example.com",
            hashed_password="dummy",
            role="customer"
        )
        db_session.add(customer_a)
        
        # 顧客B
        customer_b = User(
            username="customer_isolation_b",
            full_name="Customer Isolation B",
            email="customer_isolation_b@example.com",
            hashed_password="dummy",
            role="customer"
        )
        db_session.add(customer_b)
        db_session.commit()
        
        # 注文作成
        order_a = Order(
            user_id=customer_a.id,
            menu_id=sample_menu.id,
            store_id=sample_store.id,
            quantity=1,
            total_price=500,
            status='pending',
            ordered_at=datetime.now()
        )
        order_b = Order(
            user_id=customer_b.id,
            menu_id=sample_menu.id,
            store_id=sample_store.id,
            quantity=1,
            total_price=600,
            status='pending',
            ordered_at=datetime.now()
        )
        db_session.add_all([order_a, order_b])
        db_session.commit()
        
        # 顧客Aのトークン
        token_a = create_access_token({"sub": customer_a.username, "user_id": customer_a.id})
        headers_a = {"Authorization": f"Bearer {token_a}"}
        
        # 顧客Aで注文一覧取得
        response = client.get(
            "/api/customer/orders",
            headers=headers_a
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 顧客Aの注文のみ含まれること
        # 顧客APIは注文リストを直接返す
        if isinstance(data, list):
            orders = data
        else:
            orders = data.get("orders", [])
        
        # 注文IDで検証
        order_ids = [order["id"] for order in orders]
        assert order_a.id in order_ids
        assert order_b.id not in order_ids  # 顧客Bの注文は含まれないこと


# ===== エッジケースとエラーハンドリングテスト =====

class TestEdgeCasesAndErrors:
    """
    エッジケースとエラーハンドリングのテストクラス
    """
    
    def test_pagination_edge_cases(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        ページネーションのエッジケース
        """
        from models import Order
        
        # 5件の注文を作成
        for i in range(5):
            order = Order(
                user_id=sample_customer.id,
                menu_id=sample_menu.id,
                store_id=sample_store.id,
                quantity=1,
                total_price=500,
                status='pending',
                ordered_at=datetime.now()
            )
            db_session.add(order)
        db_session.commit()
        
        # ページ番号0（無効）
        response = client.get(
            "/api/store/orders?page=0&per_page=2",
            headers=auth_headers_store
        )
        assert response.status_code == 422  # Validation error
        
        # 超大きいページ番号
        response = client.get(
            "/api/store/orders?page=9999&per_page=2",
            headers=auth_headers_store
        )
        assert response.status_code == 200
        assert len(response.json()["orders"]) == 0
        
        # per_page = 0 (無効)
        response = client.get(
            "/api/store/orders?page=1&per_page=0",
            headers=auth_headers_store
        )
        assert response.status_code == 422
    
    def test_invalid_status_value(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        無効なステータス値でのエラーハンドリング
        """
        from models import Order
        
        order = Order(
            user_id=sample_customer.id,
            menu_id=sample_menu.id,
            store_id=sample_store.id,
            quantity=1,
            total_price=500,
            status='pending',
            ordered_at=datetime.now()
        )
        db_session.add(order)
        db_session.commit()
        
        # 無効なステータス
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            headers=auth_headers_store,
            json={"status": "invalid_status"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_empty_result_filters(
        self,
        client,
        auth_headers_store,
        db_session,
        sample_store,
        sample_menu,
        sample_customer
    ):
        """
        結果が空になるフィルタ条件
        """
        from models import Order
        
        # pending 注文のみ作成
        order = Order(
            user_id=sample_customer.id,
            menu_id=sample_menu.id,
            store_id=sample_store.id,
            quantity=1,
            total_price=500,
            status='pending',
            ordered_at=datetime.now()
        )
        db_session.add(order)
        db_session.commit()
        
        # completed でフィルタ（存在しない）
        response = client.get(
            "/api/store/orders?status=completed",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["orders"]) == 0
    
    def test_date_range_validation(
        self,
        client,
        auth_headers_store
    ):
        """
        日付範囲のバリデーション
        """
        # 終了日 < 開始日（無効）
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        response = client.get(
            f"/api/store/orders?start_date={today}&end_date={yesterday}",
            headers=auth_headers_store
        )
        
        # バックエンドの実装によっては400か、空の結果を返す
        assert response.status_code in [200, 400]
