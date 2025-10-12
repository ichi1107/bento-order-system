"""TypeScript型定義生成スクリプト"""
import json
import requests

# OpenAPI仕様を取得
response = requests.get('http://localhost:8000/openapi.json')
openapi_spec = response.json()

# TypeScript型定義を生成
def convert_type(schema_type, ref=None):
    """OpenAPIの型をTypeScriptの型に変換"""
    if ref:
        # $refから型名を抽出
        return ref.split('/')[-1]
    
    type_mapping = {
        'integer': 'number',
        'number': 'number',
        'string': 'string',
        'boolean': 'boolean',
        'array': 'Array',
        'object': 'object'
    }
    return type_mapping.get(schema_type, 'any')

def generate_interface(schema_name, schema_data):
    """スキーマからTypeScriptインターフェースを生成"""
    lines = [f'export interface {schema_name} {{']
    
    properties = schema_data.get('properties', {})
    required = schema_data.get('required', [])
    
    for prop_name, prop_info in properties.items():
        optional = '' if prop_name in required else '?'
        
        if '$ref' in prop_info:
            type_str = convert_type(None, prop_info['$ref'])
        elif prop_info.get('type') == 'array':
            items = prop_info.get('items', {})
            if '$ref' in items:
                item_type = convert_type(None, items['$ref'])
            else:
                item_type = convert_type(items.get('type', 'any'))
            type_str = f'{item_type}[]'
        else:
            type_str = convert_type(prop_info.get('type', 'any'))
        
        description = prop_info.get('description', prop_info.get('title', ''))
        if description:
            lines.append(f'  /** {description} */')
        
        lines.append(f'  {prop_name}{optional}: {type_str};')
    
    lines.append('}')
    return '\n'.join(lines)

# TypeScript型定義を生成
output = []
output.append('/**')
output.append(' * Auto-generated TypeScript type definitions')
output.append(' * Generated from: /api/openapi.json')
output.append(' * DO NOT EDIT MANUALLY')
output.append(' */')
output.append('')

schemas = openapi_spec['components']['schemas']

# 拡張されたダッシュボード関連の型定義を優先的に生成
priority_schemas = [
    'YesterdayComparison',
    'PopularMenu', 
    'HourlyOrderData',
    'OrderSummary'
]

for schema_name in priority_schemas:
    if schema_name in schemas:
        output.append(generate_interface(schema_name, schemas[schema_name]))
        output.append('')

# その他の重要な型も生成
other_schemas = [
    'UserResponse',
    'StoreResponse',
    'MenuResponse',
    'OrderResponse',
    'SuccessResponse',
    'ErrorResponse'
]

for schema_name in other_schemas:
    if schema_name in schemas:
        output.append(generate_interface(schema_name, schemas[schema_name]))
        output.append('')

typescript_code = '\n'.join(output)

# ファイルに保存
with open('static/js/types/api.ts', 'w', encoding='utf-8') as f:
    f.write(typescript_code)

print('✅ TypeScript型定義を生成しました')
print(f'📁 ファイル: static/js/types/api.ts')
print(f'📊 生成された型: {len(priority_schemas + other_schemas)}個')
print('\n--- 生成されたダッシュボード型定義のプレビュー ---')
print(typescript_code[:1500])
