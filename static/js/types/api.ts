// TypeScript型定義 - APIレスポンス用
// ⚠️ このファイルは自動生成されます。直接編集しないでください。
// schemas.pyを編集後、scripts/generate-types.shを実行してください。

// ===== 共通型定義 =====

export interface SuccessResponse {
  success: boolean;
  message: string;
}

export interface ErrorResponse {
  success: boolean;
  message: string;
  detail?: string;
}

// ===== 認証関連 =====

export interface UserCreate {
  username: string;
  email: string;
  password: string;
  full_name: string;
  role: 'customer' | 'store';
}

export interface UserLogin {
  username: string;
  password: string;
}

export interface UserResponse {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string; // ISO datetime string
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

// ===== メニュー関連 =====

export interface MenuBase {
  name: string;
  price: number;
  description?: string;
  image_url?: string;
  is_available: boolean;
}

export interface MenuCreate extends MenuBase {}

export interface MenuUpdate {
  name?: string;
  price?: number;
  description?: string;
  image_url?: string;
  is_available?: boolean;
}

export interface MenuResponse extends MenuBase {
  id: number;
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface MenuListResponse {
  menus: MenuResponse[];
  total: number;
}

// ===== 注文関連 =====

export interface OrderBase {
  menu_id: number;
  quantity: number;
  delivery_time?: string; // HH:MM:SS format
  notes?: string;
}

export interface OrderCreate extends OrderBase {}

export interface OrderStatusUpdate {
  status: 'pending' | 'confirmed' | 'preparing' | 'ready' | 'completed' | 'cancelled';
}

export interface OrderResponse {
  id: number;
  user_id: number;
  menu_id: number;
  quantity: number;
  total_price: number;
  status: string;
  delivery_time?: string; // HH:MM:SS format
  notes?: string;
  ordered_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
  menu: MenuResponse;
  user?: UserResponse;
}

export interface OrderHistoryItem {
  id: number;
  quantity: number;
  total_price: number;
  status: string;
  delivery_time?: string; // HH:MM:SS format
  notes?: string;
  ordered_at: string; // ISO datetime string
  menu_name: string;
  menu_image_url?: string;
}

export interface OrderHistoryResponse {
  orders: OrderHistoryItem[];
  total: number;
}

export interface OrderListResponse {
  orders: OrderResponse[];
  total: number;
}

export interface OrderSummary {
  total_orders: number;
  pending_orders: number;
  confirmed_orders: number;
  preparing_orders: number;
  ready_orders: number;
  completed_orders: number;
  cancelled_orders: number;
  total_sales: number;
}

// ===== レポート関連 =====

export interface DailySalesReport {
  date: string; // YYYY-MM-DD format
  total_orders: number;
  total_sales: number;
  popular_menu?: string;
}

export interface MenuSalesReport {
  menu_id: number;
  menu_name: string;
  total_quantity: number;
  total_sales: number;
}

export interface SalesReportResponse {
  period: string; // "daily", "weekly", "monthly"
  start_date: string;
  end_date: string;
  daily_reports: DailySalesReport[];
  menu_reports: MenuSalesReport[];
  total_sales: number;
  total_orders: number;
}

// ===== 検索・フィルタ関連 =====

export interface OrderFilter {
  status?: string;
  user_id?: number;
  menu_id?: number;
  start_date?: string; // YYYY-MM-DD
  end_date?: string; // YYYY-MM-DD
  page: number;
  per_page: number;
}

export interface MenuFilter {
  is_available?: boolean;
  price_min?: number;
  price_max?: number;
  search?: string;
  page: number;
  per_page: number;
}

// ===== ページネーション =====

export interface PaginationInfo {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface PaginatedResponse {
  pagination: PaginationInfo;
}