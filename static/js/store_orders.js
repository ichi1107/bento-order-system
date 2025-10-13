/**
 * 店舗注文管理 JavaScript - 拡張フィルタリング対応
 */

class OrderManager {
    constructor() {
        this.orders = [];
        this.currentFilters = {
            status: [],
            startDate: '',
            endDate: '',
            search: '',
            sort: 'newest'
        };
        this.pollingInterval = null;
        this.pollingIntervalTime = 30000;
        this.isPollingActive = false;
        this.isLoading = false; // ローディング状態フラグ
        this.pendingRequest = null; // 進行中のリクエストを管理
        this.elements = {};
        this.searchTimeout = null;
        this.dateTimeout = null; // 日付フィルタ用のデバウンスタイマー
        this.init();
    }

    async init() {
        try {
            const token = localStorage.getItem("authToken");
            if (!token) {
                window.location.href = "/login";
                return;
            }
            this.initializeElements();
            this.restoreFiltersFromURL();
            this.attachEventListeners();
            await this.loadOrders();
            this.startPolling();
            
            // ページ表示/非表示の監視
            document.addEventListener("visibilitychange", () => {
                if (document.hidden) {
                    this.stopPolling();
                } else {
                    this.startPolling();
                    this.loadOrders();
                }
            });

            // ブラウザの戻る/進むボタン対応
            window.addEventListener('popstate', () => {
                this.restoreFiltersFromURL();
                this.loadOrders();
            });
        } catch (error) {
            console.error("初期化エラー:", error);
            this.showError("初期化に失敗しました");
        }
    }

    initializeElements() {
        this.elements.ordersGrid = document.getElementById("ordersGrid");
        this.elements.sortOrder = document.getElementById("sortOrder");
        this.elements.searchInput = document.getElementById("searchInput");
        this.elements.startDate = document.getElementById("startDate");
        this.elements.endDate = document.getElementById("endDate");
        this.elements.statusCheckboxes = document.querySelectorAll(".status-checkbox");
        this.elements.clearSearchBtn = document.getElementById("clearSearchBtn");
        this.elements.clearDateBtn = document.getElementById("clearDateBtn");
        this.elements.resetFiltersBtn = document.getElementById("resetFiltersBtn");
        this.elements.searchResultsInfo = document.getElementById("searchResultsInfo");
        this.elements.totalCount = document.getElementById("totalOrdersCount");
        this.elements.pendingCount = document.getElementById("pendingOrdersCount");
        this.elements.readyCount = document.getElementById("readyCount");
        this.elements.loadingElement = document.getElementById("loadingContainer");
        this.elements.errorElement = document.getElementById("errorContainer");
        this.elements.errorMessage = document.getElementById("errorMessage");
        this.elements.emptyState = document.getElementById("emptyState");
        this.elements.modal = document.getElementById("orderDetailModal");
        this.elements.modalBody = document.getElementById("orderDetailBody");
        this.elements.toastContainer = document.getElementById("toastContainer");
        this.elements.refreshBtn = document.getElementById("refreshBtn");
        this.elements.autoRefreshStatus = document.getElementById("autoRefreshText");
    }

    attachEventListeners() {
        // ステータスチェックボックス
        this.elements.statusCheckboxes.forEach(checkbox => {
            checkbox.addEventListener("change", () => {
                this.updateFiltersAndLoad();
            });
        });

        // ソート順
        this.elements.sortOrder.addEventListener("change", () => {
            this.currentFilters.sort = this.elements.sortOrder.value;
            this.updateFiltersAndLoad();
        });

        // 検索入力（デバウンス）
        this.elements.searchInput.addEventListener("input", (e) => {
            clearTimeout(this.searchTimeout);
            const value = e.target.value.trim();
            
            // クリアボタンの表示切替
            this.elements.clearSearchBtn.style.display = value ? 'block' : 'none';
            
            this.searchTimeout = setTimeout(() => {
                this.currentFilters.search = value;
                this.updateFiltersAndLoad();
            }, 500); // 500ms のデバウンス
        });

        // 検索クリアボタン
        this.elements.clearSearchBtn.addEventListener("click", () => {
            this.elements.searchInput.value = '';
            this.currentFilters.search = '';
            this.elements.clearSearchBtn.style.display = 'none';
            this.updateFiltersAndLoad();
        });

        // 日付フィルタ（お客様の注文履歴と同じく、changeイベントで即座に適用）
        this.elements.startDate.addEventListener("change", () => {
            const newValue = this.elements.startDate.value;
            console.log('📅 Start date changed:', newValue);
            this.currentFilters.startDate = newValue;
            this.updateFiltersAndLoad();
        });

        this.elements.endDate.addEventListener("change", () => {
            const newValue = this.elements.endDate.value;
            console.log('📅 End date changed:', newValue);
            this.currentFilters.endDate = newValue;
            this.updateFiltersAndLoad();
        });

        // 日付クリアボタン
        this.elements.clearDateBtn.addEventListener("click", () => {
            this.elements.startDate.value = '';
            this.elements.endDate.value = '';
            this.currentFilters.startDate = '';
            this.currentFilters.endDate = '';
            this.updateFiltersAndLoad();
        });

        // フィルタリセットボタン
        this.elements.resetFiltersBtn.addEventListener("click", () => {
            this.resetFilters();
        });

        // 更新ボタン
        this.elements.refreshBtn.addEventListener("click", () => {
            this.loadOrders();
        });

        // モーダル
        const closeModal = () => {
            this.elements.modal.classList.remove("active");
        };
        document.getElementById("modalCloseBtn").addEventListener("click", closeModal);
        document.getElementById("modalCancelBtn").addEventListener("click", closeModal);
        document.getElementById("modalOverlay").addEventListener("click", closeModal);
        this.elements.modal.addEventListener("click", (e) => {
            if (e.target === this.elements.modal) {
                closeModal();
            }
        });
    }

    /**
     * URLからフィルター状態を復元
     */
    restoreFiltersFromURL() {
        const params = new URLSearchParams(window.location.search);
        
        // ステータス
        const statusParam = params.get('status');
        if (statusParam) {
            this.currentFilters.status = statusParam.split(',');
            this.elements.statusCheckboxes.forEach(cb => {
                cb.checked = this.currentFilters.status.includes(cb.value);
            });
        } else {
            // デフォルト: 未完了のステータスのみ
            this.currentFilters.status = ['pending', 'ready'];
            this.elements.statusCheckboxes.forEach(cb => {
                cb.checked = this.currentFilters.status.includes(cb.value);
            });
        }
        
        // 日付
        this.currentFilters.startDate = params.get('start_date') || '';
        this.currentFilters.endDate = params.get('end_date') || '';
        this.elements.startDate.value = this.currentFilters.startDate;
        this.elements.endDate.value = this.currentFilters.endDate;
        
        // 検索
        this.currentFilters.search = params.get('q') || '';
        this.elements.searchInput.value = this.currentFilters.search;
        this.elements.clearSearchBtn.style.display = this.currentFilters.search ? 'block' : 'none';
        
        // ソート
        this.currentFilters.sort = params.get('sort') || 'newest';
        this.elements.sortOrder.value = this.currentFilters.sort;
    }

    /**
     * フィルター状態をURLに反映
     */
    updateURLParams() {
        const params = new URLSearchParams();
        
        // ステータス
        const checkedStatuses = Array.from(this.elements.statusCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
        
        this.currentFilters.status = checkedStatuses;
        
        if (checkedStatuses.length > 0 && checkedStatuses.length < 6) {
            params.set('status', checkedStatuses.join(','));
        }
        
        // 日付
        if (this.currentFilters.startDate) {
            params.set('start_date', this.currentFilters.startDate);
        }
        if (this.currentFilters.endDate) {
            params.set('end_date', this.currentFilters.endDate);
        }
        
        // 検索
        if (this.currentFilters.search) {
            params.set('q', this.currentFilters.search);
        }
        
        // ソート
        if (this.currentFilters.sort !== 'newest') {
            params.set('sort', this.currentFilters.sort);
        }
        
        // URLを更新（ページリロードなし）
        const newURL = params.toString() 
            ? `${window.location.pathname}?${params.toString()}`
            : window.location.pathname;
        
        window.history.pushState({}, '', newURL);
    }

    /**
     * フィルター更新とデータ読み込み
     */
    updateFiltersAndLoad() {
        this.updateURLParams();
        this.loadOrders();
    }

    /**
     * フィルターをリセット
     */
    resetFilters() {
        // デフォルト値に戻す
        this.elements.statusCheckboxes.forEach(cb => {
            cb.checked = ['pending', 'ready'].includes(cb.value);
        });
        this.elements.startDate.value = '';
        this.elements.endDate.value = '';
        this.elements.searchInput.value = '';
        this.elements.sortOrder.value = 'newest';
        this.elements.clearSearchBtn.style.display = 'none';
        
        this.currentFilters = {
            status: ['pending', 'ready'],
            startDate: '',
            endDate: '',
            search: '',
            sort: 'newest'
        };
        
        this.updateFiltersAndLoad();
    }

    async loadOrders() {
        try {
            // 既に進行中のリクエストがある場合はキャンセル
            if (this.pendingRequest) {
                console.log('⏭️ Cancelling previous request');
                this.pendingRequest.cancelled = true;
            }
            
            // 新しいリクエストオブジェクトを作成
            const currentRequest = { cancelled: false };
            this.pendingRequest = currentRequest;
            
            console.log('🔄 Loading orders started...');
            this.isLoading = true;
            this.showLoading();
            this.hideError();
            
            const token = localStorage.getItem("authToken");
            
            // クエリパラメータを構築
            const params = new URLSearchParams();
            
            if (this.currentFilters.status.length > 0) {
                params.set('status', this.currentFilters.status.join(','));
            }
            if (this.currentFilters.startDate) {
                params.set('start_date', this.currentFilters.startDate);
            }
            if (this.currentFilters.endDate) {
                params.set('end_date', this.currentFilters.endDate);
            }
            if (this.currentFilters.search) {
                params.set('q', this.currentFilters.search);
            }
            if (this.currentFilters.sort) {
                params.set('sort', this.currentFilters.sort);
            }
            
            // 大量データ対応: per_pageを1000に設定
            params.set('per_page', '1000');
            
            const url = `/api/store/orders?${params.toString()}`;
            console.log('===== API Request Debug =====');
            console.log('URL:', url);
            console.log('Current Filters:', this.currentFilters);
            console.log('URL Params:', Object.fromEntries(params));
            console.log('=============================');
            
            const startTime = performance.now(); // パフォーマンス計測開始
            
            const response = await fetch(url, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            
            // リクエストがキャンセルされた場合は処理を中断
            if (currentRequest.cancelled) {
                console.log('❌ Request was cancelled');
                return;
            }
            
            if (!response.ok) {
                if (response.status === 401) {
                    localStorage.removeItem("authToken");
                    window.location.href = "/login";
                    return;
                }
                throw new Error("注文の取得に失敗しました");
            }
            
            const data = await response.json();
            
            // リクエストがキャンセルされた場合は処理を中断
            if (currentRequest.cancelled) {
                console.log('❌ Request was cancelled after fetch');
                return;
            }
            
            const endTime = performance.now(); // パフォーマンス計測終了
            console.log(`✅ Orders loaded in ${(endTime - startTime).toFixed(2)}ms`);
            console.log('API Response:', {
                totalOrders: data.total || data.length,
                ordersCount: data.orders ? data.orders.length : (Array.isArray(data) ? data.length : 0)
            });
            
            // レスポンスが配列であることを確認
            if (Array.isArray(data)) {
                this.orders = data;
            } else if (data && Array.isArray(data.orders)) {
                this.orders = data.orders;
            } else {
                console.error("Unexpected API response format:", data);
                this.orders = [];
            }
            
            // データ変換: APIレスポンスをフロントエンド用に整形
            this.orders = this.orders.map(order => this.normalizeOrder(order));
            
            this.displayOrders();
            this.updateCounts();
            this.updateSearchResultsInfo(data.total || this.orders.length);
            this.isLoading = false;
            this.pendingRequest = null;
            this.hideLoading();
        } catch (error) {
            console.error("注文読み込みエラー:", error);
            this.isLoading = false;
            this.pendingRequest = null;
            this.hideLoading();
            this.showError(error.message);
        }
    }

    /**
     * APIレスポンスを正規化
     */
    normalizeOrder(order) {
        return {
            id: order.id,
            status: order.status,
            quantity: order.quantity,
            total_amount: order.total_price, // API: total_price -> total_amount
            ordered_at: order.ordered_at,
            pickup_time: order.delivery_time, // API: delivery_time -> pickup_time
            notes: order.notes,
            customer_name: order.user ? order.user.full_name || order.user.username : "不明",
            menu_name: order.menu ? order.menu.name : "不明",
            price: order.menu ? order.menu.price : 0
        };
    }

    displayOrders() {
        this.elements.ordersGrid.innerHTML = "";
        if (this.orders.length === 0) {
            this.elements.emptyState.style.display = "block";
            return;
        }
        this.elements.emptyState.style.display = "none";
        
        // パフォーマンス最適化: DocumentFragmentを使用
        const fragment = document.createDocumentFragment();
        this.orders.forEach(order => {
            const card = this.createOrderCard(order);
            fragment.appendChild(card);
        });
        this.elements.ordersGrid.appendChild(fragment);
    }

    /**
     * 検索結果情報を更新
     */
    updateSearchResultsInfo(total) {
        const hasActiveFilters = 
            this.currentFilters.search ||
            this.currentFilters.startDate ||
            this.currentFilters.endDate ||
            this.currentFilters.status.length !== 4; // デフォルト以外
        
        if (!hasActiveFilters) {
            this.elements.searchResultsInfo.style.display = 'none';
            return;
        }
        
        this.elements.searchResultsInfo.style.display = 'flex';
        const resultsCount = this.elements.searchResultsInfo.querySelector('.results-count');
        const activeFilters = this.elements.searchResultsInfo.querySelector('.active-filters');
        
        resultsCount.textContent = `${total}件の注文が見つかりました`;
        
        // アクティブなフィルタを表示
        const filters = [];
        if (this.currentFilters.search) {
            filters.push(`検索: "${this.currentFilters.search}"`);
        }
        if (this.currentFilters.startDate || this.currentFilters.endDate) {
            const dateRange = `${this.currentFilters.startDate || '開始日未指定'} 〜 ${this.currentFilters.endDate || '終了日未指定'}`;
            filters.push(`期間: ${dateRange}`);
        }
        if (this.currentFilters.status.length > 0 && this.currentFilters.status.length < 4) {
            const statusNames = {
                'pending': '注文受付',
                'ready': '準備完了',
                'completed': '受取完了',
                'cancelled': 'キャンセル'
            };
            const statusLabels = this.currentFilters.status.map(s => statusNames[s]).join(', ');
            filters.push(`ステータス: ${statusLabels}`);
        }
        
        activeFilters.textContent = filters.length > 0 ? `(${filters.join(' / ')})` : '';
    }

    createOrderCard(order) {
        const card = document.createElement("div");
        card.className = `order-card status-${order.status}`;
        const orderedAt = new Date(order.ordered_at);
        const formattedDate = this.formatDateTime(orderedAt);
        let pickupTimeHtml = "";
        if (order.pickup_time) {
            const pickupTime = new Date(order.pickup_time);
            pickupTimeHtml = `<div class="order-info-item"><i class="icon">🕐</i><span>受取時間: ${this.formatTime(pickupTime)}</span></div>`;
        }

        // ステータス遷移ルールの定義（バックエンドと一致）
        const allowedTransitions = {
            'pending': ['ready', 'cancelled'],
            'ready': ['completed'],
            'completed': [],
            'cancelled': []
        };

        const currentAllowed = allowedTransitions[order.status] || [];
        const isTerminalState = currentAllowed.length === 0;

        // ドロップダウンの選択肢を生成（現在のステータス + 遷移可能なステータスのみ）
        const statusOptions = [
            { value: 'pending', label: '注文受付' },
            { value: 'ready', label: '準備完了' },
            { value: 'completed', label: '受取完了' },
            { value: 'cancelled', label: 'キャンセル' }
        ];

        const optionsHtml = statusOptions.map(opt => {
            const isCurrentStatus = opt.value === order.status;
            const isAllowed = currentAllowed.includes(opt.value);
            const shouldShow = isCurrentStatus || isAllowed;
            
            if (!shouldShow) return '';
            
            return `<option value="${opt.value}" ${isCurrentStatus ? 'selected' : ''}>${opt.label}</option>`;
        }).join('');

        card.innerHTML = `
            <div class="order-card-header">
                <div class="order-id">注文 #${order.id}</div>
                <span class="badge badge-${order.status}">${this.getStatusLabel(order.status)}</span>
            </div>
            <div class="order-card-body">
                <div class="order-menu-name">${this.escapeHtml(order.menu_name)}</div>
                <div class="order-info">
                    <div class="order-info-item"><i class="icon">👤</i><span>${this.escapeHtml(order.customer_name)}</span></div>
                    <div class="order-info-item"><i class="icon">📦</i><span>数量: ${order.quantity}</span></div>
                    <div class="order-info-item"><i class="icon">📅</i><span>${formattedDate}</span></div>
                    ${pickupTimeHtml}
                </div>
                <div class="order-total">合計: ¥${order.total_amount.toLocaleString()}</div>
            </div>
            <div class="order-card-footer">
                <div class="status-update">
                    <select class="status-select" data-order-id="${order.id}" ${isTerminalState ? 'disabled' : ''}>
                        ${optionsHtml}
                    </select>
                    <button class="btn btn-primary btn-sm update-status-btn" 
                            data-order-id="${order.id}" 
                            ${isTerminalState ? 'disabled' : ''}
                            title="${isTerminalState ? 'このステータスは変更できません' : 'ステータスを更新'}">
                        ステータス更新
                    </button>
                </div>
                <button class="btn btn-secondary btn-sm detail-btn" data-order-id="${order.id}">詳細</button>
            </div>
        `;
        
        if (!isTerminalState) {
            card.querySelector(".update-status-btn").addEventListener("click", () => this.updateOrderStatus(order.id));
        }
        card.querySelector(".detail-btn").addEventListener("click", () => this.showOrderDetail(order));
        return card;
    }

    async updateOrderStatus(orderId) {
        const selectElement = document.querySelector(`.status-select[data-order-id="${orderId}"]`);
        const newStatus = selectElement.value;
        const order = this.orders.find(o => o.id === orderId);
        const currentStatus = order.status;

        // 変更がない場合は早期リターン
        if (newStatus === currentStatus) {
            this.showToast("info", "変更なし", "ステータスは変更されていません");
            return;
        }

        // キャンセル時の確認ダイアログ
        if (newStatus === "cancelled") {
            const confirmed = confirm(
                "⚠️ この注文をキャンセルしますか?\n\n" +
                `注文 #${orderId}\n` +
                `お客様: ${order.customer_name}\n` +
                `メニュー: ${order.menu_name}\n\n` +
                "キャンセル後は元に戻せません。"
            );
            if (!confirmed) {
                selectElement.value = currentStatus;
                return;
            }
        }

        try {
            const token = localStorage.getItem("authToken");
            const response = await fetch(`/api/store/orders/${orderId}/status`, {
                method: "PUT",
                headers: { 
                    "Content-Type": "application/json", 
                    "Authorization": `Bearer ${token}` 
                },
                body: JSON.stringify({ status: newStatus })
            });

            // エラーレスポンスの詳細処理
            if (!response.ok) {
                const errorData = await response.json();
                const errorMessage = errorData.detail || "ステータスの更新に失敗しました";
                throw new Error(errorMessage);
            }

            const updatedOrder = await response.json();
            
            // 注文データを更新
            const index = this.orders.findIndex(o => o.id === orderId);
            if (index !== -1) {
                this.orders[index] = this.normalizeOrder(updatedOrder);
            }

            // UI更新
            this.displayOrders();
            this.updateCounts();
            
            // 成功メッセージ
            const statusLabels = {
                'pending': '注文受付',
                'ready': '準備完了',
                'completed': '受取完了',
                'cancelled': 'キャンセル'
            };
            this.showToast(
                "success", 
                "更新成功", 
                `ステータスを「${statusLabels[newStatus]}」に更新しました`
            );

        } catch (error) {
            console.error("ステータス更新エラー:", error);
            
            // ロールバック: UIを元のステータスに戻す
            selectElement.value = currentStatus;
            
            // エラーメッセージを表示
            this.showToast("error", "更新エラー", error.message);
        }
    }

    showOrderDetail(order) {
        const orderedAt = new Date(order.ordered_at);
        let pickupTimeHtml = "";
        if (order.pickup_time) {
            const pickupTime = new Date(order.pickup_time);
            pickupTimeHtml = `<div class="detail-row"><span class="detail-label">受取時間:</span><span class="detail-value">${this.formatDateTime(pickupTime)}</span></div>`;
        }
        let notesHtml = "";
        if (order.notes) {
            notesHtml = `<div class="detail-section"><h4>備考</h4><p>${this.escapeHtml(order.notes)}</p></div>`;
        }
        this.elements.modalBody.innerHTML = `
            <div class="detail-section">
                <h4>注文情報</h4>
                <div class="detail-row"><span class="detail-label">注文ID:</span><span class="detail-value">#${order.id}</span></div>
                <div class="detail-row"><span class="detail-label">注文日時:</span><span class="detail-value">${this.formatDateTime(orderedAt)}</span></div>
                <div class="detail-row"><span class="detail-label">ステータス:</span><span class="badge badge-${order.status}">${this.getStatusLabel(order.status)}</span></div>
                ${pickupTimeHtml}
            </div>
            <div class="detail-section">
                <h4>お客様情報</h4>
                <div class="detail-row"><span class="detail-label">氏名:</span><span class="detail-value">${this.escapeHtml(order.customer_name)}</span></div>
            </div>
            <div class="detail-section">
                <h4>メニュー情報</h4>
                <div class="detail-row"><span class="detail-label">メニュー名:</span><span class="detail-value">${this.escapeHtml(order.menu_name)}</span></div>
                <div class="detail-row"><span class="detail-label">単価:</span><span class="detail-value">¥${order.price.toLocaleString()}</span></div>
                <div class="detail-row"><span class="detail-label">数量:</span><span class="detail-value">${order.quantity}</span></div>
                <div class="detail-row"><span class="detail-label">合計:</span><span class="detail-value total-amount">¥${order.total_amount.toLocaleString()}</span></div>
            </div>
            ${notesHtml}
        `;
        this.elements.modal.classList.add("active");
    }

    updateCounts() {
        this.elements.totalCount.textContent = this.orders.length;
        this.elements.pendingCount.textContent = this.orders.filter(o => o.status === "pending").length;
        this.elements.readyCount.textContent = this.orders.filter(o => o.status === "ready").length;
    }

    startPolling() {
        if (this.isPollingActive) return;
        this.isPollingActive = true;
        this.pollingInterval = setInterval(() => {
            if (!document.hidden) this.loadOrders();
        }, this.pollingIntervalTime);
        this.updateAutoRefreshStatus();
    }

    stopPolling() {
        if (!this.isPollingActive) return;
        this.isPollingActive = false;
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        this.updateAutoRefreshStatus();
    }

    updateAutoRefreshStatus() {
        if (this.isPollingActive) {
            this.elements.autoRefreshStatus.textContent = "🔄 自動更新: 有効";
            this.elements.autoRefreshStatus.parentElement.classList.add("active");
        } else {
            this.elements.autoRefreshStatus.textContent = "⏸ 自動更新: 停止中";
            this.elements.autoRefreshStatus.parentElement.classList.remove("active");
        }
    }

    showLoading() {
        this.elements.loadingElement.style.display = "flex";
        this.elements.ordersGrid.style.display = "none";
    }

    hideLoading() {
        this.elements.loadingElement.style.display = "none";
        this.elements.ordersGrid.style.display = "grid";
    }

    showError(message) {
        this.elements.errorMessage.textContent = message;
        this.elements.errorElement.style.display = "flex";
        this.elements.ordersGrid.style.display = "none";
    }

    hideError() {
        this.elements.errorElement.style.display = "none";
    }

    showToast(type, title, message) {
        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        let icon = "";
        switch(type) {
            case "success": icon = "✓"; break;
            case "error": icon = "✕"; break;
            case "warning": icon = "⚠"; break;
            case "info": icon = "ℹ"; break;
        }
        toast.innerHTML = `
            <div class="toast-icon">${icon}</div>
            <div class="toast-content">
                <div class="toast-title">${this.escapeHtml(title)}</div>
                <div class="toast-message">${this.escapeHtml(message)}</div>
            </div>
        `;
        this.elements.toastContainer.appendChild(toast);
        setTimeout(() => toast.classList.add("show"), 10);
        setTimeout(() => {
            toast.classList.remove("show");
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    getStatusLabel(status) {
        const labels = {
            "pending": "未確認",
            "confirmed": "確認済み",
            "preparing": "準備中",
            "ready": "受取可能",
            "completed": "完了",
            "cancelled": "キャンセル"
        };
        return labels[status] || status;
    }

    formatDateTime(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        const hours = String(date.getHours()).padStart(2, "0");
        const minutes = String(date.getMinutes()).padStart(2, "0");
        return `${year}/${month}/${day} ${hours}:${minutes}`;
    }

    formatTime(date) {
        const hours = String(date.getHours()).padStart(2, "0");
        const minutes = String(date.getMinutes()).padStart(2, "0");
        return `${hours}:${minutes}`;
    }

    escapeHtml(text) {
        if (!text) return "";
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }
}

let orderManager;
document.addEventListener("DOMContentLoaded", async () => {
    // ヘッダー情報を初期化
    await UI.initializeStoreHeader();
    
    // 注文管理を初期化
    orderManager = new OrderManager();
});
