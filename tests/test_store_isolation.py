"""
マルチテナントデータ分離テスト

店舗間のデータ分離が正しく機能していることを検証するセキュリティテスト。
他店舗のデータに一切アクセスできないことを確認します。
"""

import pytest
from fastapi import status


class TestOrderIsolation:
    """注文データの店舗間分離テスト"""
    
    def test_store_a_cannot_get_store_b_order_status(
        self, client, auth_headers_owner_store_a, order_store_b
    ):
        """
        【セキュリティテスト】店舗Aユーザーが店舗Bの注文ステータスを更新できないこと
        
        悪意のあるユーザーが他店舗の注文IDを推測してステータス変更を試みるケースを想定
        """
        # 店舗Aのユーザーで店舗Bの注文のステータス更新を試みる
        response = client.put(
            f"/api/store/orders/{order_store_b.id}/status",
            json={"status": "completed"},
            headers=auth_headers_owner_store_a
        )
        
        # 404 または 403 を期待（注文が見つからない、またはアクセス拒否）
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ], f"Expected 403 or 404, got {response.status_code}"
    
    def test_store_b_cannot_get_store_a_order_status(
        self, client, auth_headers_owner_store_b, order_store_a
    ):
        """
        【セキュリティテスト】店舗Bユーザーが店舗Aの注文ステータスを更新できないこと
        
        逆方向のアクセス制御も検証
        """
        # 店舗Bのユーザーで店舗Aの注文のステータス更新を試みる
        response = client.put(
            f"/api/store/orders/{order_store_a.id}/status",
            json={"status": "cancelled"},
            headers=auth_headers_owner_store_b
        )
        
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ], f"Expected 403 or 404, got {response.status_code}"
    
    def test_order_list_contains_only_own_store_orders(
        self, client, auth_headers_owner_store_a, order_store_a, order_store_b
    ):
        """
        【セキュリティテスト】注文一覧APIで他店舗の注文が含まれないこと
        
        一覧取得時のデータ漏洩を検証
        """
        # 店舗Aのユーザーで注文一覧を取得
        response = client.get(
            "/api/store/orders",
            headers=auth_headers_owner_store_a
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # レスポンスに注文が含まれている場合
        if data["total"] > 0:
            order_ids = [order["id"] for order in data["orders"]]
            
            # 店舗Aの注文は含まれているべき
            assert order_store_a.id in order_ids, "Own store order should be included"
            
            # 店舗Bの注文は含まれていないべき
            assert order_store_b.id not in order_ids, "Other store order should NOT be included"
            
            # すべての注文がstore_id一致していることを確認
            for order in data["orders"]:
                assert order.get("store_id") == order_store_a.store_id, \
                    f"Order {order['id']} has wrong store_id"
    
    def test_order_list_isolation_with_multiple_orders(
        self, client, db_session, auth_headers_owner_store_a, 
        menu_store_a, menu_store_b, store_a, store_b,
        customer_user_a, customer_user_b
    ):
        """
        【セキュリティテスト】複数注文がある場合のデータ分離
        
        大量データでのフィルタリング漏れを検証
        """
        from models import Order
        from datetime import datetime
        
        # 店舗Aに3つの注文を作成
        for i in range(3):
            order = Order(
                user_id=customer_user_a.id,
                menu_id=menu_store_a.id,
                store_id=store_a.id,
                quantity=1,
                total_price=850,
                status="pending",
                ordered_at=datetime.utcnow(),
                notes=f"店舗A注文{i+1}"
            )
            db_session.add(order)
        
        # 店舗Bにも3つの注文を作成
        for i in range(3):
            order = Order(
                user_id=customer_user_b.id,
                menu_id=menu_store_b.id,
                store_id=store_b.id,
                quantity=1,
                total_price=900,
                status="pending",
                ordered_at=datetime.utcnow(),
                notes=f"店舗B注文{i+1}"
            )
            db_session.add(order)
        
        db_session.commit()
        
        # 店舗Aのユーザーで注文一覧を取得
        response = client.get(
            "/api/store/orders",
            headers=auth_headers_owner_store_a
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # 店舗Aの注文のみが含まれることを確認
        for order in data["orders"]:
            assert order["store_id"] == store_a.id, \
                f"Found order from wrong store: {order}"
            assert "店舗B" not in order.get("notes", ""), \
                "Store B order leaked into Store A's list"


class TestMenuIsolation:
    """メニューデータの店舗間分離テスト"""
    
    def test_store_a_cannot_update_store_b_menu(
        self, client, auth_headers_owner_store_a, menu_store_b
    ):
        """
        【セキュリティテスト】店舗Aユーザーが店舗Bのメニューを更新できないこと
        
        他店舗のメニューIDを指定した更新リクエストを送信
        """
        response = client.put(
            f"/api/store/menus/{menu_store_b.id}",
            json={
                "name": "乗っ取られたメニュー",
                "price": 1
            },
            headers=auth_headers_owner_store_a
        )
        
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ], f"Expected 403 or 404, got {response.status_code}"
    
    def test_store_b_cannot_delete_store_a_menu(
        self, client, auth_headers_owner_store_b, menu_store_a
    ):
        """
        【セキュリティテスト】店舗Bユーザーが店舗Aのメニューを削除できないこと
        
        他店舗のメニュー削除を試みる
        """
        response = client.delete(
            f"/api/store/menus/{menu_store_a.id}",
            headers=auth_headers_owner_store_b
        )
        
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ], f"Expected 403 or 404, got {response.status_code}"
    
    def test_menu_list_contains_only_own_store_menus(
        self, client, auth_headers_owner_store_a, menu_store_a, menu_store_b
    ):
        """
        【セキュリティテスト】メニュー一覧APIで他店舗のメニューが含まれないこと
        """
        response = client.get(
            "/api/store/menus",
            headers=auth_headers_owner_store_a
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        if data["total"] > 0:
            menu_ids = [menu["id"] for menu in data["menus"]]
            
            # 店舗Aのメニューは含まれているべき
            assert menu_store_a.id in menu_ids, "Own store menu should be included"
            
            # 店舗Bのメニューは含まれていないべき
            assert menu_store_b.id not in menu_ids, "Other store menu should NOT be included"
            
            # すべてのメニューのstore_idが一致していることを確認
            for menu in data["menus"]:
                assert menu.get("store_id") == menu_store_a.store_id, \
                    f"Menu {menu['id']} has wrong store_id"
    
    def test_created_menu_has_correct_store_id(
        self, client, db_session, auth_headers_owner_store_a, store_a
    ):
        """
        【セキュリティテスト】メニュー作成時に正しいstore_idが設定されること
        
        ユーザーが意図的に他店舗のstore_idを指定しても無視されることを確認
        """
        from models import Menu
        
        # メニュー作成（store_idは指定しない、またはbackendで上書きされる）
        response = client.post(
            "/api/store/menus",
            json={
                "name": "新規メニュー",
                "price": 1000,
                "description": "テスト",
                "is_available": True
            },
            headers=auth_headers_owner_store_a
        )
        
        assert response.status_code == status.HTTP_200_OK
        created_menu = response.json()
        
        # 作成されたメニューのstore_idがログインユーザーの店舗と一致することを確認
        menu = db_session.query(Menu).filter(Menu.id == created_menu["id"]).first()
        assert menu.store_id == store_a.id, \
            "Created menu should have the store_id of the authenticated user's store"


class TestDashboardIsolation:
    """ダッシュボードデータの店舗間分離テスト"""
    
    def test_dashboard_shows_only_own_store_data(
        self, client, db_session, auth_headers_owner_store_a,
        menu_store_a, menu_store_b, store_a, store_b,
        customer_user_a, customer_user_b
    ):
        """
        【セキュリティテスト】ダッシュボードに他店舗のデータが含まれないこと
        
        売上、注文数などの集計データの分離を検証
        """
        from models import Order
        from datetime import datetime, date
        
        today = date.today()
        
        # 店舗Aの注文を作成（本日）
        order_a = Order(
            user_id=customer_user_a.id,
            menu_id=menu_store_a.id,
            store_id=store_a.id,
            quantity=2,
            total_price=1700,  # 850 * 2
            status="completed",
            ordered_at=datetime.combine(today, datetime.min.time()),
            notes="店舗A本日注文"
        )
        db_session.add(order_a)
        
        # 店舗Bの注文を作成（本日）
        order_b = Order(
            user_id=customer_user_b.id,
            menu_id=menu_store_b.id,
            store_id=store_b.id,
            quantity=5,
            total_price=4500,  # 900 * 5
            status="completed",
            ordered_at=datetime.combine(today, datetime.min.time()),
            notes="店舗B本日注文"
        )
        db_session.add(order_b)
        db_session.commit()
        
        # 店舗Aのダッシュボードを取得
        response = client.get(
            "/api/store/dashboard",
            headers=auth_headers_owner_store_a
        )
        
        assert response.status_code == status.HTTP_200_OK
        dashboard = response.json()
        
        # 店舗Aのデータのみが反映されていることを確認
        # 総売上は1700であるべき（店舗Bの4500は含まれない）
        assert dashboard["total_sales"] == 1700, \
            f"Dashboard shows wrong sales: {dashboard['total_sales']}, expected 1700"
        
        # 注文数も店舗Aの分のみ
        assert dashboard["total_orders"] >= 1, "Should have at least store A's order"


class TestSalesReportIsolation:
    """売上レポートの店舗間分離テスト"""
    
    def test_sales_report_contains_only_own_store_data(
        self, client, db_session, auth_headers_owner_store_a,
        menu_store_a, menu_store_b, store_a, store_b,
        customer_user_a, customer_user_b
    ):
        """
        【セキュリティテスト】売上レポートに他店舗のデータが含まれないこと
        
        日別売上、メニュー別売上などの詳細レポートの分離を検証
        """
        from models import Order
        from datetime import datetime, timedelta
        
        # 過去7日間のテストデータを作成
        for days_ago in range(7):
            order_date = datetime.utcnow() - timedelta(days=days_ago)
            
            # 店舗Aの注文
            order_a = Order(
                user_id=customer_user_a.id,
                menu_id=menu_store_a.id,
                store_id=store_a.id,
                quantity=1,
                total_price=850,
                status="completed",
                ordered_at=order_date,
                notes=f"店舗A {days_ago}日前"
            )
            db_session.add(order_a)
            
            # 店舗Bの注文（より高額）
            order_b = Order(
                user_id=customer_user_b.id,
                menu_id=menu_store_b.id,
                store_id=store_b.id,
                quantity=10,
                total_price=9000,
                status="completed",
                ordered_at=order_date,
                notes=f"店舗B {days_ago}日前"
            )
            db_session.add(order_b)
        
        db_session.commit()
        
        # 店舗Aの売上レポートを取得
        response = client.get(
            "/api/store/reports/sales?days=7",
            headers=auth_headers_owner_store_a
        )
        
        assert response.status_code == status.HTTP_200_OK
        report = response.json()
        
        # 総売上が店舗Aの金額のみであることを確認
        # 7日 × 850円 = 5950円
        expected_sales = 850 * 7
        assert report["total_sales"] == expected_sales, \
            f"Report shows wrong sales: {report['total_sales']}, expected {expected_sales}"
        
        # 日別売上もチェック
        for daily_report in report.get("daily_sales", []):
            # 各日の売上は850円であるべき（店舗Bの9000円は含まれない）
            assert daily_report["sales"] == 850, \
                f"Daily sales leaked: {daily_report}"


class TestCrossStoreAccessDenied:
    """クロスストアアクセス拒否の総合テスト"""
    
    def test_manager_cannot_access_other_store_data(
        self, client, auth_headers_manager_store_a, order_store_b, menu_store_b
    ):
        """
        【セキュリティテスト】マネージャーも他店舗データにアクセスできないこと
        
        オーナーだけでなく、マネージャー権限でも分離が機能することを確認
        """
        # 注文ステータス更新を試みる
        response = client.put(
            f"/api/store/orders/{order_store_b.id}/status",
            json={"status": "completed"},
            headers=auth_headers_manager_store_a
        )
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        
        # メニュー更新を試みる
        response = client.put(
            f"/api/store/menus/{menu_store_b.id}",
            json={"name": "不正更新", "price": 1},
            headers=auth_headers_manager_store_a
        )
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
    
    def test_staff_cannot_access_other_store_data(
        self, client, auth_headers_staff_store_a, order_store_b
    ):
        """
        【セキュリティテスト】スタッフも他店舗データにアクセスできないこと
        
        最も権限の低いスタッフでも分離が機能することを確認
        """
        # 注文ステータス更新を試みる
        response = client.put(
            f"/api/store/orders/{order_store_b.id}/status",
            json={"status": "completed"},
            headers=auth_headers_staff_store_a
        )
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
    
    def test_no_data_leakage_in_error_messages(
        self, client, auth_headers_owner_store_a, menu_store_b
    ):
        """
        【セキュリティテスト】エラーメッセージから他店舗データが漏洩しないこと
        
        404エラーのメッセージに他店舗の存在を示唆する情報が含まれないことを確認
        """
        response = client.put(
            f"/api/store/menus/{menu_store_b.id}",
            json={"name": "test", "price": 100},
            headers=auth_headers_owner_store_a
        )
        
        # 404を返すべき（403ではなく、リソースの存在自体を隠す）
        # または、403を返しても他店舗の詳細情報は含めない
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        
        error_detail = response.json().get("detail", "")
        
        # エラーメッセージに他店舗の名前やIDが含まれていないことを確認
        assert "店舗B" not in error_detail, "Error message should not reveal other store info"
        assert str(menu_store_b.store_id) not in error_detail, "Error message should not reveal store_id"
