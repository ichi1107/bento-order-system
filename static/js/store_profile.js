// 店舗プロフィール画面のスクリプト
document.addEventListener('DOMContentLoaded', async () => {
    // 要素の取得
    const form = document.getElementById('storeProfileForm');
    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    const phoneInput = document.getElementById('phone_number');
    const addressInput = document.getElementById('address');
    const openingTimeInput = document.getElementById('opening_time');
    const closingTimeInput = document.getElementById('closing_time');
    const descriptionInput = document.getElementById('description');
    const isActiveCheckbox = document.getElementById('is_active');
    const storeImage = document.getElementById('storeImage');
    const imageInput = document.getElementById('imageInput');
    const deleteImageBtn = document.getElementById('deleteImageBtn');
    const saveBtn = document.getElementById('saveBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const charCount = document.getElementById('charCount');
    const readonlyNotice = document.getElementById('readonlyNotice');
    const imageActions = document.getElementById('imageActions');
    const formActions = document.getElementById('formActions');

    let currentUser = null;
    let originalData = null;
    let isOwner = false;

    // ユーザー情報と店舗情報を取得
    try {
        currentUser = await getCurrentUser();
        if (!currentUser) {
            window.location.href = '/login';
            return;
        }

        // ユーザーの役割を確認
        isOwner = currentUser.user_roles?.some(role => role.role.name === 'owner') || false;

        // 店舗情報を読み込み
        await loadStoreProfile();

        // オーナーでない場合は読み取り専用にする
        if (!isOwner) {
            setReadOnly();
        }
    } catch (error) {
        console.error('初期化エラー:', error);
        showError('ページの読み込み中にエラーが発生しました');
    }

    // 店舗情報の読み込み
    async function loadStoreProfile() {
        try {
            const response = await fetch('/api/store/profile', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                }
            });

            if (!response.ok) {
                throw new Error('店舗情報の取得に失敗しました');
            }

            const data = await response.json();
            originalData = { ...data };

            // フォームに値を設定
            nameInput.value = data.name || '';
            emailInput.value = data.email || '';
            phoneInput.value = data.phone_number || '';
            addressInput.value = data.address || '';
            openingTimeInput.value = data.opening_time || '';
            closingTimeInput.value = data.closing_time || '';
            descriptionInput.value = data.description || '';
            isActiveCheckbox.checked = data.is_active || false;

            // 店舗画像
            if (data.image_url) {
                storeImage.src = data.image_url;
            }

            updateCharCount();
        } catch (error) {
            console.error('店舗情報の読み込みエラー:', error);
            showError(error.message);
        }
    }

    // 読み取り専用モードに設定
    function setReadOnly() {
        readonlyNotice.style.display = 'block';
        imageActions.style.display = 'none';
        formActions.style.display = 'none';

        // すべての入力を無効化
        nameInput.disabled = true;
        emailInput.disabled = true;
        phoneInput.disabled = true;
        addressInput.disabled = true;
        openingTimeInput.disabled = true;
        closingTimeInput.disabled = true;
        descriptionInput.disabled = true;
        isActiveCheckbox.disabled = true;
    }

    // 文字数カウント更新
    function updateCharCount() {
        charCount.textContent = descriptionInput.value.length;
    }

    descriptionInput.addEventListener('input', updateCharCount);

    // フォーム送信
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!isOwner) {
            showError('オーナーのみが店舗情報を編集できます');
            return;
        }

        // バリデーション
        if (!validateForm()) {
            return;
        }

        const formData = {
            name: nameInput.value,
            email: emailInput.value || null,
            phone_number: phoneInput.value || null,
            address: addressInput.value || null,
            opening_time: openingTimeInput.value,
            closing_time: closingTimeInput.value,
            description: descriptionInput.value || null,
            is_active: isActiveCheckbox.checked
        };

        try {
            const response = await fetch('/api/store/profile', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '更新に失敗しました');
            }

            const updatedData = await response.json();
            originalData = { ...updatedData };

            showSuccess('店舗情報を更新しました');
        } catch (error) {
            console.error('更新エラー:', error);
            showError(error.message);
        }
    });

    // フォームのバリデーション
    function validateForm() {
        let isValid = true;

        // エラーメッセージをクリア
        clearErrors();

        // 店舗名
        if (!nameInput.value.trim()) {
            showFieldError('nameError', '店舗名は必須です');
            isValid = false;
        }

        // 営業時間
        if (!openingTimeInput.value) {
            showFieldError('openingTimeError', '開店時刻は必須です');
            isValid = false;
        }

        if (!closingTimeInput.value) {
            showFieldError('closingTimeError', '閉店時刻は必須です');
            isValid = false;
        }

        // 説明文の長さチェック
        if (descriptionInput.value.length > 1000) {
            showFieldError('descriptionError', '説明文は1000文字以内で入力してください');
            isValid = false;
        }

        return isValid;
    }

    // フィールドエラーの表示
    function showFieldError(elementId, message) {
        const errorElement = document.getElementById(elementId);
        if (errorElement) {
            errorElement.textContent = message;
        }
    }

    // エラーのクリア
    function clearErrors() {
        const errorElements = document.querySelectorAll('.error-message');
        errorElements.forEach(el => {
            el.textContent = '';
        });
    }

    // 画像アップロード
    imageInput.addEventListener('change', async (e) => {
        if (!isOwner) {
            showError('オーナーのみが画像を変更できます');
            return;
        }

        const file = e.target.files[0];
        if (!file) return;

        // ファイルサイズチェック (5MB)
        if (file.size > 5 * 1024 * 1024) {
            showError('画像ファイルは5MB以下にしてください');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/store/profile/image', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                },
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '画像のアップロードに失敗しました');
            }

            const data = await response.json();
            storeImage.src = data.image_url;
            showSuccess('画像を更新しました');
        } catch (error) {
            console.error('画像アップロードエラー:', error);
            showError(error.message);
        }
    });

    // 画像削除
    deleteImageBtn.addEventListener('click', async () => {
        if (!isOwner) {
            showError('オーナーのみが画像を削除できます');
            return;
        }

        if (!confirm('店舗画像を削除しますか?')) {
            return;
        }

        try {
            const response = await fetch('/api/store/profile/image', {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || '画像の削除に失敗しました');
            }

            storeImage.src = '/static/images/default-store.png';
            showSuccess('画像を削除しました');
        } catch (error) {
            console.error('画像削除エラー:', error);
            showError(error.message);
        }
    });

    // キャンセルボタン
    cancelBtn.addEventListener('click', () => {
        if (originalData) {
            nameInput.value = originalData.name || '';
            emailInput.value = originalData.email || '';
            phoneInput.value = originalData.phone_number || '';
            addressInput.value = originalData.address || '';
            openingTimeInput.value = originalData.opening_time || '';
            closingTimeInput.value = originalData.closing_time || '';
            descriptionInput.value = originalData.description || '';
            isActiveCheckbox.checked = originalData.is_active || false;

            if (originalData.image_url) {
                storeImage.src = originalData.image_url;
            }

            clearErrors();
            updateCharCount();
        }
    });

    // 成功メッセージの表示
    function showSuccess(message) {
        const successMsg = document.getElementById('successMessage');
        successMsg.querySelector('p').textContent = `✓ ${message}`;
        successMsg.style.display = 'block';
        setTimeout(() => {
            successMsg.style.display = 'none';
        }, 3000);
    }

    // エラーメッセージの表示
    function showError(message) {
        const errorMsg = document.getElementById('errorMessage');
        document.getElementById('errorText').textContent = message;
        errorMsg.style.display = 'block';
        setTimeout(() => {
            errorMsg.style.display = 'none';
        }, 5000);
    }

    // ログアウト
    document.getElementById('logoutBtn')?.addEventListener('click', logout);
});
