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
    with sqlite3.connect(DB_FILE) as conn:
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

# Initialize DB on startup
init_db()

@mcp.tool()
def record_feeding(
    amount_ml: int,
    feeding_type: str = "formula",
    timestamp: str = "",
) -> str:
    """
    Record a feeding event.
    
    Args:
        amount_ml: The amount of milk in milliliters.
        feeding_type: The type of feeding (e.g., 'formula', 'breast_milk'). Default is 'formula'.
        timestamp: Optional. The time of feeding in 'YYYY-MM-DD HH:MM:SS' format. 
                   If not provided, defaults to current Beijing Time (UTC+8).
    """
    try:
        if timestamp:
            datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

        # Handle timestamp: Use provided one or calculate current Beijing time
        if not timestamp:
            # UTC+8 calculation manually to avoid timezone dependency issues
            beijing_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
            timestamp = beijing_time.strftime('%Y-%m-%d %H:%M:%S')

        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO feedings (timestamp, amount_ml, feeding_type) VALUES (?, ?, ?)",
                (timestamp, amount_ml, feeding_type),
            )
            conn.commit()
        
        logger.info(f"Recorded feeding: {amount_ml}ml ({feeding_type}) at {timestamp}")
        return f"Successfully recorded feeding of {amount_ml}ml ({feeding_type}) at {timestamp}."
    except Exception as e:
        logger.error(f"Failed to record feeding: {e}")
        return f"Error recording feeding: {str(e)}"

@mcp.tool()
def get_daily_summary() -> dict:
    """
    Get a statistical summary of feedings for the current day (Beijing Time).
    Returns total volume, count, and average amount per feeding.
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            
            # Get today in Beijing Time
            beijing_now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
            today_str = beijing_now.strftime('%Y-%m-%d')
            tomorrow_str = (beijing_now + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            start_ts = f"{today_str} 00:00:00"
            end_ts = f"{tomorrow_str} 00:00:00"
            
            # Query for today's records using date range (more precise than LIKE)
            c.execute('''
                SELECT COUNT(*), SUM(amount_ml), AVG(amount_ml)
                FROM feedings
                WHERE timestamp >= ? AND timestamp < ?
            ''', (start_ts, end_ts))
            
            count, total_vol, avg_vol = c.fetchone()
            
            # Get last feeding time
            c.execute('SELECT timestamp FROM feedings ORDER BY timestamp DESC LIMIT 1')
            last_feeding = c.fetchone()
            last_feeding_time = last_feeding[0] if last_feeding else "None"
        
        return {
            "date": today_str,
            "timezone": "Asia/Shanghai (UTC+8)",
            "total_feedings": count or 0,
            "total_volume_ml": total_vol or 0,
            "average_volume_ml": round(avg_vol, 1) if avg_vol else 0,
            "last_feeding_time": last_feeding_time
        }
    except Exception as e:
        logger.error(f"Failed to get daily summary: {e}")
        return {
            "error": str(e),
            "date": "",
            "timezone": "Asia/Shanghai (UTC+8)",
            "total_feedings": 0,
            "total_volume_ml": 0,
            "average_volume_ml": 0,
            "last_feeding_time": "None"
        }

@mcp.tool()
def get_recent_feedings(limit: int = 5) -> List[dict]:
    """
    Retrieve a list of the most recent feeding records.
    
    Args:
        limit: The number of records to retrieve. Default is 5.
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row  # To return dict-like objects
            c = conn.cursor()
            
            c.execute(
                'SELECT id, timestamp, amount_ml, feeding_type FROM feedings ORDER BY timestamp DESC LIMIT ?',
                (limit,),
            )
            rows = c.fetchall()
            
            feedings = [dict(row) for row in rows]
        
        return feedings
    except Exception as e:
        logger.error(f"Failed to get recent feedings: {e}")
        return []

@mcp.tool()
def delete_last_feeding() -> str:
    """
    Delete the last feeding record.
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute('DELETE FROM feedings ORDER BY timestamp DESC LIMIT 1')
            conn.commit()
        
        logger.info("Deleted last feeding record")
        return "Successfully deleted last feeding record."
    except Exception as e:
        logger.error(f"Failed to delete last feeding: {e}")
        return f"Error deleting last feeding: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
