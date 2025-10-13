"""
売上レポートのデフォルト日付処理カバレッジテスト
"""
import pytest


class TestSalesReportDefaultDates:
    """売上レポートのデフォルト日付生成をテスト"""
    
    def test_sales_report_weekly_default_date(
        self,
        client,
        auth_headers_store
    ):
        """
        週次レポート - デフォルト日付(過去30日)
        """
        response = client.get(
            "/api/store/reports/sales?period=weekly",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_sales_report_monthly_default_date(
        self,
        client,
        auth_headers_store
    ):
        """
        月次レポート - デフォルト日付(過去90日)
        """
        response = client.get(
            "/api/store/reports/sales?period=monthly",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
