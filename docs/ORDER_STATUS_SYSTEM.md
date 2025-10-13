# 📋 注文ステータスシステム仕様書

## 概要

本システムでは、注文のライフサイクルを**4つのステータス**で管理します。シンプルさと機能性のバランスを重視し、明確な状態遷移ルールを持つ設計となっています。

## ステータス定義

### 1. pending (注文受付)
- **日本語表記**: 注文受付
- **意味**: 新規注文を受付けた状態。店舗側で内容確認・準備開始前
- **UI表示色**: 黄色 (`badge-warning`)
- **次の状態**: `ready`, `cancelled`

### 2. ready (準備完了)
- **日本語表記**: 準備完了
- **意味**: 商品の準備が完了し、お客様の受取を待っている状態
- **UI表示色**: 緑色 (`badge-success`)
- **次の状態**: `completed`

### 3. completed (受取完了)
- **日本語表記**: 受取完了
- **意味**: お客様が商品を受け取った最終状態
- **UI表示色**: グレー (`badge-secondary`)
- **次の状態**: なし（最終状態）

### 4. cancelled (キャンセル)
- **日本語表記**: キャンセル
- **意味**: 注文がキャンセルされた最終状態
- **UI表示色**: 赤色 (`badge-danger`)
- **次の状態**: なし（最終状態）

## ステータス遷移図

```
                    ┌─────────────┐
                    │   pending   │
                    │  注文受付   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │                         │
              ▼                         ▼
       ┌──────────┐              ┌──────────┐
       │  ready   │              │cancelled │
       │ 準備完了 │              │キャンセル│
       └────┬─────┘              └──────────┘
            │                          │
            ▼                          │
       ┌──────────┐                    │
       │completed │◄───────────────────┘
       │受取完了  │       (両方とも最終状態)
       └──────────┘
```

## 遷移ルール

### 許可される遷移

| 現在のステータス | 遷移可能なステータス | ユースケース |
|-----------------|---------------------|-------------|
| `pending` | `ready` | 商品準備が完了した |
| `pending` | `cancelled` | 注文をキャンセルする |
| `ready` | `completed` | お客様が商品を受け取った |
| `completed` | - | 変更不可（最終状態） |
| `cancelled` | - | 変更不可（最終状態） |

### 禁止される遷移

| 試行される遷移 | エラー理由 |
|---------------|-----------|
| `completed` → 任意 | 完了状態は変更できません |
| `cancelled` → 任意 | キャンセル状態は変更できません |
| `ready` → `pending` | 逆行する遷移は許可されません |
| `ready` → `cancelled` | 準備完了後のキャンセルは不可 |

## バックエンド実装

### schemas.py - OrderStatus Enum

```python
from enum import Enum
from typing import List

class OrderStatus(str, Enum):
    """注文ステータス（簡素化版）
    
    4つのステータスで注文のライフサイクルを管理:
    - pending: 注文受付（新規注文）
    - ready: 準備完了（受取可能）
    - completed: 受取完了（最終状態）
    - cancelled: キャンセル（最終状態）
    """
    PENDING = "pending"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    
    @classmethod
    def get_allowed_transitions(cls, current_status: str) -> List[str]:
        """現在のステータスから遷移可能なステータスを返す
        
        Args:
            current_status: 現在のステータス
            
        Returns:
            遷移可能なステータスのリスト
        """
        transitions = {
            cls.PENDING: [cls.READY, cls.CANCELLED],
            cls.READY: [cls.COMPLETED],
            cls.COMPLETED: [],  # 最終状態
            cls.CANCELLED: []   # 最終状態
        }
        return [status.value for status in transitions.get(current_status, [])]
```

### routers/store.py - ステータス更新API

```python
@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager', 'staff']))
):
    """注文ステータスを更新
    
    - pending → ready or cancelled
    - ready → completed
    - completed/cancelled → 変更不可
    """
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.store_id == current_user.store_id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="注文が見つかりません")
    
    # 遷移検証
    allowed = OrderStatus.get_allowed_transitions(order.status)
    if status_update.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"{order.status} から {status_update.status} への遷移は許可されていません"
        )
    
    order.status = status_update.status
    db.commit()
    return order
```

## フロントエンド実装

### store_orders.js - ステータスマッピング

```javascript
// ステータスの日本語表示
const statusNames = {
    'pending': '注文受付',
    'ready': '準備完了',
    'completed': '受取完了',
    'cancelled': 'キャンセル'
};

// デフォルトフィルタ（未完了のみ）
const defaultFilters = {
    status: ['pending', 'ready']
};
```

### store_orders.html - フィルタUI

```html
<!-- ステータスフィルタ -->
<div class="checkbox-group">
    <label class="checkbox-label">
        <input type="checkbox" class="status-checkbox" value="pending" checked>
        <span>注文受付</span>
    </label>
    <label class="checkbox-label">
        <input type="checkbox" class="status-checkbox" value="ready" checked>
        <span>準備完了</span>
    </label>
    <label class="checkbox-label">
        <input type="checkbox" class="status-checkbox" value="completed">
        <span>受取完了</span>
    </label>
    <label class="checkbox-label">
        <input type="checkbox" class="status-checkbox" value="cancelled">
        <span>キャンセル</span>
    </label>
</div>
```

### store_orders.css - バッジスタイル

```css
/* 4ステータスシステム用バッジ */
.badge-pending {
    background-color: #fff3cd;
    color: #856404;
    border: 1px solid #ffeaa7;
}

.badge-ready {
    background-color: #d1e7dd;
    color: #0f5132;
    border: 1px solid #a3cfbb;
}

.badge-completed {
    background-color: #e2e3e5;
    color: #41464b;
    border: 1px solid #c6c7c8;
}

.badge-cancelled {
    background-color: #f8d7da;
    color: #842029;
    border: 1px solid #f1aeb5;
}
```

## データベースマイグレーション

### 旧6ステータスから新4ステータスへの移行

#### マイグレーション戦略

旧システムの `confirmed` と `preparing` ステータスを `pending` に統合:

```python
# alembic/versions/003_simplify_order_status.py

def upgrade():
    # confirmed → pending
    connection.execute(text("""
        UPDATE orders SET status = 'pending' WHERE status = 'confirmed'
    """))
    
    # preparing → pending
    connection.execute(text("""
        UPDATE orders SET status = 'pending' WHERE status = 'preparing'
    """))

def downgrade():
    # ダウングレードは不可（情報損失のため）
    pass
```

#### 移行結果の確認

```sql
-- ステータス分布確認
SELECT status, COUNT(*) as count 
FROM orders 
GROUP BY status 
ORDER BY count DESC;

-- 期待される結果（4ステータスのみ）
  status   | count 
-----------+-------
 completed |    22
 pending   |    20
 ready     |     2
(3 rows)
```

## API仕様

### GET /api/store/orders

**クエリパラメータ:**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| status | string[] | No | フィルタするステータス（カンマ区切り）<br>例: `pending,ready` |
| start_date | string | No | 開始日（YYYY-MM-DD形式） |
| end_date | string | No | 終了日（YYYY-MM-DD形式） |
| search | string | No | 検索キーワード（注文ID、メニュー名など） |
| sort | string | No | ソート順（newest/oldest）デフォルト: newest |

**レスポンス例:**

```json
{
  "orders": [
    {
      "id": 48,
      "user_id": 9,
      "menu_id": 5,
      "status": "ready",
      "quantity": 2,
      "total_amount": 5600,
      "delivery_time": null,
      "notes": "辛さ控えめで",
      "created_at": "2025-10-13T10:30:00",
      "menu": {
        "name": "唐揚げ弁当",
        "price": 2800
      }
    }
  ],
  "total": 1
}
```

### PUT /api/store/orders/{order_id}/status

**リクエストボディ:**

```json
{
  "status": "ready"
}
```

**成功レスポンス (200 OK):**

```json
{
  "id": 48,
  "status": "ready",
  "updated_at": "2025-10-13T11:00:00"
}
```

**エラーレスポンス (400 Bad Request):**

```json
{
  "detail": "completed から pending への遷移は許可されていません"
}
```

## UIフロー

### 店舗スタッフの操作フロー

```
1. 注文一覧画面を開く
   ↓
2. デフォルトで「注文受付」「準備完了」が表示される
   ↓
3. 注文カードのドロップダウンでステータスを変更
   - pending → ready: 商品準備完了時
   - ready → completed: お客様受取時
   ↓
4. 「ステータス更新」ボタンをクリック
   ↓
5. APIリクエスト送信
   ↓
6. 成功 → 画面自動更新
   失敗 → エラーメッセージ表示
```

### お客様の注文状態表示

お客様向け画面では同じ4ステータスを表示:

```javascript
// customer_orders.js
const statusMap = {
    'pending': '注文受付',
    'ready': '準備完了',
    'completed': '受取完了',
    'cancelled': 'キャンセル'
};
```

## テスト観点

### 単体テスト

- ✅ `OrderStatus.get_allowed_transitions()` の動作確認
- ✅ 各遷移パターンのバリデーション
- ✅ 不正な遷移の拒否

### 統合テスト

- ✅ APIエンドポイントのステータス更新
- ✅ エラーハンドリング（400, 404）
- ✅ 店舗間データ分離

### E2Eテスト

- ✅ UIからのステータス更新フロー
- ✅ フィルタリング機能の動作
- ✅ リアルタイム更新の確認

## トラブルシューティング

### よくある問題

#### 1. ステータス更新が400エラーになる

**原因**: 許可されていない遷移を試行している

**解決策**: 
```javascript
// 現在のステータスを確認
console.log('Current status:', order.status);

// 遷移ルールを確認
// pending → ready, cancelled のみ
// ready → completed のみ
```

#### 2. フィルタで注文が表示されない

**原因**: デフォルトフィルタが `pending,ready` のみ

**解決策**:
- 「受取完了」「キャンセル」のチェックボックスを有効化
- または「フィルタリセット」ボタンをクリック

#### 3. マイグレーション後に古いステータスが残っている

**確認コマンド**:
```sql
SELECT DISTINCT status FROM orders ORDER BY status;
```

**期待される結果**: `completed`, `pending`, `ready` の3つのみ

**修正方法**:
```bash
# マイグレーションを再実行
docker-compose exec web alembic upgrade head
```

## 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2025-10-13 | 1.0.0 | 初版作成（4ステータスシステム） |
| - | - | 旧6ステータスから簡素化 |

## 関連ドキュメント

- [README.md](../README.md) - システム全体概要
- [API仕様書](../README.md#api仕様) - 全エンドポイント詳細
- [データベーススキーマ](./ER_DIAGRAM.md) - ER図とテーブル定義
