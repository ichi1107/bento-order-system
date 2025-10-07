"""
店舗向け注文API のインテグレーションテスト

テスト対象:
- GET /api/store/orders - 全注文一覧取得
- PUT /api/store/orders/{order_id}/status - 注文ステータス更新
"""

import pytest


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
        - status_filter=pendingで該当する注文のみ取得
        """
        response = client.get(
            "/api/store/orders?status_filter=pending",
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
        - 認証ヘッダーなしでアクセスすると403エラーが返されること
        """
        response = client.get("/api/store/orders")
        
        assert response.status_code == 403
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
        order = orders_for_customer_a[0]
        
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            headers=auth_headers_store,
            json={"status": "confirmed"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == order.id
        assert data["status"] == "confirmed"
    
    def test_update_status_to_preparing(
        self, 
        client, 
        auth_headers_store,
        orders_for_customer_a
    ):
        """
        テスト2: ステータスをpreparingに更新できること
        
        検証項目:
        - status=preparingが正しく設定されること
        """
        order = orders_for_customer_a[1]
        
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            headers=auth_headers_store,
            json={"status": "preparing"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "preparing"
    
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
            json={"status": "confirmed"}
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
        - 認証ヘッダーなしでアクセスすると403エラーが返されること
        """
        order = orders_for_customer_a[0]
        
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            json={"status": "confirmed"}
        )
        
        assert response.status_code == 403
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
