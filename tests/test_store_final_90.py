"""
90%達成のための最終テスト - エラーパス特化
"""

import pytest
from io import BytesIO


class TestImageUploadErrors:
    """画像アップロードのエラーケース"""
    
    def test_upload_invalid_file_extension(
        self,
        client,
        auth_headers_store
    ):
        """
        無効な拡張子のファイルをアップロード
        """
        # テキストファイル(.txt)を試す
        file_data = BytesIO(b"not an image")
        files = {
            "file": ("document.txt", file_data, "text/plain")
        }
        
        response = client.post(
            "/api/store/profile/image",
            headers=auth_headers_store,
            files=files
        )
        
        # 400エラー: 無効なファイルタイプ
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]
    
    def test_upload_with_exe_extension(
        self,
        client,
        auth_headers_store
    ):
        """
        実行ファイル形式でアップロード試行
        """
        file_data = BytesIO(b"fake exe")
        files = {
            "file": ("malicious.exe", file_data, "application/x-msdownload")
        }
        
        response = client.post(
            "/api/store/profile/image",
            headers=auth_headers_store,
            files=files
        )
        
        # 400エラー
        assert response.status_code == 400


class TestMenuCreationValidation:
    """メニュー作成のバリデーション"""
    
    def test_create_menu_with_missing_required_fields(
        self,
        client,
        auth_headers_store
    ):
        """
        必須フィールドなしでメニュー作成
        """
        response = client.post(
            "/api/store/menus",
            headers=auth_headers_store,
            json={}  # 空のペイロード
        )
        
        # 422 バリデーションエラー
        assert response.status_code == 422


class TestOrderFilteringComplete:
    """注文フィルタリングの完全テスト"""
    
    def test_filter_with_start_date_only(
        self,
        client,
        auth_headers_store
    ):
        """
        開始日のみでフィルタ
        """
        response = client.get(
            "/api/store/orders?start_date=2025-01-01",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
    
    def test_filter_with_end_date_only(
        self,
        client,
        auth_headers_store
    ):
        """
        終了日のみでフィルタ
        """
        response = client.get(
            "/api/store/orders?end_date=2025-12-31",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data


class TestSalesReportComplete:
    """売上レポートの完全テスト"""
    
    def test_sales_report_menu_aggregation(
        self,
        client,
        auth_headers_store,
        orders_for_customer_a
    ):
        """
        メニュー別売上集計
        """
        response = client.get(
            "/api/store/reports/sales",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "menu_reports" in data
        
        # メニューレポートがある場合、構造を確認
        if len(data["menu_reports"]) > 0:
            menu_report = data["menu_reports"][0]
            assert "menu_id" in menu_report
            assert "menu_name" in menu_report
            assert "total_quantity" in menu_report
            assert "total_sales" in menu_report


class TestImageDeletionComplete:
    """画像削除の完全テスト"""
    
    def test_delete_image_with_external_url(
        self,
        client,
        auth_headers_store,
        db_session,
        store_a
    ):
        """
        外部URLの画像削除（ファイル削除しない）
        """
        # 外部URLを設定
        store_a.image_url = "https://example.com/image.jpg"
        db_session.commit()
        
        response = client.delete(
            "/api/store/profile/image",
            headers=auth_headers_store
        )
        
        # 成功（外部URLはファイル削除スキップ）
        assert response.status_code == 200
        data = response.json()
        assert data["image_url"] is None
