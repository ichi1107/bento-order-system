/**
 * 店舗注文管理 JavaScript
 */

class OrderManager {
    constructor() {
        this.orders = [];
        this.filteredOrders = [];
        this.currentFilter = "all";
        this.currentSort = "newest";
        this.pollingInterval = null;
        this.pollingIntervalTime = 30000;
        this.isPollingActive = false;
        this.elements = {};
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
            this.attachEventListeners();
            await this.loadOrders();
            this.startPolling();
            document.addEventListener("visibilitychange", () => {
                if (document.hidden) {
                    this.stopPolling();
                } else {
                    this.startPolling();
                    this.loadOrders();
                }
            });
        } catch (error) {
            console.error("初期化エラー:", error);
            this.showError("初期化に失敗しました");
        }
    }

    initializeElements() {
        this.elements.ordersGrid = document.getElementById("ordersGrid");
        this.elements.filterStatus = document.getElementById("statusFilter");
        this.elements.sortOrder = document.getElementById("sortOrder");
        this.elements.totalCount = document.getElementById("totalOrdersCount");
        this.elements.pendingCount = document.getElementById("pendingOrdersCount");
        this.elements.preparingCount = document.getElementById("preparingCount");
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
        this.elements.filterStatus.addEventListener("change", () => {
            this.currentFilter = this.elements.filterStatus.value;
            this.filterAndDisplayOrders();
        });
        this.elements.sortOrder.addEventListener("change", () => {
            this.currentSort = this.elements.sortOrder.value;
            this.filterAndDisplayOrders();
        });
        this.elements.refreshBtn.addEventListener("click", () => {
            this.loadOrders();
        });
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

    async loadOrders() {
        try {
            this.showLoading();
            this.hideError();
            const token = localStorage.getItem("authToken");
            const response = await fetch("/api/store/orders", {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!response.ok) {
                if (response.status === 401) {
                    localStorage.removeItem("authToken");
                    window.location.href = "/login";
                    return;
                }
                throw new Error("注文の取得に失敗しました");
            }
            const data = await response.json();
            console.log("API Response:", data); // デバッグ用
            
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
            
            this.filterAndDisplayOrders();
            this.updateCounts();
            this.hideLoading();
        } catch (error) {
            console.error("注文読み込みエラー:", error);
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

    filterAndDisplayOrders() {
        if (this.currentFilter === "all") {
            this.filteredOrders = [...this.orders];
        } else {
            this.filteredOrders = this.orders.filter(order => order.status === this.currentFilter);
        }
        this.filteredOrders.sort((a, b) => {
            const dateA = new Date(a.ordered_at);
            const dateB = new Date(b.ordered_at);
            return this.currentSort === "newest" ? dateB - dateA : dateA - dateB;
        });
        this.displayOrders();
    }

    displayOrders() {
        this.elements.ordersGrid.innerHTML = "";
        if (this.filteredOrders.length === 0) {
            this.elements.emptyState.style.display = "block";
            return;
        }
        this.elements.emptyState.style.display = "none";
        this.filteredOrders.forEach(order => {
            const card = this.createOrderCard(order);
            this.elements.ordersGrid.appendChild(card);
        });
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
                    <select class="status-select" data-order-id="${order.id}">
                        <option value="pending" ${order.status === "pending" ? "selected" : ""}>未確認</option>
                        <option value="confirmed" ${order.status === "confirmed" ? "selected" : ""}>確認済み</option>
                        <option value="preparing" ${order.status === "preparing" ? "selected" : ""}>準備中</option>
                        <option value="ready" ${order.status === "ready" ? "selected" : ""}>受取可能</option>
                        <option value="completed" ${order.status === "completed" ? "selected" : ""}>完了</option>
                        <option value="cancelled" ${order.status === "cancelled" ? "selected" : ""}>キャンセル</option>
                    </select>
                    <button class="btn btn-primary btn-sm update-status-btn" data-order-id="${order.id}">ステータス更新</button>
                </div>
                <button class="btn btn-secondary btn-sm detail-btn" data-order-id="${order.id}">詳細</button>
            </div>
        `;
        card.querySelector(".update-status-btn").addEventListener("click", () => this.updateOrderStatus(order.id));
        card.querySelector(".detail-btn").addEventListener("click", () => this.showOrderDetail(order));
        return card;
    }

    async updateOrderStatus(orderId) {
        try {
            const selectElement = document.querySelector(`.status-select[data-order-id="${orderId}"]`);
            const newStatus = selectElement.value;
            const order = this.orders.find(o => o.id === orderId);
            const currentStatus = order.status;
            if (newStatus === currentStatus) {
                this.showToast("info", "変更なし", "ステータスは変更されていません");
                return;
            }
            if (newStatus === "cancelled" && !confirm("この注文をキャンセルしますか?")) {
                selectElement.value = currentStatus;
                return;
            }
            const token = localStorage.getItem("authToken");
            const response = await fetch(`/api/store/orders/${orderId}/status`, {
                method: "PUT",
                headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
                body: JSON.stringify({ status: newStatus })
            });
            if (!response.ok) throw new Error("ステータスの更新に失敗しました");
            const updatedOrder = await response.json();
            const index = this.orders.findIndex(o => o.id === orderId);
            if (index !== -1) {
                this.orders[index] = this.normalizeOrder(updatedOrder);
            }
            this.filterAndDisplayOrders();
            this.updateCounts();
            this.showToast("success", "更新成功", "ステータスを更新しました");
        } catch (error) {
            console.error("ステータス更新エラー:", error);
            this.showToast("error", "エラー", error.message);
            const selectElement = document.querySelector(`.status-select[data-order-id="${orderId}"]`);
            const order = this.orders.find(o => o.id === orderId);
            if (order) selectElement.value = order.status;
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
        this.elements.preparingCount.textContent = this.orders.filter(o => o.status === "preparing").length;
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
