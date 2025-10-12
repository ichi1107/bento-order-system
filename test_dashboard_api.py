"""ダッシュボードAPI拡張機能テストスクリプト"""
import requests
import json

# ログイン
resp = requests.post('http://localhost:8000/api/auth/login', 
                     json={'username': 'store1', 'password': 'password123'})
token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# ダッシュボードAPIを取得
dashboard = requests.get('http://localhost:8000/api/store/dashboard', headers=headers)
data = dashboard.json()

print('=== ダッシュボードAPI拡張テスト結果 ===\n')

print('📊 基本統計:')
print(f'  総注文数: {data["total_orders"]}')
print(f'  確定: {data["confirmed_orders"]}, 準備中: {data["preparing_orders"]}, 受取可: {data["ready_orders"]}, 完了: {data["completed_orders"]}')

print('\n💰 売上情報:')
print(f'  本日の総売上: ¥{data["today_revenue"]:,}')
print(f'  平均注文単価: ¥{data["average_order_value"]:,.2f}')

print('\n📈 前日比較:')
comp = data['yesterday_comparison']
print(f'  注文数: {comp["orders_change"]:+d} ({comp["orders_change_percent"]:+.1f}%)')
print(f'  売上: ¥{comp["revenue_change"]:+,} ({comp["revenue_change_percent"]:+.1f}%)')

print('\n🍱 人気メニュートップ3:')
for i, menu in enumerate(data['popular_menus'], 1):
    print(f'  {i}. {menu["menu_name"]}: {menu["order_count"]}件 (¥{menu["total_revenue"]:,})')

print('\n⏰ 時間帯別注文数:')
hourly = [h for h in data['hourly_orders'] if h['order_count'] > 0]
for h in hourly:
    print(f'  {h["hour"]:02d}:00 - {h["order_count"]}件')

print('\n✅ 全ての拡張フィールドが正常に返されています!')
print(f'\nレスポンスサイズ: {len(json.dumps(data))} bytes')
