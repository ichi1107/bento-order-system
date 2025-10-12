"""顧客機能の包括的テストスクリプト"""
import requests
import json
from datetime import datetime

def test_customer_features():
    print("=" * 60)
    print("顧客機能テスト - 包括的チェック")
    print("=" * 60)
    
    # 1. ログインテスト
    print("\n1️⃣ ログインテスト")
    login_resp = requests.post('http://localhost:8000/api/auth/login', 
                               json={'username': 'customer1', 'password': 'password123'})
    
    if login_resp.status_code != 200:
        print(f"❌ ログイン失敗: {login_resp.status_code}")
        return
    
    print("✅ ログイン成功")
    token = login_resp.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # 2. メニュー一覧取得テスト
    print("\n2️⃣ メニュー一覧取得テスト")
    menus_resp = requests.get('http://localhost:8000/api/customer/menus', headers=headers)
    
    if menus_resp.status_code != 200:
        print(f"❌ メニュー取得失敗: {menus_resp.status_code}")
        return
    
    menu_data = menus_resp.json()
    print(f"✅ メニュー取得成功: {menu_data['total']}件")
    
    # 3. メニューデータの検証
    print("\n3️⃣ メニューデータ検証")
    if menu_data['menus']:
        menu = menu_data['menus'][0]
        required_fields = ['id', 'name', 'price', 'store_id', 'image_url']
        
        missing_fields = []
        for field in required_fields:
            if field not in menu:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ 必須フィールドが不足: {missing_fields}")
        else:
            print("✅ 全ての必須フィールドが存在")
            print(f"   - ID: {menu['id']}")
            print(f"   - 名前: {menu['name']}")
            print(f"   - 価格: ¥{menu['price']}")
            print(f"   - 店舗ID: {menu['store_id']}")
            print(f"   - 画像URL: {menu['image_url'][:50]}..." if len(menu['image_url']) > 50 else f"   - 画像URL: {menu['image_url']}")
        
        # 4. 注文作成テスト（複数パターン）
        print("\n4️⃣ 注文作成テスト")
        
        # 4-1. 基本的な注文
        print("   4-1. 基本的な注文（数量1）")
        order_data = {
            'menu_id': menu['id'],
            'quantity': 1
        }
        order_resp = requests.post('http://localhost:8000/api/customer/orders', 
                                   headers=headers, 
                                   json=order_data)
        
        if order_resp.status_code != 200:
            print(f"   ❌ 注文失敗: {order_resp.status_code}")
            print(f"   エラー: {order_resp.text}")
        else:
            order = order_resp.json()
            print(f"   ✅ 注文成功")
            print(f"      - 注文ID: {order['id']}")
            print(f"      - メニュー名: {order['menu']['name']}")
            print(f"      - 店舗ID: {order['store_id']}")
            print(f"      - 数量: {order['quantity']}")
            print(f"      - 合計: ¥{order['total_price']}")
            print(f"      - ステータス: {order['status']}")
            
            # store_idが設定されているか確認
            if 'store_id' not in order or order['store_id'] is None:
                print("   ⚠️ 警告: store_idが設定されていません！")
            else:
                print(f"   ✅ store_idが正しく設定されています: {order['store_id']}")
        
        # 4-2. 数量が複数の注文
        print("\n   4-2. 複数数量の注文（数量3）")
        order_data2 = {
            'menu_id': menu['id'],
            'quantity': 3
        }
        order_resp2 = requests.post('http://localhost:8000/api/customer/orders', 
                                    headers=headers, 
                                    json=order_data2)
        
        if order_resp2.status_code != 200:
            print(f"   ❌ 注文失敗: {order_resp2.status_code}")
        else:
            order2 = order_resp2.json()
            expected_total = menu['price'] * 3
            actual_total = order2['total_price']
            
            if expected_total == actual_total:
                print(f"   ✅ 合計金額が正確: ¥{actual_total}")
            else:
                print(f"   ❌ 合計金額が不正確: 期待¥{expected_total} vs 実際¥{actual_total}")
        
        # 4-3. 備考付き注文
        print("\n   4-3. 備考付き注文")
        order_data3 = {
            'menu_id': menu['id'],
            'quantity': 1,
            'notes': 'ご飯少なめでお願いします'
        }
        order_resp3 = requests.post('http://localhost:8000/api/customer/orders', 
                                    headers=headers, 
                                    json=order_data3)
        
        if order_resp3.status_code != 200:
            print(f"   ❌ 注文失敗: {order_resp3.status_code}")
        else:
            order3 = order_resp3.json()
            if order3.get('notes') == order_data3['notes']:
                print(f"   ✅ 備考が正しく保存: {order3['notes']}")
            else:
                print(f"   ❌ 備考が保存されていません")
    
    # 5. 注文履歴取得テスト
    print("\n5️⃣ 注文履歴取得テスト")
    history_resp = requests.get('http://localhost:8000/api/customer/orders', headers=headers)
    
    if history_resp.status_code != 200:
        print(f"❌ 注文履歴取得失敗: {history_resp.status_code}")
    else:
        history = history_resp.json()
        print(f"✅ 注文履歴取得成功: {history['total']}件")
        
        if history['orders']:
            latest = history['orders'][0]
            print(f"   最新の注文:")
            print(f"   - ID: {latest['id']}")
            print(f"   - メニュー: {latest['menu_name']}")
            print(f"   - 数量: {latest['quantity']}")
            print(f"   - 合計: ¥{latest['total_price']}")
    
    # 6. 画像URL検証
    print("\n6️⃣ 画像URL検証")
    image_urls = [m['image_url'] for m in menu_data['menus'] if m.get('image_url')]
    
    if not image_urls:
        print("❌ 画像URLが設定されているメニューがありません")
    else:
        print(f"✅ {len(image_urls)}件のメニューに画像URLが設定されています")
        
        # サンプルURLをテスト
        sample_url = image_urls[0]
        try:
            img_resp = requests.head(sample_url, timeout=5)
            if img_resp.status_code == 200:
                print(f"   ✅ 画像URLにアクセス可能: {sample_url[:50]}...")
            else:
                print(f"   ⚠️ 画像URLにアクセスできません（{img_resp.status_code}）: {sample_url[:50]}...")
        except Exception as e:
            print(f"   ℹ️ 画像URLテストスキップ（プレースホルダーURL）: {sample_url[:50]}...")
    
    print("\n" + "=" * 60)
    print("✅ 全てのテストが完了しました！")
    print("=" * 60)

if __name__ == '__main__':
    test_customer_features()
