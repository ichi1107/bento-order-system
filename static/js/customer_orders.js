// お客様注文履歴画面専用JavaScript - customer_orders.js

class CustomerOrdersPage {
    constructor() {
        this.orders = [];
        this.filteredOrders = [];
        
        this.initializePage();
    }

    async initializePage() {
        // 認証チェック - トークンがない場合はログインページへリダイレクト
        if (!Auth.requireAuth()) return;
        
        // お客様専用ページなので、roleチェック
        if (!Auth.requireRole('customer')) return;
        
        // 共通UI初期化
        initializeCommonUI();
        
        // ユーザー情報を表示
        this.updateUserInfo();
        
        // イベントリスナーの設定
        this.setupEventListeners();
        
        // 注文履歴の読み込み
        await this.loadOrders();
    }

    updateUserInfo() {
        const userInfoElement = document.getElementById('userInfo');
        if (userInfoElement && currentUser) {
            userInfoElement.textContent = `${currentUser.full_name}さん`;
        }
    }

    setupEventListeners() {
        // ログアウトボタン
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => Auth.logout());
        }

        // フィルターイベント
        const statusFilter = document.getElementById('statusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', () => this.applyFilters());
        }

        const dateFromFilter = document.getElementById('dateFromFilter');
        if (dateFromFilter) {
            dateFromFilter.addEventListener('change', () => this.applyFilters());
        }

        const dateToFilter = document.getElementById('dateToFilter');
        if (dateToFilter) {
            dateToFilter.addEventListener('change', () => this.applyFilters());
        }
    }

    async loadOrders() {
        try {
            // ローディング表示
            this.showLoading();
            
            // APIから注文履歴を取得
            const response = await ApiClient.get('/customer/orders');
            
            if (!response || !response.orders) {
                throw new Error('注文データの形式が正しくありません');
            }
            
            // 注文を新しい順にソート
            this.orders = response.orders.sort((a, b) => {
                return new Date(b.ordered_at) - new Date(a.ordered_at);
            });
            
            this.filteredOrders = [...this.orders];
            
            // ローディングを非表示
            this.hideLoading();
            
            // データが0件の場合は空メッセージを表示
            if (this.orders.length === 0) {
                this.showEmptyMessage();
            } else {
                // 注文リストを描画
                this.renderOrders();
            }
            
        } catch (error) {
            console.error('Failed to load orders:', error);
            
            // ローディングを非表示
            this.hideLoading();
            
            let errorMessage = '注文履歴の読み込みに失敗しました';
            if (error.message.includes('401') || error.message.includes('Unauthorized')) {
                errorMessage = '認証が切れました。再度ログインしてください。';
                setTimeout(() => Auth.logout(), 2000);
            }
            
            UI.showAlert(errorMessage, 'danger');
        }
    }

    applyFilters() {
        const statusFilter = document.getElementById('statusFilter')?.value || '';
        const dateFromFilter = document.getElementById('dateFromFilter')?.value || '';
        const dateToFilter = document.getElementById('dateToFilter')?.value || '';
        
        this.filteredOrders = this.orders.filter(order => {
            // ステータスフィルター
            if (statusFilter && order.status !== statusFilter) {
                return false;
            }
            
            // 日付期間フィルター
            const orderDate = new Date(order.ordered_at).toISOString().split('T')[0];
            
            // 開始日チェック
            if (dateFromFilter && orderDate < dateFromFilter) {
                return false;
            }
            
            // 終了日チェック
            if (dateToFilter && orderDate > dateToFilter) {
                return false;
            }
            
            return true;
        });

        this.renderOrders();
    }

    renderOrders() {
        const container = document.getElementById('ordersList');
        if (!container) return;

        if (this.filteredOrders.length === 0) {
            container.innerHTML = `
                <div class="empty-message">
                    <p>該当する注文がありません。</p>
                </div>
            `;
            return;
        }

        // 注文カードを生成して追加
        container.innerHTML = this.filteredOrders
            .map(order => this.createOrderCard(order))
            .join('');
    }

    createOrderCard(order) {
        const statusText = this.getStatusText(order.status);
        const statusClass = `status-${order.status}`;
        const orderDate = this.formatDateTime(order.ordered_at);
        
        return `
            <div class="order-item">
                <div class="order-header">
                    <span class="order-id">#${order.id}</span>
                    <span class="order-status ${statusClass}">${statusText}</span>
                    <span class="order-date">${orderDate}</span>
                </div>
                <div class="order-content">
                    <div class="order-menu">
                        <img src="${order.menu_image_url || ''}" alt="${order.menu_name}" class="order-menu-image"
                             onerror="this.onerror=null; this.style.display='none';">
                        <div class="order-menu-details">
                            <div class="menu-name">${this.escapeHtml(order.menu_name)}</div>
                            <div class="menu-price">¥${order.menu_price.toLocaleString()} × ${order.quantity}個</div>
                        </div>
                    </div>
                    <div class="order-total">
                        <strong>合計: ¥${order.total_price.toLocaleString()}</strong>
                    </div>
                </div>
                <div class="order-actions">
                    ${order.status === 'pending' ? `
                        <button type="button" class="btn btn-sm btn-danger" onclick="customerOrdersPage.cancelOrder(${order.id})">
                            キャンセル
                        </button>
                    ` : ''}
                    <button type="button" class="btn btn-sm btn-secondary" onclick="customerOrdersPage.reorder(${order.menu_id})">
                        再注文
                    </button>
                </div>
            </div>
        `;
    }

    getStatusText(status) {
        const statusMap = {
            'pending': '注文受付',
            'ready': '準備完了',
            'completed': '受取完了',
            'cancelled': 'キャンセル'
        };
        return statusMap[status] || status;
    }

    showLoading() {
        const container = document.getElementById('ordersList');
        if (!container) return;

        container.innerHTML = `
            <div class="loading-container">
                <div class="loading"></div>
                <p>注文履歴を読み込み中...</p>
            </div>
        `;
    }

    hideLoading() {
        // ローディング表示はrenderOrdersやshowEmptyMessageで上書きされるので何もしない
    }

    showError(message) {
        const container = document.getElementById('ordersList');
        if (!container) return;

        container.innerHTML = `
            <div class="error-container">
                <div class="error-icon">⚠️</div>
                <h3>エラーが発生しました</h3>
                <p>${message}</p>
                <button type="button" class="btn btn-primary" onclick="location.reload()">
                    再読み込み
                </button>
            </div>
        `;
    }

    showEmptyMessage() {
        const container = document.getElementById('ordersList');
        if (!container) return;

        container.innerHTML = `
            <div class="empty-container">
                <div class="empty-icon">📋</div>
                <h3>注文履歴がありません</h3>
                <p>まだ注文をされていません。</p>
                <a href="/customer/home" class="btn btn-primary">
                    メニューを見る
                </a>
            </div>
        `;
    }

    formatDateTime(dateTimeString) {
        const date = new Date(dateTimeString);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        
        return `${year}/${month}/${day} ${hours}:${minutes}`;
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async cancelOrder(orderId) {
        if (!confirm('この注文をキャンセルしますか?')) {
            return;
        }

        try {
            await ApiClient.delete(`/customer/orders/${orderId}`);
            UI.showAlert('注文をキャンセルしました', 'success');
            await this.loadOrders(); // 注文リストを再読み込み
        } catch (error) {
            console.error('Failed to cancel order:', error);
            UI.showAlert('注文のキャンセルに失敗しました', 'danger');
        }
    }

    reorder(menuId) {
        // メニューページに遷移
        window.location.href = `/customer/home?menu=${menuId}`;
    }
}

// ページ読み込み時の初期化
let customerOrdersPage;
document.addEventListener('DOMContentLoaded', function() {
    customerOrdersPage = new CustomerOrdersPage();
});