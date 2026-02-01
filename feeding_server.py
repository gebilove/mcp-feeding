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
import os
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feeding_data.db")
DB_FILE = os.getenv("FEEDING_DB_PATH", DEFAULT_DB_PATH)

def init_db(ctx=None):
    """Initialize the SQLite database with the feeding table."""
    try:
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
            c.execute('''
                CREATE TABLE IF NOT EXISTS diaper_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    diaper_type TEXT DEFAULT 'pee'
                )
            ''')
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to init DB: {e}")
        raise e

# Initialize DB on startup
# Handled by @mcp.on_startup

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
def get_last_feeding_info() -> dict:
    """
    Get detailed information about the last feeding, including time elapsed since then.
    Useful for answering "When was the last feeding?" or "How long has it been?".
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            c.execute('SELECT timestamp, amount_ml, feeding_type FROM feedings ORDER BY timestamp DESC LIMIT 1')
            row = c.fetchone()
            
            if not row:
                return {"error": "No feeding records found."}
            
            last_feeding = dict(row)
            timestamp_str = last_feeding['timestamp']
            
            # Calculate time difference
            # Note: stored timestamp is conceptually Beijing Time string
            try:
                last_time = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                beijing_now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
                
                diff = beijing_now - last_time
                minutes_total = int(diff.total_seconds() / 60)
                
                hours = minutes_total // 60
                mins = minutes_total % 60
                
                if hours > 0:
                    desc = f"{hours}小时{mins}分钟前"
                else:
                    desc = f"{mins}分钟前"
                    
                last_feeding['minutes_since'] = minutes_total
                last_feeding['description'] = desc
                last_feeding['current_time'] = beijing_now.strftime('%Y-%m-%d %H:%M:%S')
                
            except Exception as e:
                logger.error(f"Time calc error: {e}")
                last_feeding['description'] = "时间计算错误"
                
            return last_feeding

    except Exception as e:
        logger.error(f"Failed to get last feeding info: {e}")
        return {"error": str(e)}



@mcp.tool()
def delete_last_feeding() -> str:
    """
    Delete the last feeding record.
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute('DELETE FROM feedings WHERE id = (SELECT id FROM feedings ORDER BY timestamp DESC LIMIT 1)')
            conn.commit()
        
        logger.info("Deleted last feeding record")
        return "Successfully deleted last feeding record."
    except Exception as e:
        logger.error(f"Failed to delete last feeding: {e}")
        return f"Error deleting last feeding: {str(e)}"

@mcp.tool()
def record_diaper_change(
    diaper_type: str = "pee",
    timestamp: str = "",
) -> str:
    """
    Record a diaper change event.
    
    Args:
        diaper_type: The type of diaper change ('pee', 'poop', 'both'). Default is 'pee'.
        timestamp: Optional. The time of change in 'YYYY-MM-DD HH:MM:SS' format.
                   If not provided, defaults to current Beijing Time (UTC+8).
    """
    try:
        if timestamp:
            datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

        if not timestamp:
            # UTC+8 calculation
            beijing_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
            timestamp = beijing_time.strftime('%Y-%m-%d %H:%M:%S')

        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO diaper_changes (timestamp, diaper_type) VALUES (?, ?)",
                (timestamp, diaper_type),
            )
            conn.commit()
        
        logger.info(f"Recorded diaper change: {diaper_type} at {timestamp}")
        return f"Successfully recorded diaper change ({diaper_type}) at {timestamp}."
    except Exception as e:
        logger.error(f"Failed to record diaper change: {e}")
        return f"Error recording diaper change: {str(e)}"

@mcp.tool()
def get_daily_diaper_summary() -> dict:
    """
    Get a statistical summary of diaper changes for the current day (Beijing Time).
    Returns counts for each type.
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            
            beijing_now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
            today_str = beijing_now.strftime('%Y-%m-%d')
            tomorrow_str = (beijing_now + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            start_ts = f"{today_str} 00:00:00"
            end_ts = f"{tomorrow_str} 00:00:00"
            
            c.execute('''
                SELECT diaper_type, COUNT(*)
                FROM diaper_changes
                WHERE timestamp >= ? AND timestamp < ?
                GROUP BY diaper_type
            ''', (start_ts, end_ts))
            
            rows = c.fetchall()
            stats = {row[0]: row[1] for row in rows}
            
            total = sum(stats.values())
            
            # Get last diaper change time
            c.execute('SELECT timestamp FROM diaper_changes ORDER BY timestamp DESC LIMIT 1')
            last_change = c.fetchone()
            last_change_time = last_change[0] if last_change else "None"
        
        return {
            "date": today_str,
            "timezone": "Asia/Shanghai (UTC+8)",
            "total_changes": total,
            "counts": stats,
            "last_change_time": last_change_time
        }
    except Exception as e:
        logger.error(f"Failed to get daily diaper summary: {e}")
        return {
            "error": str(e),
            "date": "",
            "total_changes": 0,
            "counts": {},
            "last_change_time": "None"
        }

@mcp.tool()
def get_last_diaper_change_info() -> dict:
    """
    Get detailed information about the last diaper change, including time elapsed since then.
    Useful for answering "When was the last diaper change?" or "How long has it been?".
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            c.execute('SELECT timestamp, diaper_type FROM diaper_changes ORDER BY timestamp DESC LIMIT 1')
            row = c.fetchone()
            
            if not row:
                return {"error": "No diaper change records found."}
            
            last_change = dict(row)
            timestamp_str = last_change['timestamp']
            
            # Calculate time difference
            try:
                last_time = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                beijing_now = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
                
                diff = beijing_now - last_time
                minutes_total = int(diff.total_seconds() / 60)
                
                hours = minutes_total // 60
                mins = minutes_total % 60
                
                if hours > 0:
                    desc = f"{hours}小时{mins}分钟前"
                else:
                    desc = f"{mins}分钟前"
                    
                last_change['minutes_since'] = minutes_total
                last_change['description'] = desc
                last_change['current_time'] = beijing_now.strftime('%Y-%m-%d %H:%M:%S')
                
            except Exception as e:
                logger.error(f"Time calc error: {e}")
                last_change['description'] = "时间计算错误"
                
            return last_change

    except Exception as e:
        logger.error(f"Failed to get last diaper change info: {e}")
        return {"error": str(e)}

@mcp.tool()
def delete_last_diaper_change() -> str:
    """
    Delete the last diaper change record.
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute('DELETE FROM diaper_changes WHERE id = (SELECT id FROM diaper_changes ORDER BY timestamp DESC LIMIT 1)')
            conn.commit()
        
        logger.info("Deleted last diaper change record")
        return "Successfully deleted last diaper change record."
    except Exception as e:
        logger.error(f"Failed to delete last diaper change: {e}")
        return f"Error deleting last diaper change: {str(e)}"

if __name__ == "__main__":
    # Initialize DB manually since @mcp.on_startup might not be available
    init_db()
    mcp.run(transport="stdio")
