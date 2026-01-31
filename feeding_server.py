from fastmcp import FastMCP
import sqlite3
import datetime
import logging
from typing import List, Optional

# Initialize the MCP server
mcp = FastMCP("FeedingTracker")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FeedingTracker")

# Database setup
DB_FILE = "feeding_data.db"

def init_db():
    """Initialize the SQLite database with the feeding table."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            amount_ml INTEGER,
            feeding_type TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

@mcp.tool()
def record_feeding(amount_ml: int, feeding_type: str = "formula", timestamp: str = "") -> str:
    """
    Record a feeding event.
    
    Args:
        amount_ml: The amount of milk in milliliters.
        feeding_type: The type of feeding (e.g., 'formula', 'breast_milk'). Default is 'formula'.
        timestamp: Optional. The time of feeding in 'YYYY-MM-DD HH:MM:SS' format. 
                   If not provided, defaults to current Beijing Time (UTC+8).
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Handle timestamp: Use provided one or calculate current Beijing time
    if not timestamp:
        # UTC+8 calculation manually to avoid timezone dependency issues
        beijing_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
        timestamp = beijing_time.strftime('%Y-%m-%d %H:%M:%S')

    c.execute(
        "INSERT INTO feedings (timestamp, amount_ml, feeding_type) VALUES (?, ?, ?)",
        (timestamp, amount_ml, feeding_type),
    )
    conn.commit()
    conn.close()
    
    logger.info(f"Recorded feeding: {amount_ml}ml ({feeding_type}) at {timestamp}")
    return f"Successfully recorded feeding of {amount_ml}ml ({feeding_type}) at {timestamp}."

@mcp.tool()
def get_daily_summary() -> dict:
    """
    Get a statistical summary of feedings for the current day (Beijing Time).
    Returns total volume, count, and average amount per feeding.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Get today in Beijing Time
    beijing_now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    today_str = beijing_now.strftime('%Y-%m-%d')
    
    # Query for today's records (Prefix matching for YYYY-MM-DD)
    c.execute('''
        SELECT COUNT(*), SUM(amount_ml), AVG(amount_ml)
        FROM feedings
        WHERE timestamp LIKE ?
    ''', (f"{today_str}%",))
    
    count, total_vol, avg_vol = c.fetchone()
    
    # Get last feeding time
    c.execute('SELECT timestamp FROM feedings ORDER BY timestamp DESC LIMIT 1')
    last_feeding = c.fetchone()
    last_feeding_time = last_feeding[0] if last_feeding else "None"
    
    conn.close()
    
    return {
        "date": today_str,
        "timezone": "Asia/Shanghai (UTC+8)",
        "total_feedings": count or 0,
        "total_volume_ml": total_vol or 0,
        "average_volume_ml": round(avg_vol, 1) if avg_vol else 0,
        "last_feeding_time": last_feeding_time
    }

@mcp.tool()
def get_recent_feedings(limit: int = 5) -> List[dict]:
    """
    Retrieve a list of the most recent feeding records.
    
    Args:
        limit: The number of records to retrieve. Default is 5.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # To return dict-like objects
    c = conn.cursor()
    
    c.execute(
        'SELECT id, timestamp, amount_ml, feeding_type FROM feedings ORDER BY timestamp DESC LIMIT ?',
        (limit,),
    )
    rows = c.fetchall()
    
    feedings = []
    for row in rows:
        feedings.append(dict(row))
    
    conn.close()
    return feedings

if __name__ == "__main__":
    mcp.run(transport="stdio")
