"""
店舗プロフィールAPI統合テスト

店舗情報管理APIの品質とセキュリティを保証するための包括的なテストスイート。
特に、役割ベースのアクセス制御(RBAC)とテナント分離を重点的に検証します。
"""

import pytest
import io
from pathlib import Path
from datetime import time


class TestStoreProfileGet:
    """店舗プロフィール取得APIのテスト"""

    def test_owner_can_get_store_profile(
        self, client, auth_headers_owner_store_a, owner_user_store_a, store_a
    ):
        """オーナーは自店舗のプロフィールを取得できる"""
        response = client.get("/api/store/profile", headers=auth_headers_owner_store_a)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == store_a.id
        assert data["name"] == store_a.name
        assert data["address"] == store_a.address
        assert data["phone_number"] == store_a.phone_number
        assert data["email"] == store_a.email
        assert data["is_active"] == store_a.is_active

    def test_manager_can_get_store_profile(
        self, client, auth_headers_manager_store_a, manager_user_store_a, store_a
    ):
        """マネージャーは自店舗のプロフィールを取得できる"""
        response = client.get("/api/store/profile", headers=auth_headers_manager_store_a)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == store_a.id
        assert data["name"] == store_a.name

    def test_staff_can_get_store_profile(
        self, client, auth_headers_staff_store_a, staff_user_store_a, store_a
    ):
        """スタッフは自店舗のプロフィールを取得できる"""
        response = client.get("/api/store/profile", headers=auth_headers_staff_store_a)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == store_a.id
        assert data["name"] == store_a.name

    def test_unauthorized_access_fails(self, client):
        """認証なしではアクセスできない"""
        response = client.get("/api/store/profile")
        assert response.status_code == 401

    def test_customer_cannot_access_store_profile(
        self, client, auth_headers_customer_a
    ):
        """顧客ユーザーは店舗プロフィールにアクセスできない"""
        response = client.get("/api/store/profile", headers=auth_headers_customer_a)
        assert response.status_code == 403

    def test_user_without_store_gets_400(
        self, client, db_session, roles
    ):
        """店舗に所属していないユーザーは400エラーを受け取る"""
        from models import User, UserRole
        from auth import get_password_hash
        
        # 店舗に所属していない店舗ユーザーを作成
        user = User(
            username="orphan_user",
            email="orphan@test.com",
            full_name="孤立ユーザー",
            hashed_password=get_password_hash("password123"),
            role="store",
            store_id=None,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # ownerロールを付与
        user_role = UserRole(user_id=user.id, role_id=roles["owner"].id)
        db_session.add(user_role)
        db_session.commit()
        
        # ログイン
        from tests.conftest import get_auth_token
        token = get_auth_token(client, "orphan_user", "password123")
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/store/profile", headers=headers)
        assert response.status_code == 400
        assert "not associated with any store" in response.json()["detail"]


class TestStoreProfileUpdate:
    """店舗プロフィール更新APIのテスト"""

    def test_owner_can_update_store_profile(
        self, client, auth_headers_owner_store_a, store_a
    ):
        """オーナーは店舗プロフィールを更新できる"""
        update_data = {
            "name": "更新された店舗名",
            "description": "新しい説明文です",
            "is_active": False
        }
        
        response = client.put(
            "/api/store/profile",
            json=update_data,
            headers=auth_headers_owner_store_a
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新された店舗名"
        assert data["description"] == "新しい説明文です"
        assert data["is_active"] is False
        assert data["id"] == store_a.id

    def test_owner_can_partially_update_store_profile(
        self, client, auth_headers_owner_store_a, store_a
    ):
        """オーナーは部分更新ができる"""
        update_data = {
            "name": "部分更新された店舗名"
        }
        
        response = client.put(
            "/api/store/profile",
            json=update_data,
            headers=auth_headers_owner_store_a
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "部分更新された店舗名"
        # 他のフィールドは変更されていない
        assert data["address"] == store_a.address
        assert data["phone_number"] == store_a.phone_number

    def test_manager_cannot_update_store_profile(
        self, client, auth_headers_manager_store_a
    ):
        """マネージャーは店舗プロフィールを更新できない（403 Forbidden）"""
        update_data = {
            "name": "マネージャーによる更新試行"
        }
        
        response = client.put(
            "/api/store/profile",
            json=update_data,
            headers=auth_headers_manager_store_a
        )
        
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]
        assert "owner" in response.json()["detail"]

    def test_staff_cannot_update_store_profile(
        self, client, auth_headers_staff_store_a
    ):
        """スタッフは店舗プロフィールを更新できない（403 Forbidden）"""
        update_data = {
            "name": "スタッフによる更新試行"
        }
        
        response = client.put(
            "/api/store/profile",
            json=update_data,
            headers=auth_headers_staff_store_a
        )
        
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

    def test_update_with_invalid_data_fails(
        self, client, auth_headers_owner_store_a
    ):
        """不正なデータでの更新は失敗する"""
        update_data = {
            "name": "",  # 空の名前は無効
        }
        
        response = client.put(
            "/api/store/profile",
            json=update_data,
            headers=auth_headers_owner_store_a
        )
        
        assert response.status_code == 422  # Validation error

    def test_unauthorized_update_fails(self, client):
        """認証なしでの更新は失敗する"""
        update_data = {"name": "不正な更新"}
        
        response = client.put("/api/store/profile", json=update_data)
        assert response.status_code == 401


class TestStoreProfileImageUpload:
    """店舗画像アップロードAPIのテスト"""

    def test_owner_can_upload_image(
        self, client, auth_headers_owner_store_a, store_a
    ):
        """オーナーは画像をアップロードできる"""
        # ダミー画像ファイルを作成
        image_data = b"fake image content"
        files = {
            "file": ("test_image.jpg", io.BytesIO(image_data), "image/jpeg")
        }
        
        response = client.post(
            "/api/store/profile/image",
            files=files,
            headers=auth_headers_owner_store_a
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["image_url"] is not None
        assert "/static/uploads/stores/" in data["image_url"]
        assert data["image_url"].endswith(".jpg")
        
        # ファイルが実際に保存されているか確認
        file_path = Path(data["image_url"].lstrip('/'))
        assert file_path.exists()
        
        # クリーンアップ
        if file_path.exists():
            file_path.unlink()

    def test_owner_can_upload_png_image(
        self, client, auth_headers_owner_store_a
    ):
        """オーナーはPNG画像をアップロードできる"""
        image_data = b"fake png image"
        files = {
            "file": ("test_image.png", io.BytesIO(image_data), "image/png")
        }
        
        response = client.post(
            "/api/store/profile/image",
            files=files,
            headers=auth_headers_owner_store_a
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["image_url"].endswith(".png")
        
        # クリーンアップ
        file_path = Path(data["image_url"].lstrip('/'))
        if file_path.exists():
            file_path.unlink()

    def test_upload_replaces_old_image(
        self, client, auth_headers_owner_store_a, db_session, store_a
    ):
        """新しい画像のアップロードは古い画像を置き換える"""
        # 1枚目の画像をアップロード
        files1 = {
            "file": ("image1.jpg", io.BytesIO(b"image 1"), "image/jpeg")
        }
        response1 = client.post(
            "/api/store/profile/image",
            files=files1,
            headers=auth_headers_owner_store_a
        )
        assert response1.status_code == 200
        old_image_url = response1.json()["image_url"]
        old_file_path = Path(old_image_url.lstrip('/'))
        
        # 2枚目の画像をアップロード
        files2 = {
            "file": ("image2.jpg", io.BytesIO(b"image 2"), "image/jpeg")
        }
        response2 = client.post(
            "/api/store/profile/image",
            files=files2,
            headers=auth_headers_owner_store_a
        )
        assert response2.status_code == 200
        new_image_url = response2.json()["image_url"]
        new_file_path = Path(new_image_url.lstrip('/'))
        
        # 古い画像ファイルが削除されていることを確認
        assert not old_file_path.exists()
        # 新しい画像ファイルが存在することを確認
        assert new_file_path.exists()
        
        # クリーンアップ
        if new_file_path.exists():
            new_file_path.unlink()

    def test_invalid_file_type_rejected(
        self, client, auth_headers_owner_store_a
    ):
        """不正なファイル形式は拒否される"""
        files = {
            "file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")
        }
        
        response = client.post(
            "/api/store/profile/image",
            files=files,
            headers=auth_headers_owner_store_a
        )
        
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_manager_cannot_upload_image(
        self, client, auth_headers_manager_store_a
    ):
        """マネージャーは画像をアップロードできない"""
        files = {
            "file": ("test.jpg", io.BytesIO(b"image"), "image/jpeg")
        }
        
        response = client.post(
            "/api/store/profile/image",
            files=files,
            headers=auth_headers_manager_store_a
        )
        
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

    def test_staff_cannot_upload_image(
        self, client, auth_headers_staff_store_a
    ):
        """スタッフは画像をアップロードできない"""
        files = {
            "file": ("test.jpg", io.BytesIO(b"image"), "image/jpeg")
        }
        
        response = client.post(
            "/api/store/profile/image",
            files=files,
            headers=auth_headers_staff_store_a
        )
        
        assert response.status_code == 403


class TestStoreProfileImageDelete:
    """店舗画像削除APIのテスト"""

    def test_owner_can_delete_image(
        self, client, auth_headers_owner_store_a, db_session, store_a
    ):
        """オーナーは画像を削除できる"""
        # まず画像をアップロード
        files = {
            "file": ("test.jpg", io.BytesIO(b"image"), "image/jpeg")
        }
        upload_response = client.post(
            "/api/store/profile/image",
            files=files,
            headers=auth_headers_owner_store_a
        )
        assert upload_response.status_code == 200
        image_url = upload_response.json()["image_url"]
        file_path = Path(image_url.lstrip('/'))
        assert file_path.exists()
        
        # 画像を削除
        delete_response = client.delete(
            "/api/store/profile/image",
            headers=auth_headers_owner_store_a
        )
        
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["image_url"] is None
        
        # ファイルが削除されていることを確認
        assert not file_path.exists()

    def test_delete_nonexistent_image(
        self, client, auth_headers_owner_store_a, store_a
    ):
        """存在しない画像の削除は成功する（冪等性）"""
        response = client.delete(
            "/api/store/profile/image",
            headers=auth_headers_owner_store_a
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["image_url"] is None

    def test_manager_cannot_delete_image(
        self, client, auth_headers_manager_store_a
    ):
        """マネージャーは画像を削除できない"""
        response = client.delete(
            "/api/store/profile/image",
            headers=auth_headers_manager_store_a
        )
        
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

    def test_staff_cannot_delete_image(
        self, client, auth_headers_staff_store_a
    ):
        """スタッフは画像を削除できない"""
        response = client.delete(
            "/api/store/profile/image",
            headers=auth_headers_staff_store_a
        )
        
        assert response.status_code == 403


class TestTenantIsolation:
    """テナント分離のテスト（最重要セキュリティテスト）"""

    def test_store_a_owner_cannot_access_store_b_data(
        self, client, auth_headers_owner_store_a, auth_headers_owner_store_b,
        owner_user_store_a, owner_user_store_b, store_a, store_b
    ):
        """店舗Aのオーナーは店舗Bのデータにアクセスできない"""
        # 店舗Aのオーナーでログイン
        response_a = client.get("/api/store/profile", headers=auth_headers_owner_store_a)
        assert response_a.status_code == 200
        data_a = response_a.json()
        
        # 店舗Bのオーナーでログイン
        response_b = client.get("/api/store/profile", headers=auth_headers_owner_store_b)
        assert response_b.status_code == 200
        data_b = response_b.json()
        
        # 店舗Aのユーザーは店舗Aのデータのみ取得
        assert data_a["id"] == store_a.id
        assert data_a["name"] == store_a.name
        
        # 店舗Bのユーザーは店舗Bのデータのみ取得
        assert data_b["id"] == store_b.id
        assert data_b["name"] == store_b.name
        
        # 店舗AとBのデータは異なる
        assert data_a["id"] != data_b["id"]
        assert data_a["name"] != data_b["name"]

    def test_store_a_owner_cannot_update_store_b_data(
        self, client, auth_headers_owner_store_a, owner_user_store_a, 
        store_a, store_b, db_session
    ):
        """店舗Aのオーナーは店舗Bのデータを更新できない"""
        # 店舗Aのオーナーで店舗情報を更新
        update_data = {
            "name": "店舗Aオーナーによる更新"
        }
        
        response = client.put(
            "/api/store/profile",
            json=update_data,
            headers=auth_headers_owner_store_a
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 更新されたのは店舗Aのデータのみ
        assert data["id"] == store_a.id
        assert data["name"] == "店舗Aオーナーによる更新"
        
        # 店舗Bのデータは変更されていない
        db_session.refresh(store_b)
        assert store_b.name == "テスト店舗B"

    def test_different_store_users_see_different_profiles(
        self, client, auth_headers_manager_store_a, auth_headers_owner_store_b,
        store_a, store_b
    ):
        """異なる店舗のユーザーは異なるプロフィールを見る"""
        # 店舗Aのマネージャー
        response_a = client.get("/api/store/profile", headers=auth_headers_manager_store_a)
        assert response_a.status_code == 200
        
        # 店舗Bのオーナー
        response_b = client.get("/api/store/profile", headers=auth_headers_owner_store_b)
        assert response_b.status_code == 200
        
        # それぞれ自分の店舗のデータを取得
        assert response_a.json()["id"] == store_a.id
        assert response_b.json()["id"] == store_b.id
        assert response_a.json()["id"] != response_b.json()["id"]


class TestRBACEnforcement:
    """役割ベースのアクセス制御の詳細テスト"""

    def test_only_owner_can_update(
        self, client, auth_headers_owner_store_a, 
        auth_headers_manager_store_a, auth_headers_staff_store_a
    ):
        """owner のみが更新操作を実行でき、manager と staff は拒否される"""
        update_data = {"name": "更新テスト"}
        
        # Owner: 成功
        owner_response = client.put(
            "/api/store/profile",
            json=update_data,
            headers=auth_headers_owner_store_a
        )
        assert owner_response.status_code == 200
        
        # Manager: 失敗
        manager_response = client.put(
            "/api/store/profile",
            json={"name": "マネージャー更新"},
            headers=auth_headers_manager_store_a
        )
        assert manager_response.status_code == 403
        
        # Staff: 失敗
        staff_response = client.put(
            "/api/store/profile",
            json={"name": "スタッフ更新"},
            headers=auth_headers_staff_store_a
        )
        assert staff_response.status_code == 403

    def test_all_roles_can_read(
        self, client, auth_headers_owner_store_a,
        auth_headers_manager_store_a, auth_headers_staff_store_a,
        store_a
    ):
        """owner, manager, staff すべてが読み取り操作を実行できる"""
        # Owner
        owner_response = client.get("/api/store/profile", headers=auth_headers_owner_store_a)
        assert owner_response.status_code == 200
        assert owner_response.json()["id"] == store_a.id
        
        # Manager
        manager_response = client.get("/api/store/profile", headers=auth_headers_manager_store_a)
        assert manager_response.status_code == 200
        assert manager_response.json()["id"] == store_a.id
        
        # Staff
        staff_response = client.get("/api/store/profile", headers=auth_headers_staff_store_a)
        assert staff_response.status_code == 200
        assert staff_response.json()["id"] == store_a.id

    def test_only_owner_can_manage_images(
        self, client, auth_headers_owner_store_a,
        auth_headers_manager_store_a, auth_headers_staff_store_a
    ):
        """owner のみが画像管理操作を実行できる"""
        files = {
            "file": ("test.jpg", io.BytesIO(b"image"), "image/jpeg")
        }
        
        # Owner: アップロード成功
        owner_upload = client.post(
            "/api/store/profile/image",
            files=files,
            headers=auth_headers_owner_store_a
        )
        assert owner_upload.status_code == 200
        
        # Manager: アップロード失敗
        files_manager = {
            "file": ("test2.jpg", io.BytesIO(b"image2"), "image/jpeg")
        }
        manager_upload = client.post(
            "/api/store/profile/image",
            files=files_manager,
            headers=auth_headers_manager_store_a
        )
        assert manager_upload.status_code == 403
        
        # Staff: アップロード失敗
        files_staff = {
            "file": ("test3.jpg", io.BytesIO(b"image3"), "image/jpeg")
        }
        staff_upload = client.post(
            "/api/store/profile/image",
            files=files_staff,
            headers=auth_headers_staff_store_a
        )
        assert staff_upload.status_code == 403
        
        # Owner: 削除成功
        owner_delete = client.delete(
            "/api/store/profile/image",
            headers=auth_headers_owner_store_a
        )
        assert owner_delete.status_code == 200
        
        # Manager: 削除失敗
        manager_delete = client.delete(
            "/api/store/profile/image",
            headers=auth_headers_manager_store_a
        )
        assert manager_delete.status_code == 403
        
        # Staff: 削除失敗
        staff_delete = client.delete(
            "/api/store/profile/image",
            headers=auth_headers_staff_store_a
        )
        assert staff_delete.status_code == 403


class TestEdgeCases:
    """エッジケースとエラーハンドリングのテスト"""

    def test_update_with_very_long_description(
        self, client, auth_headers_owner_store_a
    ):
        """非常に長い説明文での更新"""
        long_description = "x" * 1001  # 1000文字制限を超える
        
        response = client.put(
            "/api/store/profile",
            json={"description": long_description},
            headers=auth_headers_owner_store_a
        )
        
        # バリデーションエラー
        assert response.status_code == 422

    def test_update_with_valid_time_range(
        self, client, auth_headers_owner_store_a
    ):
        """有効な営業時間での更新"""
        update_data = {
            "opening_time": "09:00:00",
            "closing_time": "21:00:00"
        }
        
        response = client.put(
            "/api/store/profile",
            json=update_data,
            headers=auth_headers_owner_store_a
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["opening_time"] == "09:00:00"
        assert data["closing_time"] == "21:00:00"

    def test_update_with_empty_optional_fields(
        self, client, auth_headers_owner_store_a, store_a
    ):
        """オプショナルフィールドを空にする"""
        update_data = {
            "description": None,
            "image_url": None
        }
        
        response = client.put(
            "/api/store/profile",
            json=update_data,
            headers=auth_headers_owner_store_a
        )
        
        assert response.status_code == 200
        # name などの必須フィールドは維持されている
        assert response.json()["name"] == store_a.name

    def test_concurrent_updates_by_same_owner(
        self, client, auth_headers_owner_store_a
    ):
        """同じオーナーによる連続した更新"""
        # 1回目の更新
        response1 = client.put(
            "/api/store/profile",
            json={"name": "更新1"},
            headers=auth_headers_owner_store_a
        )
        assert response1.status_code == 200
        
        # 2回目の更新
        response2 = client.put(
            "/api/store/profile",
            json={"name": "更新2"},
            headers=auth_headers_owner_store_a
        )
        assert response2.status_code == 200
        
        # 最後の更新が反映されている
        assert response2.json()["name"] == "更新2"
