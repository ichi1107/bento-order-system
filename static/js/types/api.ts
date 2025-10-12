/**
 * Auto-generated TypeScript type definitions
 * Generated from: /api/openapi.json
 * DO NOT EDIT MANUALLY
 */

export interface YesterdayComparison {
  /** Orders Change */
  orders_change: number;
  /** Orders Change Percent */
  orders_change_percent: number;
  /** Revenue Change */
  revenue_change: number;
  /** Revenue Change Percent */
  revenue_change_percent: number;
}

export interface PopularMenu {
  /** Menu Id */
  menu_id: number;
  /** Menu Name */
  menu_name: string;
  /** Order Count */
  order_count: number;
  /** Total Revenue */
  total_revenue: number;
}

export interface HourlyOrderData {
  /** Hour */
  hour: number;
  /** Order Count */
  order_count: number;
}

export interface OrderSummary {
  /** Total Orders */
  total_orders: number;
  /** Pending Orders */
  pending_orders: number;
  /** Confirmed Orders */
  confirmed_orders: number;
  /** Preparing Orders */
  preparing_orders: number;
  /** Ready Orders */
  ready_orders: number;
  /** Completed Orders */
  completed_orders: number;
  /** Cancelled Orders */
  cancelled_orders: number;
  /** Total Sales */
  total_sales: number;
  /** Today Revenue */
  today_revenue: number;
  /** Average Order Value */
  average_order_value: number;
  yesterday_comparison: YesterdayComparison;
  /** Popular Menus */
  popular_menus: PopularMenu[];
  /** Hourly Orders */
  hourly_orders: HourlyOrderData[];
}

export interface UserResponse {
  /** Id */
  id: number;
  /** Username */
  username: string;
  /** Email */
  email: string;
  /** Full Name */
  full_name: string;
  /** Role */
  role: string;
  /** Is Active */
  is_active: boolean;
  /** Store Id */
  store_id?: any;
  /** Created At */
  created_at: string;
  /** User Roles */
  user_roles?: UserRoleResponse[];
  store?: any;
}

export interface MenuResponse {
  /** Name */
  name: string;
  /** Price */
  price: number;
  /** Description */
  description?: any;
  /** Image Url */
  image_url?: any;
  /** Is Available */
  is_available?: boolean;
  /** Id */
  id: number;
  /** Store Id */
  store_id: number;
  /** Created At */
  created_at: string;
  /** Updated At */
  updated_at: string;
  store?: any;
}

export interface OrderResponse {
  /** Id */
  id: number;
  /** User Id */
  user_id: number;
  /** Menu Id */
  menu_id: number;
  /** Store Id */
  store_id: number;
  /** Quantity */
  quantity: number;
  /** Total Price */
  total_price: number;
  /** Status */
  status: string;
  /** Delivery Time */
  delivery_time: any;
  /** Notes */
  notes: any;
  /** Ordered At */
  ordered_at: string;
  /** Updated At */
  updated_at: string;
  menu: MenuResponse;
  store?: any;
  user?: any;
}

export interface SuccessResponse {
  /** Success */
  success?: boolean;
  /** Message */
  message: string;
}
