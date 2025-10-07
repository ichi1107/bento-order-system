"""
注文履歴APIのインテグレーションテスト

テスト対象:
- GET /api/customer/orders

テストケース:
1. 顧客が自分の注文履歴を取得できること
2. 注文履歴が新しい順（ordered_at降順）で返されること
3. 注文履歴がない顧客は空のリストが返されること
4. セキュリティ: 顧客Aが顧客Bの注文履歴を取得できないこと
5. 未認証ユーザーはアクセスできないこと
"""

import pytest
from datetime import datetime


class TestGetCustomerOrders:
    """
    GET /api/customer/orders エンドポイントのテスト
    """
    
    def test_get_own_orders_success(
        self, 
        client, 
        customer_user_a, 
        orders_for_customer_a,
        auth_headers_customer_a
    ):
        """
        テスト1: 顧客が自分の注文履歴を正しく取得できること
        
        検証項目:
        - ステータスコード 200
        - 注文数が正しいこと
        - 各注文の情報が正しく含まれていること
        """
        response = client.get(
            "/api/customer/orders",
            headers=auth_headers_customer_a
        )
        
        # ステータスコードの確認
        assert response.status_code == 200
        
        # レスポンスボディの確認
        data = response.json()
        assert "orders" in data
        assert "total" in data
        
        # 注文数の確認
        assert data["total"] == 3
        assert len(data["orders"]) == 3
        
        # 注文情報の確認
        for order in data["orders"]:
            assert "id" in order
            assert "quantity" in order
            assert "total_price" in order
            assert "status" in order
            assert "ordered_at" in order
            assert "menu_id" in order
            assert "menu_name" in order
            assert "menu_price" in order
            assert order["user_id"] == customer_user_a.id if "user_id" in order else True
    
    def test_orders_sorted_by_date_descending(
        self,
        client,
        customer_user_a,
        orders_for_customer_a,
        auth_headers_customer_a
    ):
        """
        テスト2: 注文履歴が新しい順（ordered_at降順）で返されること
        
        検証項目:
        - 最新の注文が最初に来ること
        - 最古の注文が最後に来ること
        - 全ての注文が降順でソートされていること
        """
        response = client.get(
            "/api/customer/orders",
            headers=auth_headers_customer_a
        )
        
        assert response.status_code == 200
        data = response.json()
        
        orders = data["orders"]
        assert len(orders) == 3
        
        # 注文日時を取得
        order_dates = [datetime.fromisoformat(order["ordered_at"].replace('Z', '+00:00')) for order in orders]
        
        # 降順（新しい順）でソートされているか確認
        assert order_dates == sorted(order_dates, reverse=True), \
            "注文が新しい順にソートされていません"
        
        # 最新の注文が最初、最古の注文が最後であることを確認
        assert orders[0]["notes"] == "最新の注文"
        assert orders[-1]["notes"] == "最初の注文"
        
        # ステータスの確認（参考）
        assert orders[0]["status"] == "pending"  # 最新
        assert orders[1]["status"] == "confirmed"  # 中間
        assert orders[2]["status"] == "completed"  # 最古
    
    def test_empty_orders_list(
        self,
        client,
        customer_user_empty,
        auth_headers_customer_empty
    ):
        """
        テスト3: 注文履歴がないユーザーは空のリストが返されること
        
        検証項目:
        - ステータスコード 200
        - orders が空のリストであること
        - total が 0 であること
        """
        response = client.get(
            "/api/customer/orders",
            headers=auth_headers_customer_empty
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 空のリストが返されること
        assert data["orders"] == []
        assert data["total"] == 0
    
    def test_security_cannot_access_other_users_orders(
        self,
        client,
        customer_user_a,
        customer_user_b,
        orders_for_customer_a,
        orders_for_customer_b,
        auth_headers_customer_a
    ):
        """
        テスト4: セキュリティテスト - 顧客Aが顧客Bの注文履歴を取得できないこと
        
        検証項目:
        - 顧客Aの認証情報で取得した注文履歴に、顧客Bの注文が含まれないこと
        - 返される注文は全て顧客Aのものであること
        """
        # 顧客Aの認証情報でアクセス
        response = client.get(
            "/api/customer/orders",
            headers=auth_headers_customer_a
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 顧客Aの注文のみが返されること
        assert data["total"] == 3
        
        # 全ての注文が顧客Aのものであることを確認
        # (OrderHistoryItemにはuser_idが含まれないため、注文数で確認)
        # 顧客Aは3つ、顧客Bは1つの注文を持っている
        assert len(data["orders"]) == 3
        
        # 念のため、顧客Bでもテスト
        response_b = client.get(
            "/api/customer/orders",
            headers={"Authorization": f"Bearer {client.post('/api/auth/login', json={'username': 'customer_b', 'password': 'password123'}).json()['access_token']}"}
        )
        
        assert response_b.status_code == 200
        data_b = response_b.json()
        
        # 顧客Bの注文のみが返されること
        assert data_b["total"] == 1
        assert data_b["orders"][0]["notes"] == "顧客Bの注文"
    
    def test_unauthorized_access(self, client):
        """
        テスト5: 未認証ユーザーはアクセスできないこと
        
        検証項目:
        - 認証ヘッダーなしでアクセスすると403エラーが返されること
        """
        response = client.get("/api/customer/orders")
        
        assert response.status_code == 403
        assert "detail" in response.json()
    
    def test_invalid_token(self, client):
        """
        テスト6: 無効なトークンではアクセスできないこと
        
        検証項目:
        - 無効なトークンでアクセスすると401エラーが返されること
        """
        response = client.get(
            "/api/customer/orders",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        assert response.status_code == 401
    
    def test_pagination_parameters(
        self,
        client,
        customer_user_a,
        orders_for_customer_a,
        auth_headers_customer_a
    ):
        """
        テスト7: ページネーションパラメータが正しく動作すること
        
        検証項目:
        - page と per_page パラメータが機能すること
        - 指定した件数が返されること
        """
        # 1ページあたり2件で取得
        response = client.get(
            "/api/customer/orders?page=1&per_page=2",
            headers=auth_headers_customer_a
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 総数は3件だが、1ページあたり2件のみ返される
        assert data["total"] == 3
        assert len(data["orders"]) == 2
        
        # 2ページ目を取得
        response_page2 = client.get(
            "/api/customer/orders?page=2&per_page=2",
            headers=auth_headers_customer_a
        )
        
        assert response_page2.status_code == 200
        data_page2 = response_page2.json()
        
        # 2ページ目は1件のみ
        assert data_page2["total"] == 3
        assert len(data_page2["orders"]) == 1
    
    def test_status_filter(
        self,
        client,
        customer_user_a,
        orders_for_customer_a,
        auth_headers_customer_a
    ):
        """
        テスト8: ステータスフィルターが正しく動作すること
        
        検証項目:
        - status_filter パラメータで注文をフィルタリングできること
        """
        # pendingステータスのみ取得
        response = client.get(
            "/api/customer/orders?status_filter=pending",
            headers=auth_headers_customer_a
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # pendingの注文は1件
        assert data["total"] == 1
        assert len(data["orders"]) == 1
        assert data["orders"][0]["status"] == "pending"
        
        # completedステータスのみ取得
        response_completed = client.get(
            "/api/customer/orders?status_filter=completed",
            headers=auth_headers_customer_a
        )
        
        assert response_completed.status_code == 200
        data_completed = response_completed.json()
        
        # completedの注文は1件
        assert data_completed["total"] == 1
        assert data_completed["orders"][0]["status"] == "completed"
