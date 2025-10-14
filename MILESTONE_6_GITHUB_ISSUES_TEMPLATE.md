# Milestone 6: メニュー管理機能 - GitHub Issues テンプレート

**作成日**: 2025年10月13日  
**対象**: Issue #1～#10（Phase 1～3 全機能）

---

## 📊 Issue概要

| Issue | タイトル | 優先度 | 工数 |
|-------|---------|--------|------|
| #1 | メニュー管理画面の基本実装（一覧表示・フィルタ・ページネーション） | 🔴 Critical | 8-12h |
| #2 | メニュー作成・編集フォームの実装（モーダル・バリデーション） | 🔴 High | 6-8h |
| #3 | メニュー削除機能と確認ダイアログの実装（論理削除/物理削除対応） | 🔴 High | 3-4h |
| #4 | メニュー画像アップロード機能の実装（ドラッグ&ドロップ・プレビュー対応） | 🟡 Medium | 8-10h |
| #5 | メニュー一覧の並び替え・ソート機能の実装（カラムヘッダークリック） | 🟡 Medium | 4-6h |
| #6 | メニュー検索機能の実装（キーワード検索・リアルタイム検索） | 🟡 Medium | 5-7h |
| #7 | メニュー一括操作機能の実装（複数選択・一括公開/非公開） | 🟡 Medium | 6-8h |
| #8 | メニューカテゴリ管理機能の実装（カテゴリCRUD・フィルタ） | 🟢 Low | 12-16h |
| #9 | 在庫数管理・自動在庫切れ機能の実装（在庫追跡・アラート） | 🟢 Low | 10-14h |
| #10 | メニュー変更履歴・監査ログ機能の実装（変更追跡・監査対応） | 🟢 Low | 8-12h |

### フェーズ別構成

| フェーズ | Issue | 合計工数 | 説明 |
|---------|-------|---------|------|
| **Phase 1（必須）** | #1～#3 | 17-24h | 基本的なCRUD機能 |
| **Phase 2（推奨）** | #4～#7 | 23-31h | UX向上機能 |
| **Phase 3（拡張）** | #8～#10 | 30-42h | 高度な管理機能 |
| **合計** | #1～#10 | **70-97h** | 全機能 |

---

## Issue #1: メニュー管理画面の基本実装

### 📋 タイトル
**メニュー管理画面の基本実装（一覧表示・フィルタ・ページネーション）**

### 📝 説明

#### 🎯 目的（実装内容）
店舗スタッフがメニューを一覧で確認し、公開/非公開状態を管理できる画面を実装します。バックエンドAPI（`GET /api/store/menus`）は実装済み（テストカバレッジ90%）のため、フロントエンド画面のみを追加することで即座に利用可能になります。

**実装する機能**:
- ✅ メニュー一覧をテーブル形式で表示
- ✅ 公開中/非公開/すべて のフィルタ機能
- ✅ ページネーション（20件/ページ、最大100件/ページ）
- ✅ ステータスバッジ（公開=🟢緑、非公開=🔴赤）
- ✅ レスポンシブデザイン（PC・タブレット・スマホ対応）
- ✅ ローディング表示・エラーハンドリング

#### 🔧 タスク（技術仕様）

**1. HTMLテンプレート作成**
```
📁 ファイル: templates/store_menus.html
```
- 既存の`store_dashboard.html`をベースに作成
- ナビゲーションヘッダーを統一
- メニュー一覧テーブル（名前、価格、ステータス、操作列）
- フィルタボタングループ（すべて/公開中/非公開）
- ページネーションコンポーネント

**2. CSS実装**
```
📁 ファイル: static/css/store_menus.css
```
- テーブルスタイリング（zebra striping）
- ステータスバッジ（.badge-available, .badge-unavailable）
- フィルタボタングループ（.filter-group）
- レスポンシブ対応（@media queries）

**3. JavaScript実装**
```
📁 ファイル: static/js/store_menus.js
```
主要関数:
- `fetchMenus(isAvailable, page, perPage)` - メニュー一覧取得
- `renderMenuTable(menus)` - テーブル描画
- `renderPagination(total, currentPage, perPage)` - ページネーション描画
- `handleFilterChange(filter)` - フィルタ切替
- `showLoading()` / `hideLoading()` - ローディング表示制御
- `handleError(error)` - エラーハンドリング

**4. APIエンドポイント**
```
使用API: GET /api/store/menus
パラメータ:
  - is_available: boolean (optional) - 公開状態フィルタ
  - page: integer (default: 1) - ページ番号
  - per_page: integer (default: 20) - 1ページあたりの件数

レスポンス:
{
  "menus": [
    {
      "id": 1,
      "name": "特製弁当",
      "price": 1200,
      "description": "人気No.1の弁当",
      "is_available": true,
      "created_at": "2025-10-01T10:00:00Z",
      "updated_at": "2025-10-10T15:30:00Z"
    }
  ],
  "total": 45
}
```

**5. ルーティング設定**
```python
# main.py または routers/store.py に追加
@router.get("/menus", response_class=HTMLResponse)
async def menu_management_page(request: Request):
    return templates.TemplateResponse("store_menus.html", {"request": request})
```

#### ✅ 受け入れ基準

**機能要件**:
- [ ] `/store/menus` にアクセスするとメニュー一覧画面が表示される
- [ ] メニューがテーブル形式で表示される（名前、価格、ステータス、操作）
- [ ] 「すべて」フィルタで全メニューが表示される
- [ ] 「公開中」フィルタで`is_available=true`のメニューのみ表示される
- [ ] 「非公開」フィルタで`is_available=false`のメニューのみ表示される
- [ ] ページネーションが機能し、20件ずつ表示される
- [ ] ページ番号をクリックすると該当ページに移動する
- [ ] ステータスバッジが正しく色分けされている（公開=緑、非公開=赤）

**UI/UX要件**:
- [ ] レスポンシブデザイン（スマホ・タブレットで正常表示）
- [ ] データ読込中にローディングインジケータが表示される
- [ ] APIエラー時にユーザーフレンドリーなエラーメッセージが表示される
- [ ] 既存ページ（ダッシュボード、注文管理）とデザイン一貫性がある

**セキュリティ要件**:
- [ ] 未認証ユーザーはログインページにリダイレクトされる
- [ ] 店舗ユーザー（owner, manager, staff）のみアクセス可能
- [ ] 顧客ユーザーはアクセスできない（403エラー）

**パフォーマンス要件**:
- [ ] 初期表示が1秒以内に完了する
- [ ] ページ切替が500ms以内に完了する

**テスト要件**:
- [ ] E2Eテスト: メニュー一覧ページの表示
- [ ] E2Eテスト: フィルタ機能の動作確認
- [ ] E2Eテスト: ページネーション機能の動作確認
- [ ] E2Eテスト: 権限チェック（顧客ユーザーのアクセス拒否）

---

## Issue #2: メニュー作成・編集フォームの実装

### 📋 タイトル
**メニュー作成・編集フォームの実装（モーダル・バリデーション）**

### 📝 説明

#### 🎯 目的（実装内容）
店舗スタッフがメニューを作成・編集できるモーダルフォームを実装します。直感的な操作で季節限定メニューの追加や価格変更が可能になり、在庫状況に応じた迅速なメニュー管理を実現します。

**実装する機能**:
- ✅ メニュー新規作成モーダルフォーム
- ✅ メニュー編集モーダルフォーム
- ✅ クライアント側バリデーション（リアルタイム）
- ✅ サーバー側バリデーションエラー表示
- ✅ 公開/非公開トグルスイッチ
- ✅ 保存成功時のトースト通知
- ✅ フォーム送信中のローディング状態

#### 🔧 タスク（技術仕様）

**1. モーダルHTML追加**
```html
<!-- templates/store_menus.html に追加 -->
<div id="menuModal" class="modal">
  <div class="modal-content">
    <span class="close">&times;</span>
    <h2 id="modalTitle">メニューを作成</h2>
    <form id="menuForm">
      <div class="form-group">
        <label>名前 <span class="required">*</span></label>
        <input type="text" name="name" maxlength="255" required>
        <span class="error-message" id="name-error"></span>
      </div>
      
      <div class="form-group">
        <label>価格 (円) <span class="required">*</span></label>
        <input type="number" name="price" min="1" required>
        <span class="error-message" id="price-error"></span>
      </div>
      
      <div class="form-group">
        <label>説明</label>
        <textarea name="description" rows="3"></textarea>
      </div>
      
      <div class="form-group">
        <label>画像URL</label>
        <input type="url" name="image_url">
      </div>
      
      <div class="form-group">
        <label class="toggle-label">
          <input type="checkbox" name="is_available" checked>
          <span>公開する</span>
        </label>
      </div>
      
      <div class="form-actions">
        <button type="button" class="btn-secondary" onclick="closeModal()">キャンセル</button>
        <button type="submit" class="btn-primary">保存</button>
      </div>
    </form>
  </div>
</div>
```

**2. JavaScript実装**
```javascript
// static/js/store_menus.js に追加

// フォームバリデーション
function validateMenuForm(formData) {
  const errors = {};
  
  if (!formData.name || formData.name.trim().length === 0) {
    errors.name = "名前は必須です";
  } else if (formData.name.length > 255) {
    errors.name = "名前は255文字以内で入力してください";
  }
  
  if (!formData.price || formData.price < 1) {
    errors.price = "価格は1円以上で入力してください";
  }
  
  return errors;
}

// メニュー作成
async function createMenu(formData) {
  const response = await fetch('/api/store/menus', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`
    },
    body: JSON.stringify(formData)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'メニューの作成に失敗しました');
  }
  
  return await response.json();
}

// メニュー更新
async function updateMenu(menuId, formData) {
  const response = await fetch(`/api/store/menus/${menuId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`
    },
    body: JSON.stringify(formData)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'メニューの更新に失敗しました');
  }
  
  return await response.json();
}

// モーダル開閉
function openCreateModal() {
  document.getElementById('modalTitle').textContent = 'メニューを作成';
  document.getElementById('menuForm').reset();
  document.getElementById('menuModal').classList.add('active');
}

function openEditModal(menu) {
  document.getElementById('modalTitle').textContent = 'メニューを編集';
  document.querySelector('[name="name"]').value = menu.name;
  document.querySelector('[name="price"]').value = menu.price;
  document.querySelector('[name="description"]').value = menu.description || '';
  document.querySelector('[name="image_url"]').value = menu.image_url || '';
  document.querySelector('[name="is_available"]').checked = menu.is_available;
  document.getElementById('menuModal').classList.add('active');
}

function closeModal() {
  document.getElementById('menuModal').classList.remove('active');
}
```

**3. CSS実装**
```css
/* static/css/store_menus.css に追加 */
.modal {
  display: none;
  position: fixed;
  z-index: 1000;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0,0,0,0.4);
}

.modal.active {
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  background-color: white;
  padding: 30px;
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
}

.form-group {
  margin-bottom: 20px;
}

.error-message {
  color: #e74c3c;
  font-size: 14px;
  display: none;
}

.error-message.active {
  display: block;
}
```

**4. 使用API**
```
作成: POST /api/store/menus
更新: PUT /api/store/menus/{menu_id}

リクエストボディ:
{
  "name": "春の特製弁当",
  "price": 1500,
  "description": "桜エビと筍の春限定弁当",
  "image_url": "https://example.com/image.jpg",
  "is_available": true
}
```

#### ✅ 受け入れ基準

**機能要件**:
- [ ] 「+ 新規作成」ボタンをクリックすると作成モーダルが開く
- [ ] 「編集」ボタンをクリックすると編集モーダルが開く
- [ ] モーダルに既存データが正しく表示される（編集時）
- [ ] 名前・価格が未入力の場合、バリデーションエラーが表示される
- [ ] 価格が0円以下の場合、バリデーションエラーが表示される
- [ ] 公開/非公開トグルが機能する
- [ ] 「保存」ボタンでメニューが作成/更新される
- [ ] 保存成功時にトースト通知が表示される
- [ ] 保存後にモーダルが閉じる
- [ ] 保存後にメニュー一覧が自動更新される

**UI/UX要件**:
- [ ] モーダルの外側をクリックすると閉じる
- [ ] ESCキーでモーダルを閉じられる
- [ ] フォーム送信中にボタンが無効化される
- [ ] 送信中にローディング表示がある
- [ ] バリデーションエラーが該当フィールドの下に表示される
- [ ] リアルタイムバリデーション（入力中にエラーチェック）

**セキュリティ要件**:
- [ ] owner, manager のみが作成・編集できる（APIレベルで制御済み）
- [ ] staff は作成・編集できない
- [ ] XSS対策（ユーザー入力のエスケープ）

**テスト要件**:
- [ ] E2Eテスト: メニュー作成フローの動作確認
- [ ] E2Eテスト: メニュー編集フローの動作確認
- [ ] E2Eテスト: バリデーションエラー表示の確認
- [ ] E2Eテスト: 公開/非公開トグルの動作確認

---

## Issue #3: メニュー削除機能と確認ダイアログ

### 📋 タイトル
**メニュー削除機能と確認ダイアログの実装（論理削除/物理削除対応）**

### 📝 説明

#### 🎯 目的（実装内容）
メニュー削除機能を実装し、誤削除を防ぐ確認ダイアログを提供します。バックエンドのインテリジェント削除機能（既存注文がある場合は論理削除、ない場合は物理削除）を活用し、データ整合性を保ちながら安全な削除を実現します。

**実装する機能**:
- ✅ 削除ボタンの実装（各メニュー行）
- ✅ 削除確認ダイアログ
- ✅ 論理削除・物理削除の結果表示
- ✅ 削除後の一覧自動更新
- ✅ 削除権限チェック（owner のみ）

#### 🔧 タスク（技術仕様）

**1. 削除ボタン追加**
```html
<!-- templates/store_menus.html のテーブル操作列に追加 -->
<td class="actions">
  <button class="btn-sm btn-primary" onclick="openEditModal(menu)">編集</button>
  <button class="btn-sm btn-danger" onclick="confirmDelete(menu.id, menu.name)">削除</button>
</td>
```

**2. 確認ダイアログHTML**
```html
<!-- templates/store_menus.html に追加 -->
<div id="deleteModal" class="modal">
  <div class="modal-content modal-small">
    <div class="modal-header">
      <span class="warning-icon">⚠</span>
      <h3>確認</h3>
    </div>
    <div class="modal-body">
      <p id="deleteMessage"></p>
      <p id="deleteWarning" class="text-warning"></p>
    </div>
    <div class="modal-actions">
      <button class="btn-secondary" onclick="closeDeleteModal()">キャンセル</button>
      <button class="btn-danger" id="confirmDeleteBtn">削除する</button>
    </div>
  </div>
</div>
```

**3. JavaScript実装**
```javascript
// static/js/store_menus.js に追加

// 削除確認ダイアログ表示
function confirmDelete(menuId, menuName) {
  const message = `「${menuName}」を削除しますか?`;
  document.getElementById('deleteMessage').textContent = message;
  
  // 確認ボタンのクリックハンドラ設定
  const confirmBtn = document.getElementById('confirmDeleteBtn');
  confirmBtn.onclick = () => deleteMenu(menuId, menuName);
  
  // モーダル表示
  document.getElementById('deleteModal').classList.add('active');
}

// メニュー削除実行
async function deleteMenu(menuId, menuName) {
  try {
    showLoading();
    
    const response = await fetch(`/api/store/menus/${menuId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    });
    
    if (!response.ok) {
      throw new Error('削除に失敗しました');
    }
    
    const result = await response.json();
    
    // 結果に応じた通知
    if (result.message.includes("disabled")) {
      showToast(`既存の注文があるため「${menuName}」を非公開に設定しました`, 'warning');
    } else {
      showToast(`「${menuName}」を削除しました`, 'success');
    }
    
    // モーダルを閉じる
    closeDeleteModal();
    
    // メニュー一覧を更新
    await fetchMenus();
    
  } catch (error) {
    showToast('削除に失敗しました: ' + error.message, 'error');
  } finally {
    hideLoading();
  }
}

// モーダル閉じる
function closeDeleteModal() {
  document.getElementById('deleteModal').classList.remove('active');
}

// トースト通知表示
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.classList.add('active');
  }, 10);
  
  setTimeout(() => {
    toast.classList.remove('active');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}
```

**4. CSS実装**
```css
/* static/css/store_menus.css に追加 */
.btn-danger {
  background-color: #e74c3c;
  color: white;
}

.btn-danger:hover {
  background-color: #c0392b;
}

.modal-small {
  max-width: 400px;
}

.warning-icon {
  font-size: 48px;
  color: #f39c12;
}

.text-warning {
  color: #f39c12;
  font-size: 14px;
}

/* トースト通知 */
.toast {
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 15px 20px;
  border-radius: 4px;
  color: white;
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.3s ease;
  z-index: 2000;
}

.toast.active {
  opacity: 1;
  transform: translateY(0);
}

.toast-success { background-color: #27ae60; }
.toast-warning { background-color: #f39c12; }
.toast-error { background-color: #e74c3c; }
```

**5. 使用API**
```
削除: DELETE /api/store/menus/{menu_id}

レスポンス（論理削除）:
{
  "message": "Menu disabled due to existing orders"
}

レスポンス（物理削除）:
{
  "message": "Menu deleted successfully"
}
```

#### ✅ 受け入れ基準

**機能要件**:
- [ ] 「削除」ボタンをクリックすると確認ダイアログが表示される
- [ ] ダイアログにメニュー名が表示される
- [ ] 「キャンセル」で削除が中止される
- [ ] 「削除する」で削除が実行される
- [ ] 論理削除時に「非公開に設定しました」というメッセージが表示される
- [ ] 物理削除時に「削除しました」というメッセージが表示される
- [ ] 削除後にメニュー一覧が自動更新される
- [ ] 削除後にダイアログが自動的に閉じる

**UI/UX要件**:
- [ ] トースト通知が3秒間表示される
- [ ] トースト通知がフェードイン・フェードアウトする
- [ ] 削除中にローディング表示がある
- [ ] 削除ボタンが owner のみに表示される（権限チェック）

**エラーハンドリング**:
- [ ] API エラー時に適切なエラーメッセージが表示される
- [ ] ネットワークエラー時にユーザーフレンドリーなメッセージが表示される
- [ ] 権限不足時（403）に適切なエラーメッセージが表示される

**テスト要件**:
- [ ] E2Eテスト: 削除確認ダイアログの表示
- [ ] E2Eテスト: 削除のキャンセル
- [ ] E2Eテスト: 論理削除の動作確認
- [ ] E2Eテスト: 物理削除の動作確認
- [ ] E2Eテスト: 権限チェック（manager, staff は削除不可）

---

## Issue #4: メニュー画像アップロード機能

### 📋 タイトル
**メニュー画像アップロード機能の実装（ドラッグ&ドロップ・プレビュー対応）**

### 📝 説明

#### 🎯 目的（実装内容）
現在は画像URLの手入力のみ対応していますが、画像ファイルを直接アップロードできるようにすることで、スタッフの作業効率を大幅に向上させます。店舗画像アップロード機能（実装済み）を参考に、メニュー画像用のアップロード機能を実装します。

**実装する機能**:
- ✅ 画像ファイルのドラッグ&ドロップアップロード
- ✅ クリックでファイル選択ダイアログ
- ✅ アップロード前のプレビュー表示
- ✅ 画像の差し替え（古い画像の自動削除）
- ✅ ファイル形式・サイズのバリデーション
- ✅ アップロード進捗表示

#### 🔧 タスク（技術仕様）

**1. バックエンドAPI実装**
```python
# routers/store.py に追加

@router.post("/menus/{menu_id}/image", response_model=MenuResponse, summary="メニュー画像アップロード")
async def upload_menu_image(
    menu_id: int,
    file: UploadFile = File(..., description="アップロードする画像ファイル"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager']))
):
    """
    メニュー画像をアップロード
    
    **必要な権限:** owner, manager
    
    **パラメータ:**
    - **file**: 画像ファイル（JPEG, PNG, GIF, WebP対応、最大5MB）
    
    **戻り値:**
    - 更新後のメニュー情報（image_urlが更新される）
    
    **エラー:**
    - 400: 不正なファイル形式またはサイズ超過
    - 404: メニューが見つからない、または他店舗のメニュー
    """
    # ファイル形式検証
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # ファイルサイズ検証（5MB）
    file.file.seek(0, 2)  # ファイル末尾に移動
    file_size = file.file.tell()
    file.file.seek(0)  # ファイル先頭に戻る
    
    if file_size > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 5MB limit"
        )
    
    # メニュー取得（自店舗のみ）
    menu = db.query(Menu).filter(
        Menu.id == menu_id,
        Menu.store_id == current_user.store_id
    ).first()
    
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found"
        )
    
    # アップロードディレクトリの作成
    upload_dir = Path("static/uploads/menus")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # 一意のファイル名を生成
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_dir / unique_filename
    
    # 古い画像ファイルを削除（存在する場合）
    if menu.image_url and menu.image_url.startswith("/static/uploads/"):
        old_file_path = Path(menu.image_url.lstrip('/'))
        if old_file_path.exists():
            old_file_path.unlink()
    
    # ファイルを保存
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # データベースのimage_urlを更新
    menu.image_url = f"/static/uploads/menus/{unique_filename}"
    db.commit()
    db.refresh(menu)
    
    return menu


@router.delete("/menus/{menu_id}/image", response_model=MenuResponse, summary="メニュー画像削除")
def delete_menu_image(
    menu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager']))
):
    """
    メニュー画像を削除
    
    **必要な権限:** owner, manager
    """
    menu = db.query(Menu).filter(
        Menu.id == menu_id,
        Menu.store_id == current_user.store_id
    ).first()
    
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found"
        )
    
    # 画像ファイルを削除
    if menu.image_url and menu.image_url.startswith("/static/uploads/"):
        file_path = Path(menu.image_url.lstrip('/'))
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass
    
    # データベースのimage_urlをクリア
    menu.image_url = None
    db.commit()
    db.refresh(menu)
    
    return menu
```

**2. フロントエンドHTML**
```html
<!-- メニュー作成・編集モーダルに追加 -->
<div class="form-group">
  <label>メニュー画像</label>
  
  <div id="imageUploadArea" class="image-upload-area">
    <div id="imagePreview" class="image-preview">
      <img id="previewImage" src="" alt="プレビュー" style="display:none;">
      <div id="uploadPlaceholder" class="upload-placeholder">
        <span class="upload-icon">📷</span>
        <p>クリックまたはドラッグ&ドロップで画像をアップロード</p>
        <p class="upload-hint">JPEG, PNG, GIF, WebP (最大5MB)</p>
      </div>
    </div>
    <input type="file" id="imageFileInput" accept="image/jpeg,image/png,image/gif,image/webp" style="display:none;">
    <button type="button" class="btn-secondary btn-sm" id="removeImageBtn" style="display:none;">画像を削除</button>
  </div>
</div>
```

**3. JavaScript実装**
```javascript
// static/js/store_menus.js に追加

// ドラッグ&ドロップ設定
function setupImageUpload() {
  const uploadArea = document.getElementById('imageUploadArea');
  const fileInput = document.getElementById('imageFileInput');
  const previewImage = document.getElementById('previewImage');
  const uploadPlaceholder = document.getElementById('uploadPlaceholder');
  const removeBtn = document.getElementById('removeImageBtn');
  
  // クリックでファイル選択
  uploadArea.addEventListener('click', (e) => {
    if (e.target !== removeBtn) {
      fileInput.click();
    }
  });
  
  // ファイル選択時
  fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      handleImageFile(file);
    }
  });
  
  // ドラッグオーバー
  uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
  });
  
  // ドラッグ離脱
  uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('drag-over');
  });
  
  // ドロップ
  uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      handleImageFile(file);
    }
  });
  
  // 画像削除
  removeBtn.addEventListener('click', () => {
    removeImage();
  });
}

// 画像ファイル処理
function handleImageFile(file) {
  // ファイルサイズチェック
  if (file.size > 5 * 1024 * 1024) {
    showToast('ファイルサイズは5MB以下にしてください', 'error');
    return;
  }
  
  // プレビュー表示
  const reader = new FileReader();
  reader.onload = (e) => {
    document.getElementById('previewImage').src = e.target.result;
    document.getElementById('previewImage').style.display = 'block';
    document.getElementById('uploadPlaceholder').style.display = 'none';
    document.getElementById('removeImageBtn').style.display = 'block';
  };
  reader.readAsDataURL(file);
  
  // ファイルを保存（後でアップロード）
  window.currentImageFile = file;
}

// 画像アップロード実行
async function uploadImage(menuId) {
  if (!window.currentImageFile) return null;
  
  const formData = new FormData();
  formData.append('file', window.currentImageFile);
  
  const response = await fetch(`/api/store/menus/${menuId}/image`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`
    },
    body: formData
  });
  
  if (!response.ok) {
    throw new Error('画像のアップロードに失敗しました');
  }
  
  return await response.json();
}

// 画像削除
function removeImage() {
  document.getElementById('previewImage').style.display = 'none';
  document.getElementById('previewImage').src = '';
  document.getElementById('uploadPlaceholder').style.display = 'flex';
  document.getElementById('removeImageBtn').style.display = 'none';
  document.getElementById('imageFileInput').value = '';
  window.currentImageFile = null;
}
```

**4. CSS実装**
```css
/* static/css/store_menus.css に追加 */
.image-upload-area {
  border: 2px dashed #ddd;
  border-radius: 4px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.image-upload-area:hover {
  border-color: #3498db;
  background-color: #f8f9fa;
}

.image-upload-area.drag-over {
  border-color: #27ae60;
  background-color: #e8f5e9;
}

.image-preview {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-preview img {
  max-width: 100%;
  max-height: 300px;
  border-radius: 4px;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.upload-icon {
  font-size: 48px;
}

.upload-hint {
  font-size: 12px;
  color: #7f8c8d;
}
```

**5. テスト実装**
```python
# tests/test_store_menus.py に追加

def test_upload_menu_image(client, auth_headers_store, menu_store_a, db_session):
    """メニュー画像をアップロードできる"""
    from io import BytesIO
    
    # テスト用画像ファイル
    image_data = BytesIO(b"fake image data")
    image_data.name = "test.jpg"
    
    response = client.post(
        f"/api/store/menus/{menu_store_a.id}/image",
        headers=auth_headers_store,
        files={"file": ("test.jpg", image_data, "image/jpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["image_url"].startswith("/static/uploads/menus/")

def test_upload_invalid_file_type(client, auth_headers_store, menu_store_a):
    """不正なファイル形式でエラーになる"""
    from io import BytesIO
    
    file_data = BytesIO(b"fake pdf data")
    file_data.name = "test.pdf"
    
    response = client.post(
        f"/api/store/menus/{menu_store_a.id}/image",
        headers=auth_headers_store,
        files={"file": ("test.pdf", file_data, "application/pdf")}
    )
    
    assert response.status_code == 400
```

#### ✅ 受け入れ基準

**機能要件**:
- [ ] ドラッグ&ドロップで画像をアップロードできる
- [ ] クリックでファイル選択ダイアログが開く
- [ ] 選択した画像がプレビュー表示される
- [ ] アップロード前にプレビューを確認できる
- [ ] 画像を削除できる（「画像を削除」ボタン）
- [ ] 既存画像を新しい画像で置き換えられる
- [ ] 古い画像ファイルが自動削除される

**バリデーション**:
- [ ] JPEG, PNG, GIF, WebP 以外のファイルはエラーになる
- [ ] 5MB を超えるファイルはエラーになる
- [ ] バリデーションエラー時に適切なメッセージが表示される

**UI/UX要件**:
- [ ] ドラッグオーバー時に視覚的フィードバックがある
- [ ] アップロード中にプログレス表示がある
- [ ] アップロード完了時にトースト通知が表示される

**セキュリティ要件**:
- [ ] owner, manager のみがアップロードできる
- [ ] 他店舗のメニュー画像はアップロードできない
- [ ] ファイルパストラバーサル攻撃を防止

**テスト要件**:
- [ ] ユニットテスト: 画像アップロードAPI
- [ ] ユニットテスト: 不正なファイル形式のエラー
- [ ] ユニットテスト: ファイルサイズ超過のエラー
- [ ] E2Eテスト: ドラッグ&ドロップの動作確認

---

## Issue #5: メニューの並び替え・ソート機能

### 📋 タイトル
**メニュー一覧の並び替え・ソート機能の実装（カラムヘッダークリック）**

### 📝 説明

#### 🎯 目的（実装内容）
メニュー一覧の並び替えを可能にし、スタッフが目的のメニューを素早く見つけられるようにします。カラムヘッダーをクリックするだけで昇順・降順を切り替えられる直感的なUIを提供します。

**実装する機能**:
- ✅ カラムヘッダーでソート（クリックで切替）
- ✅ 昇順・降順の表示（矢印アイコン）
- ✅ ソート状態の永続化（URLパラメータ）
- ✅ 複数カラムのソート対応

**ソート対応カラム**:
- 名前（あいうえお順/逆順）
- 価格（安い順/高い順）
- 作成日時（新しい順/古い順）
- 更新日時（最近更新順）

#### 🔧 タスク（技術仕様）

**1. バックエンドAPI拡張**
```python
# routers/store.py の get_all_menus を拡張

@router.get("/menus", response_model=MenuListResponse, summary="メニュー管理一覧")
def get_all_menus(
    is_available: Optional[bool] = Query(None, description="利用可能フラグでフィルタ"),
    page: int = Query(1, ge=1, description="ページ番号"),
    per_page: int = Query(20, ge=1, le=100, description="1ページあたりの件数"),
    sort_by: str = Query("created_at", regex="^(name|price|created_at|updated_at)$", description="ソートカラム"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="ソート順序"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager', 'staff']))
):
    """
    メニュー一覧取得（ソート対応）
    
    **ソート可能なカラム:**
    - name: 名前
    - price: 価格
    - created_at: 作成日時
    - updated_at: 更新日時
    
    **ソート順序:**
    - asc: 昇順
    - desc: 降順
    """
    # ユーザーが店舗に所属しているか確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
    # 自店舗のメニューのみを取得
    query = db.query(Menu).filter(Menu.store_id == current_user.store_id)
    
    # 利用可能フラグでフィルタ
    if is_available is not None:
        query = query.filter(Menu.is_available == is_available)
    
    # ソート適用
    order_column = getattr(Menu, sort_by)
    if sort_order == "asc":
        query = query.order_by(order_column.asc())
    else:
        query = query.order_by(order_column.desc())
    
    # 総件数を取得
    total = query.count()
    
    # ページネーション
    offset = (page - 1) * per_page
    menus = query.offset(offset).limit(per_page).all()
    
    return {"menus": menus, "total": total}
```

**2. フロントエンドHTML**
```html
<!-- templates/store_menus.html のテーブルヘッダー -->
<thead>
  <tr>
    <th>
      <button class="sort-header" data-column="name">
        名前 <span class="sort-icon" id="sort-icon-name"></span>
      </button>
    </th>
    <th>
      <button class="sort-header" data-column="price">
        価格 <span class="sort-icon" id="sort-icon-price"></span>
      </button>
    </th>
    <th>ステータス</th>
    <th>
      <button class="sort-header" data-column="created_at">
        作成日 <span class="sort-icon" id="sort-icon-created_at"></span>
      </button>
    </th>
    <th>
      <button class="sort-header" data-column="updated_at">
        更新日 <span class="sort-icon" id="sort-icon-updated_at"></span>
      </button>
    </th>
    <th>操作</th>
  </tr>
</thead>
```

**3. JavaScript実装**
```javascript
// static/js/store_menus.js に追加

let currentSort = {
  column: 'created_at',
  order: 'desc'
};

// ソート状態を管理
function setupSortHeaders() {
  const sortHeaders = document.querySelectorAll('.sort-header');
  
  sortHeaders.forEach(header => {
    header.addEventListener('click', () => {
      const column = header.dataset.column;
      
      // 同じカラムならorder切替、違うカラムならdesc
      if (currentSort.column === column) {
        currentSort.order = currentSort.order === 'asc' ? 'desc' : 'asc';
      } else {
        currentSort.column = column;
        currentSort.order = 'desc';
      }
      
      // ソートアイコン更新
      updateSortIcons();
      
      // メニュー一覧を再取得
      fetchMenus();
    });
  });
  
  // 初期表示のアイコン設定
  updateSortIcons();
}

// ソートアイコン更新
function updateSortIcons() {
  // すべてのアイコンをクリア
  document.querySelectorAll('.sort-icon').forEach(icon => {
    icon.textContent = '↕';
    icon.classList.remove('active');
  });
  
  // アクティブなソートのアイコンを設定
  const activeIcon = document.getElementById(`sort-icon-${currentSort.column}`);
  if (activeIcon) {
    activeIcon.textContent = currentSort.order === 'asc' ? '↑' : '↓';
    activeIcon.classList.add('active');
  }
}

// メニュー取得（ソート対応）
async function fetchMenus() {
  try {
    showLoading();
    
    const params = new URLSearchParams({
      page: currentPage,
      per_page: perPage,
      sort_by: currentSort.column,
      sort_order: currentSort.order
    });
    
    if (currentFilter !== null) {
      params.append('is_available', currentFilter);
    }
    
    const response = await fetch(`/api/store/menus?${params}`, {
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch menus');
    }
    
    const data = await response.json();
    renderMenuTable(data.menus);
    renderPagination(data.total);
    
    // URL更新（ブラウザ履歴）
    updateURL();
    
  } catch (error) {
    showToast('メニューの取得に失敗しました', 'error');
  } finally {
    hideLoading();
  }
}

// URL更新（履歴管理）
function updateURL() {
  const params = new URLSearchParams({
    page: currentPage,
    sort_by: currentSort.column,
    sort_order: currentSort.order
  });
  
  if (currentFilter !== null) {
    params.append('filter', currentFilter);
  }
  
  const newURL = `${window.location.pathname}?${params}`;
  window.history.replaceState({}, '', newURL);
}

// 初期化時にURLパラメータから復元
function restoreStateFromURL() {
  const params = new URLSearchParams(window.location.search);
  
  if (params.has('sort_by')) {
    currentSort.column = params.get('sort_by');
  }
  if (params.has('sort_order')) {
    currentSort.order = params.get('sort_order');
  }
  if (params.has('page')) {
    currentPage = parseInt(params.get('page'));
  }
  if (params.has('filter')) {
    currentFilter = params.get('filter') === 'true';
  }
}
```

**4. CSS実装**
```css
/* static/css/store_menus.css に追加 */
.sort-header {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 5px;
  width: 100%;
  text-align: left;
}

.sort-header:hover {
  background-color: #f8f9fa;
}

.sort-icon {
  color: #bdc3c7;
  font-size: 12px;
  transition: color 0.3s;
}

.sort-icon.active {
  color: #3498db;
  font-weight: bold;
}
```

**5. テスト実装**
```python
# tests/test_store_menus.py に追加

def test_sort_by_name_asc(client, auth_headers_store):
    """名前の昇順でソートできる"""
    response = client.get(
        "/api/store/menus?sort_by=name&sort_order=asc",
        headers=auth_headers_store
    )
    
    assert response.status_code == 200
    data = response.json()
    menus = data["menus"]
    
    # 名前が昇順になっているか確認
    names = [menu["name"] for menu in menus]
    assert names == sorted(names)

def test_sort_by_price_desc(client, auth_headers_store):
    """価格の降順でソートできる"""
    response = client.get(
        "/api/store/menus?sort_by=price&sort_order=desc",
        headers=auth_headers_store
    )
    
    assert response.status_code == 200
    data = response.json()
    menus = data["menus"]
    
    # 価格が降順になっているか確認
    prices = [menu["price"] for menu in menus]
    assert prices == sorted(prices, reverse=True)
```

#### ✅ 受け入れ基準

**機能要件**:
- [ ] カラムヘッダーをクリックするとソートされる
- [ ] 同じカラムを再度クリックすると昇順・降順が切り替わる
- [ ] ソート状態がアイコンで視覚的に表示される（↑ ↓）
- [ ] 名前、価格、作成日時、更新日時でソートできる
- [ ] ソート状態がURLパラメータに保存される
- [ ] ページリロード後もソート状態が維持される

**UI/UX要件**:
- [ ] ソート中のカラムヘッダーが強調表示される
- [ ] ソートアイコンが明確に表示される
- [ ] ソート切替がスムーズ（300ms以内）

**統合要件**:
- [ ] フィルタとソートが同時に機能する
- [ ] ページネーションとソートが同時に機能する
- [ ] ソート状態がページ遷移後も維持される

**テスト要件**:
- [ ] ユニットテスト: 各カラムの昇順ソート
- [ ] ユニットテスト: 各カラムの降順ソート
- [ ] E2Eテスト: カラムヘッダークリックの動作確認
- [ ] E2Eテスト: ソート状態の永続化確認

---

## Issue #6: メニュー検索機能

### 📋 タイトル
**メニュー検索機能の実装（キーワード検索・リアルタイム検索）**

### 📝 説明

#### 🎯 目的（実装内容）
メニュー数が増加した際に、特定のメニューを素早く見つけられる検索機能を実装します。メニュー名や説明文での部分一致検索により、スタッフの作業効率を向上させます。

**実装する機能**:
- ✅ メニュー名・説明文での部分一致検索
- ✅ リアルタイム検索（入力中に自動更新）
- ✅ 検索結果の件数表示
- ✅ 検索キーワードのハイライト表示
- ✅ 検索クリアボタン

#### 🔧 タスク（技術仕様）

**1. バックエンドAPI拡張**
```python
# routers/store.py の get_all_menus に追加

@router.get("/menus", response_model=MenuListResponse)
def get_all_menus(
    is_available: Optional[bool] = Query(None),
    keyword: Optional[str] = Query(None, max_length=255, description="検索キーワード"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager', 'staff']))
):
    """
    メニュー一覧取得（検索対応）
    
    **検索対象**:
    - メニュー名（name）
    - 説明文（description）
    """
    query = db.query(Menu).filter(Menu.store_id == current_user.store_id)
    
    # キーワード検索
    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                Menu.name.ilike(search_pattern),
                Menu.description.ilike(search_pattern)
            )
        )
    
    # フィルタ・ソート・ページネーション
    # ... (既存の実装)
    
    total = query.count()
    menus = query.offset(offset).limit(per_page).all()
    
    return {"menus": menus, "total": total}
```

**2. フロントエンドHTML**
```html
<!-- templates/store_menus.html に追加 -->
<div class="search-container">
  <div class="search-box">
    <span class="search-icon">🔍</span>
    <input 
      type="text" 
      id="searchInput" 
      placeholder="メニュー名で検索..." 
      autocomplete="off"
    >
    <button id="clearSearchBtn" class="clear-btn" style="display:none;">✕</button>
  </div>
  <div id="searchResults" class="search-results">
    <span id="resultCount"></span>
  </div>
</div>
```

**3. JavaScript実装**
```javascript
// static/js/store_menus.js に追加

let searchKeyword = '';
let searchDebounceTimer = null;

// 検索設定
function setupSearch() {
  const searchInput = document.getElementById('searchInput');
  const clearBtn = document.getElementById('clearSearchBtn');
  
  // リアルタイム検索（デバウンス 500ms）
  searchInput.addEventListener('input', (e) => {
    clearTimeout(searchDebounceTimer);
    
    searchKeyword = e.target.value.trim();
    
    // クリアボタン表示切替
    if (searchKeyword) {
      clearBtn.style.display = 'block';
    } else {
      clearBtn.style.display = 'none';
    }
    
    // デバウンス
    searchDebounceTimer = setTimeout(() => {
      currentPage = 1; // 検索時は1ページ目に戻る
      fetchMenus();
    }, 500);
  });
  
  // クリアボタン
  clearBtn.addEventListener('click', () => {
    searchInput.value = '';
    searchKeyword = '';
    clearBtn.style.display = 'none';
    currentPage = 1;
    fetchMenus();
  });
  
  // Enterキーで検索実行
  searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      clearTimeout(searchDebounceTimer);
      currentPage = 1;
      fetchMenus();
    }
  });
}

// メニュー取得（検索対応）
async function fetchMenus() {
  const params = new URLSearchParams({
    page: currentPage,
    per_page: perPage,
    sort_by: currentSort.column,
    sort_order: currentSort.order
  });
  
  if (currentFilter !== null) {
    params.append('is_available', currentFilter);
  }
  
  if (searchKeyword) {
    params.append('keyword', searchKeyword);
  }
  
  // API呼び出し
  const response = await fetch(`/api/store/menus?${params}`, {
    headers: getAuthHeaders()
  });
  
  const data = await response.json();
  renderMenuTable(data.menus);
  renderPagination(data.total);
  
  // 検索結果件数表示
  if (searchKeyword) {
    document.getElementById('resultCount').textContent = 
      `「${searchKeyword}」の検索結果: ${data.total}件`;
  } else {
    document.getElementById('resultCount').textContent = '';
  }
}

// 検索キーワードのハイライト
function highlightKeyword(text, keyword) {
  if (!keyword) return text;
  
  const regex = new RegExp(`(${keyword})`, 'gi');
  return text.replace(regex, '<mark>$1</mark>');
}
```

**4. CSS実装**
```css
/* static/css/store_menus.css に追加 */
.search-container {
  margin-bottom: 20px;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
  max-width: 500px;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: #7f8c8d;
  pointer-events: none;
}

#searchInput {
  width: 100%;
  padding: 10px 40px 10px 40px;
  border: 2px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
  transition: border-color 0.3s;
}

#searchInput:focus {
  outline: none;
  border-color: #3498db;
}

.clear-btn {
  position: absolute;
  right: 10px;
  background: none;
  border: none;
  color: #7f8c8d;
  font-size: 20px;
  cursor: pointer;
  padding: 5px;
}

.clear-btn:hover {
  color: #e74c3c;
}

.search-results {
  margin-top: 10px;
  color: #7f8c8d;
  font-size: 14px;
}

mark {
  background-color: #fff59d;
  padding: 2px 4px;
  border-radius: 2px;
}
```

**5. テスト実装**
```python
# tests/test_store_menus.py に追加

def test_search_menus_by_name(client, auth_headers_store, db_session, store_a):
    """メニュー名で検索できる"""
    # テストメニュー作成
    from models import Menu
    menu1 = Menu(name="春の弁当", price=1200, store_id=store_a.id)
    menu2 = Menu(name="夏の弁当", price=1300, store_id=store_a.id)
    menu3 = Menu(name="特製弁当", price=1500, store_id=store_a.id)
    db_session.add_all([menu1, menu2, menu3])
    db_session.commit()
    
    response = client.get(
        "/api/store/menus?keyword=春",
        headers=auth_headers_store
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "春" in data["menus"][0]["name"]

def test_search_menus_by_description(client, auth_headers_store):
    """説明文で検索できる"""
    response = client.get(
        "/api/store/menus?keyword=限定",
        headers=auth_headers_store
    )
    
    assert response.status_code == 200

def test_search_no_results(client, auth_headers_store):
    """検索結果0件の場合"""
    response = client.get(
        "/api/store/menus?keyword=存在しないメニュー",
        headers=auth_headers_store
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["menus"]) == 0
```

#### ✅ 受け入れ基準

**機能要件**:
- [ ] 検索ボックスにキーワードを入力すると検索される
- [ ] メニュー名での部分一致検索が機能する
- [ ] 説明文での部分一致検索が機能する
- [ ] 大文字・小文字を区別しない検索ができる
- [ ] 検索結果件数が表示される
- [ ] 検索キーワードがハイライト表示される
- [ ] クリアボタンで検索をリセットできる

**UI/UX要件**:
- [ ] 入力中にリアルタイム検索される（デバウンス 500ms）
- [ ] 検索中のローディング表示がある
- [ ] Enterキーで即座に検索実行できる
- [ ] 検索結果0件時にメッセージが表示される

**統合要件**:
- [ ] フィルタと検索が同時に機能する
- [ ] ソートと検索が同時に機能する
- [ ] ページネーションと検索が同時に機能する
- [ ] 検索状態がURLパラメータに保存される

**パフォーマンス要件**:
- [ ] 検索レスポンスが500ms以内
- [ ] デバウンスでAPIリクエスト数を最適化

**テスト要件**:
- [ ] ユニットテスト: メニュー名検索
- [ ] ユニットテスト: 説明文検索
- [ ] ユニットテスト: 検索結果0件
- [ ] E2Eテスト: リアルタイム検索の動作確認

---

## Issue #7: 一括操作機能（複数メニューの一括公開/非公開）

### 📋 タイトル
**メニュー一括操作機能の実装（複数選択・一括公開/非公開）**

### 📝 説明

#### 🎯 目的（実装内容）
複数のメニューを同時に公開/非公開にできる一括操作機能を実装し、季節の変わり目などでの大量メニュー更新を効率化します。例えば、夏メニュー10件を一括で非公開にし、秋メニュー10件を一括で公開するような操作が可能になります。

**実装する機能**:
- ✅ チェックボックスで複数メニュー選択
- ✅ 一括公開ボタン
- ✅ 一括非公開ボタン
- ✅ 全選択/全解除機能
- ✅ 選択件数の表示
- ✅ 一括操作の確認ダイアログ

#### 🔧 タスク（技術仕様）

**1. 新規APIエンドポイント実装**
```python
# routers/store.py に追加

from typing import List
from pydantic import BaseModel

class BulkAvailabilityUpdate(BaseModel):
    """一括公開/非公開リクエスト"""
    menu_ids: List[int] = Field(..., min_items=1, description="更新対象のメニューIDリスト")
    is_available: bool = Field(..., description="設定する公開状態")

@router.put("/menus/bulk-availability", summary="メニュー一括公開/非公開")
def bulk_update_availability(
    update_data: BulkAvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager']))
):
    """
    複数メニューの公開/非公開を一括更新
    
    **必要な権限:** owner, manager
    
    **パラメータ:**
    - menu_ids: 更新対象のメニューIDリスト（1件以上必須）
    - is_available: 設定する公開状態（true=公開, false=非公開）
    
    **戻り値:**
    - updated_count: 更新されたメニュー数
    - message: 結果メッセージ
    
    **エラー:**
    - 400: ユーザーが店舗に所属していない
    - 403: 権限不足（staff は実行不可）
    - 404: 指定されたメニューが見つからない、または他店舗のメニュー
    """
    # ユーザーが店舗に所属しているか確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
    # 自店舗のメニューのみ対象
    menus = db.query(Menu).filter(
        Menu.id.in_(update_data.menu_ids),
        Menu.store_id == current_user.store_id
    ).all()
    
    if not menus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No menus found or access denied"
        )
    
    # 一括更新
    updated_count = 0
    for menu in menus:
        menu.is_available = update_data.is_available
        updated_count += 1
    
    db.commit()
    
    status_text = "公開" if update_data.is_available else "非公開"
    
    return {
        "message": f"{updated_count}件のメニューを{status_text}に設定しました",
        "updated_count": updated_count
    }
```

**2. フロントエンドHTML**
```html
<!-- templates/store_menus.html に追加 -->
<div class="bulk-actions" id="bulkActions" style="display:none;">
  <div class="bulk-info">
    <label class="checkbox-label">
      <input type="checkbox" id="selectAll">
      <span id="selectedCount">0件選択中</span>
    </label>
  </div>
  <div class="bulk-buttons">
    <button class="btn-success btn-sm" id="bulkPublishBtn">
      一括公開
    </button>
    <button class="btn-warning btn-sm" id="bulkUnpublishBtn">
      一括非公開
    </button>
  </div>
</div>

<table class="menu-table">
  <thead>
    <tr>
      <th width="40">
        <input type="checkbox" id="selectAllHeader">
      </th>
      <th>名前</th>
      <!-- ... -->
    </tr>
  </thead>
  <tbody id="menuTableBody">
    <!-- 各行にチェックボックス追加 -->
    <tr>
      <td>
        <input type="checkbox" class="menu-checkbox" data-menu-id="123">
      </td>
      <td>特製弁当</td>
      <!-- ... -->
    </tr>
  </tbody>
</table>
```

**3. JavaScript実装**
```javascript
// static/js/store_menus.js に追加

let selectedMenuIds = new Set();

// 一括操作設定
function setupBulkActions() {
  const selectAll = document.getElementById('selectAll');
  const selectAllHeader = document.getElementById('selectAllHeader');
  const bulkPublishBtn = document.getElementById('bulkPublishBtn');
  const bulkUnpublishBtn = document.getElementById('bulkUnpublishBtn');
  
  // 全選択/全解除
  selectAll.addEventListener('change', toggleSelectAll);
  selectAllHeader.addEventListener('change', toggleSelectAll);
  
  // 一括公開
  bulkPublishBtn.addEventListener('click', () => {
    confirmBulkUpdate(true);
  });
  
  // 一括非公開
  bulkUnpublishBtn.addEventListener('click', () => {
    confirmBulkUpdate(false);
  });
}

// 全選択/全解除
function toggleSelectAll(e) {
  const checkboxes = document.querySelectorAll('.menu-checkbox');
  const isChecked = e.target.checked;
  
  checkboxes.forEach(checkbox => {
    checkbox.checked = isChecked;
    const menuId = parseInt(checkbox.dataset.menuId);
    
    if (isChecked) {
      selectedMenuIds.add(menuId);
    } else {
      selectedMenuIds.delete(menuId);
    }
  });
  
  updateBulkActionsUI();
}

// チェックボックス変更時
function handleCheckboxChange(menuId, isChecked) {
  if (isChecked) {
    selectedMenuIds.add(menuId);
  } else {
    selectedMenuIds.delete(menuId);
  }
  
  updateBulkActionsUI();
}

// 一括操作UIの更新
function updateBulkActionsUI() {
  const bulkActions = document.getElementById('bulkActions');
  const selectedCount = document.getElementById('selectedCount');
  const count = selectedMenuIds.size;
  
  if (count > 0) {
    bulkActions.style.display = 'flex';
    selectedCount.textContent = `${count}件選択中`;
  } else {
    bulkActions.style.display = 'none';
  }
}

// 一括更新確認
async function confirmBulkUpdate(isAvailable) {
  const count = selectedMenuIds.size;
  const action = isAvailable ? '公開' : '非公開';
  
  const confirmed = await showConfirmDialog({
    title: '確認',
    message: `選択した${count}件のメニューを${action}にしますか?`,
    confirmText: action + 'にする',
    cancelText: 'キャンセル'
  });
  
  if (!confirmed) return;
  
  try {
    showLoading();
    
    const response = await fetch('/api/store/menus/bulk-availability', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
      },
      body: JSON.stringify({
        menu_ids: Array.from(selectedMenuIds),
        is_available: isAvailable
      })
    });
    
    if (!response.ok) {
      throw new Error('一括更新に失敗しました');
    }
    
    const result = await response.json();
    showToast(result.message, 'success');
    
    // 選択解除
    selectedMenuIds.clear();
    updateBulkActionsUI();
    
    // メニュー一覧を更新
    await fetchMenus();
    
  } catch (error) {
    showToast('一括更新に失敗しました: ' + error.message, 'error');
  } finally {
    hideLoading();
  }
}
```

**4. CSS実装**
```css
/* static/css/store_menus.css に追加 */
.bulk-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background-color: #e3f2fd;
  border: 1px solid #90caf9;
  border-radius: 4px;
  margin-bottom: 15px;
}

.bulk-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.bulk-buttons {
  display: flex;
  gap: 10px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.menu-checkbox {
  cursor: pointer;
}
```

**5. テスト実装**
```python
# tests/test_store_menus.py に追加

def test_bulk_update_availability(client, auth_headers_store, db_session, store_a):
    """複数メニューを一括更新できる"""
    from models import Menu
    
    # テストメニュー作成
    menu1 = Menu(name="弁当1", price=1000, is_available=True, store_id=store_a.id)
    menu2 = Menu(name="弁当2", price=1100, is_available=True, store_id=store_a.id)
    menu3 = Menu(name="弁当3", price=1200, is_available=True, store_id=store_a.id)
    db_session.add_all([menu1, menu2, menu3])
    db_session.commit()
    
    response = client.put(
        "/api/store/menus/bulk-availability",
        headers=auth_headers_store,
        json={
            "menu_ids": [menu1.id, menu2.id, menu3.id],
            "is_available": False
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["updated_count"] == 3
    
    # DBで確認
    db_session.refresh(menu1)
    db_session.refresh(menu2)
    db_session.refresh(menu3)
    assert menu1.is_available is False
    assert menu2.is_available is False
    assert menu3.is_available is False

def test_bulk_update_empty_list(client, auth_headers_store):
    """空のIDリストでエラーになる"""
    response = client.put(
        "/api/store/menus/bulk-availability",
        headers=auth_headers_store,
        json={
            "menu_ids": [],
            "is_available": False
        }
    )
    
    assert response.status_code == 422  # バリデーションエラー

def test_bulk_update_other_store_menus(client, auth_headers_store, store_b):
    """他店舗のメニューは更新できない"""
    from models import Menu
    
    menu = Menu(name="他店舗弁当", price=1000, store_id=store_b.id)
    db_session.add(menu)
    db_session.commit()
    
    response = client.put(
        "/api/store/menus/bulk-availability",
        headers=auth_headers_store,
        json={
            "menu_ids": [menu.id],
            "is_available": False
        }
    )
    
    assert response.status_code == 404
```

#### ✅ 受け入れ基準

**機能要件**:
- [ ] チェックボックスで複数メニューを選択できる
- [ ] 全選択/全解除チェックボックスが機能する
- [ ] 選択件数が表示される
- [ ] 「一括公開」ボタンで選択メニューが公開される
- [ ] 「一括非公開」ボタンで選択メニューが非公開になる
- [ ] 一括操作前に確認ダイアログが表示される
- [ ] 一括操作後に選択が解除される
- [ ] 一括操作後にメニュー一覧が自動更新される

**UI/UX要件**:
- [ ] 選択中のみ一括操作バーが表示される
- [ ] 一括操作中にローディング表示がある
- [ ] 操作成功時にトースト通知が表示される
- [ ] 更新件数がメッセージに表示される

**セキュリティ要件**:
- [ ] owner, manager のみが一括操作できる
- [ ] 他店舗のメニューは操作できない
- [ ] 空のIDリストはバリデーションエラー

**パフォーマンス要件**:
- [ ] 100件の一括更新が3秒以内に完了する

**テスト要件**:
- [ ] ユニットテスト: 一括公開
- [ ] ユニットテスト: 一括非公開
- [ ] ユニットテスト: 空リストのバリデーション
- [ ] ユニットテスト: 他店舗メニューのアクセス拒否
- [ ] E2Eテスト: チェックボックス選択の動作確認

---

## Issue #8: メニューカテゴリ管理機能

### 📋 タイトル
**メニューカテゴリ管理機能の実装（カテゴリCRUD・フィルタ）**

### 📝 説明

#### 🎯 目的（実装内容）
メニューをカテゴリ別に分類し、顧客の閲覧性と店舗の管理性を向上させます。和食、洋食、中華などのカテゴリを作成し、メニューを分類することで、大量のメニューを効率的に管理できるようになります。

**実装する機能**:
- ✅ カテゴリマスタ管理（CRUD）
- ✅ メニューへのカテゴリ紐付け
- ✅ カテゴリ別フィルタ
- ✅ カテゴリの表示順序設定
- ✅ カテゴリの有効/無効切替

#### 🔧 タスク（技術仕様）

**1. データベーススキーマ追加**
```python
# models.py に追加

class MenuCategory(Base):
    """メニューカテゴリテーブル"""
    __tablename__ = "menu_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    display_order = Column(Integer, default=0)  # 表示順序
    is_active = Column(Boolean, default=True)   # 有効/無効
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # リレーションシップ
    store = relationship("Store", back_populates="menu_categories")
    menus = relationship("Menu", back_populates="category")

# Menu モデルに追加
category_id = Column(Integer, ForeignKey("menu_categories.id", ondelete="SET NULL"), nullable=True, index=True)
category = relationship("MenuCategory", back_populates="menus")
```

**2. マイグレーション作成**
```bash
# Alembic マイグレーション
alembic revision --autogenerate -m "add_menu_categories"
alembic upgrade head
```

**3. APIエンドポイント実装**
```python
# routers/store.py に追加

# カテゴリ一覧
@router.get("/menu-categories", response_model=List[MenuCategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager', 'staff']))
):
    """カテゴリ一覧取得"""
    categories = db.query(MenuCategory).filter(
        MenuCategory.store_id == current_user.store_id
    ).order_by(MenuCategory.display_order).all()
    return categories

# カテゴリ作成
@router.post("/menu-categories", response_model=MenuCategoryResponse)
def create_category(
    category: MenuCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager']))
):
    """カテゴリ作成"""
    db_category = MenuCategory(**category.dict(), store_id=current_user.store_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# カテゴリ更新
@router.put("/menu-categories/{category_id}", response_model=MenuCategoryResponse)
def update_category(
    category_id: int,
    category_update: MenuCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager']))
):
    """カテゴリ更新"""
    category = db.query(MenuCategory).filter(
        MenuCategory.id == category_id,
        MenuCategory.store_id == current_user.store_id
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = category_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    return category

# カテゴリ削除
@router.delete("/menu-categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner']))
):
    """カテゴリ削除（メニューはカテゴリなしになる）"""
    category = db.query(MenuCategory).filter(
        MenuCategory.id == category_id,
        MenuCategory.store_id == current_user.store_id
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}

# メニュー一覧にカテゴリフィルタ追加
@router.get("/menus", response_model=MenuListResponse)
def get_all_menus(
    category_id: Optional[int] = Query(None, description="カテゴリIDでフィルタ"),
    # ... 既存のパラメータ
):
    """メニュー一覧取得（カテゴリフィルタ対応）"""
    query = db.query(Menu).filter(Menu.store_id == current_user.store_id)
    
    # カテゴリフィルタ
    if category_id is not None:
        query = query.filter(Menu.category_id == category_id)
    
    # ... 既存の処理
```

**4. スキーマ定義**
```python
# schemas.py に追加

class MenuCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_order: int = Field(default=0)
    is_active: bool = Field(default=True)

class MenuCategoryCreate(MenuCategoryBase):
    pass

class MenuCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_order: Optional[int] = None
    is_active: Optional[bool] = None

class MenuCategoryResponse(MenuCategoryBase):
    id: int
    store_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# MenuResponse にカテゴリ情報追加
class MenuResponse(MenuBase):
    # ... 既存のフィールド
    category: Optional[MenuCategoryResponse] = None
```

**5. フロントエンド実装**
```html
<!-- カテゴリ管理画面 -->
<div class="category-section">
  <h3>カテゴリ管理</h3>
  <button class="btn-primary" onclick="openCategoryModal()">
    + カテゴリ追加
  </button>
  
  <div class="category-list" id="categoryList">
    <!-- カテゴリ一覧 -->
  </div>
</div>

<!-- カテゴリフィルタ -->
<div class="category-filter">
  <button class="filter-btn active" data-category="all">すべて</button>
  <button class="filter-btn" data-category="1">和食</button>
  <button class="filter-btn" data-category="2">洋食</button>
  <button class="filter-btn" data-category="3">中華</button>
</div>
```

#### ✅ 受け入れ基準

**機能要件**:
- [ ] カテゴリを作成できる
- [ ] カテゴリを編集できる
- [ ] カテゴリを削除できる
- [ ] カテゴリの表示順序を設定できる
- [ ] カテゴリの有効/無効を切り替えられる
- [ ] メニューにカテゴリを設定できる
- [ ] カテゴリ別にメニューをフィルタできる
- [ ] カテゴリなしのメニューも表示できる

**データ整合性**:
- [ ] カテゴリ削除時にメニューはカテゴリなしになる
- [ ] 他店舗のカテゴリにはアクセスできない

**テスト要件**:
- [ ] ユニットテスト: カテゴリCRUD
- [ ] ユニットテスト: カテゴリフィルタ
- [ ] E2Eテスト: カテゴリ管理画面

---

## Issue #9: 在庫数管理・自動在庫切れ機能

### 📋 タイトル
**在庫数管理・自動在庫切れ機能の実装（在庫追跡・アラート）**

### 📝 説明

#### 🎯 目的（実装内容）
在庫数を管理し、在庫切れ時に自動的にメニューを非公開にすることで、在庫切れ商品の注文を防止します。また、在庫が少なくなった際にアラートを表示し、スタッフに補充を促します。

**実装する機能**:
- ✅ 在庫数の管理（設定・表示・編集）
- ✅ 注文時の自動在庫減算
- ✅ 在庫切れ時の自動非公開
- ✅ 在庫切れ閾値の設定
- ✅ 在庫アラート通知
- ✅ 在庫履歴の記録

#### 🔧 タスク（技術仕様）

**1. データベーススキーマ拡張**
```python
# models.py の Menu モデルに追加

stock_quantity = Column(Integer, default=0)                     # 在庫数
low_stock_threshold = Column(Integer, default=5)                # 在庫切れ閾値
auto_disable_on_out_of_stock = Column(Boolean, default=True)    # 在庫切れ時に自動非公開
unlimited_stock = Column(Boolean, default=False)                # 無制限在庫フラグ

# 在庫履歴テーブル追加
class MenuStockHistory(Base):
    """メニュー在庫履歴テーブル"""
    __tablename__ = "menu_stock_history"
    
    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey("menus.id", ondelete="CASCADE"), nullable=False, index=True)
    change_type = Column(String(50), nullable=False)  # "order", "restock", "adjustment"
    quantity_before = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    quantity_change = Column(Integer, nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**2. 注文処理時の在庫減算ロジック**
```python
# routers/customer.py の注文作成処理に追加

@router.post("/orders", response_model=OrderResponse)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_customer)
):
    """注文作成（在庫確認・減算付き）"""
    
    # メニュー取得
    menu = db.query(Menu).filter(Menu.id == order_data.menu_id).first()
    
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    # 在庫確認（無制限在庫でない場合）
    if not menu.unlimited_stock:
        if menu.stock_quantity < order_data.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Available: {menu.stock_quantity}"
            )
        
        # 在庫減算
        quantity_before = menu.stock_quantity
        menu.stock_quantity -= order_data.quantity
        quantity_after = menu.stock_quantity
        
        # 在庫履歴記録
        stock_history = MenuStockHistory(
            menu_id=menu.id,
            change_type="order",
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            quantity_change=-order_data.quantity,
            changed_by=current_user.id,
            notes=f"Order placed (quantity: {order_data.quantity})"
        )
        db.add(stock_history)
        
        # 在庫切れチェック
        if menu.stock_quantity == 0 and menu.auto_disable_on_out_of_stock:
            menu.is_available = False
            # アラート通知（実装は別途）
            send_out_of_stock_alert(menu, current_user.store_id)
        
        # 低在庫アラート
        elif menu.stock_quantity <= menu.low_stock_threshold:
            send_low_stock_alert(menu, current_user.store_id)
    
    # 注文作成
    # ... 既存の処理
    
    db.commit()
    return order
```

**3. 在庫管理APIエンドポイント**
```python
# routers/store.py に追加

# 在庫更新（補充・調整）
@router.put("/menus/{menu_id}/stock", response_model=MenuResponse)
def update_stock(
    menu_id: int,
    stock_update: MenuStockUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager']))
):
    """
    在庫数を更新
    
    **パラメータ:**
    - action: "set" (設定), "add" (追加), "subtract" (減算)
    - quantity: 数量
    - notes: メモ
    """
    menu = db.query(Menu).filter(
        Menu.id == menu_id,
        Menu.store_id == current_user.store_id
    ).first()
    
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    quantity_before = menu.stock_quantity
    
    # 在庫操作
    if stock_update.action == "set":
        menu.stock_quantity = stock_update.quantity
    elif stock_update.action == "add":
        menu.stock_quantity += stock_update.quantity
    elif stock_update.action == "subtract":
        menu.stock_quantity = max(0, menu.stock_quantity - stock_update.quantity)
    
    quantity_after = menu.stock_quantity
    quantity_change = quantity_after - quantity_before
    
    # 在庫履歴記録
    stock_history = MenuStockHistory(
        menu_id=menu.id,
        change_type="adjustment",
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        quantity_change=quantity_change,
        changed_by=current_user.id,
        notes=stock_update.notes
    )
    db.add(stock_history)
    
    # 在庫復活時は自動公開
    if quantity_before == 0 and quantity_after > 0:
        menu.is_available = True
    
    db.commit()
    db.refresh(menu)
    
    return menu

# 在庫履歴取得
@router.get("/menus/{menu_id}/stock-history")
def get_stock_history(
    menu_id: int,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager', 'staff']))
):
    """在庫変更履歴を取得"""
    # ... 実装
```

**4. フロントエンド実装**
```html
<!-- 在庫管理セクション -->
<div class="stock-section">
  <label>在庫数</label>
  <div class="stock-controls">
    <input type="number" id="stockQuantity" min="0" value="100">
    <label>
      <input type="checkbox" id="unlimitedStock">
      無制限在庫
    </label>
  </div>
  
  <label>在庫切れ閾値</label>
  <input type="number" id="lowStockThreshold" min="0" value="5">
  <small>この数量以下になるとアラート表示</small>
  
  <label>
    <input type="checkbox" id="autoDisable" checked>
    在庫切れ時に自動非公開
  </label>
</div>

<!-- 在庫アラート表示 -->
<div class="alert alert-warning" id="lowStockAlert" style="display:none;">
  <strong>⚠ 在庫切れ間近:</strong>
  <span id="lowStockMenus"></span>
</div>
```

#### ✅ 受け入れ基準

**機能要件**:
- [ ] メニューに在庫数を設定できる
- [ ] 在庫切れ閾値を設定できる
- [ ] 無制限在庫フラグを設定できる
- [ ] 注文時に在庫が自動減算される
- [ ] 在庫0で自動非公開になる（設定時）
- [ ] 在庫補充時に自動公開される
- [ ] 在庫切れ閾値以下でアラート表示される
- [ ] 在庫履歴が記録される

**データ整合性**:
- [ ] 在庫がマイナスにならない
- [ ] 在庫不足時に注文ができない
- [ ] トランザクション保証（在庫と注文の整合性）

**テスト要件**:
- [ ] ユニットテスト: 在庫減算
- [ ] ユニットテスト: 在庫不足エラー
- [ ] ユニットテスト: 自動非公開
- [ ] E2Eテスト: 注文フロー全体

---

## Issue #10: メニュー変更履歴・監査ログ

### 📋 タイトル
**メニュー変更履歴・監査ログ機能の実装（変更追跡・監査対応）**

### 📝 説明

#### 🎯 目的（実装内容）
メニューの変更履歴を記録し、監査・トラブルシューティング・データ分析に活用します。誰が、いつ、何を変更したかを追跡可能にすることで、不正操作の防止と問題発生時の原因特定を容易にします。

**実装する機能**:
- ✅ 価格変更履歴の記録
- ✅ 変更者・変更日時の記録
- ✅ 変更内容の差分表示
- ✅ 変更履歴の検索・フィルタ
- ✅ 変更履歴の閲覧画面
- ✅ CSV/Excel エクスポート

#### 🔧 タスク（技術仕様）

**1. データベーススキーマ追加**
```python
# models.py に追加

class MenuChangeLog(Base):
    """メニュー変更履歴テーブル"""
    __tablename__ = "menu_change_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey("menus.id", ondelete="CASCADE"), nullable=False, index=True)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    change_type = Column(String(50), nullable=False)  # "created", "updated", "deleted", "availability_changed"
    field_name = Column(String(100))  # 変更されたフィールド名
    old_value = Column(Text)          # 変更前の値（JSON）
    new_value = Column(Text)          # 変更後の値（JSON）
    ip_address = Column(String(45))   # IPアドレス
    user_agent = Column(String(255))  # ユーザーエージェント
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # リレーションシップ
    menu = relationship("Menu")
    user = relationship("User")
```

**2. 変更履歴記録ロジック**
```python
# routers/store.py に変更履歴記録を追加

import json
from fastapi import Request

def log_menu_change(
    db: Session,
    menu_id: int,
    changed_by: int,
    change_type: str,
    old_values: dict = None,
    new_values: dict = None,
    request: Request = None
):
    """メニュー変更履歴を記録"""
    
    # 変更されたフィールドを検出
    if old_values and new_values:
        for field, new_val in new_values.items():
            old_val = old_values.get(field)
            if old_val != new_val:
                log = MenuChangeLog(
                    menu_id=menu_id,
                    changed_by=changed_by,
                    change_type=change_type,
                    field_name=field,
                    old_value=json.dumps(old_val, ensure_ascii=False) if old_val is not None else None,
                    new_value=json.dumps(new_val, ensure_ascii=False) if new_val is not None else None,
                    ip_address=request.client.host if request else None,
                    user_agent=request.headers.get("user-agent") if request else None
                )
                db.add(log)
    else:
        # 作成/削除の場合
        log = MenuChangeLog(
            menu_id=menu_id,
            changed_by=changed_by,
            change_type=change_type,
            old_value=json.dumps(old_values, ensure_ascii=False) if old_values else None,
            new_value=json.dumps(new_values, ensure_ascii=False) if new_values else None,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        db.add(log)

# メニュー更新エンドポイントに追加
@router.put("/menus/{menu_id}", response_model=MenuResponse)
def update_menu(
    menu_id: int,
    menu_update: MenuUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager']))
):
    """メニュー更新（変更履歴記録付き）"""
    
    menu = db.query(Menu).filter(
        Menu.id == menu_id,
        Menu.store_id == current_user.store_id
    ).first()
    
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    # 変更前の値を保存
    old_values = {
        "name": menu.name,
        "price": menu.price,
        "description": menu.description,
        "is_available": menu.is_available
    }
    
    # 更新データを適用
    update_data = menu_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(menu, field, value)
    
    # 変更履歴記録
    log_menu_change(
        db=db,
        menu_id=menu_id,
        changed_by=current_user.id,
        change_type="updated",
        old_values=old_values,
        new_values=update_data,
        request=request
    )
    
    db.commit()
    db.refresh(menu)
    
    return menu
```

**3. 変更履歴閲覧API**
```python
# routers/store.py に追加

@router.get("/menus/{menu_id}/change-logs")
def get_menu_change_logs(
    menu_id: int,
    change_type: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager']))
):
    """
    メニュー変更履歴を取得
    
    **フィルタ:**
    - change_type: 変更タイプ
    - start_date: 開始日
    - end_date: 終了日
    """
    # メニューが自店舗のものか確認
    menu = db.query(Menu).filter(
        Menu.id == menu_id,
        Menu.store_id == current_user.store_id
    ).first()
    
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    # 変更履歴取得
    query = db.query(MenuChangeLog).filter(MenuChangeLog.menu_id == menu_id)
    
    # フィルタ適用
    if change_type:
        query = query.filter(MenuChangeLog.change_type == change_type)
    
    if start_date:
        query = query.filter(MenuChangeLog.changed_at >= start_date)
    
    if end_date:
        query = query.filter(MenuChangeLog.changed_at <= end_date)
    
    # ページネーション
    total = query.count()
    offset = (page - 1) * per_page
    logs = query.order_by(MenuChangeLog.changed_at.desc()).offset(offset).limit(per_page).all()
    
    return {
        "logs": logs,
        "total": total,
        "page": page,
        "per_page": per_page
    }

# 全メニューの変更履歴取得（監査用）
@router.get("/change-logs/all")
def get_all_change_logs(
    change_type: Optional[str] = Query(None),
    changed_by: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner']))
):
    """全メニューの変更履歴を取得（オーナー専用）"""
    # ... 実装
```

**4. フロントエンド実装**
```html
<!-- 変更履歴画面 -->
<div class="change-log-section">
  <h3>変更履歴</h3>
  
  <div class="log-filters">
    <select id="changeTypeFilter">
      <option value="">すべての変更</option>
      <option value="updated">更新</option>
      <option value="availability_changed">公開/非公開</option>
    </select>
    
    <input type="date" id="startDate">
    <input type="date" id="endDate">
    
    <button onclick="filterLogs()">フィルタ</button>
    <button onclick="exportLogs()">CSVエクスポート</button>
  </div>
  
  <table class="log-table">
    <thead>
      <tr>
        <th>日時</th>
        <th>変更者</th>
        <th>変更内容</th>
        <th>変更前</th>
        <th>変更後</th>
      </tr>
    </thead>
    <tbody id="logTableBody">
      <!-- 変更履歴一覧 -->
    </tbody>
  </table>
</div>
```

#### ✅ 受け入れ基準

**機能要件**:
- [ ] メニュー作成時に履歴が記録される
- [ ] メニュー更新時に変更内容が記録される
- [ ] メニュー削除時に履歴が記録される
- [ ] 変更者・日時が記録される
- [ ] 変更前後の値が記録される
- [ ] IPアドレス・ユーザーエージェントが記録される
- [ ] 変更履歴を閲覧できる
- [ ] 変更履歴をフィルタできる
- [ ] 変更履歴をエクスポートできる

**セキュリティ・監査**:
- [ ] owner のみが全履歴を閲覧できる
- [ ] 変更履歴は削除できない（監査証跡）
- [ ] 変更履歴は改ざんできない

**パフォーマンス**:
- [ ] 大量の履歴でもページネーションで快適に閲覧できる
- [ ] 履歴記録がメイン処理を遅延させない

**テスト要件**:
- [ ] ユニットテスト: 履歴記録
- [ ] ユニットテスト: 履歴取得
- [ ] E2Eテスト: 変更履歴画面

---

**作成者**: GitHub Copilot  
**最終更新**: 2025年10月13日
