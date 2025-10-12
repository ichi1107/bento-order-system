"""
データベースマイグレーション適用スクリプト

パフォーマンスインデックスを追加
"""

import subprocess
import sys


def run_migration():
    """Alembicマイグレーションを実行"""
    print("=" * 60)
    print("データベースマイグレーション実行")
    print("=" * 60)
    print("\nパフォーマンス最適化のためのインデックスを追加します...")
    print("- orders.ordered_at")
    print("- orders.status")
    print("- orders(store_id, ordered_at)")
    print("- orders(store_id, status)")
    print("- orders(store_id, ordered_at, status)")
    print()
    
    try:
        # Alembicでマイグレーション実行
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True
        )
        
        print("✓ マイグレーション成功")
        print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("✗ マイグレーション失敗")
        print(f"エラー: {e.stderr}")
        return False
    except FileNotFoundError:
        print("✗ Alembicが見つかりません")
        print("pip install alembic を実行してください")
        return False


def main():
    """メイン処理"""
    print("\n🚀 パフォーマンス最適化マイグレーション")
    print()
    
    success = run_migration()
    
    if success:
        print("\n" + "=" * 60)
        print("✓ インデックスの追加が完了しました")
        print("=" * 60)
        print("\n次のステップ:")
        print("1. python scripts/benchmark_dashboard.py でパフォーマンスを測定")
        print("2. サーバーを再起動してください")
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("✗ マイグレーションに失敗しました")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
