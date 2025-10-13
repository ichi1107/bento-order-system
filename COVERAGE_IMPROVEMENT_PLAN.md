# Feature #76: 90%カバレッジ達成のための追加テスト計画

## 現在の状況
- **達成**: 36/36テスト全てパス (100%)
- **カバレッジ**: 33% / 目標90%
- **不足**: 57ポイント

## 未カバー機能の分析

### 1. 店舗プロフィール管理 (Lines 50-112)
- `GET /api/store/profile` - 店舗プロフィール取得
- `PUT /api/store/profile` - 店舗プロフィール更新

**追加テスト案**:
- `test_get_store_profile_success` - プロフィール取得成功
- `test_update_store_profile_success` - プロフィール更新成功
- `test_update_store_profile_validation` - バリデーションエラー

### 2. メニュー管理 (Lines 137-240)
- `GET /api/store/menus` - メニュー一覧
- `POST /api/store/menus` - メニュー作成
- `GET /api/store/menus/{id}` - メニュー詳細
- `PUT /api/store/menus/{id}` - メニュー更新
- `DELETE /api/store/menus/{id}` - メニュー削除
- `PUT /api/store/menus/{id}/toggle` - 有効/無効切替

**追加テスト案**:
- `test_get_menus_list` - メニュー一覧取得
- `test_create_menu_success` - メニュー作成成功
- `test_create_menu_validation_error` - バリデーションエラー
- `test_get_menu_detail` - メニュー詳細取得
- `test_update_menu_success` - メニュー更新成功
- `test_delete_menu_success` - メニュー削除成功
- `test_delete_menu_with_orders` - 注文のあるメニュー削除エラー
- `test_toggle_menu_availability` - メニュー有効/無効切替

### 3. レポート機能 (Lines 277-379, 760-934)
- `GET /api/store/reports/sales` - 売上レポート
- `GET /api/store/reports/popular-menus` - 人気メニュー
- `GET /api/store/reports/hourly-orders` - 時間別注文数

**追加テスト案**:
- `test_get_sales_report_today` - 本日の売上レポート
- `test_get_sales_report_date_range` - 期間指定売上レポート
- `test_get_popular_menus` - 人気メニューレポート
- `test_get_hourly_orders` - 時間別注文レポート

### 4. 画像アップロード (Lines 414-454)
- `POST /api/store/menus/{id}/image` - メニュー画像アップロード

**追加テスト案**:
- `test_upload_menu_image_success` - 画像アップロード成功
- `test_upload_menu_image_invalid_format` - 無効な画像形式
- `test_upload_menu_image_too_large` - ファイルサイズ超過

### 5. エラーハンドリング・エッジケース
**追加テスト案**:
- `test_access_other_store_menu` - 他店舗のメニューアクセス
- `test_unauthorized_access_to_reports` - 権限なしアクセス
- `test_invalid_date_range_reports` - 無効な日付範囲

## 実装優先度

### Phase 1: 高頻度API (推定カバレッジ +30%)
1. メニュー管理 (8テスト) - 最も重要
2. 店舗プロフィール (3テスト) - 基本機能

### Phase 2: レポート機能 (推定カバレッジ +20%)
3. 売上レポート (4テスト) - ビジネスロジック

### Phase 3: 画像アップロード (推定カバレッジ +10%)
4. 画像アップロード (3テスト) - ファイル処理

### Phase 4: エッジケース (推定カバレッジ +7%)
5. エラーハンドリング (3テスト) - 安全性

**合計推定**: +67ポイント → 目標100% (実際は90%を目指す)

## 実装スケジュール

### 即時実行 (30分)
- Phase 1のテスト実装 → カバレッジ63%到達予想

### 短期実行 (1時間)
- Phase 2のテスト実装 → カバレッジ83%到達予想

### 完全実装 (1.5時間)
- Phase 3-4のテスト実装 → カバレッジ90%+到達予想

---

**次のアクション**: Phase 1のメニュー管理テストを実装開始
