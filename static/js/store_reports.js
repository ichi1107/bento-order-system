// 店舗レポート - store_reports.js

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', async () => {
    // 認証チェック
    if (!Auth.requireRole('store')) return;

    // ヘッダー情報を表示
    await UI.initializeStoreHeader();

    // 共通UI初期化（ログアウトボタンなど）
    initializeCommonUI();

    // レポートデータを読み込み
    await loadReportData();
});

/**
 * レポートデータを読み込む
 */
async function loadReportData() {
    try {
        // デフォルトは今月のレポート
        const today = new Date();
        const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
        const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        
        const params = {
            start_date: firstDay.toISOString().split('T')[0],
            end_date: lastDay.toISOString().split('T')[0]
        };

        const reportData = await ApiClient.get('/store/reports/sales', params);
        displayReportData(reportData);
    } catch (error) {
        console.error('レポートデータの読み込みに失敗:', error);
        UI.showAlert('レポートデータの読み込みに失敗しました', 'error');
    }
}

/**
 * レポートデータを表示
 */
function displayReportData(data) {
    // 合計売上を表示
    const totalSalesElement = document.getElementById('totalSales');
    if (totalSalesElement) {
        totalSalesElement.textContent = UI.formatPrice(data.total_sales || 0);
    }

    // 日別売上グラフなどを表示
    console.log('Report data:', data);
}
