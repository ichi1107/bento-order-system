/* Auto-generated TypeScript types from Pydantic schemas */
/* DO NOT EDIT MANUALLY - Run generate-types script to update */

export interface StoreCreate {
  name: string;
  address: string;
  phone_number: string;
  email: string;
  opening_time: string;
  closing_time: string;
  description?: any;
  image_url?: any;
  is_active?: boolean;
}

export interface StoreUpdate {
  name?: any;
  address?: any;
  phone_number?: any;
  email?: any;
  opening_time?: any;
  closing_time?: any;
  description?: any;
  image_url?: any;
  is_active?: any;
}

export interface StoreResponse {
  name: string;
  address: string;
  phone_number: string;
  email: string;
  opening_time: string;
  closing_time: string;
  description?: any;
  image_url?: any;
  is_active?: boolean;
  id: number;
  created_at: string;
  updated_at: string;
}

export interface StoreListResponse {
  stores: any[];
  total: number;
}

export interface MenuCreate {
  name: string;
  price: number;
  description?: any;
  image_url?: any;
  is_available?: boolean;
  store_id: number;
}

export interface MenuUpdate {
  name?: any;
  price?: any;
  description?: any;
  image_url?: any;
  is_available?: any;
}

export interface MenuResponse {
  name: string;
  price: number;
  description?: any;
  image_url?: any;
  is_available?: boolean;
  id: number;
  store_id: number;
  created_at: string;
  updated_at: string;
  store?: any;
}

export interface OrderCreate {
  menu_id: number;
  quantity: number;
  delivery_time?: any;
  notes?: any;
  store_id: number;
}

export interface OrderResponse {
  id: number;
  user_id: number;
  menu_id: number;
  store_id: number;
  quantity: number;
  total_price: number;
  status: string;
  delivery_time: any;
  notes: any;
  ordered_at: string;
  updated_at: string;
  menu: any;
  store?: any;
  user?: any;
}

export interface UserResponse {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  store_id?: any;
  created_at: string;
  store?: any;
}

