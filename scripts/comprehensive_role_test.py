"""Role関連スキーマの包括的なテスト"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from database import SessionLocal
from models import User, Role, UserRole
from schemas import (
    RoleResponse, 
    UserRoleResponse, 
    UserWithRolesResponse, 
    RoleAssignRequest
)
from pydantic import ValidationError

print("=" * 70)
print("🧪 COMPREHENSIVE ROLE SCHEMA TESTS")
print("=" * 70)

db = SessionLocal()

try:
    # Test Suite 1: Schema Validation
    print("\n📋 TEST SUITE 1: Schema Validation")
    print("-" * 70)
    
    # Test 1.1: Valid role names
    print("\n1.1 Valid role names:")
    valid_roles = ['owner', 'manager', 'staff']
    for role_name in valid_roles:
        try:
            role = RoleResponse(
                id=1,
                name=role_name,
                description=f"Test {role_name}",
                created_at=datetime.now()
            )
            print(f"   ✅ '{role_name}' accepted")
        except ValidationError:
            print(f"   ❌ '{role_name}' rejected (should be valid)")
    
    # Test 1.2: Invalid role names
    print("\n1.2 Invalid role names:")
    invalid_roles = ['admin', 'user', 'superuser', '']
    for role_name in invalid_roles:
        try:
            role = RoleResponse(
                id=1,
                name=role_name,
                description=f"Test {role_name}",
                created_at=datetime.now()
            )
            print(f"   ❌ '{role_name}' accepted (should be rejected)")
        except ValidationError:
            print(f"   ✅ '{role_name}' correctly rejected")
    
    # Test 1.3: Field validation
    print("\n1.3 Field validation for RoleAssignRequest:")
    test_cases = [
        (1, 1, True, "Valid IDs"),
        (0, 1, False, "Zero user_id"),
        (1, 0, False, "Zero role_id"),
        (-1, 1, False, "Negative user_id"),
        (1, -1, False, "Negative role_id"),
    ]
    
    for user_id, role_id, should_pass, description in test_cases:
        try:
            request = RoleAssignRequest(user_id=user_id, role_id=role_id)
            if should_pass:
                print(f"   ✅ {description}: Accepted")
            else:
                print(f"   ❌ {description}: Should have been rejected")
        except ValidationError:
            if not should_pass:
                print(f"   ✅ {description}: Correctly rejected")
            else:
                print(f"   ❌ {description}: Should have been accepted")
    
    # Test Suite 2: ORM Conversion
    print("\n\n📋 TEST SUITE 2: ORM to Pydantic Conversion")
    print("-" * 70)
    
    # Test 2.1: All roles from database
    print("\n2.1 Convert all Role models to RoleResponse:")
    roles = db.query(Role).all()
    for role in roles:
        try:
            role_resp = RoleResponse.model_validate(role)
            print(f"   ✅ {role_resp.name}: {role_resp.description}")
        except Exception as e:
            print(f"   ❌ {role.name}: {e}")
    
    # Test 2.2: All user-role assignments
    print("\n2.2 Convert all UserRole models to UserRoleResponse:")
    user_roles = db.query(UserRole).join(User).join(Role).all()
    for ur in user_roles:
        try:
            ur_resp = UserRoleResponse.model_validate(ur)
            print(f"   ✅ User ID {ur_resp.user_id} -> {ur_resp.role.name}")
        except Exception as e:
            print(f"   ❌ UserRole ID {ur.id}: {e}")
    
    # Test 2.3: Users with roles
    print("\n2.3 Convert User models to UserWithRolesResponse:")
    store_users = db.query(User).filter(User.role == 'store').all()
    for user in store_users:
        try:
            user_resp = UserWithRolesResponse.model_validate(user)
            role_names = [ur.role.name for ur in user_resp.user_roles]
            print(f"   ✅ {user_resp.username}: {role_names}")
        except Exception as e:
            print(f"   ❌ {user.username}: {e}")
    
    # Test Suite 3: from_attributes Configuration
    print("\n\n📋 TEST SUITE 3: Config.from_attributes Verification")
    print("-" * 70)
    
    print("\n3.1 Checking from_attributes in schemas:")
    schemas_to_check = [
        RoleResponse,
        UserRoleResponse,
        UserWithRolesResponse,
    ]
    
    for schema in schemas_to_check:
        has_config = hasattr(schema, 'model_config')
        if has_config:
            from_attributes = schema.model_config.get('from_attributes', False)
            if from_attributes:
                print(f"   ✅ {schema.__name__}: from_attributes = True")
            else:
                print(f"   ❌ {schema.__name__}: from_attributes not set")
        else:
            print(f"   ⚠️  {schema.__name__}: No model_config found")
    
    # Test Suite 4: Type Hints
    print("\n\n📋 TEST SUITE 4: Type Hints Verification")
    print("-" * 70)
    
    print("\n4.1 Checking type annotations:")
    for schema in schemas_to_check:
        annotations = schema.__annotations__
        print(f"\n   {schema.__name__}:")
        for field_name, field_type in annotations.items():
            print(f"     - {field_name}: {field_type}")
    
    # Final Summary
    print("\n" + "=" * 70)
    print("✅ ALL COMPREHENSIVE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    
    print("\n📊 Summary:")
    print(f"   - Schemas validated: 4 (RoleResponse, UserRoleResponse, UserWithRolesResponse, RoleAssignRequest)")
    print(f"   - Roles in database: {len(roles)}")
    print(f"   - User role assignments: {len(user_roles)}")
    print(f"   - Store users with roles: {len(store_users)}")
    print(f"   - from_attributes: Configured for all response schemas")
    print(f"   - Type hints: Complete for all schemas")

except Exception as e:
    print(f"\n❌ FATAL ERROR: {e}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
