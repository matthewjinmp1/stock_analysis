#!/usr/bin/env python3
"""
Base repository class with common database operations.
"""
import sqlite3
import os
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'consolidated.db')

class BaseRepository:
    """Base repository class with common database operations."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def get_cursor(self):
        """Context manager for database cursors."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except:
                conn.rollback()
                raise

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as dicts."""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def execute_single(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Execute a query that returns a single row."""
        results = self.execute_query(query, params)
        return results[0] if results else None

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT, UPDATE, or DELETE query."""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT query and return the last row ID."""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.lastrowid