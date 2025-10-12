"""顧客機能テストスクリプト"""
import requests
import json

# 顧客でログイン
resp = requests.post('http://localhost:8000/api/auth/login', 
                     json={'username': 'customer1', 'password': 'password123'})
print('ログイン:', resp.status_code)
token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# メニュー一覧を取得
menus = requests.get('http://localhost:8000/api/customer/menus', headers=headers)
print(f'\nメニュー一覧APIステータス: {menus.status_code}')

if menus.status_code == 200:
    menu_data = menus.json()
    print(f'総件数: {menu_data["total"]}')
    if menu_data['menus']:
        first_menu = menu_data['menus'][0]
        print(f'最初のメニュー: {first_menu["name"]}')
        print(f'  価格: ¥{first_menu["price"]}')
        print(f'  画像URL: {first_menu.get("image_url", "なし")}')
        print(f'  店舗ID: {first_menu.get("store_id", "なし")}')
        
        # 注文を試す
        print('\n=== 注文作成テスト ===')
        order_data = {
            'menu_id': first_menu['id'],
            'quantity': 1
        }
        order_resp = requests.post('http://localhost:8000/api/customer/orders', 
                                   headers=headers, 
                                   json=order_data)
        print(f'注文作成APIステータス: {order_resp.status_code}')
        
        if order_resp.status_code != 200:
            print(f'\n❌ エラー発生:')
            try:
                error_data = order_resp.json()
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print(order_resp.text)
        else:
            print(f'\n✅ 注文成功:')
            order_result = order_resp.json()
            print(f'  注文ID: {order_result["id"]}')
            print(f'  メニュー: {order_result["menu"]["name"]}')
            print(f'  数量: {order_result["quantity"]}')
            print(f'  合計: ¥{order_result["total_price"]}')
else:
    print(f'❌ メニュー一覧取得失敗: {menus.text}')
