"""Role関連スキーマのバリデーションテスト"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from schemas import RoleResponse, UserRoleResponse, UserWithRolesResponse, RoleAssignRequest
from pydantic import ValidationError

print("🧪 Testing Role Schemas Validation\n")

# Test 1: RoleResponse with valid data
print("1️⃣ RoleResponse with valid data:")
try:
    role = RoleResponse(
        id=1,
        name='owner',
        description='店舗オーナー',
        created_at=datetime.now()
    )
    print(f"   ✅ Valid: {role.name}")
except ValidationError as e:
    print(f"   ❌ Error: {e}")

# Test 2: RoleResponse with invalid role name
print("\n2️⃣ RoleResponse with invalid role name:")
try:
    role = RoleResponse(
        id=1,
        name='invalid_role',  # Should fail
        description='無効な役割',
        created_at=datetime.now()
    )
    print(f"   ❌ Should have failed but got: {role.name}")
except ValidationError as e:
    print(f"   ✅ Correctly rejected: Invalid literal")

# Test 3: RoleAssignRequest with valid data
print("\n3️⃣ RoleAssignRequest with valid data:")
try:
    request = RoleAssignRequest(user_id=1, role_id=2)
    print(f"   ✅ Valid: user_id={request.user_id}, role_id={request.role_id}")
except ValidationError as e:
    print(f"   ❌ Error: {e}")

# Test 4: RoleAssignRequest with invalid data (negative IDs)
print("\n4️⃣ RoleAssignRequest with invalid data:")
try:
    request = RoleAssignRequest(user_id=-1, role_id=0)
    print(f"   ❌ Should have failed but got: user_id={request.user_id}")
except ValidationError as e:
    print(f"   ✅ Correctly rejected: Negative/zero IDs not allowed")

# Test 5: UserWithRolesResponse
print("\n5️⃣ UserWithRolesResponse with empty roles:")
try:
    user = UserWithRolesResponse(
        id=1,
        username='test_user',
        email='test@example.com',
        full_name='テストユーザー',
        role='store',
        is_active=True,
        created_at=datetime.now(),
        user_roles=[]
    )
    print(f"   ✅ Valid: {user.username} with {len(user.user_roles)} roles")
except ValidationError as e:
    print(f"   ❌ Error: {e}")

print("\n✅ All validation tests completed!")
