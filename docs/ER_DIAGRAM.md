# データベーススキーマ - ER図

```mermaid
erDiagram
    STORES ||--o{ USERS : "employs"
    STORES ||--o{ MENUS : "offers"
    STORES ||--o{ ORDERS : "receives"
    USERS ||--o{ ORDERS : "places"
    USERS ||--o{ USER_ROLES : "has"
    ROLES ||--o{ USER_ROLES : "assigned_to"
    MENUS ||--o{ ORDERS : "ordered_in"

    STORES {
        int id PK
        string name
        string address
        string phone_number
        string email
        time opening_time
        time closing_time
        text description
        string image_url
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    USERS {
        int id PK
        string username UK
        string email UK
        string hashed_password
        string role
        string full_name
        boolean is_active
        int store_id FK
        timestamp created_at
    }

    ROLES {
        int id PK
        string name UK
        text description
        timestamp created_at
    }

    USER_ROLES {
        int id PK
        int user_id FK
        int role_id FK
        timestamp assigned_at
    }

    MENUS {
        int id PK
        string name
        int price
        text description
        string image_url
        boolean is_available
        int store_id FK
        timestamp created_at
        timestamp updated_at
    }

    ORDERS {
        int id PK
        int user_id FK
        int menu_id FK
        int store_id FK
        int quantity
        int total_price
        string status
        time delivery_time
        text notes
        timestamp ordered_at
        timestamp updated_at
    }

    PASSWORD_RESET_TOKENS {
        int id PK
        string token UK
        string email
        timestamp expires_at
        timestamp used_at
        timestamp created_at
    }
```

## テーブル説明

### STORES (店舗テーブル)
- 各店舗の基本情報を管理
- メニュー、注文、ユーザー(店舗スタッフ)と紐付け
- マルチテナント対応の中核テーブル

### USERS (ユーザーテーブル)
- お客様と店舗スタッフの両方を管理
- `role`: 'customer' または 'store'
- `store_id`: 店舗スタッフの場合のみ設定

### ROLES (役割テーブル)
- 店舗スタッフの職位管理: owner, manager, staff

### USER_ROLES (ユーザー役割紐付けテーブル)
- ユーザーと役割のN対N関係を管理

### MENUS (メニューテーブル)
- 各店舗が提供するメニュー
- `store_id`: 所属店舗 (必須)

### ORDERS (注文テーブル)
- お客様の注文情報
- `store_id`: 注文先店舗 (必須)
- `user_id`: 注文者
- `menu_id`: 注文メニュー

### PASSWORD_RESET_TOKENS (パスワードリセットトークンテーブル)
- パスワードリセット用のトークン管理
- 有効期限と使用状態を追跡

## 外部キー制約

| 子テーブル | 外部キー | 参照先 | ON DELETE |
|-----------|---------|--------|-----------|
| users | store_id | stores.id | SET NULL |
| user_roles | user_id | users.id | CASCADE |
| user_roles | role_id | roles.id | CASCADE |
| menus | store_id | stores.id | CASCADE |
| orders | user_id | users.id | - |
| orders | menu_id | menus.id | - |
| orders | store_id | stores.id | CASCADE |

## マルチテナント対応

- **店舗分離**: `store_id`により、メニューと注文を店舗ごとに完全分離
- **アクセス制御**: 各店舗スタッフは自店舗のデータのみアクセス可能
- **お客様**: 全店舗のメニューを閲覧・注文可能（`users.store_id`はNULL）
