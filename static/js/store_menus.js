// 店舗メニュー管理 - store_menus.js

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', async () => {
    // 認証チェック
    if (!Auth.requireRole('store')) return;

    // ヘッダー情報を表示
    await UI.initializeStoreHeader();

    // メニュー一覧を読み込み
    await loadMenus();
});

/**
 * メニュー一覧を読み込む
 */
async function loadMenus() {
    try {
        const menus = await ApiClient.get('/store/menus');
        displayMenus(menus);
    } catch (error) {
        console.error('メニューの読み込みに失敗:', error);
        UI.showAlert('メニューの読み込みに失敗しました', 'error');
    }
}

/**
 * メニューを表示
 */
function displayMenus(menus) {
    const menusGrid = document.getElementById('menusGrid');
    if (!menusGrid) return;

    if (menus.length === 0) {
        menusGrid.innerHTML = '<p class="empty-message">メニューが登録されていません</p>';
        return;
    }

    menusGrid.innerHTML = menus.map(menu => `
        <div class="menu-card">
            <img src="${menu.image_url || '/static/images/no-image.png'}" alt="${menu.name}">
            <h3>${menu.name}</h3>
            <p class="price">${UI.formatPrice(menu.price)}</p>
            <p class="description">${menu.description || ''}</p>
            <div class="menu-actions">
                <button onclick="editMenu(${menu.id})" class="btn-edit">編集</button>
                <button onclick="deleteMenu(${menu.id})" class="btn-delete">削除</button>
            </div>
        </div>
    `).join('');
}

// その他のメニュー管理関数（編集、削除など）は既存の実装を使用
