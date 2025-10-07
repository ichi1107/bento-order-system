// お客様注文履歴画面専用JavaScript - customer_orders.js

class CustomerOrdersPage {
    constructor() {
        this.orders = [];
        this.filteredOrders = [];
        this.currentPage = 1;
        this.perPage = 10;
        
        this.initializePage();
    }

    async initializePage() {
        // 認証チェック
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
        // フィルターイベント
        const statusFilter = document.getElementById('statusFilter');
        if (statusFilter) {
            statusFilter.addEventListener('change', () => this.applyFilters());
        }
    }

    async loadOrders() {
        try {
            this.showLoading();
            
            const response = await ApiClient.get('/customer/orders', {
                per_page: 100 // 全注文を取得
            });
            
            if (!response || !response.orders) {
                throw new Error('注文データの形式が正しくありません');
            }
            
            this.orders = response.orders;
            this.filteredOrders = [...this.orders];
            
            if (this.orders.length === 0) {
                this.showEmptyMessage();
            } else {
                this.renderOrders();
            }
            
        } catch (error) {
            console.error('Failed to load orders:', error);
            
            let errorMessage = '注文履歴の読み込みに失敗しました';
            if (error.message.includes('401')) {
                errorMessage = '認証が切れました。再度ログインしてください。';
                setTimeout(() => Auth.logout(), 2000);
            }
            
            this.showError(errorMessage);
            UI.showAlert(errorMessage, 'danger');
        }
    }

    applyFilters() {
        const statusFilter = document.getElementById('statusFilter')?.value || '';
        
        this.filteredOrders = this.orders.filter(order => {
            return !statusFilter || order.status === statusFilter;
        });

        this.currentPage = 1;
        this.renderOrders();
    }

    renderOrders() {
        const container = document.getElementById('ordersList');
        if (!container) return;

        if (this.filteredOrders.length === 0) {
            this.showEmptyState(container);
            return;
        }

        // ページネーション
        const startIndex = (this.currentPage - 1) * this.perPage;
        const endIndex = startIndex + this.perPage;
        const currentOrders = this.filteredOrders.slice(startIndex, endIndex);

        // 注文カードを生成
        container.innerHTML = currentOrders.map(order => this.createOrderCard(order)).join('');

        // ページネーション
        this.setupPagination();
    }

    createOrderCard(order) {
        const statusBadge = UI.createStatusBadge(order.status);
        const orderDate = UI.formatDate(order.ordered_at);
        
        return `
            <div class="order-card">
                <div class="order-header">
                    <div class="order-info">
                        <h3 class="order-id">注文 #${order.id}</h3>
                        <div class="order-date">${orderDate}</div>
                    </div>
                    <div class="order-status">
                        ${statusBadge.outerHTML}
                    </div>
                </div>
                <div class="order-content">
                    <div class="order-menu">
                        <img src="${order.menu_image_url || ''}" alt="${order.menu_name}" class="order-menu-image"
                             onerror="this.onerror=null; this.style.display='none';">
                        <div class="order-menu-details">
                            <div class="menu-name">${this.escapeHtml(order.menu_name)}</div>
                            <div class="menu-price">${UI.formatPrice(order.menu_price)} × ${order.quantity}個</div>
                        </div>
                    </div>
                    <div class="order-total">
                        <div class="total-price">${UI.formatPrice(order.total_price)}</div>
                    </div>
                </div>
                ${order.notes ? `
                    <div class="order-notes">
                        <strong>備考:</strong> ${this.escapeHtml(order.notes)}
                    </div>
                ` : ''}
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

    async cancelOrder(orderId) {
        if (!confirm('この注文をキャンセルしますか？')) return;

        try {
            await ApiClient.put(`/customer/orders/${orderId}/cancel`);
            UI.showAlert('注文をキャンセルしました', 'success');
            await this.loadOrders();
        } catch (error) {
            console.error('Cancel order failed:', error);
            UI.showAlert('注文のキャンセルに失敗しました', 'danger');
        }
    }

    reorder(menuId) {
        // メニューページに移動
        window.location.href = `/customer/home#menu-${menuId}`;
    }

    setupPagination() {
        const totalPages = Math.ceil(this.filteredOrders.length / this.perPage);
        const paginationContainer = document.getElementById('pagination');
        
        if (paginationContainer) {
            Pagination.create(paginationContainer, this.currentPage, totalPages, (page) => {
                this.currentPage = page;
                this.renderOrders();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }
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

    showEmptyState(container) {
        container.innerHTML = `
            <div class="empty-container">
                <div class="empty-icon">🔍</div>
                <h3>該当する注文がありません</h3>
                <p>検索条件を変更してみてください。</p>
                <button type="button" class="btn btn-secondary" onclick="customerOrdersPage.applyFilters()">
                    フィルターをクリア
                </button>
            </div>
        `;
    }

    escapeHtml(text) {
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