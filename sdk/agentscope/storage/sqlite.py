"""SQLite storage implementation for AgentScope."""

import json
import logging
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .base import BaseStorage, StorageError, TraceNotFoundError

logger = logging.getLogger(__name__)


class SQLiteStorage(BaseStorage):
    """SQLite storage backend for production use.
    
    Provides persistent storage with ACID guarantees.
    Automatically creates tables and indexes on initialization.
    """
    
    def __init__(self, db_path: str = "agentscope.db"):
        """Initialize SQLite storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self._db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS traces (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        duration_ms REAL,
                        input_query TEXT,
                        tags TEXT,  -- JSON array
                        metadata TEXT,  -- JSON object
                        steps TEXT,  -- JSON array
                        child_trace_ids TEXT,  -- JSON array
                        parent_trace_id TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        total_tokens INTEGER DEFAULT 0,
                        total_latency_ms REAL DEFAULT 0.0,
                        cost_estimate REAL DEFAULT 0.0,
                        llm_call_count INTEGER DEFAULT 0,
                        tool_call_count INTEGER DEFAULT 0
                    )
                """)
                
                # Create indexes for common queries
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_traces_start_time 
                    ON traces(start_time DESC)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_traces_status 
                    ON traces(status)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_traces_name 
                    ON traces(name)
                """)
                
                conn.commit()
                logger.info(f"SQLite storage initialized: {self._db_path}")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize SQLite database: {e}")
            raise StorageError(f"Database initialization failed: {e}") from e
    
    def save_trace(self, trace: Dict[str, Any]) -> str:
        """Save a trace to SQLite."""
        try:
            trace_id = trace.get("id")
            if not trace_id:
                raise StorageError("Trace must have an 'id' field")
            
            with sqlite3.connect(self._db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO traces 
                    (id, name, status, start_time, end_time, duration_ms,
                     input_query, tags, metadata, steps, child_trace_ids, parent_trace_id,
                     total_tokens, total_latency_ms, cost_estimate, llm_call_count, tool_call_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        trace_id,
                        trace.get("name", ""),
                        trace.get("status", ""),
                        trace.get("start_time"),
                        trace.get("end_time"),
                        trace.get("duration_ms"),
                        trace.get("input_query", ""),
                        json.dumps(trace.get("tags", [])),
                        json.dumps(trace.get("metadata", {})),
                        json.dumps(trace.get("steps", [])),
                        json.dumps(trace.get("child_trace_ids", [])),
                        trace.get("parent_trace_id"),
                        trace.get("total_tokens", 0),
                        trace.get("total_latency_ms", 0.0),
                        trace.get("cost_estimate", 0.0),
                        trace.get("llm_call_count", 0),
                        trace.get("tool_call_count", 0),
                    )
                )
                conn.commit()
            
            logger.debug(f"Saved trace {trace_id} to SQLite (tokens={trace.get('total_tokens', 0)}, cost={trace.get('cost_estimate', 0.0)})")
            return trace_id
            
        except sqlite3.Error as e:
            logger.error(f"Failed to save trace: {e}")
            raise StorageError(f"Failed to save trace: {e}") from e
    
    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a trace from SQLite."""
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM traces WHERE id = ?",
                    (trace_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return self._row_to_dict(row)
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get trace {trace_id}: {e}")
            raise StorageError(f"Failed to get trace: {e}") from e
    
    def list_traces(
        self,
        limit: int = 100,
        offset: int = 0,
        tags: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List traces from SQLite with filtering."""
        try:
            query = "SELECT * FROM traces WHERE 1=1"
            params = []
            
            # Build dynamic query
            if start_time:
                query += " AND start_time >= ?"
                params.append(start_time.isoformat())
            
            if end_time:
                query += " AND start_time <= ?"
                params.append(end_time.isoformat())
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            # Note: Tag filtering is done in Python for simplicity
            # For production, consider JSON1 extension or separate tags table
            
            query += " ORDER BY start_time DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            with sqlite3.connect(self._db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                traces = [self._row_to_dict(row) for row in rows]
                
                # Filter by tags in Python
                if tags:
                    traces = [
                        t for t in traces
                        if any(tag in t.get("tags", []) for tag in tags)
                    ]
                
                return traces
                
        except sqlite3.Error as e:
            logger.error(f"Failed to list traces: {e}")
            raise StorageError(f"Failed to list traces: {e}") from e
    
    def count_traces(
        self,
        tags: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> int:
        """Count matching traces."""
        try:
            query = "SELECT COUNT(*) FROM traces WHERE 1=1"
            params = []
            
            if start_time:
                query += " AND start_time >= ?"
                params.append(start_time.isoformat())
            
            if end_time:
                query += " AND start_time <= ?"
                params.append(end_time.isoformat())
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.execute(query, params)
                return cursor.fetchone()[0]
                
        except sqlite3.Error as e:
            logger.error(f"Failed to count traces: {e}")
            raise StorageError(f"Failed to count traces: {e}") from e
    
    def delete_trace(self, trace_id: str) -> bool:
        """Delete a trace from SQLite."""
        try:
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM traces WHERE id = ?",
                    (trace_id,)
                )
                conn.commit()
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.debug(f"Deleted trace {trace_id}")
                return deleted
                
        except sqlite3.Error as e:
            logger.error(f"Failed to delete trace {trace_id}: {e}")
            raise StorageError(f"Failed to delete trace: {e}") from e
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            with sqlite3.connect(self._db_path) as conn:
                # Count traces
                cursor = conn.execute("SELECT COUNT(*) FROM traces")
                total = cursor.fetchone()[0]
                
                # Count by status
                cursor = conn.execute(
                    "SELECT status, COUNT(*) FROM traces GROUP BY status"
                )
                by_status = dict(cursor.fetchall())
                
                # Database file size
                db_size = Path(self._db_path).stat().st_size
                
                return {
                    "backend": "sqlite",
                    "db_path": self._db_path,
                    "total_traces": total,
                    "by_status": by_status,
                    "storage_size_bytes": db_size,
                }
                
        except sqlite3.Error as e:
            logger.error(f"Failed to get stats: {e}")
            raise StorageError(f"Failed to get stats: {e}") from e
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert SQLite row to dictionary."""
        result = dict(row)
        
        # Parse JSON fields
        for field in ["tags", "metadata", "steps", "child_trace_ids"]:
            if result.get(field):
                try:
                    result[field] = json.loads(result[field])
                except json.JSONDecodeError:
                    result[field] = []
        
        return result
