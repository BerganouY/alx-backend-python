#!/usr/bin/env python3
"""
Database Query Logger Decorator
"""

import sqlite3
import functools
import time


def log_queries(func):
    """
    Decorator that logs SQL queries with timestamps before execution

    Args:
        func: The function to be decorated

    Returns:
        A wrapped function that logs queries with timestamps
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract the query from either args or kwargs
        query = kwargs.get('query', args[0] if args and isinstance(args[0], str) else None)

        # Get current timestamp using time module
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

        # Log the query with timestamp if found
        if query:
            print(f"[{timestamp}] Executing query: {query}")
        else:
            print(f"[{timestamp}] Warning: No query detected to log")

        # Execute the original function
        return func(*args, **kwargs)

    return wrapper


@log_queries
def fetch_all_users(query):
    """
    Fetches all users from the database

    Args:
        query: SQL query string

    Returns:
        List of user records
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


if __name__ == "__main__":
    # Example usage
    users = fetch_all_users(query="SELECT * FROM users")
    print(f"Retrieved {len(users)} users")