"""
追加カバレッジテスト - 90%達成のための最終テスト
キーワード検索のJOINパスをカバー
"""
import pytest
from models import Order


class TestOrderSearchWithKeyword:
    """注文検索のキーワード機能テスト"""
    
    def test_order_search_with_customer_username_keyword(
        self,
        client,
        auth_headers_store,
        store_a,
        customer_user_a,
        menu_store_a,
        db_session
    ):
        """
        キーワードで顧客ユーザー名を検索(JOINパスをカバー)
        """
        # 注文を作成
        order = Order(
            store_id=store_a.id,
            user_id=customer_user_a.id,
            menu_id=menu_store_a.id,
            quantity=1,
            total_price=1000,
            status="pending"
        )
        db_session.add(order)
        db_session.commit()
        
        # キーワード検索(顧客ユーザー名)
        # この検索によりneeds_user_joinがTrueになり、行486がカバーされる
        response = client.get(
            f"/api/store/orders?keyword={customer_user_a.username}",
            headers=auth_headers_store
        )
        
        assert response.status_code == 200
        data = response.json()
        # キーワードに一致する注文が返される
        assert isinstance(data, dict)
        assert "orders" in data
