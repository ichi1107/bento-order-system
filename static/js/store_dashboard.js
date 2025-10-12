// 店舗ダッシュボード - store_dashboard.js

/**
 * ダッシュボードデータ管理クラス
 */
class DashboardManager {
    constructor() {
        this.data = null;
        this.isLoading = false;
    }

    /**
     * ローディング表示を制御
     */
    showLoading(show = true) {
        const indicator = document.getElementById('loadingIndicator');
        const statsGrid = document.getElementById('statsGrid');
        
        if (indicator) {
            indicator.style.display = show ? 'block' : 'none';
        }
        
        if (statsGrid) {
            statsGrid.style.opacity = show ? '0.5' : '1';
        }
    }

    /**
     * エラーメッセージを表示
     */
    showError(message) {
        const errorElement = document.getElementById('errorMessage');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
            
            // 5秒後に自動で非表示
            setTimeout(() => {
                errorElement.style.display = 'none';
            }, 5000);
        }
    }

    /**
     * エラーメッセージを非表示
     */
    hideError() {
        const errorElement = document.getElementById('errorMessage');
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    }

    /**
     * ダッシュボードデータを取得
     */
    async fetchData() {
        if (this.isLoading) {
            console.log('Already loading...');
            return;
        }

        this.isLoading = true;
        this.showLoading(true);
        this.hideError();

        try {
            const data = await ApiClient.get('/store/dashboard');
            this.data = data;
            this.renderAll();
            console.log('Dashboard data loaded successfully:', data);
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showError('ダッシュボードデータの読み込みに失敗しました。ページを再読み込みしてください。');
            UI.showAlert('データの読み込みに失敗しました', 'error');
        } finally {
            this.isLoading = false;
            this.showLoading(false);
        }
    }

    /**
     * 全てのUI要素を更新
     */
    renderAll() {
        if (!this.data) return;

        this.renderStatCards();
        this.renderPopularMenus();
    }

    /**
     * 統計カードを更新
     */
    renderStatCards() {
        const data = this.data;

        // 今日の注文数
        this.updateElement('total-orders', data.total_orders);
        
        // 注文数の前日比
        this.updateOrdersChange(data.yesterday_comparison);

        // 今日の売上
        this.updateElement('total-revenue', UI.formatPrice(data.today_revenue));
        
        // 売上の前日比
        this.updateRevenueChange(data.yesterday_comparison);

        // 待機中の注文数
        this.updateElement('pending-orders', data.pending_orders);
        
        // 平均注文単価
        this.updateElement('average-order-value', `平均 ${UI.formatPrice(Math.round(data.average_order_value))}`);

        // トップメニュー
        if (data.popular_menus && data.popular_menus.length > 0) {
            const topMenu = data.popular_menus[0];
            this.updateElement('top-menu-name', topMenu.menu_name);
            this.updateElement('top-menu-count', `${topMenu.order_count}回注文`);
        } else {
            this.updateElement('top-menu-name', 'データなし');
            this.updateElement('top-menu-count', '-');
        }
    }

    /**
     * 注文数の前日比を更新
     */
    updateOrdersChange(comparison) {
        const element = document.getElementById('orders-change');
        if (!element) return;

        const change = comparison.orders_change;
        const percent = comparison.orders_change_percent;

        if (change > 0) {
            element.className = 'stat-change positive';
            element.innerHTML = `↑ ${change}件 (${percent > 0 ? '+' : ''}${percent.toFixed(1)}%)`;
        } else if (change < 0) {
            element.className = 'stat-change negative';
            element.innerHTML = `↓ ${Math.abs(change)}件 (${percent.toFixed(1)}%)`;
        } else {
            element.className = 'stat-change';
            element.textContent = '変動なし';
        }
    }

    /**
     * 売上の前日比を更新
     */
    updateRevenueChange(comparison) {
        const element = document.getElementById('revenue-change');
        if (!element) return;

        const change = comparison.revenue_change;
        const percent = comparison.revenue_change_percent;

        if (change > 0) {
            element.className = 'stat-change positive';
            element.innerHTML = `↑ ${UI.formatPrice(change)} (${percent > 0 ? '+' : ''}${percent.toFixed(1)}%)`;
        } else if (change < 0) {
            element.className = 'stat-change negative';
            element.innerHTML = `↓ ${UI.formatPrice(Math.abs(change))} (${percent.toFixed(1)}%)`;
        } else {
            element.className = 'stat-change';
            element.textContent = '変動なし';
        }
    }

    /**
     * 人気メニューリストを更新
     */
    renderPopularMenus() {
        const container = document.getElementById('popular-menus-list');
        if (!container) return;

        const menus = this.data.popular_menus || [];

        if (menus.length === 0) {
            container.innerHTML = '<p class="loading-text">本日の注文データがありません</p>';
            return;
        }

        const html = menus.map((menu, index) => {
            const rank = index + 1;
            const rankClass = `rank-${rank}`;
            
            return `
                <div class="popular-menu-item">
                    <div class="menu-rank ${rankClass}">${rank}</div>
                    <div class="menu-info">
                        <span class="menu-name">${this.escapeHtml(menu.menu_name)}</span>
                        <div class="menu-stats">
                            <span class="menu-stat"><strong>${menu.order_count}</strong>回注文</span>
                            <span class="menu-stat">売上 <strong>${UI.formatPrice(menu.total_revenue)}</strong></span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = html;
    }

    /**
     * DOM要素のテキストを更新
     */
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    /**
     * HTMLエスケープ
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * データを再読み込み
     */
    async refresh() {
        await this.fetchData();
        UI.showAlert('データを更新しました', 'success');
    }
}

// グローバルインスタンス
const dashboardManager = new DashboardManager();

/**
 * ページ読み込み時の初期化
 */
document.addEventListener('DOMContentLoaded', async () => {
    // 認証チェック
    if (!Auth.requireRole('store')) return;

    // ヘッダー情報を表示
    await UI.initializeStoreHeader();

    // 共通UI初期化（ログアウトボタンなど）
    initializeCommonUI();

    // ダッシュボードデータを読み込み
    await dashboardManager.fetchData();
});

/**
 * データ更新関数（グローバル）
 * HTMLのonclick属性から呼び出される
 */
async function refreshDashboard() {
    await dashboardManager.refresh();
}
