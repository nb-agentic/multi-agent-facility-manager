#!/usr/bin/env python3
import psutil
import time
import json
from datetime import datetime

def monitor_memory(interval=5, duration=60):
    """Monitor memory usage over time"""
    results = []
    start_time = time.time()
    
    while time.time() - start_time < duration:
        memory_info = psutil.virtual_memory()
        process_info = psutil.Process().memory_info()
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'memory_percent': memory_info.percent,
            'memory_used_mb': memory_info.used / 1024 / 1024,
            'memory_available_mb': memory_info.available / 1024 / 1024,
            'process_memory_mb': process_info.rss / 1024 / 1024
        }
        
        results.append(result)
        time.sleep(interval)
    
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Monitor memory usage')
    parser.add_argument('--interval', type=int, default=5, help='Monitoring interval in seconds')
    parser.add_argument('--duration', type=int, default=60, help='Monitoring duration in seconds')
    args = parser.parse_args()
    
    results = monitor_memory(args.interval, args.duration)
    
    with open('memory_monitoring_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Memory monitoring complete. Results saved to memory_monitoring_results.json")
