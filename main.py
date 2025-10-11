"""
FastAPI メインアプリケーション

弁当注文管理システムのメインアプリケーション
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, customer, store
from database import engine, Base

# データベーステーブルを作成
Base.metadata.create_all(bind=engine)

# FastAPIアプリケーション作成
app = FastAPI(
    title="弁当注文管理システム",
    description="お客様と店舗向けの弁当注文管理システム",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に設定してください
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静的ファイルとテンプレート設定
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ルーター登録
app.include_router(auth.router, prefix="/api")
app.include_router(customer.router, prefix="/api")
app.include_router(store.router, prefix="/api")


# ===== フロントエンド画面ルーティング =====

@app.get("/", response_class=HTMLResponse, summary="ホーム画面")
async def home(request: Request):
    """ホーム画面（ログイン画面へリダイレクト）"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/login", response_class=HTMLResponse, summary="ログイン画面")
async def login_page(request: Request):
    """ログイン画面"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse, summary="新規登録画面")
async def register_page(request: Request):
    """新規登録画面"""
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/customer/home", response_class=HTMLResponse, summary="お客様メニュー画面")
async def customer_home(request: Request):
    """お客様向けメニュー画面"""
    return templates.TemplateResponse("customer_home.html", {"request": request})


@app.get("/customer/orders", response_class=HTMLResponse, summary="お客様注文履歴画面")
async def customer_orders(request: Request):
    """お客様向け注文履歴画面"""
    return templates.TemplateResponse("customer_orders.html", {"request": request})


@app.get("/store/dashboard", response_class=HTMLResponse, summary="店舗ダッシュボード")
async def store_dashboard(request: Request):
    """店舗向けダッシュボード画面"""
    return templates.TemplateResponse("store_dashboard.html", {"request": request})


@app.get("/store/orders", response_class=HTMLResponse, summary="店舗注文管理画面")
async def store_orders(request: Request):
    """店舗向け注文管理画面"""
    return templates.TemplateResponse("store_orders.html", {"request": request})


@app.get("/store/menus", response_class=HTMLResponse, summary="店舗メニュー管理画面")
async def store_menus(request: Request):
    """店舗向けメニュー管理画面"""
    return templates.TemplateResponse("store_menus.html", {"request": request})


@app.get("/store/reports", response_class=HTMLResponse, summary="店舗売上レポート画面")
async def store_reports(request: Request):
    """店舗向け売上レポート画面"""
    return templates.TemplateResponse("store_reports.html", {"request": request})


# ===== パスワードリセット画面 =====

@app.get("/password-reset-request", response_class=HTMLResponse, summary="パスワードリセット要求画面")
async def password_reset_request(request: Request):
    """パスワードリセット要求画面"""
    return templates.TemplateResponse("password_reset_request.html", {"request": request})


@app.get("/reset-password", response_class=HTMLResponse, summary="パスワード再設定画面")
async def reset_password(request: Request):
    """パスワード再設定画面（メール内のリンクから遷移）"""
    return templates.TemplateResponse("password_reset_confirm.html", {"request": request})


# ===== ヘルスチェック =====

@app.get("/health", summary="ヘルスチェック")
async def health_check():
    """サーバーのヘルスチェック"""
    return {"status": "healthy", "message": "Bento Order System is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )