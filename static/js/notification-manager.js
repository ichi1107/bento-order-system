/**
 * 通知管理システム
 * ブラウザ通知、サウンド、バッジ管理を統合
 */

class NotificationManager {
    constructor() {
        this.notificationPermission = 'default';
        this.soundEnabled = this.loadSoundPreference();
        this.audio = null;
        this.useWebAudioAPI = false; // Web Audio API フォールバック
        this.unconfirmedCount = 0;
        this.previousOrderIds = new Set();
        this.init();
    }

    async init() {
        // Notification API のサポート確認
        if ('Notification' in window) {
            this.notificationPermission = Notification.permission;
        }

        // Audio の初期化
        this.initAudio();

        // 初回アクセス時の通知許可リクエスト
        if (this.notificationPermission === 'default') {
            this.showPermissionBanner();
        }
    }

    /**
     * 通知音の初期化
     */
    initAudio() {
        try {
            // まず実際の音声ファイルをロード
            this.audio = new Audio('/static/sounds/notification.mp3');
            this.audio.volume = 0.5; // 50%のボリューム
            
            // プリロード
            this.audio.load();

            // ロードエラー時のフォールバック: Web Audio APIでビープ音生成
            this.audio.addEventListener('error', () => {
                console.log('音声ファイルが見つかりません。Web Audio APIを使用します。');
                this.useWebAudioAPI = true;
            });
        } catch (error) {
            console.error('Audio initialization failed:', error);
            this.useWebAudioAPI = true;
        }
    }

    /**
     * Web Audio API でビープ音を生成
     */
    generateBeep() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            // 音の設定
            oscillator.frequency.value = 800; // 800Hz のビープ音
            oscillator.type = 'sine';

            // ボリューム設定
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

            // 再生
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
        } catch (error) {
            console.error('Web Audio API error:', error);
        }
    }

    /**
     * 通知許可バナーを表示
     */
    showPermissionBanner() {
        const banner = document.createElement('div');
        banner.className = 'notification-permission-banner';
        banner.innerHTML = `
            <div class="permission-banner-content">
                <span class="banner-icon">🔔</span>
                <div class="banner-text">
                    <strong>新規注文の通知を受け取りますか?</strong>
                    <p>デスクトップ通知を有効にすると、画面を見ていなくても注文を見逃しません。</p>
                </div>
                <div class="banner-actions">
                    <button class="btn btn-primary btn-sm" id="allowNotificationBtn">
                        許可する
                    </button>
                    <button class="btn btn-secondary btn-sm" id="denyNotificationBtn">
                        後で
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(banner);

        // イベントリスナー
        document.getElementById('allowNotificationBtn').addEventListener('click', async () => {
            await this.requestNotificationPermission();
            banner.remove();
        });

        document.getElementById('denyNotificationBtn').addEventListener('click', () => {
            banner.remove();
        });

        // 5秒後にフェードイン
        setTimeout(() => banner.classList.add('show'), 100);
    }

    /**
     * 通知許可をリクエスト
     */
    async requestNotificationPermission() {
        if (!('Notification' in window)) {
            console.warn('このブラウザは通知機能をサポートしていません');
            return false;
        }

        try {
            const permission = await Notification.requestPermission();
            this.notificationPermission = permission;
            
            if (permission === 'granted') {
                this.showTestNotification();
                return true;
            } else {
                console.log('通知が拒否されました');
                return false;
            }
        } catch (error) {
            console.error('通知許可リクエストエラー:', error);
            return false;
        }
    }

    /**
     * テスト通知を表示
     */
    showTestNotification() {
        this.showNotification(
            '通知が有効になりました',
            '新しい注文が入ると、このような通知が表示されます。',
            '/static/images/logo.png'
        );
    }

    /**
     * デスクトップ通知を表示
     */
    showNotification(title, body, icon = null) {
        if (this.notificationPermission !== 'granted') {
            console.log('通知許可がありません');
            return;
        }

        try {
            const notification = new Notification(title, {
                body: body,
                icon: icon || '/static/images/notification-icon.png',
                badge: '/static/images/badge-icon.png',
                tag: 'order-notification',
                requireInteraction: false, // 自動で消える
                vibrate: [200, 100, 200], // バイブレーション (モバイル)
            });

            // 通知クリック時の動作
            notification.onclick = () => {
                window.focus();
                notification.close();
            };

            // 3秒後に自動クローズ
            setTimeout(() => notification.close(), 5000);

        } catch (error) {
            console.error('通知表示エラー:', error);
        }
    }

    /**
     * 新規注文通知
     */
    notifyNewOrder(order) {
        // デスクトップ通知
        this.showNotification(
            '🍱 新規注文が入りました!',
            `お客様: ${order.customer_name}\nメニュー: ${order.menu_name} × ${order.quantity}個\n合計: ¥${order.total_amount.toLocaleString()}`,
            order.menu_image_url || null
        );

        // サウンド再生
        this.playNotificationSound();

        // 未確認カウント増加
        this.incrementUnconfirmedCount();
    }

    /**
     * 通知音を再生
     */
    playNotificationSound() {
        if (!this.soundEnabled) {
            return;
        }

        try {
            // Web Audio API を使用する場合
            if (this.useWebAudioAPI) {
                this.generateBeep();
                return;
            }

            // 音声ファイルを使用する場合
            if (!this.audio) {
                return;
            }

            // 再生中の場合はリセット
            this.audio.currentTime = 0;
            
            // 再生
            const playPromise = this.audio.play();
            
            if (playPromise !== undefined) {
                playPromise.catch(error => {
                    console.warn('Audio playback failed:', error);
                    // フォールバック: Web Audio API を試す
                    this.useWebAudioAPI = true;
                    this.generateBeep();
                });
            }
        } catch (error) {
            console.error('Sound playback error:', error);
        }
    }

    /**
     * サウンド設定の切り替え
     */
    toggleSound() {
        this.soundEnabled = !this.soundEnabled;
        this.saveSoundPreference();
        
        // テスト再生
        if (this.soundEnabled) {
            this.playNotificationSound();
        }
        
        return this.soundEnabled;
    }

    /**
     * サウンド設定を保存
     */
    saveSoundPreference() {
        try {
            localStorage.setItem('notificationSoundEnabled', JSON.stringify(this.soundEnabled));
        } catch (error) {
            console.error('Failed to save sound preference:', error);
        }
    }

    /**
     * サウンド設定を読み込み
     */
    loadSoundPreference() {
        try {
            const saved = localStorage.getItem('notificationSoundEnabled');
            return saved !== null ? JSON.parse(saved) : true; // デフォルトON
        } catch (error) {
            console.error('Failed to load sound preference:', error);
            return true;
        }
    }

    /**
     * 新規注文を検出
     */
    detectNewOrders(currentOrders) {
        const newOrders = [];
        const currentOrderIds = new Set(currentOrders.map(o => o.id));

        // 初回ロード時は既存の注文IDを記録するだけ
        if (this.previousOrderIds.size === 0) {
            this.previousOrderIds = currentOrderIds;
            return newOrders;
        }

        // 前回のポーリングから増えた注文を検出
        currentOrders.forEach(order => {
            if (!this.previousOrderIds.has(order.id) && order.status === 'pending') {
                newOrders.push(order);
            }
        });

        // 現在の注文IDを保存
        this.previousOrderIds = currentOrderIds;

        return newOrders;
    }

    /**
     * 未確認カウントを増加
     */
    incrementUnconfirmedCount() {
        this.unconfirmedCount++;
        this.updateBadge();
        this.updatePageTitle();
    }

    /**
     * 未確認カウントを減少
     */
    decrementUnconfirmedCount() {
        if (this.unconfirmedCount > 0) {
            this.unconfirmedCount--;
            this.updateBadge();
            this.updatePageTitle();
        }
    }

    /**
     * 未確認カウントをリセット
     */
    resetUnconfirmedCount() {
        this.unconfirmedCount = 0;
        this.updateBadge();
        this.updatePageTitle();
    }

    /**
     * バッジ表示を更新
     */
    updateBadge() {
        const badge = document.getElementById('notificationBadge');
        if (badge) {
            if (this.unconfirmedCount > 0) {
                badge.textContent = this.unconfirmedCount > 99 ? '99+' : this.unconfirmedCount;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
    }

    /**
     * ページタイトルを更新
     */
    updatePageTitle() {
        const baseTitle = '注文管理 - 弁当注文管理システム';
        
        if (this.unconfirmedCount > 0) {
            document.title = `(${this.unconfirmedCount}) ${baseTitle}`;
        } else {
            document.title = baseTitle;
        }
    }

    /**
     * サウンド状態を取得
     */
    isSoundEnabled() {
        return this.soundEnabled;
    }

    /**
     * 通知許可状態を取得
     */
    getNotificationPermission() {
        return this.notificationPermission;
    }
}

// グローバルインスタンス
window.notificationManager = new NotificationManager();
