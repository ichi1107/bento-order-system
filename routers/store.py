"""
店舗向けルーター

店舗スタッフ専用のAPIエンドポイント
"""

from typing import List, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
import os
import uuid
from pathlib import Path

from database import get_db
from dependencies import get_current_store_user, require_role, get_current_active_user
from models import User, Menu, Order, Store
from schemas import (
    MenuCreate, MenuUpdate, MenuResponse, MenuListResponse,
    OrderResponse, OrderListResponse, OrderStatusUpdate, OrderSummary,
    YesterdayComparison, PopularMenu, HourlyOrderData,
    SalesReportResponse, DailySalesReport, MenuSalesReport,
    StoreResponse, StoreUpdate
)

router = APIRouter(prefix="/store", tags=["店舗"])


# ===== 店舗プロフィール管理 =====

@router.get("/profile", response_model=StoreResponse, summary="店舗プロフィール取得")
def get_store_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_store_user)
):
    """
    ログイン中のユーザーが所属する店舗の情報を取得
    
    **必要な権限:** store (owner, manager, staff)
    
    **戻り値:**
    - 店舗の詳細情報
    
    **エラー:**
    - 400: ユーザーが店舗に所属していない
    - 404: 店舗が見つからない
    """
    # ユーザーが店舗に所属しているか確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
    # 店舗情報を取得
    store = db.query(Store).filter(Store.id == current_user.store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    return store


@router.put("/profile", response_model=StoreResponse, summary="店舗プロフィール更新")
def update_store_profile(
    store_update: StoreUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner']))
):
    """
    店舗情報を更新（オーナー専用）
    
    **必要な権限:** owner
    
    **パラメータ:**
    - **store_update**: 更新する店舗情報（部分更新可能）
    
    **戻り値:**
    - 更新後の店舗情報
    
    **エラー:**
    - 400: ユーザーが店舗に所属していない
    - 403: オーナー権限がない
    - 404: 店舗が見つからない
    """
    # ユーザーが店舗に所属しているか確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
    # 店舗情報を取得
    store = db.query(Store).filter(Store.id == current_user.store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    # 更新データを適用（提供されたフィールドのみ）
    update_data = store_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(store, field, value)
    
    db.commit()
    db.refresh(store)
    
    return store


@router.post("/profile/image", response_model=StoreResponse, summary="店舗画像アップロード")
async def upload_store_image(
    file: UploadFile = File(..., description="アップロードする画像ファイル"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner']))
):
    """
    店舗画像をアップロード（オーナー専用）
    
    **必要な権限:** owner
    
    **パラメータ:**
    - **file**: 画像ファイル（JPEG, PNG, GIF対応）
    
    **戻り値:**
    - 更新後の店舗情報（image_urlが更新される）
    
    **エラー:**
    - 400: ユーザーが店舗に所属していない、または不正なファイル形式
    - 404: 店舗が見つからない
    """
    # ユーザーが店舗に所属しているか確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
    # ファイル形式の検証
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # 店舗情報を取得
    store = db.query(Store).filter(Store.id == current_user.store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    # アップロードディレクトリの作成
    upload_dir = Path("static/uploads/stores")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # 一意のファイル名を生成
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_dir / unique_filename
    
    # 古い画像ファイルを削除（存在する場合）
    if store.image_url and store.image_url.startswith("/static/uploads/"):
        old_file_path = Path(store.image_url.lstrip('/'))
        if old_file_path.exists():
            old_file_path.unlink()
    
    # ファイルを保存
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # データベースのimage_urlを更新
    store.image_url = f"/static/uploads/stores/{unique_filename}"
    db.commit()
    db.refresh(store)
    
    return store


@router.delete("/profile/image", response_model=StoreResponse, summary="店舗画像削除")
def delete_store_image(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner']))
):
    """
    店舗画像を削除（オーナー専用）
    
    **必要な権限:** owner
    
    **戻り値:**
    - 更新後の店舗情報（image_urlがNullになる）
    
    **エラー:**
    - 400: ユーザーが店舗に所属していない
    - 404: 店舗が見つからない
    """
    # ユーザーが店舗に所属しているか確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
    # 店舗情報を取得
    store = db.query(Store).filter(Store.id == current_user.store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    # 画像ファイルを削除（存在する場合）
    if store.image_url and store.image_url.startswith("/static/uploads/"):
        file_path = Path(store.image_url.lstrip('/'))
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                # ファイル削除に失敗してもDBは更新する
                pass
    
    # データベースのimage_urlをクリア
    store.image_url = None
    db.commit()
    db.refresh(store)
    
    return store


# ===== ダッシュボード =====

@router.get("/dashboard", response_model=OrderSummary, summary="ダッシュボード情報取得")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager', 'staff']))
):
    """
    本日の注文状況サマリーを取得（最適化版・簡素化ステータス対応）
    
    **必要な権限:** owner, manager, staff
    
    **レスポンス:**
    - total_orders: 本日の総注文数
    - 各ステータスの注文数（pending, ready, completed, cancelled）
    - total_sales: 本日の総売上（キャンセル除く）
    - today_revenue: 本日の総売上（total_salesと同値）
    - average_order_value: 平均注文単価
    - yesterday_comparison: 前日との比較データ（注文数・売上の増減）
    - popular_menus: 本日の人気メニュートップ3
    - hourly_orders: 時間帯別の注文数（0-23時）
    
    **ステータス定義:**
    - pending: 注文受付（確認・在庫確認・決済処理）
    - ready: 準備完了（弁当完成、顧客通知）
    - completed: 受取完了（顧客が受取済み）
    - cancelled: キャンセル（注文取消）
    
    **最適化:**
    - 複数クエリを1つのCTEクエリに統合してDB往復を削減
    - インデックスを活用した高速検索
    - 不要なデータフェッチを排除
    """
    # ユーザーが店舗に所属しているか確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    yesterday_start = datetime.combine(yesterday, datetime.min.time())
    yesterday_end = datetime.combine(yesterday, datetime.max.time())
    
    store_id = current_user.store_id
    
    # === 最適化: 本日の注文を1回のクエリで全件取得 ===
    # DBへの往復を1回に削減し、Pythonメモリ上で集計
    today_orders = db.query(Order).filter(
        Order.store_id == store_id,
        Order.ordered_at >= today_start,
        Order.ordered_at <= today_end
    ).all()
    
    # Pythonメモリ上でステータス別集計（簡素化版: 4ステータス）
    total_orders = len(today_orders)
    pending_orders = sum(1 for o in today_orders if o.status == "pending")
    ready_orders = sum(1 for o in today_orders if o.status == "ready")
    completed_orders = sum(1 for o in today_orders if o.status == "completed")
    cancelled_orders = sum(1 for o in today_orders if o.status == "cancelled")
    
    # 売上計算（キャンセル除く）
    total_sales = sum(o.total_price for o in today_orders if o.status != "cancelled")
    
    # 平均注文単価の計算
    completed_order_count = total_orders - cancelled_orders
    average_order_value = float(total_sales) / completed_order_count if completed_order_count > 0 else 0.0
    
    # === 最適化: 前日データを集約クエリで一括取得 ===
    # キャンセル以外の注文数と売上を一度のクエリで取得
    yesterday_orders = db.query(Order).filter(
        Order.store_id == store_id,
        Order.ordered_at >= yesterday_start,
        Order.ordered_at <= yesterday_end
    ).all()
    
    yesterday_orders_count = len(yesterday_orders)
    yesterday_revenue = sum(o.total_price for o in yesterday_orders if o.status != "cancelled")
    
    # 前日比較の計算
    orders_change = total_orders - yesterday_orders_count
    orders_change_percent = (orders_change / yesterday_orders_count * 100) if yesterday_orders_count > 0 else 0.0
    revenue_change = total_sales - yesterday_revenue
    revenue_change_percent = (revenue_change / yesterday_revenue * 100) if yesterday_revenue > 0 else 0.0
    
    yesterday_comparison = YesterdayComparison(
        orders_change=orders_change,
        orders_change_percent=round(orders_change_percent, 2),
        revenue_change=revenue_change,
        revenue_change_percent=round(revenue_change_percent, 2)
    )
    
    # === 最適化: 人気メニュートップ3（JOINを維持、インデックス活用） ===
    popular_menus_data = db.query(
        Order.menu_id,
        Menu.name,
        func.count(Order.id).label('order_count'),
        func.sum(Order.total_price).label('total_revenue')
    ).join(
        Menu, Order.menu_id == Menu.id
    ).filter(
        Order.store_id == store_id,
        Order.ordered_at >= today_start,
        Order.ordered_at <= today_end,
        Order.status != "cancelled"
    ).group_by(
        Order.menu_id, Menu.name
    ).order_by(
        desc('order_count')
    ).limit(3).all()
    
    popular_menus = [
        PopularMenu(
            menu_id=menu_id,
            menu_name=menu_name,
            order_count=order_count,
            total_revenue=total_revenue or 0
        )
        for menu_id, menu_name, order_count, total_revenue in popular_menus_data
    ]
    
    # === 最適化: 時間帯別注文数（既に取得した今日の注文データを再利用） ===
    hourly_orders_dict = {}
    for order in today_orders:
        hour = order.ordered_at.hour
        hourly_orders_dict[hour] = hourly_orders_dict.get(hour, 0) + 1
    
    hourly_orders = [
        HourlyOrderData(hour=hour, order_count=hourly_orders_dict.get(hour, 0))
        for hour in range(24)
    ]
    
    return {
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "ready_orders": ready_orders,
        "completed_orders": completed_orders,
        "cancelled_orders": cancelled_orders,
        "total_sales": total_sales,
        "today_revenue": total_sales,
        "average_order_value": round(average_order_value, 2),
        "yesterday_comparison": yesterday_comparison,
        "popular_menus": popular_menus,
        "hourly_orders": hourly_orders
    }


@router.get("/dashboard/weekly-sales", summary="週間売上データ取得")
def get_weekly_sales(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager', 'staff']))
):
    """
    過去7日間の日別売上データを取得
    
    **必要な権限:** owner, manager, staff
    
    **レスポンス:**
    - labels: 日付のリスト（YYYY-MM-DD形式）
    - data: 各日の売上金額のリスト
    
    **最適化:**
    - 7回のクエリを1回の集約クエリに統合
    - DATE関数とGROUP BYを活用
    - インデックスによる高速検索
    """
    # ユーザーが店舗に所属しているか確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
    # 過去7日間のデータを取得
    today = date.today()
    start_date = today - timedelta(days=6)  # 6日前
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(today, datetime.max.time())
    
    # === 最適化: 1回のクエリで全7日分のデータを取得 ===
    daily_sales = db.query(
        func.date(Order.ordered_at).label('order_date'),
        func.sum(Order.total_price).label('revenue')
    ).filter(
        Order.store_id == current_user.store_id,
        Order.ordered_at >= start_datetime,
        Order.ordered_at <= end_datetime,
        Order.status != "cancelled"
    ).group_by(
        func.date(Order.ordered_at)
    ).all()
    
    # 日付をキーとした辞書に変換
    sales_dict = {str(day): revenue for day, revenue in daily_sales}
    
    # 7日分のデータを構築（データがない日は0円）
    weekly_data = []
    for days_ago in range(6, -1, -1):
        target_date = today - timedelta(days=days_ago)
        date_str = target_date.strftime("%Y-%m-%d")
        revenue = sales_dict.get(date_str, 0) or 0
        
        weekly_data.append({
            "date": date_str,
            "revenue": revenue
        })
    
    return {
        "labels": [item["date"] for item in weekly_data],
        "data": [item["revenue"] for item in weekly_data]
    }


# ===== 注文管理 =====

@router.get("/orders", response_model=OrderListResponse, summary="全注文一覧取得")
def get_all_orders(
    order_status: Optional[str] = Query(None, alias="status", description="ステータスでフィルタ（カンマ区切りで複数指定可）"),
    start_date: Optional[str] = Query(None, description="開始日 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="終了日 (YYYY-MM-DD)"),
    q: Optional[str] = Query(None, description="検索キーワード（顧客名、メニュー名）"),
    sort: Optional[str] = Query("newest", description="ソート順: newest, oldest, price_high, price_low"),
    page: int = Query(1, ge=1, description="ページ番号"),
    per_page: int = Query(100, ge=1, le=1000, description="1ページあたりの件数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager', 'staff']))
):
    """
    全ての注文一覧を取得（自店舗のみ）
    
    - 最新の注文から順に表示
    - ステータス、日付、キーワードでフィルタリング可能
    - 注文日時、金額でソート可能
    - ユーザー情報とメニュー情報を含む
    
    **必要な権限:** owner, manager, staff
    """
    # ユーザーが店舗に所属しているか確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
    # 自店舗の注文のみを取得
    query = db.query(Order).filter(Order.store_id == current_user.store_id)
    
    # キーワード検索がある場合はJOINを追加
    needs_user_join = False
    needs_menu_join = False
    
    # ステータスフィルタ（複数選択対応）
    if order_status:
        status_list = [s.strip() for s in order_status.split(',')]
        query = query.filter(Order.status.in_(status_list))
    
    # 日付フィルタ
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Order.ordered_at >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            # 終了日の23:59:59まで含める
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Order.ordered_at <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )
    
    # キーワード検索（顧客名、メニュー名）
    if q:
        search_term = f"%{q}%"
        # JOINを1回だけ行う
        if not needs_user_join:
            query = query.join(User, Order.user_id == User.id)
            needs_user_join = True
        if not needs_menu_join:
            query = query.join(Menu, Order.menu_id == Menu.id)
            needs_menu_join = True
        
        query = query.filter(
            (User.full_name.ilike(search_term)) |
            (User.username.ilike(search_term)) |
            (Menu.name.ilike(search_term))
        )
    
    # ソート
    if sort == "oldest":
        query = query.order_by(Order.ordered_at.asc())
    elif sort == "price_high":
        query = query.order_by(Order.total_price.desc())
    elif sort == "price_low":
        query = query.order_by(Order.total_price.asc())
    else:  # newest (デフォルト)
        query = query.order_by(Order.ordered_at.desc())
    
    # 総件数を取得
    total = query.count()
    
    # ページネーション
    offset = (page - 1) * per_page
    orders = query.offset(offset).limit(per_page).all()
    
    # ユーザー情報とメニュー情報を含める（JOINしていない場合）
    if not needs_user_join or not needs_menu_join:
        for order in orders:
            if not needs_user_join:
                order.user = db.query(User).filter(User.id == order.user_id).first()
            if not needs_menu_join:
                order.menu = db.query(Menu).filter(Menu.id == order.menu_id).first()
    
    return {"orders": orders, "total": total}


@router.put("/orders/{order_id}/status", response_model=OrderResponse, summary="注文ステータス更新")
def update_order_status(
    order_id: int,
    status_update: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager', 'staff']))
):
    """
    注文のステータスを更新（自店舗の注文のみ・簡素化ステータス対応）
    
    可能なステータス:
    - pending: 注文受付（確認・在庫確認・決済処理）
    - ready: 準備完了（弁当完成、顧客通知）
    - completed: 受取完了（顧客が受取済み）
    - cancelled: キャンセル（注文取消）
    
    **ステータス遷移ルール:**
    - pending → ready または cancelled
    - ready → completed
    - completed → 変更不可
    - cancelled → 変更不可
    
    **必要な権限:** owner, manager, staff
    """
    # ユーザーが店舗に所属しているか確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
    # 自店舗の注文のみを取得
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.store_id == current_user.store_id  # 店舗フィルタ追加
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # ステータス遷移のバリデーション（簡素化ステータス対応）
    from schemas import OrderStatus
    
    allowed_transitions = OrderStatus.get_allowed_transitions(order.status)
    new_status = status_update.status.value if hasattr(status_update.status, 'value') else status_update.status
    
    if new_status not in allowed_transitions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from '{order.status}' to '{new_status}'. Allowed: {allowed_transitions}"
        )
    
    order.status = new_status
    db.commit()
    db.refresh(order)
    
    # ユーザー情報とメニュー情報を含める
    order.user = db.query(User).filter(User.id == order.user_id).first()
    order.menu = db.query(Menu).filter(Menu.id == order.menu_id).first()
    
    return order


# ===== メニュー管理 =====

@router.get("/menus", response_model=MenuListResponse, summary="メニュー管理一覧")
def get_all_menus(
    is_available: Optional[bool] = Query(None, description="利用可能フラグでフィルタ"),
    page: int = Query(1, ge=1, description="ページ番号"),
    per_page: int = Query(20, ge=1, le=100, description="1ページあたりの件数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager', 'staff']))
):
    """
    全てのメニュー一覧を取得（自店舗のみ、管理用）
    
    **必要な権限:** owner, manager, staff
    """
    # ユーザーが店舗に所属しているか確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
    # 自店舗のメニューのみを取得
    query = db.query(Menu).filter(Menu.store_id == current_user.store_id)
    
    # 利用可能フラグでフィルタ
    if is_available is not None:
        query = query.filter(Menu.is_available == is_available)
    
    # 総件数を取得
    total = query.count()
    
    # ページネーション
    offset = (page - 1) * per_page
    menus = query.offset(offset).limit(per_page).all()
    
    return {"menus": menus, "total": total}


@router.post("/menus", response_model=MenuResponse, summary="メニュー作成")
def create_menu(
    menu: MenuCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager']))
):
    """
    新しいメニューを作成（自店舗に紐づけ）
    
    **必要な権限:** owner, manager
    """
    # ユーザーが店舗に所属しているか確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
    # メニュー作成時に自動的にstore_idを設定
    db_menu = Menu(**menu.dict(), store_id=current_user.store_id)
    
    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)
    
    return db_menu


@router.put("/menus/{menu_id}", response_model=MenuResponse, summary="メニュー更新")
def update_menu(
    menu_id: int,
    menu_update: MenuUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager']))
):
    """
    既存メニューを更新（自店舗のみ）
    
    **必要な権限:** owner, manager
    """
    # ユーザーが店舗に所属しているか確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
    # 自店舗のメニューのみを取得
    menu = db.query(Menu).filter(
        Menu.id == menu_id,
        Menu.store_id == current_user.store_id  # 店舗フィルタ追加
    ).first()
    
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found"
        )
    
    # 更新データを適用
    update_data = menu_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(menu, field, value)
    
    db.commit()
    db.refresh(menu)
    
    return menu


@router.delete("/menus/{menu_id}", summary="メニュー削除")
def delete_menu(
    menu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner']))
):
    """
    メニューを削除（自店舗のみ）
    
    注意: 既存の注文がある場合は論理削除（is_available = False）を推奨
    
    **必要な権限:** owner
    """
    # ユーザーが店舗に所属しているか確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
    # 自店舗のメニューのみを取得
    menu = db.query(Menu).filter(
        Menu.id == menu_id,
        Menu.store_id == current_user.store_id  # 店舗フィルタ追加
    ).first()
    
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found"
        )
    
    # 既存の注文があるかチェック
    existing_orders = db.query(Order).filter(Order.menu_id == menu_id).first()
    if existing_orders:
        # 論理削除
        menu.is_available = False
        db.commit()
        return {"message": "Menu disabled due to existing orders"}
    else:
        # 物理削除
        db.delete(menu)
        db.commit()
        return {"message": "Menu deleted successfully"}


# ===== 売上レポート =====

@router.get("/reports/sales", response_model=SalesReportResponse, summary="売上レポート取得")
def get_sales_report(
    period: str = Query("daily", description="レポート期間 (daily, weekly, monthly)"),
    start_date: Optional[str] = Query(None, description="開始日 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="終了日 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager']))
):
    """
    売上レポートを取得（自店舗のみ）
    
    - 日別、週別、月別の売上集計
    - メニュー別売上ランキング
    - 指定期間での集計
    
    **必要な権限:** owner, manager
    """
    # ユーザーが店舗に所属しているか確認
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
    # デフォルトの期間設定
    if not start_date:
        if period == "daily":
            start_date = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
        elif period == "weekly":
            start_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        else:  # monthly
            start_date = (date.today() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    if not end_date:
        end_date = date.today().strftime("%Y-%m-%d")
    
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    # 指定期間の注文を取得（自店舗のみ、キャンセル除く）
    orders_query = db.query(Order).filter(
        and_(
            Order.store_id == current_user.store_id,  # 店舗フィルタ追加
            Order.ordered_at >= start_dt,
            Order.ordered_at <= end_dt,
            Order.status != "cancelled"
        )
    )
    
    # 日別売上集計
    daily_reports = []
    current_date = start_dt.date()
    end_date_obj = end_dt.date()
    
    while current_date <= end_date_obj:
        day_start = datetime.combine(current_date, datetime.min.time())
        day_end = datetime.combine(current_date, datetime.max.time())
        
        day_orders = orders_query.filter(
            and_(
                Order.ordered_at >= day_start,
                Order.ordered_at <= day_end
            )
        )
        
        day_count = day_orders.count()
        day_sales = db.query(func.sum(Order.total_price)).filter(
            and_(
                Order.store_id == current_user.store_id,  # 店舗フィルタ追加
                Order.ordered_at >= day_start,
                Order.ordered_at <= day_end,
                Order.status != "cancelled"
            )
        ).scalar() or 0
        
        # 人気メニューを取得（自店舗のみ）
        popular_menu = db.query(
            Menu.name,
            func.sum(Order.quantity).label("total_quantity")
        ).join(Order).filter(
            and_(
                Order.store_id == current_user.store_id,  # 店舗フィルタ追加
                Order.ordered_at >= day_start,
                Order.ordered_at <= day_end,
                Order.status != "cancelled"
            )
        ).group_by(Menu.name).order_by(desc("total_quantity")).first()
        
        daily_reports.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "total_orders": day_count,
            "total_sales": day_sales,
            "popular_menu": popular_menu[0] if popular_menu else None
        })
        
        current_date += timedelta(days=1)
    
    # メニュー別売上集計（自店舗のみ）
    menu_reports = db.query(
        Menu.id,
        Menu.name,
        func.sum(Order.quantity).label("total_quantity"),
        func.sum(Order.total_price).label("total_sales")
    ).join(Order).filter(
        and_(
            Order.store_id == current_user.store_id,  # 店舗フィルタ追加
            Order.ordered_at >= start_dt,
            Order.ordered_at <= end_dt,
            Order.status != "cancelled"
        )
    ).group_by(Menu.id, Menu.name).order_by(desc("total_sales")).all()
    
    menu_report_list = [
        {
            "menu_id": report.id,
            "menu_name": report.name,
            "total_quantity": report.total_quantity,
            "total_sales": report.total_sales
        }
        for report in menu_reports
    ]
    
    # 合計集計（自店舗のみ）
    total_orders = orders_query.count()
    total_sales = db.query(func.sum(Order.total_price)).filter(
        and_(
            Order.store_id == current_user.store_id,  # 店舗フィルタ追加
            Order.ordered_at >= start_dt,
            Order.ordered_at <= end_dt,
            Order.status != "cancelled"
        )
    ).scalar() or 0
    
    return {
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "daily_reports": daily_reports,
        "menu_reports": menu_report_list,
        "total_sales": total_sales,
        "total_orders": total_orders
    }
