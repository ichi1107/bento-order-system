"""ORMモデルからPydanticスキーマへの変換テスト"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal
from models import User, Role, UserRole
from schemas import RoleResponse, UserRoleResponse, UserWithRolesResponse

print("🧪 Testing ORM to Pydantic Schema Conversion\n")

db = SessionLocal()

try:
    # Test 1: Role -> RoleResponse
    print("1️⃣ Role -> RoleResponse:")
    role = db.query(Role).filter(Role.name == 'owner').first()
    if role:
        role_response = RoleResponse.model_validate(role)
        print(f"   ✅ {role_response.name}: {role_response.description}")
    else:
        print("   ❌ No owner role found")

    # Test 2: UserRole -> UserRoleResponse
    print("\n2️⃣ UserRole -> UserRoleResponse:")
    user_role = db.query(UserRole).join(User).filter(User.username == 'admin').first()
    if user_role:
        user_role_response = UserRoleResponse.model_validate(user_role)
        print(f"   ✅ User ID {user_role_response.user_id} -> Role: {user_role_response.role.name}")
    else:
        print("   ❌ No user role found for admin")

    # Test 3: User with roles -> UserWithRolesResponse
    print("\n3️⃣ User with roles -> UserWithRolesResponse:")
    user = db.query(User).filter(User.username == 'admin').first()
    if user:
        user_with_roles = UserWithRolesResponse.model_validate(user)
        print(f"   ✅ {user_with_roles.username} ({user_with_roles.email})")
        print(f"      Roles: {[ur.role.name for ur in user_with_roles.user_roles]}")
    else:
        print("   ❌ No admin user found")

    # Test 4: All roles
    print("\n4️⃣ All Roles in Database:")
    roles = db.query(Role).all()
    for role in roles:
        role_resp = RoleResponse.model_validate(role)
        print(f"   - {role_resp.name}: {role_resp.description}")

    # Test 5: All user role assignments
    print("\n5️⃣ All User Role Assignments:")
    user_roles = db.query(UserRole).join(User).join(Role).all()
    for ur in user_roles:
        ur_resp = UserRoleResponse.model_validate(ur)
        print(f"   - User ID {ur_resp.user_id} -> {ur_resp.role.name}")

    print("\n✅ All ORM conversion tests passed!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
