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

        const dateFilter = document.getElementById('dateFilter');
        if (dateFilter) {
            dateFilter.addEventListener('change', () => this.applyFilters());
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
                // フィルターを表示
                this.showFilters();
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
        const dateFilter = document.getElementById('dateFilter')?.value || '';
        
        this.filteredOrders = this.orders.filter(order => {
            // ステータスフィルター
            if (statusFilter && order.status !== statusFilter) {
                return false;
            }
            
            // 日付フィルター
            if (dateFilter) {
                const orderDate = new Date(order.ordered_at).toISOString().split('T')[0];
                if (orderDate !== dateFilter) {
                    return false;
                }
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
                <div class="order-details">
                    <div class="order-items">
                        <p>${this.escapeHtml(order.menu_name)} × ${order.quantity}</p>
                        ${order.notes ? `<p class="order-notes-text">備考: ${this.escapeHtml(order.notes)}</p>` : ''}
                    </div>
                    <div class="order-total">
                        <strong>合計: ${this.formatPrice(order.total_price)}</strong>
                    </div>
                </div>
            </div>
        `;
    }

    showLoading() {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'block';
        }
    }

    hideLoading() {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
    }

    showEmptyMessage() {
        const emptyMessage = document.getElementById('emptyMessage');
        if (emptyMessage) {
            emptyMessage.style.display = 'block';
        }
    }

    showFilters() {
        const ordersFilters = document.getElementById('ordersFilters');
        if (ordersFilters) {
            ordersFilters.style.display = 'flex';
        }
    }

    getStatusText(status) {
        const statusMap = {
            'pending': '注文中',
            'confirmed': '確認済み',
            'preparing': '準備中',
            'ready': '受取準備完了',
            'completed': '完了',
            'cancelled': 'キャンセル'
        };
        return statusMap[status] || status;
    }

    formatPrice(price) {
        return `¥${price.toLocaleString('ja-JP')}`;
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
}

// ページ読み込み時の初期化
let customerOrdersPage;
document.addEventListener('DOMContentLoaded', function() {
    customerOrdersPage = new CustomerOrdersPage();
});