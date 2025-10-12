# トラブルシューティングガイド

## 🔧 発生した問題と解決方法

### 問題1: SQLAlchemy `func.case()` エラー

#### エラー内容
```
TypeError: Function.__init__() got an unexpected keyword argument 'else_'
```

#### 原因
SQLAlchemyの`func.case()`で`else_`パラメータの使用方法が誤っていた。

#### 修正前のコード
```python
yesterday_stats = db.query(
    func.count(Order.id).label('order_count'),
    func.sum(func.case(
        (Order.status != 'cancelled', Order.total_price),
        else_=0  # ❌ 誤った構文
    )).label('revenue')
).filter(...)
```

#### 修正後のコード
```python
# シンプルにデータを取得してPythonで集計
yesterday_orders = db.query(Order).filter(
    Order.store_id == store_id,
    Order.ordered_at >= yesterday_start,
    Order.ordered_at <= yesterday_end
).all()

yesterday_orders_count = len(yesterday_orders)
yesterday_revenue = sum(o.total_price for o in yesterday_orders if o.status != "cancelled")
```

#### 教訓
- 複雑なSQL関数よりもシンプルなクエリ + Python集計の方が安全
- SQLAlchemyの関数は正確な構文で使用する
- パフォーマンスと可読性のバランスを考慮

---

### 問題2: マイグレーションファイルのリビジョンID不一致

#### エラー内容
```
KeyError: '001'
Revision 001 referenced from 001 -> 002 is not present
```

#### 原因
新規作成したマイグレーションファイルの`down_revision`が存在しないリビジョンIDを参照していた。

#### 解決方法
```python
# 修正前
revision = '002'
down_revision = '001'  # ❌ 存在しないリビジョン

# 修正後
revision = '002_perf_indexes'
down_revision = '82c749cdf529'  # ✅ 実際に存在するリビジョン
```

#### 代替アプローチ
マイグレーションの代わりに直接SQLでインデックスを追加:
```bash
docker-compose exec db psql -U postgres -d bento_db -c "CREATE INDEX ..."
```

---

### 問題3: ベンチマークスクリプトのログイン失敗

#### エラー履歴

**エラー1: 404 Not Found**
```
Status Code: 404
Response: {"detail":"Not Found"}
```
原因: ベースURLに`/api`プレフィックスがなかった
修正: `http://localhost:8000` → `http://localhost:8000/api`

**エラー2: 422 Unprocessable Entity**
```
Status Code: 422
Response: Input should be a valid dictionary or object
```
原因: `data={}` でフォームデータとして送信していた
修正: `json={}` でJSON形式に変更

#### 最終的な正しいコード
```python
def login(self, username: str, password: str) -> bool:
    response = requests.post(
        f"{self.base_url}/auth/login",  # /api/auth/login
        json={  # JSON形式
            "username": username,
            "password": password
        }
    )
    if response.status_code == 200:
        self.token = response.json()["access_token"]
        return True
    return False
```

---

## 📝 一般的なトラブルシューティング

### データベース関連

#### インデックスが適用されていない
```bash
# インデックス一覧を確認
docker-compose exec db psql -U postgres -d bento_db -c "
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'orders';
"

# インデックスが欠けている場合は追加
docker-compose exec db psql -U postgres -d bento_db -c "
CREATE INDEX ix_orders_ordered_at ON orders(ordered_at);
"
```

#### クエリプランの確認
```sql
EXPLAIN ANALYZE
SELECT * FROM orders
WHERE store_id = 1 
AND ordered_at >= '2025-10-12'
AND status != 'cancelled';
```

良い結果の例:
```
Index Scan using ix_orders_store_ordered_status on orders  (cost=0.15..8.17 rows=1 width=...)
  Index Cond: ((store_id = 1) AND (ordered_at >= '2025-10-12'::timestamp))
  Filter: (status <> 'cancelled')
```

悪い結果の例:
```
Seq Scan on orders  (cost=0.00..1000.00 rows=50000 width=...)
  Filter: ((store_id = 1) AND (ordered_at >= '2025-10-12'::timestamp))
```

### アプリケーション関連

#### 500エラーが発生する
```bash
# ログを確認
docker-compose logs web --tail=100

# 詳細なスタックトレースを確認
docker-compose logs web | grep -A 20 "Traceback"
```

#### パフォーマンスが改善されない
1. インデックスが適用されているか確認
2. データベース統計を更新
   ```sql
   ANALYZE orders;
   ```
3. クエリプランを確認
4. サーバーを再起動
   ```bash
   docker-compose restart web
   ```

### Docker関連

#### コンテナが起動しない
```bash
# コンテナの状態確認
docker-compose ps

# ログ確認
docker-compose logs

# 再ビルド
docker-compose down
docker-compose up --build
```

#### データベース接続エラー
```bash
# データベースコンテナの状態確認
docker-compose exec db pg_isready

# データベースに直接接続できるか確認
docker-compose exec db psql -U postgres -d bento_db -c "SELECT 1;"
```

---

## 🔍 デバッグ手法

### 1. レスポンス時間の内訳確認

Pythonコードに計測コードを追加:
```python
import time

start = time.time()
result = db.query(Order).filter(...).all()
print(f"Query time: {(time.time() - start) * 1000}ms")

start = time.time()
# 処理...
print(f"Processing time: {(time.time() - start) * 1000}ms")
```

### 2. SQLクエリのログ出力

`database.py`にクエリログを追加:
```python
engine = create_engine(
    DATABASE_URL,
    echo=True  # SQLクエリをログ出力
)
```

### 3. プロファイリング

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# 測定したいコード
get_dashboard(db, current_user)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

---

## ✅ チェックリスト

問題が発生した場合の確認手順:

1. [ ] サーバーログを確認
2. [ ] データベース接続を確認
3. [ ] インデックスが適用されているか確認
4. [ ] クエリプランを確認
5. [ ] データベース統計を更新 (`ANALYZE`)
6. [ ] サーバーを再起動
7. [ ] ベンチマークを再実行
8. [ ] ブラウザのキャッシュをクリア

---

## 📚 参考資料

- [SQLAlchemy Error Messages](https://docs.sqlalchemy.org/en/20/errors.html)
- [PostgreSQL Performance Tips](https://www.postgresql.org/docs/current/performance-tips.html)
- [FastAPI Debugging](https://fastapi.tiangolo.com/tutorial/debugging/)
- [Docker Compose Troubleshooting](https://docs.docker.com/compose/faq/)
