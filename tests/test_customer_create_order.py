"""
顧客向け注文作成API のインテグレーションテスト

テスト対象:
- POST /api/customer/orders - 注文作成
"""

import pytest


class TestCreateOrder:
    """
    POST /api/customer/orders のテストクラス
    """
    
    def test_create_order_success(
        self, 
        client, 
        db_session,
        auth_headers_customer_a,
        customer_user_a,
        test_menu
    ):
        """
        テスト1: 注文を正常に作成できること
        
        検証項目:
        - ステータスコード200が返されること
        - 注文情報が正しく作成されること
        - 合計金額が正しく計算されること
        """
        order_data = {
            "menu_id": test_menu.id,
            "quantity": 2,
            "notes": "テスト注文"
        }
        
        response = client.post(
            "/api/customer/orders",
            headers=auth_headers_customer_a,
            json=order_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["menu_id"] == test_menu.id
        assert data["quantity"] == 2
        assert data["total_price"] == test_menu.price * 2
        assert data["notes"] == "テスト注文"
        assert data["status"] == "pending"
        assert "id" in data
        assert "ordered_at" in data
    
    def test_create_order_with_delivery_time(
        self, 
        client, 
        auth_headers_customer_a,
        test_menu
    ):
        """
        テスト2: 受取時間を指定して注文を作成できること
        
        検証項目:
        - delivery_timeが正しく設定されること
        """
        order_data = {
            "menu_id": test_menu.id,
            "quantity": 1,
            "delivery_time": "12:00:00",  # time型なのでHH:MM:SS形式
            "notes": "12時受取希望"
        }
        
        response = client.post(
            "/api/customer/orders",
            headers=auth_headers_customer_a,
            json=order_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "delivery_time" in data
        assert data["notes"] == "12時受取希望"
    
    def test_create_order_invalid_menu(
        self, 
        client, 
        auth_headers_customer_a
    ):
        """
        テスト3: 存在しないメニューで404エラーが返されること
        
        検証項目:
        - 存在しないmenu_idで404が返されること
        """
        order_data = {
            "menu_id": 99999,
            "quantity": 1
        }
        
        response = client.post(
            "/api/customer/orders",
            headers=auth_headers_customer_a,
            json=order_data
        )
        
        assert response.status_code == 404
        assert "detail" in response.json()
    
    def test_create_order_unavailable_menu(
        self, 
        client, 
        auth_headers_customer_a,
        test_menu_unavailable
    ):
        """
        テスト4: 在庫切れメニューで404エラーが返されること
        
        検証項目:
        - is_available=falseのメニューで404が返されること
        """
        order_data = {
            "menu_id": test_menu_unavailable.id,
            "quantity": 1
        }
        
        response = client.post(
            "/api/customer/orders",
            headers=auth_headers_customer_a,
            json=order_data
        )
        
        assert response.status_code == 404
        assert "detail" in response.json()
    
    def test_create_order_invalid_quantity_zero(
        self, 
        client, 
        auth_headers_customer_a,
        test_menu
    ):
        """
        テスト5: 数量0で422エラーが返されること
        
        検証項目:
        - quantity=0でバリデーションエラーが返されること
        """
        order_data = {
            "menu_id": test_menu.id,
            "quantity": 0
        }
        
        response = client.post(
            "/api/customer/orders",
            headers=auth_headers_customer_a,
            json=order_data
        )
        
        assert response.status_code == 422
    
    def test_create_order_invalid_quantity_over_limit(
        self, 
        client, 
        auth_headers_customer_a,
        test_menu
    ):
        """
        テスト6: 数量11以上で422エラーが返されること
        
        検証項目:
        - quantity=11でバリデーションエラーが返されること
        """
        order_data = {
            "menu_id": test_menu.id,
            "quantity": 11
        }
        
        response = client.post(
            "/api/customer/orders",
            headers=auth_headers_customer_a,
            json=order_data
        )
        
        assert response.status_code == 422
    
    def test_create_order_notes_max_length(
        self, 
        client, 
        auth_headers_customer_a,
        test_menu
    ):
        """
        テスト7: 備考が500文字を超えると422エラーが返されること
        
        検証項目:
        - notes=501文字でバリデーションエラーが返されること
        """
        order_data = {
            "menu_id": test_menu.id,
            "quantity": 1,
            "notes": "あ" * 501
        }
        
        response = client.post(
            "/api/customer/orders",
            headers=auth_headers_customer_a,
            json=order_data
        )
        
        assert response.status_code == 422
    
    def test_create_order_missing_menu_id(
        self, 
        client, 
        auth_headers_customer_a
    ):
        """
        テスト8: menu_idが欠けている場合422エラーが返されること
        
        検証項目:
        - 必須フィールド欠如でバリデーションエラーが返されること
        """
        order_data = {
            "quantity": 1
        }
        
        response = client.post(
            "/api/customer/orders",
            headers=auth_headers_customer_a,
            json=order_data
        )
        
        assert response.status_code == 422
    
    def test_unauthorized_access(self, client, test_menu):
        """
        テスト9: 未認証ユーザーはアクセスできないこと
        
        検証項目:
        - 認証ヘッダーなしでアクセスすると403エラーが返されること
        """
        order_data = {
            "menu_id": test_menu.id,
            "quantity": 1
        }
        
        response = client.post("/api/customer/orders", json=order_data)
        
        assert response.status_code == 403
        assert "detail" in response.json()
    
    def test_store_user_cannot_create_order(
        self, 
        client, 
        auth_headers_store,
        test_menu
    ):
        """
        テスト10: 店舗ユーザーは注文を作成できないこと
        
        検証項目:
        - 店舗ユーザーで403エラーが返されること
        """
        order_data = {
            "menu_id": test_menu.id,
            "quantity": 1
        }
        
        response = client.post(
            "/api/customer/orders",
            headers=auth_headers_store,
            json=order_data
        )
        
        assert response.status_code == 403
        assert "detail" in response.json()
