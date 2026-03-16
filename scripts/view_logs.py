# scripts/view_logs.py
import argparse
from pathlib import Path
import re
from datetime import datetime

LOG_DIR = Path(__file__).parent.parent / "backend" / "logs"

def view_logs(log_type="app", lines=50, level=None, search=None):
    """View logs with filters"""
    
    log_files = {
        "app": LOG_DIR / "app.log",
        "error": LOG_DIR / "error.log",
        "detector": LOG_DIR / "detector.log",
        "api": LOG_DIR / "api.log",
        "all": None
    }
    
    if log_type == "all":
        files = list(LOG_DIR.glob("*.log"))
    else:
        files = [log_files.get(log_type)]
        if not files[0].exists():
            print(f"❌ Log file not found: {files[0]}")
            return
    
    for file in files:
        if not file or not file.exists():
            continue
            
        print(f"\n{'='*60}")
        print(f"📄 {file.name}")
        print('='*60)
        
        with open(file, 'r') as f:
            all_lines = f.readlines()
            shown = 0
            
            for line in reversed(all_lines):
                # Apply filters
                if level and level.upper() not in line:
                    continue
                if search and search.lower() not in line.lower():
                    continue
                    
                print(line.strip())
                shown += 1
                if shown >= lines:
                    break
            
            if shown == 0:
                print("No matching logs found")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View logs")
    parser.add_argument("--type", "-t", default="app", 
                       choices=["app", "error", "detector", "api", "all"])
    parser.add_argument("--lines", "-n", type=int, default=50)
    parser.add_argument("--level", "-l", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--search", "-s", help="Search term")
    
    args = parser.parse_args()
    view_logs(args.type, args.lines, args.level, args.search)