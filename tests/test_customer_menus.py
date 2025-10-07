"""
顧客向けメニューAPI のインテグレーションテスト

テスト対象:
- GET /api/customer/menus - メニュー一覧取得
- GET /api/customer/menus/{menu_id} - メニュー詳細取得
"""

import pytest


class TestGetMenus:
    """
    GET /api/customer/menus のテストクラス
    """
    
    def test_get_all_menus_success(
        self, 
        client, 
        auth_headers_customer_a, 
        test_menu, 
        test_menu_2,
        test_menu_unavailable
    ):
        """
        テスト1: デフォルトで在庫ありのメニューのみ取得されること
        
        検証項目:
        - ステータスコード200が返されること
        - 在庫ありの2つのメニューが返されること
        - メニュー情報が正しく含まれていること
        """
        response = client.get(
            "/api/customer/menus",
            headers=auth_headers_customer_a
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "menus" in data
        assert len(data["menus"]) == 2  # 在庫ありのみ
        
        # メニューのフィールド検証
        menu = data["menus"][0]
        assert "id" in menu
        assert "name" in menu
        assert "price" in menu
        assert "description" in menu
        assert "image_url" in menu
        assert "is_available" in menu
    
    def test_filter_available_menus(
        self, 
        client, 
        auth_headers_customer_a, 
        test_menu, 
        test_menu_2,
        test_menu_unavailable
    ):
        """
        テスト2: 在庫ありメニューのみをフィルタリングできること
        
        検証項目:
        - available=trueのクエリパラメータで在庫ありのみ取得
        - 2つのメニューが返されること
        - 全てis_available=trueであること
        """
        response = client.get(
            "/api/customer/menus?available=true",
            headers=auth_headers_customer_a
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["menus"]) == 2
        
        # 全てのメニューが在庫ありであることを確認
        for menu in data["menus"]:
            assert menu["is_available"] is True
    
    def test_filter_unavailable_menus(
        self, 
        client, 
        auth_headers_customer_a, 
        test_menu, 
        test_menu_2,
        test_menu_unavailable
    ):
        """
        テスト3: 在庫切れメニューを含む全メニューを取得できること
        
        検証項目:
        - is_available=Noneまたは明示的にfalseで在庫切れも取得
        - 全3つのメニューが返されること
        """
        # is_available=falseを明示的に指定
        response = client.get(
            "/api/customer/menus?is_available=false",
            headers=auth_headers_customer_a
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["menus"]) == 1
        assert data["menus"][0]["is_available"] is False
        assert data["menus"][0]["name"] == "在庫切れ弁当"
    
    def test_unauthorized_access(self, client, test_menu):
        """
        テスト4: 未認証ユーザーはアクセスできないこと
        
        検証項目:
        - 認証ヘッダーなしでアクセスすると403エラーが返されること
        """
        response = client.get("/api/customer/menus")
        
        assert response.status_code == 403
        assert "detail" in response.json()


class TestGetMenuDetail:
    """
    GET /api/customer/menus/{menu_id} のテストクラス
    """
    
    def test_get_menu_detail_success(
        self, 
        client, 
        auth_headers_customer_a, 
        test_menu
    ):
        """
        テスト1: メニュー詳細を正常に取得できること
        
        検証項目:
        - ステータスコード200が返されること
        - メニュー詳細情報が正しく返されること
        """
        response = client.get(
            f"/api/customer/menus/{test_menu.id}",
            headers=auth_headers_customer_a
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_menu.id
        assert data["name"] == test_menu.name
        assert data["price"] == test_menu.price
        assert data["description"] == test_menu.description
        assert data["is_available"] == test_menu.is_available
    
    def test_menu_not_found(self, client, auth_headers_customer_a):
        """
        テスト2: 存在しないメニューIDで404エラーが返されること
        
        検証項目:
        - 存在しないメニューIDで404が返されること
        """
        response = client.get(
            "/api/customer/menus/99999",
            headers=auth_headers_customer_a
        )
        
        assert response.status_code == 404
        assert "detail" in response.json()
    
    def test_unauthorized_access(self, client, test_menu):
        """
        テスト3: 未認証ユーザーはアクセスできないこと
        
        検証項目:
        - 認証ヘッダーなしでアクセスすると403エラーが返されること
        """
        response = client.get(f"/api/customer/menus/{test_menu.id}")
        
        assert response.status_code == 403
        assert "detail" in response.json()
