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
from dependencies import get_current_store_user, require_role
from models import User, Menu, Order, Store
from schemas import (
    MenuCreate, MenuUpdate, MenuResponse, MenuListResponse,
    OrderResponse, OrderListResponse, OrderStatusUpdate, OrderSummary,
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
        "period": period,
        "start_date": start_date,
        "end_date": end_date,
        "daily_reports": daily_reports,
        "menu_reports": menu_report_list,
        "total_sales": total_sales,
        "total_orders": total_orders
    }


# ===== 店舗プロフィール =====

@router.get("/profile", response_model=StoreResponse, summary="店舗プロフィール取得")
def get_store_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_store_user)
):
    """
    ログイン中のユーザーが所属する店舗の情報を取得
    
    **必要な権限:** store (owner, manager, staff)
    """
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
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
    """
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
    store = db.query(Store).filter(Store.id == current_user.store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    # 部分更新をサポート
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
    店舗画像をアップロード（オーナー専用）
    
    **必要な権限:** owner
    **対応ファイル形式:** JPEG, PNG, GIF, WebP
    """
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
    store = db.query(Store).filter(Store.id == current_user.store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    # ファイル形式を検証
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # 保存先ディレクトリを作成
    upload_dir = Path("static/uploads/stores")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # 一意のファイル名を生成
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_dir / unique_filename
    
    # ファイルを保存
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # 古い画像ファイルを削除
    if store.image_url:
        old_file_path = Path(store.image_url.lstrip('/'))
        if old_file_path.exists():
            try:
                old_file_path.unlink()
            except Exception:
                pass  # 削除に失敗しても続行
    
    # データベースを更新
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
    """
    if not current_user.store_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any store"
        )
    
    store = db.query(Store).filter(Store.id == current_user.store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Store not found"
        )
    
    # 画像ファイルを削除
    if store.image_url:
        file_path = Path(store.image_url.lstrip('/'))
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass  # 削除に失敗しても続行
    
    # データベースを更新
    store.image_url = None
    db.commit()
    db.refresh(store)
    
    return store


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