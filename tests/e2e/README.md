# 店舗プロフィール画面 E2Eテスト

## 概要

Playwrightを使用した店舗プロフィール画面のエンドツーエンド(E2E)テストです。実際のユーザー操作をシミュレートし、以下を検証します:

- ✅ Owner権限での編集機能
- ✅ Manager/Staff権限での読み取り専用アクセス
- ✅ フォームバリデーション
- ✅ 画像アップロード機能
- ✅ ナビゲーション
- ✅ 認証・認可

## セットアップ

### 1. 依存関係のインストール

```bash
# Pythonパッケージをインストール
pip install -r requirements.txt

# Playwrightブラウザをインストール
playwright install chromium
```

### 2. アプリケーションの起動

E2Eテストを実行する前に、アプリケーションが起動している必要があります:

```bash
# Dockerで起動
docker-compose up -d

# アプリケーションが起動するまで待機
sleep 10
```

### 3. テストデータのセットアップ

```bash
# テストユーザーと店舗を作成
docker-compose exec web python setup_store_data.py
```

## テスト実行

### すべてのE2Eテストを実行

```bash
# ヘッドレスモードで実行
pytest tests/e2e/test_store_profile.py -v

# マーカーでフィルタ
pytest tests/e2e/test_store_profile.py -m e2e -v
```

### 特定のテストのみ実行

```bash
# Owner編集テストのみ
pytest tests/e2e/test_store_profile.py::TestStoreProfileE2E::test_owner_can_view_and_edit_store_profile -v

# Manager読み取り専用テストのみ
pytest tests/e2e/test_store_profile.py::TestStoreProfileE2E::test_manager_has_readonly_access_to_store_profile -v

# バリデーションテストのみ
pytest tests/e2e/test_store_profile.py -k "validation" -v
```

### ヘッド付きモード（デバッグ用）

ブラウザの動作を目視確認したい場合:

```bash
# conftest.pyでheadless=Falseに変更
# または環境変数で制御
HEADED=1 pytest tests/e2e/test_store_profile.py -v
```

### カバレッジ付きで実行

```bash
pytest tests/e2e/test_store_profile.py --cov=. --cov-report=html -v
```

## テストシナリオ

### 1. Owner権限のテスト

#### `test_owner_can_view_and_edit_store_profile`
- 店舗プロフィールページにアクセス
- すべてのフィールドが編集可能であることを確認
- 情報を更新
- 成功メッセージを確認
- 変更が保持されることを確認

#### `test_owner_can_upload_store_image`
- 画像アップロードボタンが表示されることを確認

### 2. Manager権限のテスト

#### `test_manager_has_readonly_access_to_store_profile`
- 店舗プロフィールページにアクセス
- すべてのフィールドが無効化されていることを確認
- 保存ボタンが表示されないことを確認
- 読み取り専用メッセージが表示されることを確認

#### `test_manager_cannot_upload_store_image`
- 画像アップロード/削除ボタンが表示されないことを確認

### 3. フォームバリデーションのテスト

#### `test_form_validation_empty_name`
- 店舗名を空にして保存
- エラーメッセージが表示されることを確認

#### `test_form_validation_description_too_long`
- 説明文に1001文字入力して保存
- エラーメッセージが表示されることを確認

### 4. ユーザーフローのテスト

#### `test_cancel_button_reverts_changes`
- フォームの値を変更
- キャンセルボタンをクリック
- 元の値に戻ることを確認

#### `test_navigation_from_dashboard`
- ダッシュボードから店舗情報リンクをクリック
- 店舗プロフィールページに遷移することを確認

#### `test_unauthorized_user_redirected_to_login`
- 未ログイン状態で店舗プロフィールにアクセス
- ログインページにリダイレクトされることを確認

### 5. 機能テスト

#### `test_business_hours_validation`
- 営業時間を設定
- 正しく保存されることを確認

#### `test_active_status_toggle`
- 営業中/休業中ステータスを切り替え
- 変更が保存されることを確認

## テストデータ

テストで使用するユーザー:

| ユーザー名 | パスワード | 役割 |
|----------|----------|------|
| store1 | password123 | owner |
| store2 | password123 | manager |
| admin | admin@123 | owner |

## トラブルシューティング

### テストが失敗する場合

1. **アプリケーションが起動していない**
   ```bash
   docker-compose ps
   docker-compose logs web
   ```

2. **テストデータが存在しない**
   ```bash
   docker-compose exec web python setup_store_data.py
   ```

3. **ポートが使用されている**
   ```bash
   # 8000番ポートを使用しているプロセスを確認
   netstat -ano | findstr :8000
   ```

4. **Playwrightブラウザがインストールされていない**
   ```bash
   playwright install chromium
   ```

### デバッグモード

テスト失敗時のスクリーンショットとトレースを有効化:

```python
# conftest.pyに追加
@pytest.fixture(scope="function")
def context(browser):
    context = browser.new_context(
        record_video_dir="test-results/videos",
        record_video_size={"width": 1280, "height": 720}
    )
    yield context
    context.close()
```

### スローモーション実行

テストの動作をゆっくり確認:

```python
# conftest.pyで調整
browser = playwright.chromium.launch(
    headless=False,
    slow_mo=1000  # 各操作を1秒遅延
)
```

## CI/CD統合

### GitHub Actions例

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      
      - name: Start application
        run: |
          docker-compose up -d
          sleep 10
      
      - name: Setup test data
        run: docker-compose exec -T web python setup_store_data.py
      
      - name: Run E2E tests
        run: pytest tests/e2e/test_store_profile.py -v
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results/
```

## ベストプラクティス

1. **各テストは独立させる**: テスト間で状態を共有しない
2. **明示的な待機を使用**: `page.wait_for_selector()`や`expect().to_be_visible()`
3. **セレクタは安定させる**: data-testid属性を使用
4. **テストデータをクリーンアップ**: 各テスト後に元の状態に戻す
5. **タイムアウトを適切に設定**: ネットワーク遅延を考慮

## 参考資料

- [Playwright Documentation](https://playwright.dev/python/)
- [pytest Documentation](https://docs.pytest.org/)
- [E2E Testing Best Practices](https://playwright.dev/python/docs/best-practices)
