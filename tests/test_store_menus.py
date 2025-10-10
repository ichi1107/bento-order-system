"""
店舗向けメニュー管理API のインテグレーションテスト

テスト対象:
- POST /api/store/menus - メニュー作成
- PUT /api/store/menus/{menu_id} - メニュー更新
- DELETE /api/store/menus/{menu_id} - メニュー削除
"""

import pytest


class TestCreateMenu:
    """
    POST /api/store/menus のテストクラス
    """
    
    def test_create_menu_success(
        self, 
        client, 
        auth_headers_store
    ):
        """
        テスト1: メニューを正常に作成できること
        
        検証項目:
        - ステータスコード200が返されること
        - メニュー情報が正しく作成されること
        """
        menu_data = {
            "name": "新規弁当",
            "price": 1200,
            "description": "新しいメニューです",
            "image_url": "https://example.com/new.jpg",
            "is_available": True
        }
        
        response = client.post(
            "/api/store/menus",
            headers=auth_headers_store,
            json=menu_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "新規弁当"
        assert data["price"] == 1200
        assert data["description"] == "新しいメニューです"
        assert data["is_available"] is True
        assert "id" in data
    
    def test_create_menu_without_optional_fields(
        self, 
        client, 
        auth_headers_store
    ):
        """
        テスト2: 任意項目なしでメニューを作成できること
        
        検証項目:
        - description, image_urlなしでも作成可能
        """
        menu_data = {
            "name": "シンプル弁当",
            "price": 800
        }
        
        response = client.post(
            "/api/store/menus",
            headers=auth_headers_store,
            json=menu_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "シンプル弁当"
        assert data["price"] == 800
    
    def test_create_menu_invalid_price(
        self, 
        client, 
        auth_headers_store
    ):
        """
        テスト3: 価格が0以下で422エラーが返されること
        
        検証項目:
        - price=0でバリデーションエラーが返されること
        """
        menu_data = {
            "name": "無効弁当",
            "price": 0
        }
        
        response = client.post(
            "/api/store/menus",
            headers=auth_headers_store,
            json=menu_data
        )
        
        assert response.status_code == 422
    
    def test_unauthorized_access(self, client):
        """
        テスト4: 未認証ユーザーはアクセスできないこと
        
        検証項目:
        - 認証ヘッダーなしでアクセスすると401エラーが返されること
        """
        menu_data = {
            "name": "テスト弁当",
            "price": 800
        }
        
        response = client.post("/api/store/menus", json=menu_data)
        
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_customer_cannot_create_menu(
        self, 
        client, 
        auth_headers_customer_a
    ):
        """
        テスト5: 顧客ユーザーはメニューを作成できないこと
        
        検証項目:
        - 顧客ユーザーで403エラーが返されること
        """
        menu_data = {
            "name": "テスト弁当",
            "price": 800
        }
        
        response = client.post(
            "/api/store/menus",
            headers=auth_headers_customer_a,
            json=menu_data
        )
        
        assert response.status_code == 403
        assert "detail" in response.json()


class TestUpdateMenu:
    """
    PUT /api/store/menus/{menu_id} のテストクラス
    """
    
    def test_update_menu_success(
        self, 
        client, 
        auth_headers_store,
        test_menu
    ):
        """
        テスト1: メニューを正常に更新できること
        
        検証項目:
        - ステータスコード200が返されること
        - メニュー情報が正しく更新されること
        """
        update_data = {
            "name": "更新された弁当",
            "price": 1000,
            "description": "価格改定しました"
        }
        
        response = client.put(
            f"/api/store/menus/{test_menu.id}",
            headers=auth_headers_store,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_menu.id
        assert data["name"] == "更新された弁当"
        assert data["price"] == 1000
        assert data["description"] == "価格改定しました"
    
    def test_update_menu_partial(
        self, 
        client, 
        auth_headers_store,
        test_menu
    ):
        """
        テスト2: 一部のフィールドのみ更新できること
        
        検証項目:
        - 一部のフィールドのみ更新可能
        """
        update_data = {
            "price": 850
        }
        
        response = client.put(
            f"/api/store/menus/{test_menu.id}",
            headers=auth_headers_store,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["price"] == 850
        assert data["name"] == test_menu.name  # 変更されていない
    
    def test_update_menu_availability(
        self, 
        client, 
        auth_headers_store,
        test_menu
    ):
        """
        テスト3: 在庫状態を更新できること
        
        検証項目:
        - is_availableが更新されること
        """
        update_data = {
            "is_available": False
        }
        
        response = client.put(
            f"/api/store/menus/{test_menu.id}",
            headers=auth_headers_store,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_available"] is False
    
    def test_update_menu_not_found(
        self, 
        client, 
        auth_headers_store
    ):
        """
        テスト4: 存在しないメニューで404エラーが返されること
        
        検証項目:
        - 存在しないmenu_idで404が返されること
        """
        update_data = {
            "name": "存在しない"
        }
        
        response = client.put(
            "/api/store/menus/99999",
            headers=auth_headers_store,
            json=update_data
        )
        
        assert response.status_code == 404
        assert "detail" in response.json()
    
    def test_unauthorized_access(self, client, test_menu):
        """
        テスト5: 未認証ユーザーはアクセスできないこと
        
        検証項目:
        - 認証ヘッダーなしでアクセスすると401エラーが返されること
        """
        update_data = {
            "name": "更新"
        }
        
        response = client.put(
            f"/api/store/menus/{test_menu.id}",
            json=update_data
        )
        
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_customer_cannot_update_menu(
        self, 
        client, 
        auth_headers_customer_a,
        test_menu
    ):
        """
        テスト6: 顧客ユーザーはメニューを更新できないこと
        
        検証項目:
        - 顧客ユーザーで403エラーが返されること
        """
        update_data = {
            "name": "更新"
        }
        
        response = client.put(
            f"/api/store/menus/{test_menu.id}",
            headers=auth_headers_customer_a,
            json=update_data
        )
        
        assert response.status_code == 403
        assert "detail" in response.json()


class TestDeleteMenu:
    """
    DELETE /api/store/menus/{menu_id} のテストクラス
    """
    
    def test_delete_menu_with_orders_logical_delete(
        self, 
        client, 
        db_session,
        auth_headers_store,
        test_menu,
        orders_for_customer_a
    ):
        """
        テスト1: 既存注文があるメニューは論理削除されること
        
        検証項目:
        - 既存注文があるメニューはis_available=falseになること
        - メッセージが返されること
        """
        response = client.delete(
            f"/api/store/menus/{test_menu.id}",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "existing orders" in data["message"].lower()
        
        # メニューがまだ存在し、is_available=falseになっていることを確認
        from models import Menu
        updated_menu = db_session.query(Menu).filter(Menu.id == test_menu.id).first()
        assert updated_menu is not None
        assert updated_menu.is_available is False
    
    def test_delete_menu_without_orders_physical_delete(
        self, 
        client, 
        db_session,
        auth_headers_store,
        test_menu_2
    ):
        """
        テスト2: 注文のないメニューは物理削除されること
        
        検証項目:
        - 注文のないメニューは完全に削除されること
        """
        menu_id = test_menu_2.id
        
        response = client.delete(
            f"/api/store/menus/{menu_id}",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        
        # メニューが削除されていることを確認
        from models import Menu
        deleted_menu = db_session.query(Menu).filter(Menu.id == menu_id).first()
        assert deleted_menu is None
    
    def test_delete_menu_not_found(
        self, 
        client, 
        auth_headers_store
    ):
        """
        テスト3: 存在しないメニューで404エラーが返されること
        
        検証項目:
        - 存在しないmenu_idで404が返されること
        """
        response = client.delete(
            "/api/store/menus/99999",
            headers=auth_headers_store
        )
        
        assert response.status_code == 404
        assert "detail" in response.json()
    
    def test_unauthorized_access(self, client, test_menu):
        """
        テスト4: 未認証ユーザーはアクセスできないこと
        
        検証項目:
        - 認証ヘッダーなしでアクセスすると401エラーが返されること
        """
        response = client.delete(f"/api/store/menus/{test_menu.id}")
        
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_customer_cannot_delete_menu(
        self, 
        client, 
        auth_headers_customer_a,
        test_menu
    ):
        """
        テスト5: 顧客ユーザーはメニューを削除できないこと
        
        検証項目:
        - 顧客ユーザーで403エラーが返されること
        """
        response = client.delete(
            f"/api/store/menus/{test_menu.id}",
            headers=auth_headers_customer_a
        )
        
        assert response.status_code == 403
        assert "detail" in response.json()
