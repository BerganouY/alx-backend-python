#!/usr/bin/env python3
"""
Database Query Logger Decorator
"""

import sqlite3
import functools


def log_queries(func):
    """
    Decorator that logs SQL queries executed by any function

    Args:
        func: The function to be decorated

    Returns:
        A wrapped function that logs queries
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extract query from args or kwargs
        query = kwargs.get('query', args[0] if args else None)

        # Log the query if found
        if query:
            print(f"Executing query: {query}")
        else:
            print("Warning: No query detected to log")

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