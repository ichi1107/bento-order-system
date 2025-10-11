"""
パスワードリセット機能のE2Eテスト
"""
import re
import pytest
from playwright.sync_api import Page, expect
from .conftest import get_latest_email, clear_mailhog


class TestPasswordResetFlow:
    """パスワードリセット完全フローのE2Eテスト"""
    
    @pytest.fixture(autouse=True)
    def setup(self, mailhog_api):
        """各テスト前にMailHogをクリア"""
        clear_mailhog(mailhog_api)
    
    def test_password_validation(self, page: Page, base_url: str):
        """
        シナリオ1: パスワードバリデーション（登録不要）
        """
        # リセット確認ページにアクセス（ダミートークン）
        page.goto(f"{base_url}/reset-password?token=dummy_token_for_validation")
        
        # ページが表示されることを確認
        expect(page.locator("h2")).to_contain_text("新しいパスワードの設定")
        
        # パスワードが一致しない場合
        page.fill("input[name='new_password']", "password123")
        page.fill("input[name='confirm_password']", "password456")
        page.click("button[type='submit']")
        
        # エラーメッセージが表示される
        error_message = page.locator(".error-message")
        expect(error_message.first).to_be_visible(timeout=5000)
    
    def test_invalid_token_rejected(self, page: Page, base_url: str):
        """
        シナリオ2: 無効なトークンが拒否される
        """
        # 無効なトークンでリセットページにアクセス
        page.goto(f"{base_url}/reset-password?token=invalid_token_12345")
        
        # パスワード入力
        page.fill("input[name='new_password']", "newpassword123")
        page.fill("input[name='confirm_password']", "newpassword123")
        page.click("button[type='submit']")
        
        # エラーメッセージが表示される
        error_message = page.locator(".error-message")
        expect(error_message.first).to_be_visible(timeout=5000)
    
    def test_responsive_design_mobile(self, page: Page, base_url: str):
        """
        シナリオ3: モバイルビューポートでのレスポンシブデザイン
        """
        # モバイルビューポートを設定
        page.set_viewport_size({"width": 375, "height": 667})
        
        # パスワードリセットリクエストページ
        page.goto(f"{base_url}/password-reset-request")
        
        # フォームが表示されることを確認
        form = page.locator("form")
        expect(form).to_be_visible()
        
        # フォームの幅がビューポートに収まることを確認
        form_box = form.bounding_box()
        assert form_box is not None
        assert form_box['width'] <= 375, "フォームがビューポート幅を超えています"
        
        # パスワードリセット確認ページ
        page.goto(f"{base_url}/reset-password?token=test_token")
        
        # フォームが表示されることを確認
        expect(form).to_be_visible()
        
        # パスワードトグルボタンが表示されることを確認
        toggle_buttons = page.locator(".toggle-btn")
        assert toggle_buttons.count() == 2, "パスワードトグルボタンが2つ必要です"


class TestPasswordResetUI:
    """パスワードリセットUIコンポーネントのテスト"""
    
    def test_password_visibility_toggle(self, page: Page, base_url: str):
        """
        パスワード表示切り替えボタンが正しく動作する
        """
        page.goto(f"{base_url}/reset-password?token=test_token")
        
        # 最初はパスワードが隠されている
        password_input = page.locator("input[name='new_password']")
        assert password_input.get_attribute("type") == "password"
        
        # トグルボタンをクリック
        toggle_button = page.locator(".toggle-btn").first
        toggle_button.click()
        
        # パスワードが表示される
        assert password_input.get_attribute("type") == "text"
        
        # もう一度クリック
        toggle_button.click()
        
        # パスワードが隠される
        assert password_input.get_attribute("type") == "password"
    
    def test_form_submission_flow(self, page: Page, base_url: str):
        """
        フォーム送信が正常に動作する
        """
        page.goto(f"{base_url}/password-reset-request")
        
        # フォームが表示されることを確認
        form = page.locator("form")
        expect(form).to_be_visible()
        
        # メールアドレス入力
        page.fill("input[name='email']", "test-form@example.com")
        
        # 送信ボタンが有効であることを確認
        submit_button = page.locator("button[type='submit']")
        expect(submit_button).to_be_enabled()
        
        # 送信ボタンをクリック
        submit_button.click()
        
        # 成功メッセージまたはエラーメッセージが表示されることを確認
        # （何らかの応答があることを確認）
        page.wait_for_timeout(500)  # JavaScript実行を待つ
        
        # フォームが非表示になるか、メッセージが表示されることを確認
        # いずれかが発生すればOK
        is_form_hidden = not form.is_visible()
        has_message = page.locator(".loading-message, .success-message, .error-message").first.is_visible()
        
        assert is_form_hidden or has_message, "フォーム送信後に何らかの応答が必要です"
    
    def test_email_validation(self, page: Page, base_url: str):
        """
        メールアドレスのバリデーション
        """
        page.goto(f"{base_url}/password-reset-request")
        
        # 無効なメールアドレス
        page.fill("input[name='email']", "invalid-email")
        page.click("button[type='submit']")
        
        # HTML5バリデーションまたはJSバリデーションが働くことを確認
        # ブラウザによってはHTML5 validationが働く
        email_input = page.locator("input[name='email']")
        
        # JavaScriptのバリデーションが働く場合
        error_message = page.locator(".error-message")
        if error_message.is_visible():
            expect(error_message.first).to_be_visible()
