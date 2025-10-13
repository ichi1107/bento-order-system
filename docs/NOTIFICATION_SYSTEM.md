# 注文通知システム実装ガイド

## 概要

Feature #75 で実装されたブラウザ通知とサウンドによるリアルタイム注文通知機能のドキュメントです。

## 機能概要

### 1. デスクトップ通知 (Notification API)
- 新規注文が入った際にブラウザのデスクトップ通知を表示
- アプリが非アクティブ(別タブ表示中)でも通知が届く
- 通知には注文詳細(お客様名、メニュー名、数量、金額)を表示

### 2. 通知音 (Web Audio API)
- 新規注文時に通知音を再生
- ON/OFF 切り替え可能
- 設定は LocalStorage に保存され、ブラウザリロード後も維持
- 音声ファイルが利用できない場合は Web Audio API でビープ音を生成

### 3. 未確認注文バッジ
- ナビゲーションバーの「注文管理」にバッジ表示
- ページタイトルにも未確認数を表示 `(3) 注文管理 - 弁当注文管理システム`
- ステータスを pending から変更すると自動的にカウントが減少

### 4. 通知許可リクエストUI
- 初回アクセス時に通知許可を求めるバナーを表示
- わかりやすいUI/UXで許可を促進

## アーキテクチャ

### ファイル構成

```
static/
├── js/
│   ├── notification-manager.js    # 通知管理の中核クラス
│   └── store_orders.js             # 注文管理(通知統合済み)
├── sounds/
│   └── notification.mp3            # 通知音ファイル(要配置)
└── css/
    ├── common.css                   # ヘッダーバッジスタイル
    └── store_orders.css             # 通知UI追加スタイル

templates/
├── store_orders.html               # 通知UI要素追加
└── includes/
    └── store_header.html            # バッジ追加
```

### クラス設計

#### NotificationManager
通知機能を一元管理するシングルトンクラス

**主要メソッド:**
- `init()` - 初期化、Notification API サポート確認
- `requestNotificationPermission()` - 通知許可リクエスト
- `showNotification(title, body, icon)` - デスクトップ通知表示
- `notifyNewOrder(order)` - 新規注文通知(通知+音)
- `playNotificationSound()` - 通知音再生
- `toggleSound()` - サウンド ON/OFF 切り替え
- `detectNewOrders(currentOrders)` - ポーリングで新規注文検出
- `incrementUnconfirmedCount()` - 未確認カウント増加
- `decrementUnconfirmedCount()` - 未確認カウント減少
- `updateBadge()` - バッジUI更新
- `updatePageTitle()` - ページタイトル更新

**状態管理:**
- `notificationPermission` - 通知許可状態 (default|granted|denied)
- `soundEnabled` - 通知音ON/OFF (LocalStorage保存)
- `unconfirmedCount` - 未確認注文数
- `previousOrderIds` - 前回ポーリング時の注文IDセット

#### OrderManager (拡張)
既存の注文管理クラスに通知機能を統合

**追加プロパティ:**
- `this.notificationManager` - NotificationManager インスタンス

**変更箇所:**
1. `loadOrders()` - 新規注文検出・通知ロジック追加
2. `updateOrderStatus()` - ステータス変更時の未確認カウント減少
3. `initializeElements()` - 通知関連UI要素の取得
4. `attachEventListeners()` - サウンドトグルボタンイベント追加

## 実装詳細

### 1. 新規注文の検出ロジック

```javascript
// NotificationManager.detectNewOrders()
detectNewOrders(currentOrders) {
    const newOrders = [];
    const currentOrderIds = new Set(currentOrders.map(o => o.id));

    // 初回ロード時は既存IDを記録するだけ
    if (this.previousOrderIds.size === 0) {
        this.previousOrderIds = currentOrderIds;
        return newOrders;
    }

    // 前回から増えた pending 注文を検出
    currentOrders.forEach(order => {
        if (!this.previousOrderIds.has(order.id) && order.status === 'pending') {
            newOrders.push(order);
        }
    });

    this.previousOrderIds = currentOrderIds;
    return newOrders;
}
```

**ポイント:**
- 初回ロード時は通知しない(既存注文を新規として誤検出しないため)
- `pending` ステータスのみ対象
- 注文IDのSetを比較して差分を検出

### 2. 通知許可フロー

```
ページ初回訪問
    ↓
Notification.permission === 'default' ?
    ↓ YES
許可バナー表示(5秒後にフェードイン)
    ↓
ユーザーが「許可する」をクリック
    ↓
Notification.requestPermission()
    ↓
granted → テスト通知表示
denied  → ログ出力のみ
```

### 3. サウンド再生フォールバック

```
通知音再生リクエスト
    ↓
soundEnabled === true ?
    ↓ YES
音声ファイル読み込み成功?
    ↓ NO
Web Audio API でビープ音生成
    ↓
800Hz sine wave, 0.5秒間再生
```

### 4. LocalStorage 設定永続化

```javascript
// 保存
saveSoundPreference() {
    localStorage.setItem('notificationSoundEnabled', JSON.stringify(this.soundEnabled));
}

// 読み込み
loadSoundPreference() {
    const saved = localStorage.getItem('notificationSoundEnabled');
    return saved !== null ? JSON.parse(saved) : true; // デフォルトON
}
```

## UI/UX

### 通知許可バナー
- 位置: 画面上部中央、ヘッダー直下
- デザイン: グラデーション背景(#667eea → #764ba2)
- アニメーション: フェードイン
- アクション: 「許可する」「後で」

### サウンドトグルボタン
- 位置: ページヘッダー右側、更新ボタンの左
- 状態表示:
  - ON: 🔔 通知音: ON (緑グラデーション)
  - OFF: 🔕 通知音: OFF (グレー)
- クリック時: トースト通知で状態確認

### 未確認バッジ
- 位置: ヘッダーナビゲーション「📋 注文管理」の右上
- デザイン: 赤背景、白文字、パルスアニメーション
- 表示条件: unconfirmedCount > 0
- 最大表示: 99+ (100件以上の場合)

### ページタイトル
- 形式: `(未確認数) 注文管理 - 弁当注文管理システム`
- 例: `(3) 注文管理 - 弁当注文管理システム`
- タブ切り替え時に目立つ

## ブラウザ互換性

### Notification API
- ✅ Chrome 22+
- ✅ Firefox 22+
- ✅ Safari 7+
- ✅ Edge 14+
- ❌ IE 全バージョン

### Web Audio API
- ✅ Chrome 35+
- ✅ Firefox 25+
- ✅ Safari 6+
- ✅ Edge 12+

### LocalStorage
- ✅ 全モダンブラウザ

## セットアップ

### 1. 通知音ファイルの配置

実際の通知音ファイルを配置してください:

```bash
# 推奨: 1-2秒の短い音
# フォーマット: MP3 (広範な互換性)
# 音量: 適度(ファイル内で調整済みが望ましい)

# 配置先
static/sounds/notification.mp3
```

**無料音源の入手先:**
- https://notificationsounds.com/
- https://freesound.org/
- https://soundbible.com/

### 2. 画像ファイル(任意)

通知アイコンを用意する場合:

```bash
static/images/notification-icon.png  # 通知に表示されるアイコン
static/images/badge-icon.png         # バッジアイコン(Android)
static/images/logo.png                # テスト通知用
```

## テスト方法

### 1. 通知許可テスト

```javascript
// ブラウザコンソールで実行
await window.notificationManager.requestNotificationPermission();
```

### 2. テスト通知表示

```javascript
window.notificationManager.showTestNotification();
```

### 3. 新規注文シミュレーション

```javascript
// 手動でカウント増加
window.notificationManager.incrementUnconfirmedCount();

// 通知音再生テスト
window.notificationManager.playNotificationSound();

// テスト注文での通知
const testOrder = {
    id: 9999,
    customer_name: 'テスト太郎',
    menu_name: 'テスト弁当',
    quantity: 1,
    total_amount: 500,
    menu_image_url: null
};
window.notificationManager.notifyNewOrder(testOrder);
```

### 4. LocalStorage 確認

```javascript
// 現在の設定確認
localStorage.getItem('notificationSoundEnabled');

// 設定リセット
localStorage.removeItem('notificationSoundEnabled');
location.reload();
```

## トラブルシューティング

### 通知が表示されない

**原因1: 通知許可がない**
```javascript
// 確認
console.log(Notification.permission);
// 'denied' の場合 → ブラウザ設定からサイトの通知を許可
```

**原因2: ブラウザ非対応**
```javascript
if (!('Notification' in window)) {
    console.log('このブラウザは通知をサポートしていません');
}
```

### 通知音が再生されない

**原因1: ユーザーインタラクション不足**
- 初回アクセス時、ブラウザの自動再生ポリシーで音声がブロックされる場合がある
- ユーザーが何かクリックした後に有効化される

**解決策:**
- サウンドトグルボタンをクリックしてテスト再生
- Web Audio API フォールバックが自動適用される

**原因2: 音声ファイルが見つからない**
```javascript
// コンソールエラー確認
// "404 Not Found: /static/sounds/notification.mp3"
// → ファイルを正しく配置する
```

### バッジが更新されない

**原因: NotificationManager が初期化されていない**
```javascript
// 確認
console.log(window.notificationManager);
// undefined の場合 → notification-manager.js の読み込み順序を確認
```

**解決策:**
- `<script src="/static/js/notification-manager.js"></script>` を
  `store_orders.js` より前に配置

## パフォーマンス考慮事項

### ポーリング間隔
- デフォルト: 30秒 (`pollingIntervalTime = 30000`)
- 新規注文検出は O(n) の複雑度
- 注文数が多い場合でも高速に動作

### メモリ使用量
- `previousOrderIds`: Set<number> - 数百件でも数KB程度
- 音声ファイル: プリロードで数百KB
- Web Audio API: 軽量

### バッテリー消費
- ポーリング: 30秒間隔は妥当
- 通知音: 短時間のため影響小
- ページ非表示時はポーリング停止

## 今後の拡張案

### Phase 2: WebSocket によるリアルタイム通知
- ポーリング → WebSocket 切り替え
- 即座の通知(遅延ゼロ)
- サーバー負荷軽減

### Phase 3: プッシュ通知 (Service Worker)
- ブラウザを閉じていても通知受信
- オフライン対応

### Phase 4: 通知設定画面
- 通知タイプごとの ON/OFF
- 音量調整
- 通知音カスタマイズ

### Phase 5: 通知履歴
- 過去の通知を一覧表示
- 既読/未読管理

## まとめ

この実装により、店舗スタッフは:
- ✅ 新規注文を即座に認識できる
- ✅ 常に画面を注視する必要がない
- ✅ 注文の見落としを防げる
- ✅ オペレーションの属人性が低減される

結果として、顧客対応速度が向上し、店舗運営の効率化が実現されます。
