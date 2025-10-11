"""
/api/auth/me エンドポイントのテストスクリプト
"""
import requests

# ログイン
login_response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"username": "store_a", "password": "password"}
)

if login_response.status_code == 200:
    token_data = login_response.json()
    access_token = token_data["access_token"]
    
    # /api/auth/me を呼び出し
    me_response = requests.get(
        "http://localhost:8000/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if me_response.status_code == 200:
        user_data = me_response.json()
        print("✅ /api/auth/me レスポンス:")
        print(f"   Username: {user_data['username']}")
        print(f"   Email: {user_data['email']}")
        print(f"   Role: {user_data['role']}")
        print(f"   user_roles: {user_data.get('user_roles', 'NOT FOUND')}")
        
        if 'user_roles' in user_data and len(user_data['user_roles']) > 0:
            print("\n✅ user_roles が正しく返されました:")
            for ur in user_data['user_roles']:
                print(f"   - Role ID: {ur['id']}, Name: {ur['role']['name']}")
        else:
            print("\n❌ user_roles が空または存在しません")
    else:
        print(f"❌ /api/auth/me エラー: {me_response.status_code}")
        print(me_response.text)
else:
    print(f"❌ ログインエラー: {login_response.status_code}")
    print(login_response.text)
