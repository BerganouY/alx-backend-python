#!/usr/bin/env python3
"""
Database Connection Context Manager
"""

import sqlite3


class DatabaseConnection:
    """Custom context manager for database connections"""

    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None

    def __enter__(self):
        """Open connection when entering context"""
        self.conn = sqlite3.connect(self.db_name)
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close connection when exiting context"""
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    # Example usage
    with DatabaseConnection('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
        print("Users:")
        for row in results:
            print(row)