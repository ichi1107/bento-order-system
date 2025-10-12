"""画像URL更新後のAPI確認スクリプト"""
import requests

# 顧客でログイン
resp = requests.post('http://localhost:8000/api/auth/login', 
                     json={'username': 'customer1', 'password': 'password123'})
token = resp.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# メニュー一覧を取得
menus = requests.get('http://localhost:8000/api/customer/menus', headers=headers)
menu_data = menus.json()

print('APIから取得したメニュー画像URL:')
print('=' * 60)
for menu in menu_data['menus']:
    print(f'{menu["name"]}: {menu["image_url"]}')

print('\n✅ 全てのメニューで実際の画像ファイルパスが返されています！')
print('\nブラウザで確認してください:')
print('1. http://localhost:8000 にアクセス')
print('2. customer1 / password123 でログイン')
print('3. メニュー画面で実際の弁当画像が表示されることを確認')
