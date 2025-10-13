"""
注文管理以外の店舗API機能のテスト

Feature #76の一環として、注文管理以外のAPIエンドポイントの
テストカバレッジを向上させる
"""

import pytest
from datetime import datetime, date, time, timedelta


# ===== 店舗プロフィール管理のテスト =====

class TestStoreProfile:
    """店舗プロフィール管理のテストクラス"""
    
    def test_get_store_profile_success(
        self,
        client,
        auth_headers_store,
        store_a
    ):
        """
        店舗プロフィール取得成功
        """
        response = client.get(
            "/api/store/profile",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == store_a.id
        assert data["name"] == store_a.name
        assert "address" in data
        assert "email" in data
    
    def test_update_store_profile_success(
        self,
        client,
        auth_headers_store,
        store_a
    ):
        """
        店舗プロフィール更新成功
        """
        update_data = {
            "name": "更新された店舗名",
            "address": "更新された住所",
            "description": "更新された説明"
        }
        
        response = client.put(
            "/api/store/profile",
            headers=auth_headers_store,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert data["address"] == update_data["address"]


# ===== メニュー管理のテスト =====

class TestMenuManagement:
    """メニュー管理機能のテストクラス"""
    
    def test_get_menus_list(
        self,
        client,
        auth_headers_store,
        test_menu
    ):
        """
        メニュー一覧取得
        """
        response = client.get(
            "/api/store/menus",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "menus" in data
        assert len(data["menus"]) > 0
    
    def test_create_menu_success(
        self,
        client,
        auth_headers_store,
        store_a
    ):
        """
        メニュー作成成功
        """
        menu_data = {
            "name": "新しい弁当",
            "description": "美味しい弁当",
            "price": 1000,
            "is_available": True
        }
        
        response = client.post(
            "/api/store/menus",
            headers=auth_headers_store,
            json=menu_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == menu_data["name"]
        assert data["price"] == menu_data["price"]
        assert data["store_id"] == store_a.id
    
    def test_create_menu_validation_error(
        self,
        client,
        auth_headers_store
    ):
        """
        メニュー作成時のバリデーションエラー
        """
        invalid_data = {
            "name": "",  # 空の名前
            "price": -100  # 負の価格
        }
        
        response = client.post(
            "/api/store/menus",
            headers=auth_headers_store,
            json=invalid_data
        )
        
        assert response.status_code == 422
    
    # メニュー詳細取得APIは未実装のためスキップ
    # def test_get_menu_detail(
    #     self,
    #     client,
    #     auth_headers_store,
    #     test_menu
    # ):
    #     """
    #     メニュー詳細取得
    #     """
    #     response = client.get(
    #         f"/api/store/menus/{test_menu.id}",
    #         headers=auth_headers_store
    #     )
    #     
    #     assert response.status_code == 200
    #     data = response.json()
    #     
    #     assert data["id"] == test_menu.id
    #     assert data["name"] == test_menu.name
    
    def test_update_menu_success(
        self,
        client,
        auth_headers_store,
        test_menu
    ):
        """
        メニュー更新成功
        """
        update_data = {
            "name": "更新されたメニュー名",
            "price": 1200,
            "description": "更新された説明"
        }
        
        response = client.put(
            f"/api/store/menus/{test_menu.id}",
            headers=auth_headers_store,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert data["price"] == update_data["price"]
    
    def test_delete_menu_success(
        self,
        client,
        auth_headers_store,
        db_session,
        store_a
    ):
        """
        メニュー削除成功（注文のないメニュー）
        """
        from models import Menu
        
        # 注文のないメニューを作成
        menu = Menu(
            name="削除用メニュー",
            store_id=store_a.id,
            price=500,
            is_available=True
        )
        db_session.add(menu)
        db_session.commit()
        db_session.refresh(menu)
        
        response = client.delete(
            f"/api/store/menus/{menu.id}",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
    
    # メニュー有効/無効切替APIは未実装のためスキップ
    # def test_toggle_menu_availability(
    #     self,
    #     client,
    #     auth_headers_store,
    #     test_menu
    # ):
    #     """
    #     メニュー有効/無効切替
    #     """
    #     original_status = test_menu.is_available
    #     
    #     response = client.put(
    #         f"/api/store/menus/{test_menu.id}/toggle",
    #         headers=auth_headers_store
    #     )
    #     
    #     assert response.status_code == 200
    #     data = response.json()
    #     
    #     assert data["is_available"] != original_status


# ===== ダッシュボードのテスト =====

class TestDashboard:
    """ダッシュボード機能のテストクラス"""
    
    def test_get_dashboard(
        self,
        client,
        auth_headers_store,
        orders_for_customer_a
    ):
        """
        ダッシュボード情報取得
        """
        response = client.get(
            "/api/store/dashboard",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 実際のレスポンス構造に合わせる
        assert "pending_orders" in data
        assert "completed_orders" in data
        assert "cancelled_orders" in data
        assert "average_order_value" in data
        assert "hourly_orders" in data
    
    def test_get_weekly_sales(
        self,
        client,
        auth_headers_store
    ):
        """
        週間売上データ取得
        """
        response = client.get(
            "/api/store/dashboard/weekly-sales",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 実際のレスポンス構造に合わせる
        assert "labels" in data
        assert "data" in data
        assert isinstance(data["labels"], list)
        assert isinstance(data["data"], list)


# ===== レポート機能のテスト =====

class TestReports:
    """レポート機能のテストクラス"""
    
    def test_get_sales_report_today(
        self,
        client,
        auth_headers_store,
        orders_for_customer_a
    ):
        """
        本日の売上レポート取得
        """
        response = client.get(
            "/api/store/reports/sales",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 実際のレスポンス構造に合わせる
        assert "daily_reports" in data
        assert "menu_reports" in data
        assert "total_sales" in data
        assert "total_orders" in data
    
    def test_get_sales_report_date_range(
        self,
        client,
        auth_headers_store
    ):
        """
        期間指定の売上レポート取得
        """
        start_date = (date.today() - timedelta(days=7)).isoformat()
        end_date = date.today().isoformat()
        
        response = client.get(
            f"/api/store/reports/sales?start_date={start_date}&end_date={end_date}",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 実際のレスポンス構造に合わせる
        assert "daily_reports" in data
        assert "start_date" in data
        assert "end_date" in data
    
    # 人気メニューと時間別注文のAPIは未実装のためスキップ
    # def test_get_popular_menus(
    #     self,
    #     client,
    #     auth_headers_store,
    #     orders_for_customer_a
    # ):
    #     """
    #     人気メニューレポート取得
    #     """
    #     response = client.get(
    #         "/api/store/reports/popular-menus",
    #         headers=auth_headers_store
    #     )
    #     
    #     assert response.status_code == 200
    #     data = response.json()
    #     
    #     assert isinstance(data, list)
    # 
    # def test_get_hourly_orders(
    #     self,
    #     client,
    #     auth_headers_store
    # ):
    #     """
    #     時間別注文数レポート取得
    #     """
    #     response = client.get(
    #         "/api/store/reports/hourly-orders",
    #         headers=auth_headers_store
    #     )
    #     
    #     assert response.status_code == 200
    #     data = response.json()
    #     
    #     assert isinstance(data, list)
