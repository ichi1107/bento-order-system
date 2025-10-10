"""TypeScript型定義を生成"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic2ts import generate_typescript_defs

print('🔄 Generating TypeScript types from Pydantic schemas...')

output_path = Path(__file__).parent.parent / 'static' / 'js' / 'types' / 'api.ts'

try:
    generate_typescript_defs(
        'schemas.py',
        str(output_path)
    )
    print(f'✅ TypeScript types generated successfully!')
    print(f'   Output: {output_path}')
    
    # ファイルサイズを確認
    if output_path.exists():
        size = output_path.stat().st_size
        print(f'   File size: {size} bytes')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
