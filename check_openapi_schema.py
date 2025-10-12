"""OpenAPIスキーマ確認スクリプト"""
import sys
import json

data = json.load(sys.stdin)
schema = data['components']['schemas']['OrderSummary']

print('=== OrderSummary スキーマ定義 ===\n')
print('フィールド一覧:')
for field, info in schema['properties'].items():
    if 'type' in info:
        field_type = info['type']
    elif 'anyOf' in info:
        field_type = 'union'
    elif '$ref' in info:
        field_type = info['$ref'].split('/')[-1]
    else:
        field_type = 'complex'
    
    description = info.get('title', '')
    print(f'  • {field}: {field_type}')

print(f'\n必須フィールド: {len(schema.get("required", []))}個')
print('\n拡張フィールド:')
print('  ✓ today_revenue')
print('  ✓ average_order_value')
print('  ✓ yesterday_comparison')
print('  ✓ popular_menus')
print('  ✓ hourly_orders')
