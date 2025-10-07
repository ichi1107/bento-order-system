// お客様メニュー画面専用JavaScript - ちらつき完全解消版

class CustomerMenuPage {
    constructor() {
        this.menus = [];
        this.filteredMenus = [];
        this.currentPage = 1;
        this.perPage = 12;
        this.orderItems = new Map();
        this.menuCardsCache = new Map(); // DOM要素をキャッシュ
        
        this.initializePage();
    }

    async initializePage() {
        console.log('Initializing page...'); // デバッグ
        
        if (!Auth.requireRole('customer')) return;
        
        console.log('Auth check passed'); // デバッグ
        
        this.updateUserInfo();
        this.setupEventListeners();
        
        console.log('Loading menus...'); // デバッグ
        await this.loadMenus();
        
        console.log('Menus loaded:', this.menus.length); // デバッグ
        
        this.renderAllMenusOnce();
        
        console.log('Applying filters...'); // デバッグ
        this.applyFilters();
        console.log('Filters applied'); // デバッグ
    }

    updateUserInfo() {
        const userInfoElement = document.getElementById('userInfo');
        if (userInfoElement && currentUser) {
            userInfoElement.textContent = `${currentUser.full_name}さん`;
        }
    }

    setupEventListeners() {
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

        [searchInput, priceMinInput, priceMaxInput].forEach(input => {
            if (input) {
                input.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') this.applyFilters();
                });
            }
        });

        // イベント委譲で数量変更ボタンを処理
        const container = document.getElementById('menuGrid');
        if (container) {
            container.addEventListener('click', (e) => {
                const btn = e.target.closest('.quantity-btn');
                if (btn) {
                    e.stopPropagation();
                    const menuCard = btn.closest('.menu-card');
                    const menuId = parseInt(menuCard.dataset.menuId);
                    const action = btn.dataset.action;
                    this.updateQuantity(menuId, action);
                    return;
                }

                const orderBtn = e.target.closest('.order-now-btn');
                if (orderBtn) {
                    e.stopPropagation();
                    const menuCard = orderBtn.closest('.menu-card');
                    const menuId = parseInt(menuCard.dataset.menuId);
                    this.orderNow(menuId);
                    return;
                }

                const detailBtn = e.target.closest('.view-detail-btn');
                if (detailBtn) {
                    e.stopPropagation();
                    const menuCard = detailBtn.closest('.menu-card');
                    const menuId = parseInt(menuCard.dataset.menuId);
                    this.showMenuDetail(menuId);
                }
            });
        }
    }

    async loadMenus() {
        try {
            this.showLoading();
            
            const response = await ApiClient.get('/customer/menus', { per_page: 100 });
            
            console.log('Menu response:', response); // デバッグログ
            
            if (!response || !response.menus) {
                throw new Error('メニューデータの形式が正しくありません');
            }
            
            this.menus = response.menus;
            this.filteredMenus = [...this.menus];
            this.hideLoading();
            
            if (this.menus.length === 0) {
                this.showEmptyMessage();
            }
            
        } catch (error) {
            console.error('Failed to load menus:', error);
            this.hideLoading();
            
            let errorMessage = 'メニューの読み込みに失敗しました';
            if (error.message && error.message.includes('401')) {
                errorMessage = '認証が切れました。再度ログインしてください。';
                setTimeout(() => Auth.logout(), 2000);
            } else if (error.message) {
                errorMessage = error.message;
            }
            
            this.showError(errorMessage);
            UI.showAlert(errorMessage, 'danger');
        }
    }

    renderAllMenusOnce() {
        console.log('renderAllMenusOnce called, menus.length:', this.menus.length); // デバッグ
        
        const container = document.getElementById('menuGrid');
        if (!container) {
            console.error('menuGrid container not found!'); // デバッグ
            return;
        }
        
        if (this.menus.length === 0) {
            console.log('No menus to render'); // デバッグ
            return;
        }

        // 一度だけHTMLを生成してDOM挿入
        const fragment = document.createDocumentFragment();
        
        this.menus.forEach(menu => {
            const card = this.createMenuCardElement(menu);
            this.menuCardsCache.set(menu.id, card);
            fragment.appendChild(card);
        });
        
        console.log('Cards created:', this.menuCardsCache.size); // デバッグ
        
        container.innerHTML = '';
        container.appendChild(fragment);
        
        console.log('Fragment appended to container'); // デバッグ
    }

    createMenuCardElement(menu) {
        const card = document.createElement('div');
        card.className = 'menu-card hidden';
        card.dataset.menuId = menu.id;
        
        card.innerHTML = `
            <div style="position: relative;">
                <img src="${menu.image_url}" alt="${menu.name}" class="menu-image" 
                     onerror="this.src='https://via.placeholder.com/300x200?text=No+Image'">
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
                
                <div class="order-summary-fixed">
                    <span class="order-summary-text">小計: <span class="order-summary-price">¥0</span></span>
                </div>
                
                <div class="menu-actions">
                    <button type="button" class="btn btn-primary btn-sm order-now-btn" disabled>
                        今すぐ注文
                    </button>
                    <button type="button" class="btn btn-secondary btn-sm view-detail-btn">
                        詳細を見る
                    </button>
                </div>
            </div>
        `;
        
        return card;
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
        console.log('updateMenuVisibility called'); // デバッグ
        
        const container = document.getElementById('menuGrid');
        if (!container) return;

        // ページネーション計算
        const startIndex = (this.currentPage - 1) * this.perPage;
        const endIndex = startIndex + this.perPage;
        
        const visibleMenuIds = new Set(
            this.filteredMenus
                .slice(startIndex, endIndex)
                .map(menu => menu.id)
        );

        console.log('Visible menu IDs:', Array.from(visibleMenuIds)); // デバッグ
        console.log('Total cards in cache:', this.menuCardsCache.size); // デバッグ

        // CSSクラスのみ変更（リフロー最小化）
        this.menuCardsCache.forEach((card, menuId) => {
            if (visibleMenuIds.has(menuId)) {
                card.classList.remove('hidden');
                console.log('Showing card:', menuId); // デバッグ
            } else {
                card.classList.add('hidden');
            }
        });

        // 空メッセージ表示
        let emptyState = container.querySelector('.empty-state');
        if (this.filteredMenus.length === 0) {
            if (!emptyState) {
                emptyState = document.createElement('div');
                emptyState.className = 'empty-state';
                emptyState.innerHTML = `
                    <div class="no-menus-icon">🔍</div>
                    <h3>メニューが見つかりません</h3>
                    <p>検索条件を変更してみてください</p>
                    <button type="button" class="btn btn-secondary" onclick="customerMenuPage.clearFilters()">
                        フィルターをクリア
                    </button>
                `;
                container.appendChild(emptyState);
            }
            emptyState.classList.remove('hidden');
        } else if (emptyState) {
            emptyState.classList.add('hidden');
        }

        this.setupPagination();
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

        this.updateMenuCardUI(menuId, newQuantity);
    }

    updateMenuCardUI(menuId, quantity) {
        const card = this.menuCardsCache.get(menuId);
        if (!card) return;

        const menu = this.menus.find(m => m.id === menuId);
        if (!menu) return;

        // DOM要素を一度だけ取得
        const elements = {
            quantityInput: card.querySelector('.quantity-input'),
            decreaseBtn: card.querySelector('[data-action="decrease"]'),
            increaseBtn: card.querySelector('[data-action="increase"]'),
            orderBtn: card.querySelector('.order-now-btn'),
            summaryText: card.querySelector('.order-summary-text'),
            summaryPrice: card.querySelector('.order-summary-price')
        };

        // すべての更新を1つのrequestAnimationFrameにまとめる
        requestAnimationFrame(() => {
            const totalPrice = menu.price * quantity;

            elements.quantityInput.value = quantity;
            elements.decreaseBtn.disabled = quantity <= 0;
            elements.increaseBtn.disabled = quantity >= 10;
            elements.orderBtn.disabled = quantity <= 0;

            if (quantity > 0) {
                elements.summaryPrice.textContent = UI.formatPrice(totalPrice);
                elements.summaryText.style.visibility = 'visible';
            } else {
                elements.summaryText.style.visibility = 'hidden';
            }
        });
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

        const confirmed = confirm(`${menu.name} を ${quantity}個 注文しますか？\n合計金額: ${UI.formatPrice(menu.price * quantity)}`);
        if (!confirmed) return;

        try {
            await ApiClient.post('/customer/orders', {
                menu_id: menuId,
                quantity: quantity
            });

            UI.showAlert('注文を受け付けました！', 'success');
            this.orderItems.delete(menuId);
            this.updateMenuCardUI(menuId, 0);

        } catch (error) {
            console.error('Failed to create order:', error);
            
            let errorMessage = '注文に失敗しました';
            if (error.message.includes('401')) {
                errorMessage = '認証が切れました。再度ログインしてください。';
                setTimeout(() => Auth.logout(), 2000);
            } else if (error.message.includes('400')) {
                errorMessage = '注文内容に問題があります。';
            }
            
            UI.showAlert(errorMessage, 'danger');
        }
    }

    showMenuDetail(menuId) {
        const menu = this.menus.find(m => m.id === menuId);
        if (!menu) return;

        const modalContent = `
            <div class="menu-detail-modal">
                <img src="${menu.image_url}" alt="${menu.name}" class="modal-menu-image">
                <h2>${this.escapeHtml(menu.name)}</h2>
                <p class="modal-description">${this.escapeHtml(menu.description || '')}</p>
                <p class="modal-price">価格: ${UI.formatPrice(menu.price)}</p>
            </div>
        `;

        UI.showModal('メニュー詳細', modalContent);
    }

    setupPagination() {
        const paginationContainer = document.getElementById('pagination');
        if (!paginationContainer) return;

        const totalPages = Math.ceil(this.filteredMenus.length / this.perPage);
        
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        let paginationHTML = '<ul class="pagination">';
        
        paginationHTML += `
            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                <button class="page-link" onclick="customerMenuPage.goToPage(${this.currentPage - 1})" ${this.currentPage === 1 ? 'disabled' : ''}>
                    前へ
                </button>
            </li>
        `;

        const maxVisiblePages = 5;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
        
        if (endPage - startPage < maxVisiblePages - 1) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `
                <li class="page-item ${i === this.currentPage ? 'active' : ''}">
                    <button class="page-link" onclick="customerMenuPage.goToPage(${i})">${i}</button>
                </li>
            `;
        }

        paginationHTML += `
            <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
                <button class="page-link" onclick="customerMenuPage.goToPage(${this.currentPage + 1})" ${this.currentPage === totalPages ? 'disabled' : ''}>
                    次へ
                </button>
            </li>
        `;

        paginationHTML += '</ul>';
        paginationContainer.innerHTML = paginationHTML;
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.filteredMenus.length / this.perPage);
        if (page < 1 || page > totalPages) return;
        
        this.currentPage = page;
        this.updateMenuVisibility();
    }

    updateResultCount() {
        const resultCountElement = document.getElementById('resultCount');
        if (resultCountElement) {
            resultCountElement.textContent = `${this.filteredMenus.length}件のメニュー`;
        }
    }

    showLoading() {
        const container = document.getElementById('menuGrid');
        if (container) {
            container.innerHTML = '<div class="loading-overlay"><div class="spinner"></div></div>';
        }
    }

    hideLoading() {
        const loadingOverlay = document.querySelector('.loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.remove();
        }
    }

    showError(message) {
        const container = document.getElementById('menuGrid');
        if (container) {
            container.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>${message}</p>
                </div>
            `;
        }
    }

    showEmptyMessage() {
        const container = document.getElementById('menuGrid');
        if (container) {
            container.innerHTML = `
                <div class="no-menus">
                    <div class="no-menus-icon">📝</div>
                    <h3>現在メニューがありません</h3>
                    <p>メニューが登録されるまでお待ちください</p>
                </div>
            `;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

let customerMenuPage;
document.addEventListener('DOMContentLoaded', () => {
    customerMenuPage = new CustomerMenuPage();
});
