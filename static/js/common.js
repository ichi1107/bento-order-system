// 共通JavaScript - common.js

// APIクライアント設定
const API_BASE_URL = '/api';
let authToken = localStorage.getItem('authToken');
let currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');

// API呼び出し用のヘルパー関数
class ApiClient {
    static async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // 認証トークンがある場合は追加
        if (authToken) {
            config.headers['Authorization'] = `Bearer ${authToken}`;
        }

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    static async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url);
    }

    static async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    static async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }
}

// 認証関連のヘルパー関数
class Auth {
    static login(token, user) {
        authToken = token;
        currentUser = user;
        localStorage.setItem('authToken', token);
        localStorage.setItem('currentUser', JSON.stringify(user));
    }

    static logout() {
        authToken = null;
        currentUser = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        window.location.href = '/login';
    }

    static isLoggedIn() {
        return !!authToken && !!currentUser;
    }

    static requireAuth() {
        if (!this.isLoggedIn()) {
            window.location.href = '/login';
            return false;
        }
        return true;
    }

    static requireRole(role) {
        if (!this.requireAuth()) return false;
        
        if (currentUser.role !== role) {
            alert('アクセス権限がありません');
            this.logout();
            return false;
        }
        return true;
    }
}

// UI関連のヘルパー関数
class UI {
    static showAlert(message, type = 'info', duration = 5000) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.textContent = message;
        
        // ページの先頭に挿入
        const container = document.querySelector('.container') || document.body;
        container.insertBefore(alertDiv, container.firstChild);
        
        // 自動で消去
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, duration);
    }

    static showLoading(element) {
        const originalContent = element.innerHTML;
        element.innerHTML = '<span class="loading"></span> 処理中...';
        element.disabled = true;
        
        return () => {
            element.innerHTML = originalContent;
            element.disabled = false;
        };
    }

    /**
     * ヘッダーのナビゲーションリンクを初期化
     * customerロールの場合のみ注文履歴リンクを表示
     */
    static initializeHeader() {
        if (!currentUser) return;

        // お客様の場合、注文履歴リンクを表示
        if (currentUser.role === 'customer') {
            const navLinks = document.querySelector('.nav-links');
            if (navLinks) {
                // 既に注文履歴リンクが存在するか確認
                const ordersLink = navLinks.querySelector('a[href="/customer/orders"]');
                if (!ordersLink) {
                    // 注文履歴リンクを追加
                    const li = document.createElement('li');
                    const a = document.createElement('a');
                    a.href = '/customer/orders';
                    a.textContent = '注文履歴';
                    
                    // 現在のページがordersの場合はactiveクラスを追加
                    if (window.location.pathname === '/customer/orders') {
                        a.classList.add('active');
                    }
                    
                    li.appendChild(a);
                    navLinks.appendChild(li);
                }
            }
        }

        // ユーザー情報の表示
        const userInfoElement = document.getElementById('userInfo');
        if (userInfoElement) {
            const roleText = currentUser.role === 'customer' ? 'お客様' : '店舗';
            userInfoElement.textContent = `${currentUser.full_name}さん`;
        }
    }

    static formatPrice(price) {
        return new Intl.NumberFormat('ja-JP', {
            style: 'currency',
            currency: 'JPY'
        }).format(price);
    }

    static formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ja-JP', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    static formatTime(timeString) {
        if (!timeString) return '';
        return timeString.slice(0, 5); // HH:MM形式
    }

    static getStatusText(status) {
        const statusMap = {
            'pending': '注文受付',
            'confirmed': '注文確認済み',
            'preparing': '調理中',
            'ready': '受取準備完了',
            'completed': '受取完了',
            'cancelled': 'キャンセル'
        };
        return statusMap[status] || status;
    }

    static getStatusClass(status) {
        const statusClasses = {
            'pending': 'warning',
            'confirmed': 'info',
            'preparing': 'primary',
            'ready': 'success',
            'completed': 'secondary',
            'cancelled': 'danger'
        };
        return statusClasses[status] || 'secondary';
    }

    static createStatusBadge(status) {
        const span = document.createElement('span');
        span.className = `badge bg-${this.getStatusClass(status)}`;
        span.textContent = this.getStatusText(status);
        return span;
    }
}

// モーダル関連のヘルパー関数
class Modal {
    static show(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }
    }

    static hide(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    }

    static setupCloseHandlers(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        // 閉じるボタンのクリック
        const closeBtn = modal.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hide(modalId));
        }

        // モーダル外クリック
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.hide(modalId);
            }
        });

        // ESCキー
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.style.display === 'block') {
                this.hide(modalId);
            }
        });
    }
}

// ページネーション関連
class Pagination {
    static create(container, currentPage, totalPages, onPageClick) {
        container.innerHTML = '';
        
        if (totalPages <= 1) return;

        const nav = document.createElement('nav');
        nav.innerHTML = `
            <ul class="pagination justify-content-center">
                ${this.generatePageItems(currentPage, totalPages)}
            </ul>
        `;
        
        container.appendChild(nav);
        
        // イベントリスナーを設定
        nav.addEventListener('click', (e) => {
            e.preventDefault();
            if (e.target.classList.contains('page-link')) {
                const page = parseInt(e.target.dataset.page);
                if (page && page !== currentPage) {
                    onPageClick(page);
                }
            }
        });
    }

    static generatePageItems(current, total) {
        let items = '';
        
        // 前のページ
        if (current > 1) {
            items += `<li class="page-item">
                <a class="page-link" href="#" data-page="${current - 1}">前</a>
            </li>`;
        }
        
        // ページ番号
        const start = Math.max(1, current - 2);
        const end = Math.min(total, current + 2);
        
        for (let i = start; i <= end; i++) {
            const active = i === current ? 'active' : '';
            items += `<li class="page-item ${active}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>`;
        }
        
        // 次のページ
        if (current < total) {
            items += `<li class="page-item">
                <a class="page-link" href="#" data-page="${current + 1}">次</a>
            </li>`;
        }
        
        return items;
    }
}

// フォームバリデーション
class Validator {
    static validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    static validateRequired(value) {
        return value && value.trim().length > 0;
    }

    static validateMinLength(value, minLength) {
        return value && value.length >= minLength;
    }

    static validateNumber(value, min = null, max = null) {
        const num = parseFloat(value);
        if (isNaN(num)) return false;
        if (min !== null && num < min) return false;
        if (max !== null && num > max) return false;
        return true;
    }
}

// 共通イベントリスナーの設定
document.addEventListener('DOMContentLoaded', function() {
    // ヘッダーの初期化
    UI.initializeHeader();

    // ログアウトボタンの処理
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (confirm('ログアウトしますか？')) {
                Auth.logout();
            }
        });
    }

    // 現在のページに応じたナビゲーションのアクティブ状態
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-links a');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});

// エラーハンドリング用のグローバル関数
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    UI.showAlert('予期しないエラーが発生しました', 'danger');
});

// APIエラーハンドリング
window.handleApiError = function(error) {
    console.error('API Error:', error);
    
    if (error.message.includes('401') || error.message.includes('Unauthorized')) {
        UI.showAlert('認証が必要です。再度ログインしてください。', 'warning');
        Auth.logout();
    } else if (error.message.includes('403') || error.message.includes('Forbidden')) {
        UI.showAlert('この操作を実行する権限がありません。', 'danger');
    } else {
        UI.showAlert(`エラー: ${error.message}`, 'danger');
    }
};

// デバッグ用
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    window.debugAuth = () => {
        console.log('Current user:', currentUser);
        console.log('Auth token:', authToken);
    };
}

// 共通UI初期化フラグ
let commonUIInitialized = false;

// ログアウトハンドラー関数
function handleLogout(e) {
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();
    
    // ウィンドウにフォーカスを当ててからダイアログを表示
    window.focus();
    
    if (confirm('ログアウトしますか?')) {
        Auth.logout();
    }
}

// 共通UI初期化関数
function initializeCommonUI() {
    if (commonUIInitialized) {
        return;
    }
    
    // ログアウトボタンの初期化
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        // 既存のイベントリスナーを削除（クローンして置き換える）
        const newLogoutBtn = logoutBtn.cloneNode(true);
        logoutBtn.parentNode.replaceChild(newLogoutBtn, logoutBtn);
        
        // 新しいボタンにイベントリスナーを追加
        newLogoutBtn.addEventListener('click', handleLogout, true);
        
        commonUIInitialized = true;
    }
}
// �J�[�g�Ǘ��N���X
class Cart {
    constructor() {
        this.items = this.loadFromStorage();
    }

    // LocalStorage����J�[�g�f�[�^��ǂݍ���
    loadFromStorage() {
        const cartData = localStorage.getItem('cart');
        return cartData ? JSON.parse(cartData) : [];
    }

    // LocalStorage�ɃJ�[�g�f�[�^��ۑ�
    saveToStorage() {
        localStorage.setItem('cart', JSON.stringify(this.items));
    }

    // �J�[�g�ɃA�C�e����ǉ�
    addItem(menu, quantity = 1) {
        const existingItem = this.items.find(item => item.id === menu.id);
        
        if (existingItem) {
            existingItem.quantity += quantity;
        } else {
            this.items.push({
                id: menu.id,
                name: menu.name,
                price: menu.price,
                image_url: menu.image_url,
                quantity: quantity
            });
        }
        
        this.saveToStorage();
        this.updateCartCount();
    }

    // �J�[�g���̃A�C�e���̐��ʂ��X�V
    updateQuantity(menuId, quantity) {
        const item = this.items.find(item => item.id === menuId);
        
        if (item) {
            if (quantity <= 0) {
                this.removeItem(menuId);
            } else {
                item.quantity = quantity;
                this.saveToStorage();
                this.updateCartCount();
            }
        }
    }

    // �J�[�g����A�C�e�����폜
    removeItem(menuId) {
        this.items = this.items.filter(item => item.id !== menuId);
        this.saveToStorage();
        this.updateCartCount();
    }

    // �J�[�g���N���A
    clear() {
        this.items = [];
        this.saveToStorage();
        this.updateCartCount();
    }

    // カート内の全アイテムを取得
    getItems() {
        return this.items;
    }

    // カート内のアイテム数を取得
    getItemCount() {
        return this.items.reduce((total, item) => total + item.quantity, 0);
    }

    // カートの合計金額を取得
    getTotalPrice() {
        return this.items.reduce((total, item) => total + (item.price * item.quantity), 0);
    }

    // カートアイコンのバッジを更新
    updateCartCount() {
        const badge = document.getElementById('cartCount');
        const count = this.getItemCount();
        
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        }
    }
}

// グローバルカートインスタンス
const cart = new Cart();

// ===== 認証関連の共通関数 =====

// 現在のユーザー情報を取得
async function getCurrentUser() {
    const token = localStorage.getItem('accessToken');
    if (!token) {
        return null;
    }

    try {
        const response = await fetch('/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                // トークンが無効な場合はクリア
                localStorage.removeItem('accessToken');
                localStorage.removeItem('currentUser');
                return null;
            }
            throw new Error('ユーザー情報の取得に失敗しました');
        }

        const user = await response.json();
        localStorage.setItem('currentUser', JSON.stringify(user));
        return user;
    } catch (error) {
        console.error('getCurrentUser error:', error);
        return null;
    }
}

// ログアウト処理
function logout() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('currentUser');
    localStorage.removeItem('cart');
    window.location.href = '/login';
}
