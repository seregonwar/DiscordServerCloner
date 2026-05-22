import json
import os
from datetime import datetime

STATS_FILE = "logs/cloning_stats.json"

def save_stats(stats_data: dict):
    """Saves a cloning session stats to a central JSON file."""
    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    
    all_stats = []
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                all_stats = json.load(f)
        except:
            all_stats = []
            
    # Add timestamp if not present
    if "timestamp" not in stats_data:
        stats_data["timestamp"] = datetime.now().isoformat()
        
    all_stats.append(stats_data)
    
    # Keep only last 100 sessions to avoid huge file
    if len(all_stats) > 100:
        all_stats = all_stats[-100:]
        
    with open(STATS_FILE, "w") as f:
        json.dump(all_stats, f, indent=4)

def load_all_stats():
    """Loads all cloning sessions stats."""
    if not os.path.exists(STATS_FILE):
        return []
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except:
        return []
