# scripts/benchmark.py
import time
from datetime import datetime, timedelta
from backend.database import SessionLocal
from backend import models
from backend.utils.query_optimizer import QueryOptimizer
from sqlalchemy import func
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_benchmark():
    """Run performance benchmarks before/after optimizations"""
    
    db = SessionLocal()
    optimizer = QueryOptimizer(db)
    
    print("\n" + "="*60)
    print("PERFORMANCE BENCHMARK")
    print("="*60)
    
    def test_recent_errors():
        cutoff = datetime.utcnow() - timedelta(minutes=5)
        return db.query(models.Log).filter(
            models.Log.level == 'ERROR',
            models.Log.timestamp >= cutoff
        ).all()
    
    results, elapsed = optimizer.benchmark_query(test_recent_errors)
    print(f"\nRecent errors query:")
    print(f"  Time: {elapsed:.2f} ms")
    print(f"  Results: {len(results)} rows")

    def test_error_stats():
        cutoff = datetime.utcnow() - timedelta(minutes=60)
        return db.query(
            models.Log.service,
            func.count().label('count')
        ).filter(
            models.Log.level == 'ERROR',
            models.Log.timestamp >= cutoff
        ).group_by(models.Log.service).all()
    
    results, elapsed = optimizer.benchmark_query(test_error_stats)
    print(f"\nError stats query:")
    print(f"  Time: {elapsed:.2f} ms")
    print(f"  Services found: {len(results)}")
    
    def test_incident_stats():
        cutoff = datetime.utcnow() - timedelta(days=7)
        return db.query(
            models.Incident.severity,
            func.count().label('count')
        ).filter(
            models.Incident.detected_at >= cutoff
        ).group_by(models.Incident.severity).all()
    
    results, elapsed = optimizer.benchmark_query(test_incident_stats)
    print(f"\nIncident stats query:")
    print(f"  Time: {elapsed:.2f} ms")
    print(f"  Severity groups: {len(results)}")
    
    def test_search():
        return db.query(models.Log).filter(
            models.Log.message.ilike('%error%')
        ).limit(20).all()
    
    results, elapsed = optimizer.benchmark_query(test_search)
    print(f"\nSearch query:")
    print(f"  Time: {elapsed:.2f} ms")
    print(f"  Results: {len(results)} rows")
    

    def test_log_count():
        return db.query(func.count(models.Log.id)).scalar()
    
    count, elapsed = optimizer.benchmark_query(test_log_count)
    print(f"\nLog count query:")
    print(f"  Time: {elapsed:.2f} ms")
    print(f"  Total logs: {count}")
    
    print("\n" + "="*60)
    print("QUERY PLANS")
    print("="*60)
    
    query = db.query(
        models.Log.service,
        func.count().label('count')
    ).filter(
        models.Log.level == 'ERROR',
        models.Log.timestamp >= datetime.utcnow() - timedelta(minutes=60)
    ).group_by(models.Log.service)
    
    plan = optimizer.analyze_query_plan(query)
    if plan:
        print("\nError stats query plan:")
        if len(plan) > 500:
            print(plan[:500] + "...")
        else:
            print(plan)
    else:
        print("Could not get query plan (may need EXPLAIN privileges)")
    
    db.close()
    
    print("\n" + "="*60)
    print("BENCHMARK COMPLETE")
    print("="*60)

if __name__ == "__main__":
    run_benchmark()