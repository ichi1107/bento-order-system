// 店舗注文管理 - store_orders.js

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', async () => {
    // 認証チェック
    if (!Auth.requireRole('store')) return;

    // ヘッダー情報を表示
    await UI.initializeStoreHeader();

    // 共通UI初期化（ログアウトボタンなど）
    initializeCommonUI();

    // 注文一覧を読み込み
    await loadOrders();
});

/**
 * 注文一覧を読み込む
 */
async function loadOrders() {
    try {
        const orders = await ApiClient.get('/store/orders');
        displayOrders(orders);
    } catch (error) {
        console.error('注文の読み込みに失敗:', error);
        UI.showAlert('注文の読み込みに失敗しました', 'error');
    }
}

/**
 * 注文を表示
 */
function displayOrders(orders) {
    const ordersTable = document.getElementById('ordersTable');
    if (!ordersTable) return;

    if (orders.length === 0) {
        ordersTable.innerHTML = '<tr><td colspan="6" class="empty-message">注文がありません</td></tr>';
        return;
    }

    ordersTable.innerHTML = orders.map(order => `
        <tr>
            <td>${order.id}</td>
            <td>${order.menu ? order.menu.name : '-'}</td>
            <td>${order.quantity}</td>
            <td>${UI.formatPrice(order.total_price)}</td>
            <td><span class="status-badge status-${order.status}">${UI.getStatusText(order.status)}</span></td>
            <td>
                <button onclick="viewOrderDetail(${order.id})" class="btn-view">詳細</button>
                <button onclick="updateOrderStatus(${order.id})" class="btn-update">更新</button>
            </td>
        </tr>
    `).join('');
}

// その他の注文管理関数（詳細表示、ステータス更新など）は既存の実装を使用
