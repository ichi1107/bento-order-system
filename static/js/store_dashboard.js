// 店舗ダッシュボード - store_dashboard.js

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', async () => {
    // 認証チェック
    if (!Auth.requireRole('store')) return;

    // ヘッダー情報を表示
    await UI.initializeStoreHeader();

    // 共通UI初期化（ログアウトボタンなど）
    initializeCommonUI();

    // ダッシュボードデータを読み込み
    await loadDashboardData();
});

/**
 * ダッシュボードデータを読み込む
 */
async function loadDashboardData() {
    try {
        const data = await ApiClient.get('/store/dashboard');
        
        // 本日の注文数を表示
        const todayOrdersElement = document.getElementById('todayOrders');
        if (todayOrdersElement) {
            todayOrdersElement.textContent = data.today_orders || 0;
        }

        // 本日の売上を表示
        const todayRevenueElement = document.getElementById('todayRevenue');
        if (todayRevenueElement) {
            todayRevenueElement.textContent = UI.formatPrice(data.today_revenue || 0);
        }

        // その他のダッシュボードデータがあれば表示
        console.log('Dashboard data loaded:', data);
    } catch (error) {
        console.error('ダッシュボードデータの読み込みに失敗:', error);
        UI.showAlert('ダッシュボードデータの読み込みに失敗しました', 'error');
    }
}

/**
 * ダッシュボードデータを更新
 */
async function refreshDashboard() {
    await loadDashboardData();
    UI.showAlert('データを更新しました', 'success');
}
