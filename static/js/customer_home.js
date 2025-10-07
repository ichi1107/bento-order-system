// お客様メニュー画面専用JavaScript - customer_home.js

class CustomerMenuPage {
    constructor() {
        this.menus = [];
        this.filteredMenus = [];
        this.currentPage = 1;
        this.perPage = 12;
        this.orderItems = new Map(); // menuId -> quantity
        this.isRendered = false; // 初回レンダリング完了フラグ
        
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
        
        // メニューデータの読み込み
        await this.loadMenus();
        
        // 初回は全メニューをレンダリング
        if (!this.isRendered) {
            this.renderAllMenus();
            this.isRendered = true;
        }
        
        // フィルターの初期化（表示/非表示を切り替えるだけ）
        this.applyFilters();
    }

    updateUserInfo() {
        const userInfoElement = document.getElementById('userInfo');
        if (userInfoElement && currentUser) {
            userInfoElement.textContent = `${currentUser.full_name} さん`;
        }
    }

    setupEventListeners() {
        // 検索フィルター
        const searchInput = document.getElementById('searchInput');
        const priceMinInput = document.getElementById('priceMin');
        const priceMaxInput = document.getElementById('priceMax');
        const filterBtn = document.getElementById('filterBtn');
        const clearFilterBtn = document.getElementById('clearFilterBtn');

        // 検索入力のデバウンス処理
        let searchTimeout;
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => this.applyFilters(), 300);
            });
        }
        
        if (filterBtn) {
            filterBtn.addEventListener('click', () => this.applyFilters());
        }
        
        if (clearFilterBtn) {
            clearFilterBtn.addEventListener('click', () => this.clearFilters());
        }

        // Enterキーでフィルター実行
        [searchInput, priceMinInput, priceMaxInput].forEach(input => {
            if (input) {
                input.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.applyFilters();
                    }
                });
            }
        });
    }

    async loadMenus() {
        try {
            this.showLoading();
            
            const response = await ApiClient.get('/customer/menus', {
                per_page: 100 // 全メニューを取得
            });
            
            if (!response || !response.menus) {
                throw new Error('メニューデータの形式が正しくありません');
            }
            
            this.menus = response.menus;
            this.filteredMenus = [...this.menus];
            
            this.hideLoading();
            
            if (this.menus.length === 0) {
                this.showEmptyMessage();
            } else {
                this.renderMenus();
            }
            
        } catch (error) {
            console.error('Failed to load menus:', error);
            
            this.hideLoading();
            
            // 具体的なエラーメッセージを表示
            let errorMessage = 'メニューの読み込みに失敗しました';
            if (error.message.includes('401')) {
                errorMessage = '認証が切れました。再度ログインしてください。';
                setTimeout(() => Auth.logout(), 2000);
            } else if (error.message.includes('403')) {
                errorMessage = 'メニューにアクセスする権限がありません。';
            } else if (error.message.includes('500')) {
                errorMessage = 'サーバーエラーが発生しました。しばらく時間をおいて再度お試しください。';
            }
            
            this.showError(errorMessage);
            UI.showAlert(errorMessage, 'danger');
        }
    }

    renderAllMenus() {
        const container = document.getElementById('menuGrid');
        if (!container) return;

        // 全メニューを一度だけレンダリング
        const allMenuCards = this.menus.map(menu => this.createMenuCard(menu)).join('');
        container.innerHTML = allMenuCards;
        
        // イベントリスナーを設定
        this.setupMenuCardListeners();
    }

    applyFilters() {
        const searchTerm = document.getElementById('searchInput')?.value.toLowerCase() || '';
        const priceMin = parseInt(document.getElementById('priceMin')?.value) || 0;
        const priceMax = parseInt(document.getElementById('priceMax')?.value) || Infinity;

        this.filteredMenus = this.menus.filter(menu => {
            const matchesSearch = menu.name.toLowerCase().includes(searchTerm) ||
                                 menu.description?.toLowerCase().includes(searchTerm);
            const matchesPrice = menu.price >= priceMin && menu.price <= priceMax;
            
            return matchesSearch && matchesPrice;
        });

        this.currentPage = 1;
        this.updateMenuVisibility();
        this.updateResultCount();
    }

    clearFilters() {
        document.getElementById('searchInput').value = '';
        document.getElementById('priceMin').value = '';
        document.getElementById('priceMax').value = '';
        
        this.filteredMenus = [...this.menus];
        this.currentPage = 1;
        this.updateMenuVisibility();
        this.updateResultCount();
    }

    updateMenuVisibility() {
        const container = document.getElementById('menuGrid');
        if (!container) return;

        if (this.filteredMenus.length === 0) {
            // 全カードを非表示
            const allCards = container.querySelectorAll('.menu-card');
            allCards.forEach(card => card.classList.add('hidden'));
            
            // 空メッセージを表示
            let emptyState = container.querySelector('.empty-state');
            if (!emptyState) {
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = `
                    <div class="empty-state">
                        <div class="no-menus-icon">🔍</div>
                        <h3>メニューが見つかりません</h3>
                        <p>検索条件を変更してみてください</p>
                        <button type="button" class="btn btn-secondary" onclick="customerMenuPage.clearFilters()">
                            フィルターをクリア
                        </button>
                    </div>
                `;
                emptyState = tempDiv.firstElementChild;
                container.appendChild(emptyState);
            } else {
                emptyState.classList.remove('hidden');
            }
            return;
        }

        // 空メッセージを非表示
        const emptyState = container.querySelector('.empty-state');
        if (emptyState) {
            emptyState.classList.add('hidden');
        }

        // ページネーション計算
        const startIndex = (this.currentPage - 1) * this.perPage;
        const endIndex = startIndex + this.perPage;
        
        // 現在のページに表示すべきメニューIDのセット
        const visibleMenuIds = new Set(
            this.filteredMenus
                .slice(startIndex, endIndex)
                .map(menu => String(menu.id))
        );

        // リフローを最小化: 一度にすべてのクラスを変更
        const allCards = container.querySelectorAll('.menu-card');
        const fragment = document.createDocumentFragment();
        
        allCards.forEach(card => {
            const menuId = card.dataset.menuId;
            if (visibleMenuIds.has(menuId)) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });

        // ページネーション更新
        this.setupPagination();
    }

    renderMenus() {
        // 後方互換性のため残す（updateMenuVisibilityに委譲）
        this.updateMenuVisibility();
    }

    createMenuCard(menu) {
        return `
            <div class="menu-card" data-menu-id="${menu.id}">
                <div style="position: relative;">
                    <img src="${menu.image_url}" alt="${menu.name}" class="menu-image" 
                         onerror="this.onerror=null; this.style.display='none';">
                    <span class="availability-badge badge-available">利用可能</span>
                </div>
                <div class="menu-content">
                    <h3 class="menu-name">${this.escapeHtml(menu.name)}</h3>
                    <p class="menu-description">${this.escapeHtml(menu.description || '')}</p>
                    <div class="menu-price">${UI.formatPrice(menu.price)}</div>
                    
                    <div class="order-controls">
                        <div class="quantity-control">
                            <button type="button" class="quantity-btn" data-action="decrease">-</button>
                            <input type="number" class="quantity-input" value="0" min="0" max="10" readonly>
                            <button type="button" class="quantity-btn" data-action="increase">+</button>
                        </div>
                    </div>
                    
                    <div class="order-summary-static">
                        <span class="summary-label">小計:</span> <span class="order-summary-price">&nbsp;</span>
                    </div>
                    
                    <div class="menu-actions">
                        <button type="button" class="btn btn-primary btn-sm order-now-btn">
                            今すぐ注文
                        </button>
                        <button type="button" class="btn btn-secondary btn-sm view-detail-btn">
                            詳細を見る
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    setupMenuCardListeners() {
        // 数量変更ボタン
        document.querySelectorAll('.quantity-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = btn.dataset.action;
                const menuCard = btn.closest('.menu-card');
                const menuId = parseInt(menuCard.dataset.menuId);
                
                this.updateQuantity(menuId, action);
            });
        });

        // 今すぐ注文ボタン
        document.querySelectorAll('.order-now-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const menuCard = btn.closest('.menu-card');
                const menuId = parseInt(menuCard.dataset.menuId);
                
                this.orderNow(menuId);
            });
        });

        // 詳細表示ボタン
        document.querySelectorAll('.view-detail-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const menuCard = btn.closest('.menu-card');
                const menuId = parseInt(menuCard.dataset.menuId);
                
                this.showMenuDetail(menuId);
            });
        });
    }

    updateQuantity(menuId, action) {
        const currentQuantity = this.orderItems.get(menuId) || 0;
        let newQuantity = currentQuantity;

        if (action === 'increase' && currentQuantity < 10) {
            newQuantity = currentQuantity + 1;
        } else if (action === 'decrease' && currentQuantity > 0) {
            newQuantity = currentQuantity - 1;
        }

        if (newQuantity <= 0) {
            this.orderItems.delete(menuId);
        } else {
            this.orderItems.set(menuId, newQuantity);
        }

        // UIを更新
        this.updateMenuCardUI(menuId);
    }

    updateMenuCardUI(menuId) {
        const menuCard = document.querySelector(`[data-menu-id="${menuId}"]`);
        if (!menuCard) return;

        const quantity = this.orderItems.get(menuId) || 0;
        const menu = this.menus.find(m => m.id === menuId);
        if (!menu) return;
        
        const totalPrice = menu.price * quantity;

        // DOM要素を取得
        const quantityInput = menuCard.querySelector('.quantity-input');
        const decreaseBtn = menuCard.querySelector('[data-action="decrease"]');
        const increaseBtn = menuCard.querySelector('[data-action="increase"]');
        const orderBtn = menuCard.querySelector('.order-now-btn');
        const summaryLabel = menuCard.querySelector('.summary-label');
        const orderSummaryPrice = menuCard.querySelector('.order-summary-price');

        // 一括更新（リフロー最小化）
        if (quantityInput) quantityInput.value = quantity;
        if (decreaseBtn) decreaseBtn.disabled = quantity <= 0;
        if (increaseBtn) increaseBtn.disabled = quantity >= 10;
        if (orderBtn) orderBtn.disabled = quantity <= 0;
        
        // 小計の表示：テキストのみ変更（要素の表示/非表示なし）
        if (summaryLabel && orderSummaryPrice) {
            if (quantity > 0) {
                summaryLabel.style.visibility = 'visible';
                orderSummaryPrice.textContent = UI.formatPrice(totalPrice);
            } else {
                summaryLabel.style.visibility = 'hidden';
                orderSummaryPrice.textContent = '\u00A0'; // 非改行スペース（高さ維持）
            }
        }
    }

    async orderNow(menuId) {
        const quantity = this.orderItems.get(menuId);
        if (!quantity || quantity <= 0) {
            UI.showAlert('数量を選択してください', 'warning');
            return;
        }

        const menu = this.menus.find(m => m.id === menuId);
        if (!menu) {
            UI.showAlert('メニューが見つかりません', 'danger');
            return;
        }

        // 注文確認
        const confirmed = confirm(`${menu.name} を ${quantity}個 注文しますか？\n合計金額: ${UI.formatPrice(menu.price * quantity)}`);
        if (!confirmed) return;

        try {
            // ボタンを無効化してローディング表示
            const menuCard = document.querySelector(`[data-menu-id="${menuId}"]`);
            const orderBtn = menuCard?.querySelector('.order-now-btn');
            if (orderBtn) {
                orderBtn.disabled = true;
                orderBtn.textContent = '注文中...';
            }

            const orderData = {
                menu_id: menuId,
                quantity: quantity,
                notes: ''
            };

            const response = await ApiClient.post('/customer/orders', orderData);
            
            if (!response || !response.id) {
                throw new Error('注文の作成に失敗しました');
            }
            
            UI.showAlert(`${menu.name} を ${quantity}個 注文しました！\n注文番号: ${response.id}`, 'success');
            
            // 注文後、数量をリセット
            this.orderItems.delete(menuId);
            this.updateMenuCardUI(menuId);
            
        } catch (error) {
            console.error('Order failed:', error);
            
            // 具体的なエラーメッセージを表示
            let errorMessage = '注文に失敗しました';
            if (error.message.includes('401')) {
                errorMessage = '認証が切れました。再度ログインしてください。';
                setTimeout(() => Auth.logout(), 2000);
            } else if (error.message.includes('404')) {
                errorMessage = '選択されたメニューは現在利用できません。';
            } else if (error.message.includes('400')) {
                errorMessage = '注文内容に問題があります。数量を確認してください。';
            } else if (error.message.includes('500')) {
                errorMessage = 'サーバーエラーが発生しました。しばらく時間をおいて再度お試しください。';
            }
            
            UI.showAlert(errorMessage, 'danger');
        } finally {
            // ボタンを元に戻す
            const menuCard = document.querySelector(`[data-menu-id="${menuId}"]`);
            const orderBtn = menuCard?.querySelector('.order-now-btn');
            if (orderBtn) {
                orderBtn.disabled = this.orderItems.get(menuId) <= 0;
                orderBtn.textContent = '今すぐ注文';
            }
        }
    }

    showMenuDetail(menuId) {
        const menu = this.menus.find(m => m.id === menuId);
        if (!menu) return;

        // モーダルでメニュー詳細を表示
        const modalHtml = `
            <div id="menuDetailModal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2 class="modal-title">${this.escapeHtml(menu.name)}</h2>
                        <button type="button" class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <img src="${menu.image_url}" alt="${menu.name}" style="width: 100%; max-height: 300px; object-fit: cover; border-radius: 8px; margin-bottom: 1rem;"
                             onerror="this.onerror=null; this.style.display='none';">
                        <p style="color: #6c757d; line-height: 1.6; margin-bottom: 1rem;">
                            ${this.escapeHtml(menu.description || 'メニューの説明はありません。')}
                        </p>
                        <div style="font-size: 1.5rem; font-weight: bold; color: #007bff; margin-bottom: 1rem;">
                            ${UI.formatPrice(menu.price)}
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" onclick="Modal.hide('menuDetailModal')">閉じる</button>
                        <button type="button" class="btn btn-primary" onclick="customerMenuPage.orderFromModal(${menuId})">注文する</button>
                    </div>
                </div>
            </div>
        `;

        // モーダルを表示
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        Modal.setupCloseHandlers('menuDetailModal');
        Modal.show('menuDetailModal');
    }

    orderFromModal(menuId) {
        Modal.hide('menuDetailModal');
        
        // 数量を1に設定して注文
        this.orderItems.set(menuId, 1);
        this.orderNow(menuId);
        
        // モーダルを削除
        setTimeout(() => {
            const modal = document.getElementById('menuDetailModal');
            if (modal) modal.remove();
        }, 300);
    }

    setupPagination() {
        const totalPages = Math.ceil(this.filteredMenus.length / this.perPage);
        const paginationContainer = document.getElementById('pagination');
        
        if (paginationContainer) {
            Pagination.create(paginationContainer, this.currentPage, totalPages, (page) => {
                this.currentPage = page;
                this.renderMenus();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }
    }

    updateResultCount() {
        const countElement = document.getElementById('resultCount');
        if (countElement) {
            countElement.textContent = `${this.filteredMenus.length}件のメニューが見つかりました`;
        }
    }

    showLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'flex';
        }
    }

    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    showError(message) {
        const container = document.getElementById('menuGrid');
        if (!container) return;

        container.innerHTML = `
            <div class="empty-state">
                <div class="no-menus-icon">⚠️</div>
                <h3>エラーが発生しました</h3>
                <p>${message}</p>
                <button type="button" class="btn btn-primary" onclick="location.reload()">
                    再読み込み
                </button>
            </div>
        `;
    }

    showEmptyMessage() {
        const container = document.getElementById('menuGrid');
        if (!container) return;

        container.innerHTML = `
            <div class="empty-state">
                <div class="no-menus-icon">🍱</div>
                <h3>メニューがありません</h3>
                <p>現在、利用可能なメニューがありません。</p>
                <button type="button" class="btn btn-primary" onclick="location.reload()">
                    再読み込み
                </button>
            </div>
        `;
    }

    showEmptyState(container) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="no-menus-icon">🔍</div>
                <h3>メニューが見つかりません</h3>
                <p>検索条件を変更してみてください</p>
                <button type="button" class="btn btn-secondary" onclick="customerMenuPage.clearFilters()">
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

// デバウンス関数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ページ読み込み時の初期化
let customerMenuPage;
document.addEventListener('DOMContentLoaded', function() {
    customerMenuPage = new CustomerMenuPage();
});