/**
 * パスワードリセット要求画面のJavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('reset-request-form');
    const emailInput = document.getElementById('email');
    const emailError = document.getElementById('email-error');
    const submitBtn = document.getElementById('submit-btn');
    const loadingMessage = document.getElementById('loading-message');
    const successMessage = document.getElementById('success-message');
    const errorBox = document.getElementById('error-box');
    const errorText = document.getElementById('error-text');

    // メールアドレスのバリデーション
    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    // エラーメッセージをクリア
    function clearErrors() {
        emailError.textContent = '';
        emailInput.classList.remove('error');
        errorBox.style.display = 'none';
        successMessage.style.display = 'none';
    }

    // リアルタイムバリデーション
    emailInput.addEventListener('blur', function() {
        clearErrors();
        const email = emailInput.value.trim();
        
        if (email && !validateEmail(email)) {
            emailError.textContent = '有効なメールアドレスを入力してください';
            emailInput.classList.add('error');
        }
    });

    emailInput.addEventListener('input', function() {
        if (emailInput.classList.contains('error')) {
            clearErrors();
        }
    });

    // フォーム送信処理
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        clearErrors();

        const email = emailInput.value.trim();

        // クライアントサイドバリデーション
        if (!email) {
            emailError.textContent = 'メールアドレスを入力してください';
            emailInput.classList.add('error');
            return;
        }

        if (!validateEmail(email)) {
            emailError.textContent = '有効なメールアドレスを入力してください';
            emailInput.classList.add('error');
            return;
        }

        // 送信中の状態
        submitBtn.disabled = true;
        form.style.display = 'none';
        loadingMessage.style.display = 'block';

        try {
            const response = await fetch('/api/auth/password-reset-request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email: email })
            });

            const data = await response.json();

            if (response.ok) {
                // 成功
                loadingMessage.style.display = 'none';
                successMessage.style.display = 'block';
                
                // 5秒後にログイン画面にリダイレクト
                setTimeout(() => {
                    window.location.href = '/login';
                }, 5000);
            } else if (response.status === 429) {
                // レート制限エラー
                throw new Error('送信回数が上限に達しました。しばらく経ってから再度お試しください。');
            } else if (response.status === 422) {
                // バリデーションエラー
                throw new Error('入力内容に誤りがあります。メールアドレスを確認してください。');
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
