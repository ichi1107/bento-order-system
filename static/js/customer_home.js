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
        
        // カートバッジの初期化
        cart.updateCartCount();
        
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
        // カートボタン
        const cartBtn = document.getElementById('cartBtn');
        if (cartBtn) {
            cartBtn.addEventListener('click', () => this.openCart());
        }

        // カートモーダル閉じるボタン
        const closeCartBtn = document.getElementById('closeCartBtn');
        if (closeCartBtn) {
            closeCartBtn.addEventListener('click', () => this.closeCart());
        }

        // カートクリアボタン
        const clearCartBtn = document.getElementById('clearCartBtn');
        if (clearCartBtn) {
            clearCartBtn.addEventListener('click', () => this.clearCart());
        }

        // チェックアウトボタン
        const checkoutBtn = document.getElementById('checkoutBtn');
        if (checkoutBtn) {
            checkoutBtn.addEventListener('click', () => this.checkout());
        }

        // モーダル外クリックで閉じる
        const cartModal = document.getElementById('cartModal');
        if (cartModal) {
            cartModal.addEventListener('click', (e) => {
                if (e.target === cartModal) {
                    this.closeCart();
                }
            });
        }

        // メニューカード内のボタンイベント（イベント委譲）
        const menuGrid = document.getElementById('menuGrid');
        if (menuGrid) {
            menuGrid.addEventListener('click', (e) => {
                const card = e.target.closest('.menu-card');
                if (!card) return;

                const menuId = parseInt(card.dataset.menuId);
                const menu = this.menus.find(m => m.id === menuId);
                if (!menu) return;

                // カゴへ入れるボタン
                if (e.target.closest('.add-to-cart-btn')) {
                    this.addToCart(menu, card);
                }

                // 数量増減ボタン
                if (e.target.closest('.quantity-btn')) {
                    const action = e.target.closest('.quantity-btn').dataset.action;
                    this.updateQuantity(card, action);
                }
            });
        }

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
            this.showLoading(true);
            
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
                this.renderMenus(false); // 初回ロードはフェード不要
                this.isInitialLoad = false;
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
                        <button type="button" class="btn btn-primary btn-block add-to-cart-btn">
                            🛒 カゴへ入れる
                        </button>
                    </div>
                </div>
            </div>
        `;
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

    // カート操作メソッド
    addToCart(menu, card) {
        console.log('Adding to cart - menu object:', menu);
        const quantityInput = card.querySelector('.quantity-input');
        const quantity = parseInt(quantityInput.value) || 1;
        
        if (quantity <= 0) {
            UI.showAlert('数量を選択してください', 'warning');
            return;
        }

        cart.addItem(menu, quantity);
        UI.showAlert(`${menu.name} をカートに追加しました`, 'success');
        
        // 数量をリセット
        quantityInput.value = 0;
        this.updateCardSubtotal(card);
    }

    openCart() {
        console.log('Opening cart...');
        console.log('Cart items:', cart.getItems());
        this.renderCart();
        const modal = document.getElementById('cartModal');
        console.log('Modal element:', modal);
        if (modal) {
            modal.classList.add('show');
            console.log('Modal classes:', modal.className);
        } else {
            console.error('Cart modal element not found!');
        }
    }

    closeCart() {
        const modal = document.getElementById('cartModal');
        if (modal) {
            modal.classList.remove('show');
        }
    }

    renderCart() {
        console.log('Rendering cart...');
        const cartItems = cart.getItems();
        console.log('Cart items to render:', cartItems);
        const container = document.getElementById('cartItems');
        const totalPriceElement = document.getElementById('cartTotalPrice');
        
        console.log('Cart container:', container);
        console.log('Total price element:', totalPriceElement);
        
        if (!container) {
            console.error('Cart items container not found!');
            return;
        }

        if (cartItems.length === 0) {
            container.innerHTML = `
                <div class="empty-cart">
                    <div class="empty-cart-icon">🛒</div>
                    <h3>カートは空です</h3>
                    <p>メニューから商品を選んでください</p>
                </div>
            `;
            if (totalPriceElement) {
                totalPriceElement.textContent = '¥0';
            }
            return;
        }

        container.innerHTML = cartItems.map(item => `
            <div class="cart-item" data-menu-id="${item.id}">
                <img src="${item.image_url || ''}" alt="${item.name}" class="cart-item-image"
                     onerror="this.onerror=null; this.style.display='none';">
                <div class="cart-item-details">
                    <div class="cart-item-name">${this.escapeHtml(item.name)}</div>
                    <div class="cart-item-price">¥${(item.price || 0).toLocaleString()} × ${item.quantity}個</div>
                </div>
                <div class="cart-item-controls">
                    <div class="quantity-control">
                        <button type="button" class="quantity-btn" onclick="customerMenuPage.updateCartQuantity(${item.id}, ${item.quantity - 1})">-</button>
                        <input type="number" class="quantity-input" value="${item.quantity}" min="1" readonly>
                        <button type="button" class="quantity-btn" onclick="customerMenuPage.updateCartQuantity(${item.id}, ${item.quantity + 1})">+</button>
                    </div>
                    <button type="button" class="remove-item-btn" onclick="customerMenuPage.removeFromCart(${item.id})">削除</button>
                </div>
            </div>
        `).join('');

        if (totalPriceElement) {
            totalPriceElement.textContent = `¥${cart.getTotalPrice().toLocaleString()}`;
        }
    }

    updateCartQuantity(menuId, newQuantity) {
        cart.updateQuantity(menuId, newQuantity);
        this.renderCart();
    }

    removeFromCart(menuId) {
        if (confirm('この商品をカートから削除しますか?')) {
            cart.removeItem(menuId);
            this.renderCart();
            UI.showAlert('カートから削除しました', 'success');
        }
    }

    clearCart() {
        if (cart.getItemCount() === 0) {
            UI.showAlert('カートは既に空です', 'info');
            return;
        }

        if (confirm('カート内のすべての商品を削除しますか?')) {
            cart.clear();
            this.renderCart();
            UI.showAlert('カートをクリアしました', 'success');
        }
    }

    async checkout() {
        const items = cart.getItems();
        
        if (items.length === 0) {
            UI.showAlert('カートに商品がありません', 'warning');
            return;
        }

        try {
            // 各商品を個別に注文
            for (const item of items) {
                await ApiClient.post('/customer/orders', {
                    menu_id: item.id,
                    quantity: item.quantity
                });
            }

            UI.showAlert('注文が完了しました!', 'success');
            cart.clear();
            this.closeCart();
            
            // 注文履歴ページへリダイレクト
            setTimeout(() => {
                window.location.href = '/customer/orders';
            }, 1500);

        } catch (error) {
            console.error('Checkout failed:', error);
            UI.showAlert('注文に失敗しました。もう一度お試しください。', 'danger');
        }
    }

    updateCardSubtotal(card) {
        const quantityInput = card.querySelector('.quantity-input');
        const subtotalElement = card.querySelector('.order-summary-price');
        const menuId = parseInt(card.dataset.menuId);
        const menu = this.menus.find(m => m.id === menuId);
        
        if (!menu || !quantityInput || !subtotalElement) return;
        
        const quantity = parseInt(quantityInput.value) || 0;
        const subtotal = menu.price * quantity;
        
        if (quantity > 0) {
            subtotalElement.textContent = UI.formatPrice(subtotal);
        } else {
            subtotalElement.innerHTML = '&nbsp;';
        }
    }

    updateQuantity(card, action) {
        const input = card.querySelector('.quantity-input');
        if (!input) return;

        let currentValue = parseInt(input.value) || 0;
        const max = parseInt(input.getAttribute('max')) || 10;

        if (action === 'increase' && currentValue < max) {
            input.value = currentValue + 1;
        } else if (action === 'decrease' && currentValue > 0) {
            input.value = currentValue - 1;
        }

        this.updateCardSubtotal(card);
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