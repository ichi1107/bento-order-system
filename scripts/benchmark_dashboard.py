"""
ダッシュボードAPIパフォーマンス測定スクリプト

使用方法:
    python scripts/benchmark_dashboard.py
"""

import time
import statistics
from typing import List, Dict
import requests
from datetime import datetime


class DashboardBenchmark:
    """ダッシュボードAPIのベンチマークテスト"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api"):
        self.base_url = base_url
        self.token = None
        
    def login(self, username: str, password: str) -> bool:
        """ログインしてトークンを取得"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={
                    "username": username,
                    "password": password
                }
            )
            
            print(f"  Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"  Response: {response.text}")
                return False
            
            self.token = response.json()["access_token"]
            return True
        except Exception as e:
            print(f"  Error: {e}")
            return False
    
    def measure_endpoint(self, endpoint: str, iterations: int = 10) -> Dict:
        """エンドポイントのレスポンスタイムを測定"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response_times: List[float] = []
        
        print(f"\n{'='*60}")
        print(f"測定対象: {endpoint}")
        print(f"試行回数: {iterations}回")
        print(f"{'='*60}")
        
        for i in range(iterations):
            start_time = time.time()
            response = requests.get(f"{self.base_url}{endpoint}", headers=headers)
            end_time = time.time()
            
            elapsed = (end_time - start_time) * 1000  # ミリ秒に変換
            response_times.append(elapsed)
            
            status = "✓" if response.status_code == 200 else "✗"
            print(f"  試行 {i+1:2d}: {elapsed:7.2f}ms {status}")
        
        # 統計計算
        avg = statistics.mean(response_times)
        median = statistics.median(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        stdev = statistics.stdev(response_times) if len(response_times) > 1 else 0
        
        print(f"\n統計情報:")
        print(f"  平均: {avg:.2f}ms")
        print(f"  中央値: {median:.2f}ms")
        print(f"  最小: {min_time:.2f}ms")
        print(f"  最大: {max_time:.2f}ms")
        print(f"  標準偏差: {stdev:.2f}ms")
        
        # パフォーマンス評価
        if avg < 100:
            grade = "🟢 優秀"
        elif avg < 300:
            grade = "🟡 良好"
        elif avg < 500:
            grade = "🟠 許容範囲"
        else:
            grade = "🔴 要改善"
        
        print(f"  評価: {grade}")
        
        return {
            "endpoint": endpoint,
            "average": avg,
            "median": median,
            "min": min_time,
            "max": max_time,
            "stdev": stdev,
            "iterations": iterations
        }
    
    def run_full_benchmark(self) -> None:
        """全エンドポイントのベンチマークを実行"""
        print("\n" + "="*60)
        print("ダッシュボードAPIパフォーマンスベンチマーク")
        print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        endpoints = [
            "/api/store/dashboard",
            "/api/store/dashboard/weekly-sales"
        ]
        
        results = []
        for endpoint in endpoints:
            result = self.measure_endpoint(endpoint, iterations=10)
            results.append(result)
        
        # サマリー表示
        print(f"\n{'='*60}")
        print("ベンチマーク結果サマリー")
        print(f"{'='*60}")
        print(f"{'エンドポイント':<40} {'平均(ms)':>10} {'評価':>8}")
        print(f"{'-'*60}")
        
        for result in results:
            avg = result['average']
            if avg < 100:
                grade = "🟢 優秀"
            elif avg < 300:
                grade = "🟡 良好"
            elif avg < 500:
                grade = "🟠 許容"
            else:
                grade = "🔴 要改善"
            
            print(f"{result['endpoint']:<40} {avg:>10.2f} {grade:>8}")
        
        # 目標達成状況
        print(f"\n{'='*60}")
        print("目標達成状況")
        print(f"{'='*60}")
        
        dashboard_avg = results[0]['average']
        target = 500  # 500ms以下が目標
        
        if dashboard_avg <= target:
            status = "✓ 達成"
            print(f"ダッシュボードAPI: {dashboard_avg:.2f}ms ≤ {target}ms {status}")
        else:
            status = "✗ 未達成"
            improvement = dashboard_avg - target
            print(f"ダッシュボードAPI: {dashboard_avg:.2f}ms > {target}ms {status}")
            print(f"  あと {improvement:.2f}ms の改善が必要です")


def main():
    """メイン処理"""
    benchmark = DashboardBenchmark()
    
    # ログイン（店舗ユーザー）
    print("ログイン中...")
    if not benchmark.login("admin", "admin@123"):
        print("❌ ログインに失敗しました")
        return
    
    print("✓ ログイン成功")
    
    # ベンチマーク実行
    benchmark.run_full_benchmark()


if __name__ == "__main__":
    main()
