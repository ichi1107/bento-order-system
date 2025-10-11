# マルチテナントデータ分離セキュリティテスト結果レポート

**テスト実施日:** 2025年10月12日  
**対象ブランチ:** feature/47-test-multi-tenant-data-isolation  
**テスト実行環境:** Docker  
**テスト実施者:** GitHub Copilot

## エグゼクティブサマリー

マルチテナント環境におけるデータ分離の包括的なセキュリティテストを実施しました。  
**結果: 13個すべてのテストが失敗** - **重大なセキュリティ脆弱性を検出**

現在のシステムは**店舗間のデータ分離が一切機能していません**。  
ある店舗のユーザーが他店舗のデータ（注文、メニュー、売上など）に**完全にアクセス可能**な状態です。

## 🔴 検出された重大なセキュリティ脆弱性

### 1. クロスストアデータアクセス（CRITICAL）

| 脆弱性 | 深刻度 | 説明 |
|--------|--------|------|
| 他店舗の注文更新 | **CRITICAL** | 店舗Aのユーザーが店舗Bの注文IDを指定して、ステータスを変更できる |
| 他店舗のメニュー更新 | **CRITICAL** | 店舗Aのユーザーが店舗Bのメニューを編集・削除できる |
| データ漏洩（一覧API） | **HIGH** | 注文一覧・メニュー一覧に他店舗のデータが含まれる |
| 売上データ漏洩 | **CRITICAL** | ダッシュボード・レポートで他店舗の売上が混在 |

### 2. 具体的な脆弱性の詳細

#### 2.1 注文データへの不正アクセス

**テストケース:** `test_store_a_cannot_get_store_b_order_status`
- **期待:** 403 Forbidden または 404 Not Found
- **実際:** 200 OK （成功してしまう）
- **影響:** 店舗Aが店舗Bの注文を「completed」に変更可能

```python
# 攻撃例
PUT /api/store/orders/{store_b_order_id}/status
Authorization: Bearer {store_a_token}
{
  "status": "completed"
}
# → 200 OK (本来は403/404であるべき)
```

#### 2.2 メニューデータへの不正アクセス

**テストケース:** `test_store_a_cannot_update_store_b_menu`
- **期待:** 403 Forbidden または 404 Not Found
- **実際:** 200 OK （成功してしまう）
- **影響:** 店舗Aが店舗Bのメニューを改ざん・削除可能

```python
# 攻撃例
PUT /api/store/menus/{store_b_menu_id}
Authorization: Bearer {store_a_token}
{
  "name": "乗っ取られたメニュー",
  "price": 1
}
# → 200 OK (本来は403/404であるべき)
```

#### 2.3 一覧APIでのデータ漏洩

**テストケース:** `test_order_list_contains_only_own_store_orders`
- **期待:** 店舗Aの注文のみ取得
- **実際:** 店舗A+店舗Bの全注文が取得される
- **影響:** 他店舗の注文詳細（顧客情報、金額、メニュー等）が漏洩

```python
GET /api/store/orders
Authorization: Bearer {store_a_token}

# 実際のレスポンス:
{
  "orders": [
    {"id": 1, "store_id": 1, ...},  # 店舗A（正常）
    {"id": 2, "store_id": 2, ...}   # 店舗B（漏洩！）
  ]
}
```

#### 2.4 売上データの混在

**テストケース:** `test_dashboard_shows_only_own_store_data`
- **期待値:** 店舗Aの売上 = 1,700円
- **実際値:** 6,200円（店舗A+Bの合算）
- **影響:** 経営データが正確でない、他店舗の売上情報が漏洩

**テストケース:** `test_sales_report_contains_only_own_store_data`
- **期待値:** 店舗Aの7日間売上 = 5,950円
- **実際値:** 68,950円（全店舗の合算）
- **影響:** レポート機能が使用不能、重大なデータ漏洩

## 📊 テスト結果サマリー

### 全テスト結果

| テストクラス | テストケース | 結果 |
|-------------|-------------|------|
| TestOrderIsolation | test_store_a_cannot_get_store_b_order_status | ❌ FAIL |
| TestOrderIsolation | test_store_b_cannot_get_store_a_order_status | ❌ FAIL |
| TestOrderIsolation | test_order_list_contains_only_own_store_orders | ❌ FAIL |
| TestOrderIsolation | test_order_list_isolation_with_multiple_orders | ❌ FAIL |
| TestMenuIsolation | test_store_a_cannot_update_store_b_menu | ❌ FAIL |
| TestMenuIsolation | test_store_b_cannot_delete_store_a_menu | ❌ FAIL |
| TestMenuIsolation | test_menu_list_contains_only_own_store_menus | ❌ FAIL |
| TestMenuIsolation | test_created_menu_has_correct_store_id | ❌ FAIL |
| TestDashboardIsolation | test_dashboard_shows_only_own_store_data | ❌ FAIL |
| TestSalesReportIsolation | test_sales_report_contains_only_own_store_data | ❌ FAIL |
| TestCrossStoreAccessDenied | test_manager_cannot_access_other_store_data | ❌ FAIL |
| TestCrossStoreAccessDenied | test_staff_cannot_access_other_store_data | ❌ FAIL |
| TestCrossStoreAccessDenied | test_no_data_leakage_in_error_messages | ❌ FAIL |

**合計: 0 passed, 13 failed**

## 🔍 根本原因分析

### 問題のあるAPIエンドポイント

以下のエンドポイントでstore_idによるフィルタリングが実装されていません:

1. `PUT /api/store/orders/{order_id}/status` - 注文ステータス更新
2. `GET /api/store/orders` - 注文一覧取得
3. `PUT /api/store/menus/{menu_id}` - メニュー更新
4. `DELETE /api/store/menus/{menu_id}` - メニュー削除
5. `GET /api/store/menus` - メニュー一覧取得
6. `POST /api/store/menus` - メニュー作成
7. `GET /api/store/dashboard` - ダッシュボード
8. `GET /api/store/reports/sales` - 売上レポート

### コード分析

**現在の実装 (routers/store.py):**

```python
# 問題のあるコード例
@router.get("/orders", response_model=OrderListResponse)
def get_all_orders(...):
    query = db.query(Order)  # ← store_idフィルタなし！
    # ...
    return {"orders": orders, "total": total}

@router.put("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(order_id: int, ...):
    order = db.query(Order).filter(Order.id == order_id).first()  # ← store_idフィルタなし！
    # ...
```

**必要な修正:**

```python
# 修正後のコード
@router.get("/orders", response_model=OrderListResponse)
def get_all_orders(current_user: User = Depends(...)):
    query = db.query(Order).filter(Order.store_id == current_user.store_id)  # ✓ フィルタ追加
    # ...

@router.put("/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(order_id: int, current_user: User = Depends(...)):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.store_id == current_user.store_id  # ✓ フィルタ追加
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # ...
```

## 🚨 ビジネスインパクト

### セキュリティリスク

- **データ侵害:** 他店舗の機密情報（売上、顧客、メニュー）が漏洩
- **データ改ざん:** 悪意のあるユーザーが他店舗のデータを変更・削除可能
- **プライバシー侵害:** 顧客情報、注文履歴が他店舗に見える
- **GDPR/個人情報保護法違反:** データアクセス制御の不備

### 運用リスク

- **信頼性:** 売上レポートが不正確
- **業務妨害:** 他店舗が注文ステータスを変更し業務を妨害可能
- **法的責任:** データ漏洩による損害賠償のリスク

## ✅ 推奨される修正アクション

### 緊急対応（即座に実施）

1. **全APIエンドポイントにstore_idフィルタを追加**
   - 対象: routers/store.py の全エンドポイント
   - 優先度: CRITICAL
   
2. **データ取得時の強制フィルタリング**
   ```python
   # すべてのクエリに追加
   .filter(Model.store_id == current_user.store_id)
   ```

3. **データ作成時のstore_id自動設定**
   ```python
   # メニュー作成時
   db_menu = Menu(**menu.dict(), store_id=current_user.store_id)
   ```

4. **404エラーの返却**
   - 403 Forbiddenではなく404 Not Foundを返す
   - 理由: 他店舗のリソース存在を隠蔽

### 中期対応（1週間以内）

1. **統合テストの自動化**
   - CI/CDパイプラインにtest_store_isolation.pyを追加
   - 全PRでデータ分離テストを必須化

2. **コードレビュープロセスの強化**
   - 新規APIエンドポイント作成時のチェックリスト
   - store_idフィルタの有無を必須確認項目に

3. **セキュリティ監査**
   - 既存の全エンドポイントを再監査
   - customer向けAPIも同様に確認

### 長期対応（1ヶ月以内）

1. **アーキテクチャレベルの改善**
   - Base Queryクラスで自動的にstore_idフィルタを適用
   - Dependency Injectionで強制的にフィルタリング

2. **侵入テストの実施**
   - 外部セキュリティ専門家によるペネトレーションテスト
   - 脆弱性診断ツールの導入

3. **セキュリティドキュメント整備**
   - マルチテナント開発ガイドライン作成
   - セキュアコーディング基準の策定

## 📝 次のステップ

1. ✅ **完了:** セキュリティテスト実装
2. ✅ **完了:** 脆弱性の特定と文書化
3. ⏳ **次:** routers/store.py にstore_idフィルタリングを追加
4. ⏳ **次:** 修正後の再テスト実施
5. ⏳ **次:** すべてのテストがPASSすることを確認

## 🔗 関連ドキュメント

- テストコード: `tests/test_store_isolation.py`
- 対象ソースコード: `routers/store.py`
- データモデル: `models.py`
- マイグレーション: `alembic/versions/assign_default_store_id_to_existing_data.py`

---

**レポート作成:** GitHub Copilot  
**レビュー必須:** システム管理者、セキュリティチーム
