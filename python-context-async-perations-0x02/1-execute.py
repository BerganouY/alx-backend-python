#!/usr/bin/env python3
"""
Reusable Query Context Manager
"""

import sqlite3


class ExecuteQuery:
    """Context manager for executing parameterized queries"""

    def __init__(self, db_name, query, params=()):
        self.db_name = db_name
        self.query = query
        self.params = params
        self.conn = None
        self.cursor = None

    def __enter__(self):
        """Execute query when entering context"""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute(self.query, self.params)
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when exiting context"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    # Example usage
    query = "SELECT * FROM users WHERE age > ?"
    with ExecuteQuery('users.db', query, (25,)) as cursor:
        results = cursor.fetchall()
        print("Users older than 25:")
        for row in results:
            print(row)