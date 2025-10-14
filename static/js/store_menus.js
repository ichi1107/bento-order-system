// メニュー管理画面 JavaScript - store_menus.js// 店舗メニュー管理 - store_menus.js



// ===== グローバル変数 =====// ページ読み込み時の初期化

let currentPage = 1;document.addEventListener('DOMContentLoaded', async () => {

let perPage = 20;    // 認証チェック

let totalMenus = 0;    if (!Auth.requireRole('store')) return;

let currentFilter = null; // null=すべて, true=公開中, false=非公開

let menus = [];    // ヘッダー情報を表示

    await UI.initializeStoreHeader();

// ===== 初期化 =====

document.addEventListener('DOMContentLoaded', async () => {    // 共通UI初期化（ログアウトボタンなど）

    console.log('メニュー管理画面を初期化中...');    initializeCommonUI();

    

    // 認証チェック    // メニュー一覧を読み込み

    if (!checkAuth()) {    await loadMenus();

        console.warn('未認証のため、ログイン画面へリダイレクト');});

        window.location.href = '/login';

        return;/**

    } * メニュー一覧を読み込む

 */

    // 店舗ユーザーかチェックasync function loadMenus() {

    const user = getCurrentUser();    try {

    if (!user || user.role === 'customer') {        const menus = await ApiClient.get('/store/menus');

        console.error('店舗ユーザーではないため、アクセス拒否');        displayMenus(menus);

        showToast('アクセス権限がありません', 'error');    } catch (error) {

        setTimeout(() => {        console.error('メニューの読み込みに失敗:', error);

            window.location.href = '/login';        UI.showAlert('メニューの読み込みに失敗しました', 'error');

        }, 2000);    }

        return;}

    }

/**

    // イベントリスナー設定 * メニューを表示

    setupEventListeners(); */

function displayMenus(menus) {

    // メニューデータを取得して表示    const menusGrid = document.getElementById('menusGrid');

    await fetchMenus();    if (!menusGrid) return;

});

    if (menus.length === 0) {

// ===== イベントリスナー設定 =====        menusGrid.innerHTML = '<p class="empty-message">メニューが登録されていません</p>';

function setupEventListeners() {        return;

    // フィルタボタン    }

    document.querySelectorAll('.filter-btn').forEach(btn => {

        btn.addEventListener('click', (e) => {    menusGrid.innerHTML = menus.map(menu => `

            handleFilterChange(e.target.closest('.filter-btn'));        <div class="menu-card">

        });            <img src="${menu.image_url || '/static/images/no-image.png'}" alt="${menu.name}">

    });            <h3>${menu.name}</h3>

            <p class="price">${UI.formatPrice(menu.price)}</p>

    // 表示件数変更            <p class="description">${menu.description || ''}</p>

    const perPageSelect = document.getElementById('perPageSelect');            <div class="menu-actions">

    if (perPageSelect) {                <button onclick="editMenu(${menu.id})" class="btn-edit">編集</button>

        perPageSelect.addEventListener('change', (e) => {                <button onclick="deleteMenu(${menu.id})" class="btn-delete">削除</button>

            perPage = parseInt(e.target.value);            </div>

            currentPage = 1; // 1ページ目に戻る        </div>

            fetchMenus();    `).join('');

        });}

    }

// その他のメニュー管理関数（編集、削除など）は既存の実装を使用

    // メニュー追加ボタン（将来実装）
    const addMenuBtn = document.getElementById('addMenuBtn');
    if (addMenuBtn) {
        addMenuBtn.addEventListener('click', () => {
            showToast('メニュー追加機能は次のフェーズで実装予定です', 'warning');
        });
    }
}

// ===== フィルタ変更 =====
function handleFilterChange(btn) {
    // すべてのフィルタボタンからactiveクラスを削除
    document.querySelectorAll('.filter-btn').forEach(b => {
        b.classList.remove('active');
    });

    // クリックされたボタンにactiveクラスを追加
    btn.classList.add('active');

    // フィルタ値を取得
    const filterValue = btn.dataset.filter;
    
    if (filterValue === 'all') {
        currentFilter = null;
    } else {
        currentFilter = filterValue === 'true';
    }

    // ページを1に戻して再取得
    currentPage = 1;
    fetchMenus();
}

// ===== メニュー一覧取得 =====
async function fetchMenus() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorMessage = document.getElementById('errorMessage');
    const tableSection = document.querySelector('.table-section');

    try {
        // ローディング表示
        loadingIndicator.style.display = 'block';
        errorMessage.style.display = 'none';
        tableSection.style.opacity = '0.5';

        // APIパラメータ構築
        const params = new URLSearchParams({
            page: currentPage,
            per_page: perPage
        });

        // フィルタが設定されている場合
        if (currentFilter !== null) {
            params.append('is_available', currentFilter);
        }

        // API呼び出し
        console.log(`メニュー取得中: ${params.toString()}`);
        const data = await ApiClient.get(`/store/menus?${params}`);

        console.log('メニュー取得成功:', data);

        // データを保存
        menus = data.menus || [];
        totalMenus = data.total || 0;

        // テーブルを描画
        renderMenuTable();

        // ページネーションを描画
        renderPagination();

        // フィルタ情報を更新
        updateFilterInfo();

        // カウントを更新
        await updateFilterCounts();

    } catch (error) {
        console.error('メニュー取得エラー:', error);
        errorMessage.textContent = `エラー: ${error.message}`;
        errorMessage.style.display = 'block';
        
        // エラーの場合は空メッセージを表示
        const emptyMessage = document.getElementById('emptyMessage');
        const emptyMessageText = document.getElementById('emptyMessageText');
        emptyMessage.style.display = 'block';
        emptyMessageText.textContent = 'データの取得に失敗しました';
        
        document.querySelector('.table-container').style.display = 'none';
        document.getElementById('paginationSection').style.display = 'none';
    } finally {
        // ローディング非表示
        loadingIndicator.style.display = 'none';
        tableSection.style.opacity = '1';
    }
}

// ===== メニューテーブル描画 =====
function renderMenuTable() {
    const tableBody = document.getElementById('menuTableBody');
    const emptyMessage = document.getElementById('emptyMessage');
    const tableContainer = document.querySelector('.table-container');

    // データがない場合
    if (!menus || menus.length === 0) {
        tableContainer.style.display = 'none';
        emptyMessage.style.display = 'block';
        
        const emptyMessageText = document.getElementById('emptyMessageText');
        if (currentFilter !== null) {
            emptyMessageText.textContent = currentFilter ? 
                '公開中のメニューがありません' : 
                '非公開のメニューがありません';
        } else {
            emptyMessageText.textContent = 'メニューを追加してください';
        }
        return;
    }

    // データがある場合
    tableContainer.style.display = 'block';
    emptyMessage.style.display = 'none';

    // テーブル行を生成
    tableBody.innerHTML = menus.map(menu => {
        const statusBadge = menu.is_available ?
            '<span class="status-badge badge-available">🟢 公開中</span>' :
            '<span class="status-badge badge-unavailable">🔴 非公開</span>';

        const imageHtml = menu.image_url ?
            `<img src="${menu.image_url}" alt="${escapeHtml(menu.name)}" class="menu-image">` :
            '<div class="menu-no-image">🍱</div>';

        const description = menu.description ?
            `<div class="menu-description">${escapeHtml(menu.description)}</div>` :
            '';

        return `
            <tr>
                <td>${menu.id}</td>
                <td>${imageHtml}</td>
                <td>
                    <div class="menu-name">${escapeHtml(menu.name)}</div>
                    ${description}
                </td>
                <td>
                    <span class="menu-price">¥${menu.price.toLocaleString()}</span>
                </td>
                <td>${statusBadge}</td>
                <td>
                    <span class="menu-date">${formatDate(menu.created_at)}</span>
                </td>
                <td>
                    <span class="menu-date">${formatDate(menu.updated_at)}</span>
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-sm btn-edit" onclick="editMenu(${menu.id})" title="編集">
                            ✏️ 編集
                        </button>
                        <button class="btn-sm btn-delete" onclick="deleteMenu(${menu.id})" title="削除">
                            🗑️ 削除
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// ===== ページネーション描画 =====
function renderPagination() {
    const paginationSection = document.getElementById('paginationSection');
    const pagination = document.getElementById('pagination');
    const paginationInfo = document.getElementById('paginationInfo');

    // メニューがない場合は非表示
    if (totalMenus === 0) {
        paginationSection.style.display = 'none';
        return;
    }

    paginationSection.style.display = 'flex';

    // 総ページ数計算
    const totalPages = Math.ceil(totalMenus / perPage);

    // ページ情報テキスト
    const startIndex = (currentPage - 1) * perPage + 1;
    const endIndex = Math.min(currentPage * perPage, totalMenus);
    paginationInfo.textContent = `${startIndex}-${endIndex} / ${totalMenus}件`;

    // ページネーションボタンを生成
    let paginationHtml = '';

    // 前へボタン
    const prevDisabled = currentPage === 1 ? 'disabled' : '';
    paginationHtml += `
        <button class="page-btn" ${prevDisabled} onclick="goToPage(${currentPage - 1})">
            ‹ 前へ
        </button>
    `;

    // ページ番号ボタン
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    // 表示範囲を調整
    if (endPage - startPage + 1 < maxVisiblePages) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    // 最初のページ
    if (startPage > 1) {
        paginationHtml += `<button class="page-btn" onclick="goToPage(1)">1</button>`;
        if (startPage > 2) {
            paginationHtml += `<button class="page-btn" disabled>...</button>`;
        }
    }

    // ページ番号
    for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === currentPage ? 'active' : '';
        paginationHtml += `
            <button class="page-btn ${activeClass}" onclick="goToPage(${i})">
                ${i}
            </button>
        `;
    }

    // 最後のページ
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHtml += `<button class="page-btn" disabled>...</button>`;
        }
        paginationHtml += `<button class="page-btn" onclick="goToPage(${totalPages})">${totalPages}</button>`;
    }

    // 次へボタン
    const nextDisabled = currentPage === totalPages ? 'disabled' : '';
    paginationHtml += `
        <button class="page-btn" ${nextDisabled} onclick="goToPage(${currentPage + 1})">
            次へ ›
        </button>
    `;

    pagination.innerHTML = paginationHtml;
}

// ===== ページ移動 =====
function goToPage(page) {
    const totalPages = Math.ceil(totalMenus / perPage);
    
    if (page < 1 || page > totalPages) {
        return;
    }

    currentPage = page;
    fetchMenus();

    // ページトップにスクロール
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ===== フィルタ情報更新 =====
function updateFilterInfo() {
    const filterInfo = document.getElementById('filterInfo');
    
    if (currentFilter === null) {
        filterInfo.textContent = '全メニューを表示中';
    } else if (currentFilter === true) {
        filterInfo.textContent = '公開中のメニューを表示中';
    } else {
        filterInfo.textContent = '非公開のメニューを表示中';
    }
}

// ===== フィルタカウント更新 =====
async function updateFilterCounts() {
    try {
        // 全メニュー数を取得
        const allData = await ApiClient.get('/store/menus?page=1&per_page=1');
        document.getElementById('countAll').textContent = allData.total || 0;

        // 公開中メニュー数を取得
        const availableData = await ApiClient.get('/store/menus?page=1&per_page=1&is_available=true');
        document.getElementById('countAvailable').textContent = availableData.total || 0;

        // 非公開メニュー数を取得
        const unavailableData = await ApiClient.get('/store/menus?page=1&per_page=1&is_available=false');
        document.getElementById('countUnavailable').textContent = unavailableData.total || 0;

    } catch (error) {
        console.error('フィルタカウント取得エラー:', error);
    }
}

// ===== メニュー編集（将来実装） =====
function editMenu(menuId) {
    console.log('メニュー編集:', menuId);
    showToast('メニュー編集機能は次のフェーズで実装予定です', 'warning');
}

// ===== メニュー削除（将来実装） =====
function deleteMenu(menuId) {
    console.log('メニュー削除:', menuId);
    showToast('メニュー削除機能は次のフェーズで実装予定です', 'warning');
}

// ===== ユーティリティ関数 =====

// 日付フォーマット
function formatDate(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}/${month}/${day} ${hours}:${minutes}`;
}

// HTMLエスケープ
function escapeHtml(text) {
    if (!text) return '';
    
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    
    return text.replace(/[&<>"']/g, (m) => map[m]);
}

// Toast通知表示
function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toastContainer');
    
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    const titles = {
        success: '成功',
        error: 'エラー',
        warning: '警告',
        info: '情報'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-content">
            <div class="toast-title">${titles[type] || titles.info}</div>
            <div class="toast-message">${escapeHtml(message)}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;

    toastContainer.appendChild(toast);

    // 5秒後に自動削除
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// 認証チェック
function checkAuth() {
    const token = localStorage.getItem('authToken');
    return !!token;
}

// 現在のユーザー取得
function getCurrentUser() {
    const userJson = localStorage.getItem('currentUser');
    return userJson ? JSON.parse(userJson) : null;
}
