"""
店舗APIのロールベースアクセス制御(RBAC)テスト

各エンドポイントへのアクセス制御を、owner/manager/staffの権限に基づいてテストします。
"""

import pytest
from datetime import datetime


class TestDashboardRBAC:
    """ダッシュボードエンドポイントのRBACテスト"""
    
    def test_owner_can_access_dashboard(self, client, auth_headers_owner):
        """オーナーはダッシュボードにアクセスできる"""
        response = client.get("/api/store/dashboard", headers=auth_headers_owner)
        assert response.status_code == 200
        data = response.json()
        assert "total_orders" in data
        assert "total_sales" in data
    
    def test_manager_can_access_dashboard(self, client, auth_headers_manager):
        """マネージャーはダッシュボードにアクセスできる"""
        response = client.get("/api/store/dashboard", headers=auth_headers_manager)
        assert response.status_code == 200
        data = response.json()
        assert "total_orders" in data
        assert "total_sales" in data
    
    def test_staff_can_access_dashboard(self, client, auth_headers_staff):
        """スタッフはダッシュボードにアクセスできる"""
        response = client.get("/api/store/dashboard", headers=auth_headers_staff)
        assert response.status_code == 200
        data = response.json()
        assert "total_orders" in data
        assert "total_sales" in data


class TestOrdersRBAC:
    """注文管理エンドポイントのRBACテスト"""
    
    def test_owner_can_get_orders(self, client, auth_headers_owner):
        """オーナーは注文一覧を取得できる"""
        response = client.get("/api/store/orders", headers=auth_headers_owner)
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert "total" in data
    
    def test_manager_can_get_orders(self, client, auth_headers_manager):
        """マネージャーは注文一覧を取得できる"""
        response = client.get("/api/store/orders", headers=auth_headers_manager)
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert "total" in data
    
    def test_staff_can_get_orders(self, client, auth_headers_staff):
        """スタッフは注文一覧を取得できる"""
        response = client.get("/api/store/orders", headers=auth_headers_staff)
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert "total" in data
    
    def test_owner_can_update_order_status(self, client, auth_headers_owner, db_session, customer_user_a, test_menu):
        """オーナーは注文ステータスを更新できる"""
        from models import Order
        
        # テスト用の注文を作成
        order = Order(
            user_id=customer_user_a.id,
            menu_id=test_menu.id,
            quantity=1,
            total_price=test_menu.price,
            status="pending",
            ordered_at=datetime.utcnow()
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            headers=auth_headers_owner,
            json={"status": "confirmed"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"
    
    def test_manager_can_update_order_status(self, client, auth_headers_manager, db_session, customer_user_a, test_menu):
        """マネージャーは注文ステータスを更新できる"""
        from models import Order
        
        # テスト用の注文を作成
        order = Order(
            user_id=customer_user_a.id,
            menu_id=test_menu.id,
            quantity=1,
            total_price=test_menu.price,
            status="pending",
            ordered_at=datetime.utcnow()
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            headers=auth_headers_manager,
            json={"status": "confirmed"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"
    
    def test_staff_can_update_order_status(self, client, auth_headers_staff, db_session, customer_user_a, test_menu):
        """スタッフは注文ステータスを更新できる"""
        from models import Order
        
        # テスト用の注文を作成
        order = Order(
            user_id=customer_user_a.id,
            menu_id=test_menu.id,
            quantity=1,
            total_price=test_menu.price,
            status="pending",
            ordered_at=datetime.utcnow()
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        response = client.put(
            f"/api/store/orders/{order.id}/status",
            headers=auth_headers_staff,
            json={"status": "confirmed"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"


class TestMenusReadRBAC:
    """メニュー閲覧エンドポイントのRBACテスト"""
    
    def test_owner_can_get_menus(self, client, auth_headers_owner):
        """オーナーはメニュー一覧を取得できる"""
        response = client.get("/api/store/menus", headers=auth_headers_owner)
        assert response.status_code == 200
        data = response.json()
        assert "menus" in data
        assert "total" in data
    
    def test_manager_can_get_menus(self, client, auth_headers_manager):
        """マネージャーはメニュー一覧を取得できる"""
        response = client.get("/api/store/menus", headers=auth_headers_manager)
        assert response.status_code == 200
        data = response.json()
        assert "menus" in data
        assert "total" in data
    
    def test_staff_can_get_menus(self, client, auth_headers_staff):
        """スタッフはメニュー一覧を取得できる"""
        response = client.get("/api/store/menus", headers=auth_headers_staff)
        assert response.status_code == 200
        data = response.json()
        assert "menus" in data
        assert "total" in data


class TestMenusCreateRBAC:
    """メニュー作成エンドポイントのRBACテスト"""
    
    def test_owner_can_create_menu(self, client, auth_headers_owner):
        """オーナーはメニューを作成できる"""
        menu_data = {
            "name": "新しい弁当",
            "price": 1000,
            "description": "テスト用の弁当",
            "image_url": "https://example.com/test.jpg",
            "is_available": True
        }
        response = client.post("/api/store/menus", headers=auth_headers_owner, json=menu_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "新しい弁当"
        assert data["price"] == 1000
    
    def test_manager_can_create_menu(self, client, auth_headers_manager):
        """マネージャーはメニューを作成できる"""
        menu_data = {
            "name": "マネージャーの弁当",
            "price": 1200,
            "description": "マネージャーが作成したメニュー",
            "image_url": "https://example.com/manager.jpg",
            "is_available": True
        }
        response = client.post("/api/store/menus", headers=auth_headers_manager, json=menu_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "マネージャーの弁当"
        assert data["price"] == 1200
    
    def test_staff_cannot_create_menu(self, client, auth_headers_staff):
        """スタッフはメニューを作成できない (403エラー)"""
        menu_data = {
            "name": "スタッフの弁当",
            "price": 800,
            "description": "スタッフが作成しようとしたメニュー",
            "image_url": "https://example.com/staff.jpg",
            "is_available": True
        }
        response = client.post("/api/store/menus", headers=auth_headers_staff, json=menu_data)
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]


class TestMenusUpdateRBAC:
    """メニュー更新エンドポイントのRBACテスト"""
    
    def test_owner_can_update_menu(self, client, auth_headers_owner, test_menu):
        """オーナーはメニューを更新できる"""
        update_data = {
            "name": "更新された弁当",
            "price": 1500
        }
        response = client.put(f"/api/store/menus/{test_menu.id}", headers=auth_headers_owner, json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新された弁当"
        assert data["price"] == 1500
    
    def test_manager_can_update_menu(self, client, auth_headers_manager, test_menu):
        """マネージャーはメニューを更新できる"""
        update_data = {
            "name": "マネージャー更新",
            "price": 1600
        }
        response = client.put(f"/api/store/menus/{test_menu.id}", headers=auth_headers_manager, json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "マネージャー更新"
        assert data["price"] == 1600
    
    def test_staff_cannot_update_menu(self, client, auth_headers_staff, test_menu):
        """スタッフはメニューを更新できない (403エラー)"""
        update_data = {
            "name": "スタッフ更新",
            "price": 900
        }
        response = client.put(f"/api/store/menus/{test_menu.id}", headers=auth_headers_staff, json=update_data)
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]


class TestMenusDeleteRBAC:
    """メニュー削除エンドポイントのRBACテスト"""
    
    def test_owner_can_delete_menu(self, client, auth_headers_owner, db_session):
        """オーナーはメニューを削除できる"""
        from models import Menu
        
        # テスト用メニューを作成
        menu = Menu(
            name="削除テスト弁当",
            price=1000,
            description="削除テスト用",
            image_url="https://example.com/delete.jpg",
            is_available=True
        )
        db_session.add(menu)
        db_session.commit()
        db_session.refresh(menu)
        
        response = client.delete(f"/api/store/menus/{menu.id}", headers=auth_headers_owner)
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"] or "disabled" in response.json()["message"]
    
    def test_manager_cannot_delete_menu(self, client, auth_headers_manager, test_menu):
        """マネージャーはメニューを削除できない (403エラー)"""
        response = client.delete(f"/api/store/menus/{test_menu.id}", headers=auth_headers_manager)
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]
    
    def test_staff_cannot_delete_menu(self, client, auth_headers_staff, test_menu):
        """スタッフはメニューを削除できない (403エラー)"""
        response = client.delete(f"/api/store/menus/{test_menu.id}", headers=auth_headers_staff)
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]


class TestSalesReportRBAC:
    """売上レポートエンドポイントのRBACテスト"""
    
    def test_owner_can_view_sales_report(self, client, auth_headers_owner):
        """オーナーは売上レポートを閲覧できる"""
        response = client.get("/api/store/reports/sales", headers=auth_headers_owner)
        assert response.status_code == 200
        data = response.json()
        assert "total_sales" in data
        assert "total_orders" in data
        assert "daily_reports" in data
    
    def test_manager_can_view_sales_report(self, client, auth_headers_manager):
        """マネージャーは売上レポートを閲覧できる"""
        response = client.get("/api/store/reports/sales", headers=auth_headers_manager)
        assert response.status_code == 200
        data = response.json()
        assert "total_sales" in data
        assert "total_orders" in data
        assert "daily_reports" in data
    
    def test_staff_cannot_view_sales_report(self, client, auth_headers_staff):
        """スタッフは売上レポートを閲覧できない (403エラー)"""
        response = client.get("/api/store/reports/sales", headers=auth_headers_staff)
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]
