#!/usr/bin/env python3
"""
注文管理テスト実行スクリプト

Usage:
    python scripts/run_order_tests.py [options]
    
Options:
    --full         : 全テストを実行
    --coverage     : カバレッジレポート生成
    --unit         : ユニットテストのみ
    --integration  : インテグレーションテストのみ
    --verbose      : 詳細出力
"""

import subprocess
import sys
import os
from pathlib import Path


def run_tests(
    test_path="tests/test_store_orders.py",
    coverage=True,
    markers=None,
    verbose=True,
    fail_under=90
):
    """
    テストを実行
    
    Args:
        test_path: テストファイルのパス
        coverage: カバレッジ計測の有無
        markers: pytest マーカー (例: "unit", "integration")
        verbose: 詳細出力
        fail_under: カバレッジの最小値
    """
    # プロジェクトルートに移動
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # コマンド構築
    cmd = ["pytest", test_path]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=routers.store",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            f"--cov-fail-under={fail_under}"
        ])
    
    if markers:
        cmd.extend(["-m", markers])
    
    print(f"🧪 Running command: {' '.join(cmd)}")
    print("=" * 70)
    
    # テスト実行
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1


def main():
    """
    メイン処理
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="注文管理テスト実行スクリプト"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="全テストを実行"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        default=True,
        help="カバレッジレポート生成 (デフォルト: True)"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="カバレッジ計測を無効化"
    )
    parser.add_argument(
        "--unit",
        action="store_true",
        help="ユニットテストのみ"
    )
    parser.add_argument(
        "--integration",
        action="store_true",
        help="インテグレーションテストのみ"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=True,
        help="詳細出力"
    )
    parser.add_argument(
        "--fail-under",
        type=int,
        default=90,
        help="カバレッジの最小値 (デフォルト: 90%%)"
    )
    
    args = parser.parse_args()
    
    # テストパスの決定
    if args.full:
        test_path = "tests/"
    else:
        test_path = "tests/test_store_orders.py"
    
    # カバレッジ
    coverage = args.coverage and not args.no_coverage
    
    # マーカー
    markers = None
    if args.unit:
        markers = "unit"
    elif args.integration:
        markers = "integration"
    
    # テスト実行
    print("=" * 70)
    print("🧪 注文管理テスト実行")
    print("=" * 70)
    print(f"📁 Test path: {test_path}")
    print(f"📊 Coverage: {coverage}")
    print(f"🏷️  Markers: {markers or 'all'}")
    print(f"📈 Fail under: {args.fail_under}%")
    print("=" * 70)
    
    returncode = run_tests(
        test_path=test_path,
        coverage=coverage,
        markers=markers,
        verbose=args.verbose,
        fail_under=args.fail_under
    )
    
    # 結果サマリー
    print("\n" + "=" * 70)
    if returncode == 0:
        print("✅ All tests passed!")
        if coverage:
            print(f"📊 Coverage report: htmlcov/index.html")
    else:
        print("❌ Some tests failed")
    print("=" * 70)
    
    sys.exit(returncode)


if __name__ == "__main__":
    main()
