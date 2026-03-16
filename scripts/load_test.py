# scripts/load_test.py
import requests
import time
import random
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the correct function from mock_data
from scripts.mock_data import generate_valid_log

API_URL = "http://localhost:8000/logs/"
TEST_DURATION = 60  # seconds
BATCH_SIZE = 100
NUM_THREADS = 5

# Stats tracking
total_logs = 0
successful_logs = 0
failed_logs = 0
response_times = []
lock = threading.Lock()

def send_batch(batch_id, num_logs):
    """Send a batch of logs and track performance"""
    global total_logs, successful_logs, failed_logs, response_times
    
    logs = []
    for i in range(num_logs):
        # Use the correct function name
        log = generate_valid_log()
        logs.append(log)
    
    start_time = time.time()
    try:
        response = requests.post(API_URL, json=logs, timeout=5)
        duration = (time.time() - start_time) * 1000  # ms
        
        with lock:
            response_times.append(duration)
            total_logs += len(logs)
            
            if response.status_code == 200:
                successful_logs += len(logs)
                status = "✅"
            else:
                failed_logs += len(logs)
                status = "❌"
            
            print(f"{status} Batch {batch_id}: {len(logs)} logs in {duration:.2f}ms")
            
    except Exception as e:
        with lock:
            failed_logs += len(logs)
            print(f"❌ Batch {batch_id} failed: {e}")

def run_load_test(total_logs=10000, threads=NUM_THREADS):
    """Run the main load test"""
    print("\n" + "="*60)
    print(f"🚀 LOAD TEST - Sending {total_logs} logs")
    print("="*60)
    print(f"Threads: {threads}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"API URL: {API_URL}")
    print("="*60 + "\n")
    
    num_batches = total_logs // BATCH_SIZE
    remaining = total_logs % BATCH_SIZE
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        
        # Submit batches
        for i in range(num_batches):
            future = executor.submit(send_batch, i+1, BATCH_SIZE)
            futures.append(future)
        
        if remaining > 0:
            future = executor.submit(send_batch, num_batches+1, remaining)
            futures.append(future)
        
        # Wait for all to complete
        for future in as_completed(futures):
            future.result()
    
    total_time = time.time() - start_time
    
    # Calculate statistics
    avg_time = sum(response_times) / len(response_times) if response_times else 0
    success_rate = (successful_logs / total_logs) * 100 if total_logs > 0 else 0
    
    print("\n" + "="*60)
    print("📊 LOAD TEST RESULTS")
    print("="*60)
    print(f"Total logs sent:     {total_logs}")
    print(f"Successful:          {successful_logs} ({success_rate:.1f}%)")
    print(f"Failed:              {failed_logs}")
    print(f"Total time:          {total_time:.2f} seconds")
    print(f"Logs/second:         {total_logs/total_time:.2f}")
    print(f"Avg response time:   {avg_time:.2f} ms")
    if response_times:
        print(f"Min response time:   {min(response_times):.2f} ms")
        print(f"Max response time:   {max(response_times):.2f} ms")
    print("="*60)
    
    return success_rate

def monitor_system(duration=TEST_DURATION):
    """Monitor system during test"""
    print(f"\n📡 Monitoring system for {duration} seconds...")
    
    start = time.time()
    while time.time() - start < duration:
        try:
            # Check health
            health = requests.get("http://localhost:8000/health", timeout=2)
            if health.status_code == 200:
                print(f"🟢 Health check OK at {datetime.now().strftime('%H:%M:%S')}")
            else:
                print(f"🟡 Health check warning: {health.status_code}")
        except:
            print(f"🔴 Health check FAILED at {datetime.now().strftime('%H:%M:%S')}")
        
        # Check stats
        try:
            stats = requests.get("http://localhost:8000/logs/stats?minutes=5", timeout=2)
            if stats.status_code == 200:
                data = stats.json()
                print(f"📊 Current logs: {data.get('total_logs', 0)} total, {data.get('error_count', 0)} errors")
        except:
            pass
        
        time.sleep(5)
    
    print("📡 Monitoring complete")

def check_bottlenecks():
    """Check for potential bottlenecks"""
    print("\n🔍 CHECKING FOR BOTTLENECKS")
    print("-" * 40)
    
    checks = []
    
    # Check database connections
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            checks.append(("Database connection", "✅ OK"))
        else:
            checks.append(("Database connection", "❌ Failed"))
    except:
        checks.append(("Database connection", "❌ Failed"))
    
    # Check response times
    if response_times:
        avg = sum(response_times) / len(response_times)
        if avg < 50:
            checks.append(("Response time", f"✅ Excellent ({avg:.1f}ms)"))
        elif avg < 100:
            checks.append(("Response time", f"🟡 Good ({avg:.1f}ms)"))
        else:
            checks.append(("Response time", f"🔴 Slow ({avg:.1f}ms)"))
    
    # Check success rate
    if total_logs > 0:
        rate = (successful_logs / total_logs) * 100
        if rate > 99:
            checks.append(("Success rate", f"✅ {rate:.1f}%"))
        elif rate > 95:
            checks.append(("Success rate", f"🟡 {rate:.1f}%"))
        else:
            checks.append(("Success rate", f"🔴 {rate:.1f}%"))
    
    # Print results
    for check, result in checks:
        print(f"{check:20} {result}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load test the log analyzer")
    parser.add_argument("--logs", type=int, default=10000, help="Number of logs to send")
    parser.add_argument("--threads", type=int, default=5, help="Number of concurrent threads")
    parser.add_argument("--monitor", action="store_true", help="Monitor system during test")
    parser.add_argument("--bottlenecks", action="store_true", help="Check for bottlenecks")
    
    args = parser.parse_args()
    
    if args.bottlenecks:
        check_bottlenecks()
    else:
        if args.monitor:
            # Run monitor in separate thread
            import threading
            monitor_thread = threading.Thread(target=monitor_system)
            monitor_thread.daemon = True
            monitor_thread.start()
        
        run_load_test(args.logs, args.threads)
        
        if args.monitor:
            monitor_thread.join(timeout=5)