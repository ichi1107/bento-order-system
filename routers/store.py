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

from database import get_db
from dependencies import get_current_store_user, require_role
from models import User, Menu, Order, Store
from schemas import (
    MenuCreate, MenuUpdate, MenuResponse, MenuListResponse,
    OrderResponse, OrderListResponse, OrderStatusUpdate, OrderSummary,
    SalesReportResponse, DailySalesReport, MenuSalesReport,
    StoreResponse, StoreUpdate
)

router = APIRouter(prefix="/store", tags=["店舗"])


# ===== ダッシュボード =====

@router.get("/dashboard", response_model=OrderSummary, summary="ダッシュボード情報取得")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager', 'staff']))
):
    """
    本日の注文状況サマリーを取得
    
    **必要な権限:** owner, manager, staff
    """
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # 本日の注文を取得
    today_orders = db.query(Order).filter(
        and_(
            Order.ordered_at >= today_start,
            Order.ordered_at <= today_end
        )
    )
    
    # ステータス別の集計
    total_orders = today_orders.count()
    pending_orders = today_orders.filter(Order.status == "pending").count()
    confirmed_orders = today_orders.filter(Order.status == "confirmed").count()
    preparing_orders = today_orders.filter(Order.status == "preparing").count()
    ready_orders = today_orders.filter(Order.status == "ready").count()
    completed_orders = today_orders.filter(Order.status == "completed").count()
    cancelled_orders = today_orders.filter(Order.status == "cancelled").count()
    
    # 売上計算（キャンセル除く）
    total_sales = db.query(func.sum(Order.total_price)).filter(
        and_(
            Order.ordered_at >= today_start,
            Order.ordered_at <= today_end,
            Order.status != "cancelled"
        )
    ).scalar() or 0
    
    return {
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "confirmed_orders": confirmed_orders,
        "preparing_orders": preparing_orders,
        "ready_orders": ready_orders,
        "completed_orders": completed_orders,
        "cancelled_orders": cancelled_orders,
        "total_sales": total_sales
    }


# ===== 注文管理 =====

@router.get("/orders", response_model=OrderListResponse, summary="全注文一覧取得")
def get_all_orders(
    status_filter: Optional[str] = Query(None, description="ステータスでフィルタ"),
    start_date: Optional[str] = Query(None, description="開始日 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="終了日 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="ページ番号"),
    per_page: int = Query(20, ge=1, le=100, description="1ページあたりの件数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager', 'staff']))
):
    """
    全ての注文一覧を取得
    
    - 最新の注文から順に表示
    - ステータスや日付でフィルタリング可能
    - ユーザー情報とメニュー情報を含む
    
    **必要な権限:** owner, manager, staff
    """
    query = db.query(Order)
    
    # ステータスフィルタ
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
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
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Order.ordered_at <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )
    
    # 最新順でソート
    query = query.order_by(desc(Order.ordered_at))
    
    # 総件数を取得
    total = query.count()
    
    # ページネーション
    offset = (page - 1) * per_page
    orders = query.offset(offset).limit(per_page).all()
    
    # ユーザー情報とメニュー情報を含める
    for order in orders:
        order.user = db.query(User).filter(User.id == order.user_id).first()
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
    注文のステータスを更新
    
    可能なステータス:
    - pending: 注文受付
    - confirmed: 注文確認済み
    - preparing: 調理中
    - ready: 受取準備完了
    - completed: 受取完了
    - cancelled: キャンセル
    
    **必要な権限:** owner, manager, staff
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    order.status = status_update.status
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
    全てのメニュー一覧を取得（管理用）
    
    **必要な権限:** owner, manager, staff
    """
    query = db.query(Menu)
    
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
    新しいメニューを作成
    
    **必要な権限:** owner, manager
    """
    db_menu = Menu(**menu.dict())
    
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
    既存メニューを更新
    
    **必要な権限:** owner, manager
    """
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    
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
    メニューを削除
    
    注意: 既存の注文がある場合は論理削除（is_available = False）を推奨
    
    **必要な権限:** owner
    """
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    
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
    売上レポートを取得
    
    - 日別、週別、月別の売上集計
    - メニュー別売上ランキング
    - 指定期間での集計
    
    **必要な権限:** owner, manager
    """
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
    
    # 指定期間の注文を取得（キャンセル除く）
    orders_query = db.query(Order).filter(
        and_(
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
                Order.ordered_at >= day_start,
                Order.ordered_at <= day_end,
                Order.status != "cancelled"
            )
        ).scalar() or 0
        
        # 人気メニューを取得
        popular_menu = db.query(
            Menu.name,
            func.sum(Order.quantity).label("total_quantity")
        ).join(Order).filter(
            and_(
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
    
    # メニュー別売上集計
    menu_reports = db.query(
        Menu.id,
        Menu.name,
        func.sum(Order.quantity).label("total_quantity"),
        func.sum(Order.total_price).label("total_sales")
    ).join(Order).filter(
        and_(
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
    
    # 合計集計
    total_orders = orders_query.count()
    total_sales = db.query(func.sum(Order.total_price)).filter(
        and_(
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


# ===== 店舗プロフィール管理 =====

@router.get("/profile", response_model=StoreResponse, summary="店舗情報取得")
def get_store_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner', 'manager', 'staff']))
):
    """
    店舗情報を取得
    
    **必要な権限:** owner, manager, staff
    """
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found. User is not associated with any store."
        )
    
    store = db.query(Store).filter(Store.id == current_user.store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    return store


@router.put("/profile", response_model=StoreResponse, summary="店舗情報更新")
def update_store_profile(
    store_update: StoreUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner']))
):
    """
    店舗情報を更新
    
    **必要な権限:** owner
    """
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found. User is not associated with any store."
        )
    
    store = db.query(Store).filter(Store.id == current_user.store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    # 更新
    update_data = store_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(store, field, value)
    
    db.commit()
    db.refresh(store)
    
    return store


@router.post("/profile/image", response_model=StoreResponse, summary="店舗画像アップロード")
async def upload_store_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(['owner']))
):
    """
    店舗画像をアップロード
    
    **必要な権限:** owner
    """
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found. User is not associated with any store."
        )
    
    store = db.query(Store).filter(Store.id == current_user.store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    # ファイル検証
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only images are allowed."
        )
    
    # 古い画像を削除
    if store.image_url:
        old_file_path = store.image_url.replace('/static/', 'static/')
        if os.path.exists(old_file_path):
            os.remove(old_file_path)
    
    # ファイル保存
    upload_dir = "static/uploads/stores"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_extension = file.filename.split('.')[-1] if file.filename else 'jpg'
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # データベース更新
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
    店舗画像を削除
    
    **必要な権限:** owner
    """
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found. User is not associated with any store."
        )
    
    store = db.query(Store).filter(Store.id == current_user.store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    # ファイル削除
    if store.image_url:
        file_path = store.image_url.replace('/static/', 'static/')
        if os.path.exists(file_path):
            os.remove(file_path)
    
    # データベース更新
    store.image_url = None
    db.commit()
    db.refresh(store)
    
    return store