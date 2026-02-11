"""
Sprint 5: Test History Analyzer
Analyzes historical test data and generates trend reports
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import statistics

class TestHistoryAnalyzer:
    """Analyzes test execution history for trends and insights"""
    
    def __init__(self, history_file: str = "test_results/test_history.json"):
        self.history_file = Path(history_file)
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load historical test data"""
        if not self.history_file.exists():
            print(f"⚠️  No history file found: {self.history_file}")
            return []
        
        with open(self.history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_stats(self) -> Dict[str, Any]:
        """Calculate statistical metrics from history"""
        if not self.history:
            return {}
        
        pass_rates = [run['pass_rate'] for run in self.history]
        durations = [run['duration'] for run in self.history]
        
        return {
            "total_runs": len(self.history),
            "avg_pass_rate": round(statistics.mean(pass_rates), 2),
            "min_pass_rate": round(min(pass_rates), 2),
            "max_pass_rate": round(max(pass_rates), 2),
            "stdev_pass_rate": round(statistics.stdev(pass_rates), 2) if len(pass_rates) > 1 else 0,
            "avg_duration": round(statistics.mean(durations), 2),
            "min_duration": round(min(durations), 2),
            "max_duration": round(max(durations), 2),
            "latest_pass_rate": pass_rates[-1] if pass_rates else 0,
            "trend": self._calculate_trend(pass_rates)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from recent values"""
        if len(values) < 2:
            return "stable"
        
        # Compare last 5 runs vs previous 5 runs
        recent_count = min(5, len(values) // 2)
        if recent_count == 0:
            return "stable"
        
        recent = values[-recent_count:]
        previous = values[-recent_count*2:-recent_count] if len(values) >= recent_count*2 else values[:-recent_count]
        
        if not previous:
            return "stable"
        
        recent_avg = statistics.mean(recent)
        previous_avg = statistics.mean(previous)
        
        diff = recent_avg - previous_avg
        
        if diff > 5:
            return "improving ⬆️"
        elif diff < -5:
            return "declining ⬇️"
        else:
            return "stable ➡️"
    
    def print_report(self):
        """Print historical analysis report"""
        stats = self.get_stats()
        
        if not stats:
            print("\n⚠️  No historical data available yet")
            return
        
        print("\n" + "=" * 80)
        print("📈 TEST HISTORY ANALYSIS")
        print("=" * 80)
        
        print(f"\nTotal Test Runs: {stats['total_runs']}")
        print(f"\nPass Rate Statistics:")
        print(f"  Average:  {stats['avg_pass_rate']}%")
        print(f"  Min:      {stats['min_pass_rate']}%")
        print(f"  Max:      {stats['max_pass_rate']}%")
        print(f"  Std Dev:  {stats['stdev_pass_rate']}%")
        print(f"  Latest:   {stats['latest_pass_rate']}%")
        print(f"  Trend:    {stats['trend']}")
        
        print(f"\nExecution Time Statistics:")
        print(f"  Average:  {stats['avg_duration']:.1f}s")
        print(f"  Min:      {stats['min_duration']:.1f}s")
        print(f"  Max:      {stats['max_duration']:.1f}s")
        
        # Recent runs
        print(f"\n{'RECENT TEST RUNS':^80}")
        print("-" * 80)
        print(f"{'Timestamp':<25} {'Tests':<10} {'Passed':<10} {'Pass Rate':<12} {'Duration'}")
        print("-" * 80)
        
        for run in self.history[-10:]:  # Last 10 runs
            timestamp = datetime.fromisoformat(run['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
            status_icon = "✅" if run['pass_rate'] >= 90 else "⚠️" if run['pass_rate'] >= 70 else "🚨"
            print(f"{timestamp:<25} {run['total_tests']:<10} {run['passed']:<10} {run['pass_rate']:>5.1f}% {status_icon:<5} {run['duration']:.1f}s")
        
        print("=" * 80 + "\n")
    
    def get_latest_results(self) -> Dict[str, Any]:
        """Get results from most recent test run"""
        if not self.history:
            return {}
        return self.history[-1]


def main():
    """Analyze test history"""
    analyzer = TestHistoryAnalyzer()
    analyzer.print_report()


if __name__ == "__main__":
    main()
