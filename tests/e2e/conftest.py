"""
E2Eテスト用のconftest.py
"""
import pytest
from playwright.sync_api import sync_playwright
import requests
import time


@pytest.fixture(scope="session")
def browser():
    """Playwrightブラウザセッション"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    """新しいページコンテキスト"""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def base_url():
    """アプリケーションのベースURL"""
    return "http://localhost:8000"


@pytest.fixture
def mailhog_api():
    """MailHog APIのベースURL"""
    return "http://mailhog:8025/api/v2"


def get_latest_email(mailhog_api: str, recipient: str, timeout: int = 10):
    """
    MailHogから最新のメールを取得
    
    Args:
        mailhog_api: MailHog APIのURL
        recipient: 受信者のメールアドレス
        timeout: タイムアウト秒数
    
    Returns:
        メールの内容（dict）またはNone
    """
    for _ in range(timeout):
        response = requests.get(f"{mailhog_api}/messages")
        if response.status_code == 200:
            messages = response.json()
            if messages and 'items' in messages:
                # 最新のメールを取得
                for msg in messages['items']:
                    to_addresses = msg.get('Content', {}).get('Headers', {}).get('To', [])
                    if any(recipient in addr for addr in to_addresses):
                        return msg
        time.sleep(1)
    return None


def clear_mailhog(mailhog_api: str):
    """MailHogの全メールを削除"""
    requests.delete(f"{mailhog_api}/messages")
