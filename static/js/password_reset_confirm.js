/**
 * パスワード再設定画面のJavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('reset-confirm-form');
    const tokenInput = document.getElementById('reset-token');
    const newPasswordInput = document.getElementById('new-password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    const passwordError = document.getElementById('password-error');
    const confirmError = document.getElementById('confirm-error');
    const submitBtn = document.getElementById('submit-btn');
    const loadingMessage = document.getElementById('loading-message');
    const successMessage = document.getElementById('success-message');
    const errorBox = document.getElementById('error-box');
    const errorText = document.getElementById('error-text');
    const toggleBtn1 = document.getElementById('toggle-password-1');
    const toggleBtn2 = document.getElementById('toggle-password-2');

    // URLパラメータからトークンを取得
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    if (!token) {
        errorBox.style.display = 'block';
        errorText.textContent = '無効なリンクです。パスワードリセットを再度要求してください。';
        form.style.display = 'none';
        return;
    }

    tokenInput.value = token;

    // パスワード表示/非表示トグル
    toggleBtn1.addEventListener('click', function() {
        const type = newPasswordInput.type === 'password' ? 'text' : 'password';
        newPasswordInput.type = type;
        toggleBtn1.textContent = type === 'password' ? '👁️' : '🙈';
    });

    toggleBtn2.addEventListener('click', function() {
        const type = confirmPasswordInput.type === 'password' ? 'text' : 'password';
        confirmPasswordInput.type = type;
        toggleBtn2.textContent = type === 'password' ? '👁️' : '🙈';
    });

    // エラーメッセージをクリア
    function clearErrors() {
        passwordError.textContent = '';
        confirmError.textContent = '';
        newPasswordInput.classList.remove('error');
        confirmPasswordInput.classList.remove('error');
        errorBox.style.display = 'none';
        successMessage.style.display = 'none';
    }

    // パスワードのバリデーション
    function validatePassword(password) {
        if (password.length < 6) {
            return 'パスワードは6文字以上で入力してください';
        }
        return null;
    }

    // パスワード入力時のリアルタイムバリデーション
    newPasswordInput.addEventListener('blur', function() {
        const password = newPasswordInput.value;
        const error = validatePassword(password);
        
        if (error) {
            passwordError.textContent = error;
            newPasswordInput.classList.add('error');
        } else {
            passwordError.textContent = '';
            newPasswordInput.classList.remove('error');
        }
    });

    // 確認パスワード入力時のリアルタイムバリデーション
    confirmPasswordInput.addEventListener('blur', function() {
        const password = newPasswordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        
        if (confirmPassword && password !== confirmPassword) {
            confirmError.textContent = 'パスワードが一致しません';
            confirmPasswordInput.classList.add('error');
        } else {
            confirmError.textContent = '';
            confirmPasswordInput.classList.remove('error');
        }
    });

    newPasswordInput.addEventListener('input', function() {
        if (newPasswordInput.classList.contains('error')) {
            clearErrors();
        }
    });

    confirmPasswordInput.addEventListener('input', function() {
        if (confirmPasswordInput.classList.contains('error')) {
            confirmError.textContent = '';
            confirmPasswordInput.classList.remove('error');
        }
    });

    // フォーム送信処理
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        clearErrors();

        const password = newPasswordInput.value;
        const confirmPassword = confirmPasswordInput.value;

        // クライアントサイドバリデーション
        let hasError = false;

        const passwordValidationError = validatePassword(password);
        if (passwordValidationError) {
            passwordError.textContent = passwordValidationError;
            newPasswordInput.classList.add('error');
            hasError = true;
        }

        if (password !== confirmPassword) {
            confirmError.textContent = 'パスワードが一致しません';
            confirmPasswordInput.classList.add('error');
            hasError = true;
        }

        if (hasError) {
            return;
        }

        // 送信中の状態
        submitBtn.disabled = true;
        form.style.display = 'none';
        loadingMessage.style.display = 'block';

        try {
            const response = await fetch('/api/auth/password-reset-confirm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    token: token,
                    new_password: password
                })
            });

            const data = await response.json();

            if (response.ok) {
                // 成功
                loadingMessage.style.display = 'none';
                successMessage.style.display = 'block';
                
                // 3秒後にログイン画面にリダイレクト
                setTimeout(() => {
                    window.location.href = '/login';
                }, 3000);
            } else if (response.status === 404) {
                // トークンが無効
                throw new Error('リセットリンクが無効です。パスワードリセットを再度要求してください。');
            } else if (response.status === 400) {
                // トークン期限切れまたは使用済み
                const detail = data.detail || '';
                if (detail.includes('expired')) {
                    throw new Error('リセットリンクの有効期限が切れています。パスワードリセットを再度要求してください。');
                } else if (detail.includes('already been used')) {
                    throw new Error('このリセットリンクは既に使用されています。新しいリンクを要求してください。');
                } else {
                    throw new Error('エラーが発生しました。パスワードリセットを再度要求してください。');
                }
            } else if (response.status === 422) {
                // バリデーションエラー
                throw new Error('入力内容に誤りがあります。パスワードは6文字以上で入力してください。');
            } else {
                // その他のエラー
                throw new Error(data.detail || 'エラーが発生しました。もう一度お試しください。');
            }
        } catch (error) {
            // エラー表示
            loadingMessage.style.display = 'none';
            form.style.display = 'block';
            errorBox.style.display = 'block';
            errorText.textContent = error.message;
            submitBtn.disabled = false;
        }
    });
});
