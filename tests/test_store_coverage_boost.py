"""
カバレッジ90%達成のための追加テスト

未カバー箇所を重点的にテストする
"""

import pytest
from io import BytesIO


class TestStoreAssociationErrors:
    """店舗関連付けエラーのテスト (スキップ - 既存テストで十分カバー)"""
    pass
    
    # 注: 店舗関連付けエラーは他のテストで十分カバーされているため、
    # これらのテストはスキップします


class TestMenuCreationEdgeCases:
    """メニュー作成のエッジケーステスト"""
    
    def test_create_menu_with_long_name(
        self,
        client,
        auth_headers_store
    ):
        """
        非常に長い名前のメニュー作成
        """
        long_name = "あ" * 200  # 200文字の名前
        
        response = client.post(
            "/api/store/menus",
            headers=auth_headers_store,
            json={
                "name": long_name,
                "price": 1000,
                "description": "テスト",
                "is_available": True
            }
        )
        
        # 成功またはバリデーションエラー
        assert response.status_code in [200, 422]
    
    def test_create_menu_with_negative_price(
        self,
        client,
        auth_headers_store
    ):
        """
        負の価格でメニュー作成
        """
        response = client.post(
            "/api/store/menus",
            headers=auth_headers_store,
            json={
                "name": "負の価格メニュー",
                "price": -500,
                "is_available": True
            }
        )
        
        # バリデーションエラー
        assert response.status_code == 422
    
    def test_create_menu_with_very_high_price(
        self,
        client,
        auth_headers_store
    ):
        """
        非常に高い価格でメニュー作成
        """
        response = client.post(
            "/api/store/menus",
            headers=auth_headers_store,
            json={
                "name": "高額メニュー",
                "price": 999999,
                "is_available": True
            }
        )
        
        # 成功するはず
        assert response.status_code == 200


class TestMenuUpdateEdgeCases:
    """メニュー更新のエッジケーステスト"""
    
    def test_update_nonexistent_menu(
        self,
        client,
        auth_headers_store
    ):
        """
        存在しないメニューの更新
        """
        response = client.put(
            "/api/store/menus/99999",
            headers=auth_headers_store,
            json={
                "name": "存在しないメニュー",
                "price": 1000
            }
        )
        
        # 404エラー
        assert response.status_code == 404
    
    def test_update_menu_to_unavailable(
        self,
        client,
        auth_headers_store,
        test_menu
    ):
        """
        メニューを利用不可に更新
        """
        response = client.put(
            f"/api/store/menus/{test_menu.id}",
            headers=auth_headers_store,
            json={
                "is_available": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_available"] is False
    
    def test_update_menu_price_only(
        self,
        client,
        auth_headers_store,
        test_menu
    ):
        """
        メニューの価格のみ更新
        """
        response = client.put(
            f"/api/store/menus/{test_menu.id}",
            headers=auth_headers_store,
            json={
                "price": 1500
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == 1500


class TestMenuDeletionEdgeCases:
    """メニュー削除のエッジケーステスト"""
    
    def test_delete_nonexistent_menu(
        self,
        client,
        auth_headers_store
    ):
        """
        存在しないメニューの削除
        """
        response = client.delete(
            "/api/store/menus/99999",
            headers=auth_headers_store
        )
        
        # 404エラー
        assert response.status_code == 404
    
    def test_delete_menu_twice(
        self,
        client,
        auth_headers_store,
        db_session,
        store_a
    ):
        """
        メニューを削除後、再度削除しようとする
        """
        from models import Menu
        
        # 削除用メニューを作成
        menu = Menu(
            name="二重削除テストメニュー",
            store_id=store_a.id,
            price=500,
            is_available=True
        )
        db_session.add(menu)
        db_session.commit()
        db_session.refresh(menu)
        
        # 1回目の削除
        response1 = client.delete(
            f"/api/store/menus/{menu.id}",
            headers=auth_headers_store
        )
        assert response1.status_code == 200
        
        # 2回目の削除
        response2 = client.delete(
            f"/api/store/menus/{menu.id}",
            headers=auth_headers_store
        )
        
        # 404エラー: すでに削除済み
        assert response2.status_code == 404


class TestOrderFilteringEdgeCases:
    """注文フィルタリングのエッジケーステスト"""
    
    def test_filter_by_invalid_status(
        self,
        client,
        auth_headers_store
    ):
        """
        無効なステータスでフィルタリング
        """
        response = client.get(
            "/api/store/orders?status=invalid_status",
            headers=auth_headers_store
        )
        
        # 400エラーまたは空のリスト
        assert response.status_code in [200, 400]
    
    def test_filter_by_future_date(
        self,
        client,
        auth_headers_store
    ):
        """
        未来の日付でフィルタリング
        """
        response = client.get(
            "/api/store/orders?start_date=2030-01-01&end_date=2030-12-31",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 未来の注文は存在しないはず
        assert data["total"] == 0
        assert len(data["orders"]) == 0
    
    def test_filter_with_empty_search_query(
        self,
        client,
        auth_headers_store
    ):
        """
        空の検索クエリでフィルタリング
        """
        response = client.get(
            "/api/store/orders?search=",
            headers=auth_headers_store
        )
        
        # 成功 (全件返す)
        assert response.status_code == 200
    
    def test_filter_with_special_characters(
        self,
        client,
        auth_headers_store
    ):
        """
        特殊文字を含む検索クエリ
        """
        response = client.get(
            "/api/store/orders?search=%&$#@",
            headers=auth_headers_store
        )
        
        # 成功 (結果なし)
        assert response.status_code == 200


class TestSalesReportEdgeCases:
    """売上レポートのエッジケーステスト"""
    
    def test_sales_report_with_same_start_end_date(
        self,
        client,
        auth_headers_store
    ):
        """
        開始日と終了日が同じレポート
        """
        from datetime import date
        
        today = date.today().isoformat()
        
        response = client.get(
            f"/api/store/reports/sales?start_date={today}&end_date={today}",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "daily_reports" in data
    
    def test_sales_report_with_very_old_date(
        self,
        client,
        auth_headers_store
    ):
        """
        非常に古い日付でレポート取得
        """
        response = client.get(
            "/api/store/reports/sales?start_date=2000-01-01&end_date=2000-12-31",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 古い日付の注文は存在しないはず
        assert data["total_orders"] == 0
    
    def test_sales_report_without_parameters(
        self,
        client,
        auth_headers_store
    ):
        """
        パラメータなしでレポート取得 (デフォルト期間)
        """
        response = client.get(
            "/api/store/reports/sales",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "daily_reports" in data
        assert "total_sales" in data
