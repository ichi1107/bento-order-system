// 店舗ダッシュボード - store_dashboard.js

/**
 * ダッシュボードデータ管理クラス
 */
class DashboardManager {
    constructor() {
        this.data = null;
        this.isLoading = false;
        this.chart = null; // Chart.jsインスタンスを保存
        this.pollingInterval = null; // ポーリング用のインターバルID
        this.pollingIntervalTime = 60000; // 60秒ごとに更新
        this.isPageVisible = true; // ページの可視性状態
    }

    /**
     * ポーリングを開始
     */
    startPolling() {
        // 既存のインターバルをクリア
        this.stopPolling();
        
        // 60秒ごとにデータを更新
        this.pollingInterval = setInterval(() => {
            if (this.isPageVisible) {
                console.log('Auto-refreshing dashboard data...');
                this.fetchData(true); // 自動更新フラグを渡す
            }
        }, this.pollingIntervalTime);
        
        console.log('Polling started (interval: 60s)');
    }

    /**
     * ポーリングを停止
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
            console.log('Polling stopped');
        }
    }

    /**
     * Page Visibility APIでページの可視性を監視
     */
    setupVisibilityListener() {
        document.addEventListener('visibilitychange', () => {
            this.isPageVisible = !document.hidden;
            
            if (this.isPageVisible) {
                console.log('Page became visible - resuming polling');
                // ページが再びアクティブになったら即座にデータを更新
                this.fetchData(true);
            } else {
                console.log('Page became hidden - polling will pause');
            }
        });
    }

    /**
     * 最終更新時刻を更新
     */
    updateLastUpdatedTime() {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        const timeString = `${hours}:${minutes}:${seconds}`;
        
        const timeElement = document.getElementById('lastUpdatedTime');
        if (timeElement) {
            timeElement.textContent = timeString;
        }
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
     * @param {boolean} isAutoRefresh - 自動更新かどうか（trueの場合、UIフィードバックを控えめにする）
     */
    async fetchData(isAutoRefresh = false) {
        if (this.isLoading) {
            console.log('Already loading...');
            return;
        }

        this.isLoading = true;
        
        // 自動更新の場合は控えめなローディング表示
        if (!isAutoRefresh) {
            this.showLoading(true);
        }
        this.hideError();

        try {
            const data = await ApiClient.get('/store/dashboard');
            this.data = data;
            this.renderAll();
            this.updateLastUpdatedTime(); // 最終更新時刻を更新
            console.log('Dashboard data loaded successfully:', data);
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            
            // 自動更新時はエラーメッセージを控えめに
            if (!isAutoRefresh) {
                this.showError('ダッシュボードデータの読み込みに失敗しました。ページを再読み込みしてください。');
                UI.showAlert('データの読み込みに失敗しました', 'error');
            } else {
                console.warn('Auto-refresh failed, will retry on next interval');
            }
        } finally {
            this.isLoading = false;
            if (!isAutoRefresh) {
                this.showLoading(false);
            }
        }
    }

    /**
     * 全てのUI要素を更新
     */
    renderAll() {
        if (!this.data) return;

        this.renderStatCards();
        this.renderPopularMenus();
        this.renderWeeklySalesChart(); // チャート描画を追加
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
     * 週間売上チャートを描画
     */
    async renderWeeklySalesChart() {
        try {
            // 週間売上データを取得
            const weeklySalesData = await ApiClient.get('/store/dashboard/weekly-sales');
            
            // Canvas要素を取得
            const canvas = document.getElementById('weeklySalesChart');
            if (!canvas) {
                console.error('Canvas element not found');
                return;
            }

            const ctx = canvas.getContext('2d');

            // 既存のチャートがあれば破棄
            if (this.chart) {
                this.chart.destroy();
            }

            // Chart.jsでグラフを作成
            this.chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: weeklySalesData.labels,
                    datasets: [{
                        label: '売上 (円)',
                        data: weeklySalesData.data,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        pointBackgroundColor: '#667eea',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                font: {
                                    size: 14,
                                    family: "'Noto Sans JP', sans-serif"
                                },
                                padding: 15
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            titleFont: {
                                size: 14,
                                family: "'Noto Sans JP', sans-serif"
                            },
                            bodyFont: {
                                size: 13,
                                family: "'Noto Sans JP', sans-serif"
                            },
                            padding: 12,
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    label += UI.formatPrice(context.parsed.y);
                                    return label;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                font: {
                                    size: 12,
                                    family: "'Noto Sans JP', sans-serif"
                                },
                                callback: function(value) {
                                    return '¥' + value.toLocaleString();
                                }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        },
                        x: {
                            ticks: {
                                font: {
                                    size: 12,
                                    family: "'Noto Sans JP', sans-serif"
                                }
                            },
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });

            console.log('Weekly sales chart rendered successfully');
        } catch (error) {
            console.error('Failed to render weekly sales chart:', error);
            // チャート描画エラーは致命的ではないので、アラートは表示しない
        }
    }

    /**
     * データを再読み込み（手動更新）
     */
    async refresh() {
        await this.fetchData(false); // 手動更新なので false
        UI.showAlert('データを更新しました', 'success');
    }

    /**
     * クリーンアップ処理
     */
    cleanup() {
        this.stopPolling();
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
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
    
    // Page Visibility APIを設定
    dashboardManager.setupVisibilityListener();
    
    // 自動更新ポーリングを開始
    dashboardManager.startPolling();
});

/**
 * ページアンロード時のクリーンアップ
 */
window.addEventListener('beforeunload', () => {
    dashboardManager.cleanup();
});

/**
 * データ更新関数（グローバル）
 * HTMLのonclick属性から呼び出される
 */
async function refreshDashboard() {
    await dashboardManager.refresh();
}
