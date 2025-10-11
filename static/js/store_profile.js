/**
 * 店舗プロフィール画面のJavaScriptロジック
 */

// グローバル変数
let storeData = null;
let userRoles = [];
let isOwner = false;
let originalImageUrl = null;

// 初期化
document.addEventListener('DOMContentLoaded', async () => {
    // 認証チェック
    if (!Auth.requireRole('store')) return;

    // ヘッダー情報を表示
    await UI.initializeStoreHeader();

    // 共通UI初期化（ログアウトボタンなど）
    initializeCommonUI();

    // 店舗プロフィールを読み込む
    await loadStoreProfile();
});

/**
 * 店舗プロフィールを読み込む
 */
async function loadStoreProfile() {
    const loading = document.getElementById('loading');
    const errorMessage = document.getElementById('error-message');
    const storeContent = document.getElementById('store-content');

    try {
        loading.style.display = 'block';
        errorMessage.style.display = 'none';

        // 認証チェック
        const authToken = localStorage.getItem('authToken');
        if (!authToken) {
            // 未ログインの場合はログインページにリダイレクト
            window.location.href = '/login?redirect=/store/profile';
            return;
        }

        // ユーザー情報を取得
        const currentUser = await apiClient.getCurrentUser();
        userRoles = currentUser.user_roles.map(ur => ur.role.name);
        isOwner = userRoles.includes('owner');

        // 店舗情報を取得
        const response = await apiClient.get('/store/profile');
        storeData = response;

        // 画面を表示
        displayStoreInfo(storeData);
        setupFormBehavior();

        loading.style.display = 'none';
        storeContent.style.display = 'block';

    } catch (error) {
        loading.style.display = 'none';
        
        // 401エラーの場合はログインページにリダイレクト
        if (error.message && error.message.includes('401')) {
            localStorage.removeItem('authToken');
            localStorage.removeItem('currentUser');
            window.location.href = '/login?redirect=/store/profile';
            return;
        }
        
        errorMessage.style.display = 'block';
        document.getElementById('error-text').textContent = 
            `エラーが発生しました: ${error.message || '店舗情報を読み込めませんでした'}`;
        console.error('Error loading store profile:', error);
    }
}

/**
 * 店舗情報を画面に表示
 */
function displayStoreInfo(store) {
    // 画像
    const storeImage = document.getElementById('store-image');
    if (store.image_url) {
        storeImage.src = store.image_url;
        originalImageUrl = store.image_url;
        if (isOwner) {
            document.getElementById('delete-image-button').style.display = 'inline-block';
        }
    } else {
        storeImage.src = '/static/images/no-image.svg';
        originalImageUrl = null;
        document.getElementById('delete-image-button').style.display = 'none';
    }

    // 基本情報
    document.getElementById('store-name').value = store.name || '';
    document.getElementById('store-email').value = store.email || '';
    document.getElementById('store-phone').value = store.phone_number || '';
    document.getElementById('store-address').value = store.address || '';

    // 営業時間
    document.getElementById('opening-time').value = store.opening_time || '';
    document.getElementById('closing-time').value = store.closing_time || '';

    // 説明
    document.getElementById('store-description').value = store.description || '';

    // ステータス
    document.getElementById('store-active').checked = store.is_active;

    // メタ情報
    document.getElementById('created-at').textContent = formatDateTime(store.created_at);
    document.getElementById('updated-at').textContent = formatDateTime(store.updated_at);
}

/**
 * フォームの動作を設定
 */
function setupFormBehavior() {
    const form = document.getElementById('store-form');
    const inputs = form.querySelectorAll('input, textarea');
    const saveButtonSection = document.getElementById('save-button-section');
    const readonlyMessage = document.getElementById('readonly-message');
    const imageUploadSection = document.getElementById('image-upload-section');
    const imageFile = document.getElementById('image-file');
    const deleteImageButton = document.getElementById('delete-image-button');
    const cancelButton = document.getElementById('cancel-button');

    if (isOwner) {
        // オーナー: 編集可能
        inputs.forEach(input => input.disabled = false);
        saveButtonSection.style.display = 'flex';
        imageUploadSection.style.display = 'block';
        document.getElementById('page-description').textContent = '店舗の基本情報を確認・編集';

        // フォーム送信
        form.addEventListener('submit', handleFormSubmit);

        // キャンセルボタン
        cancelButton.addEventListener('click', () => {
            if (confirm('変更を破棄してもよろしいですか?')) {
                displayStoreInfo(storeData);
            }
        });

        // 画像アップロード
        imageFile.addEventListener('change', handleImageUpload);

        // 画像削除
        deleteImageButton.addEventListener('click', handleImageDelete);

    } else {
        // マネージャー/スタッフ: 読み取り専用
        inputs.forEach(input => input.disabled = true);
        readonlyMessage.style.display = 'block';
        document.getElementById('page-description').textContent = '店舗の基本情報を確認（読み取り専用）';
    }
}

/**
 * フォーム送信処理
 */
async function handleFormSubmit(event) {
    event.preventDefault();

    const saveButton = document.getElementById('save-button');
    const originalText = saveButton.textContent;

    try {
        saveButton.disabled = true;
        saveButton.textContent = '保存中...';

        // フォームデータを収集
        const formData = {
            name: document.getElementById('store-name').value.trim(),
            email: document.getElementById('store-email').value.trim() || null,
            phone_number: document.getElementById('store-phone').value.trim() || null,
            address: document.getElementById('store-address').value.trim() || null,
            opening_time: document.getElementById('opening-time').value || null,
            closing_time: document.getElementById('closing-time').value || null,
            description: document.getElementById('store-description').value.trim() || null,
            is_active: document.getElementById('store-active').checked
        };

        // バリデーション
        if (!formData.name) {
            throw new Error('店舗名は必須です');
        }

        if (formData.description && formData.description.length > 1000) {
            throw new Error('説明文は1000文字以内で入力してください');
        }

        // API呼び出し
        const response = await apiClient.put('/store/profile', formData);
        storeData = response;

        // 成功メッセージを表示
        showSuccessMessage('店舗情報を更新しました');

        // 画面を更新
        displayStoreInfo(storeData);

    } catch (error) {
        showErrorMessage(error.message || '更新に失敗しました');
        console.error('Error updating store profile:', error);
    } finally {
        saveButton.disabled = false;
        saveButton.textContent = originalText;
    }
}

/**
 * 画像アップロード処理
 */
async function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    // ファイル形式チェック
    const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
        showErrorMessage('JPEG, PNG, GIF, WebP 形式の画像のみアップロードできます');
        event.target.value = '';
        return;
    }

    // ファイルサイズチェック（5MB）
    if (file.size > 5 * 1024 * 1024) {
        showErrorMessage('画像サイズは5MB以下にしてください');
        event.target.value = '';
        return;
    }

    try {
        // FormDataを作成
        const formData = new FormData();
        formData.append('file', file);

        // API呼び出し
        const response = await apiClient.uploadImage('/store/profile/image', formData);
        storeData = response;

        // 画像を更新
        document.getElementById('store-image').src = response.image_url;
        originalImageUrl = response.image_url;
        document.getElementById('delete-image-button').style.display = 'inline-block';

        showSuccessMessage('画像をアップロードしました');

    } catch (error) {
        showErrorMessage(error.message || '画像のアップロードに失敗しました');
        console.error('Error uploading image:', error);
    } finally {
        event.target.value = '';
    }
}

/**
 * 画像削除処理
 */
async function handleImageDelete() {
    if (!confirm('店舗画像を削除してもよろしいですか?')) {
        return;
    }

    try {
        const response = await apiClient.delete('/store/profile/image');
        storeData = response;

        // 画像を更新
        document.getElementById('store-image').src = '/static/images/no-image.svg';
        originalImageUrl = null;
        document.getElementById('delete-image-button').style.display = 'none';

        showSuccessMessage('画像を削除しました');

    } catch (error) {
        showErrorMessage(error.message || '画像の削除に失敗しました');
        console.error('Error deleting image:', error);
    }
}

/**
 * 成功メッセージを表示
 */
function showSuccessMessage(message) {
    const successMessage = document.getElementById('success-message');
    const successText = document.getElementById('success-text');
    
    successText.textContent = message;
    successMessage.style.display = 'block';

    // スクロール
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // 3秒後に非表示
    setTimeout(() => {
        successMessage.style.display = 'none';
    }, 3000);
}

/**
 * エラーメッセージを表示
 */
function showErrorMessage(message) {
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    
    errorText.textContent = message;
    errorMessage.style.display = 'block';

    // スクロール
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // 5秒後に非表示
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 5000);
}

/**
 * 日時フォーマット
 */
function formatDateTime(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}年${month}月${day}日 ${hours}:${minutes}`;
}
