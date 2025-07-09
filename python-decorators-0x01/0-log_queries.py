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
    import sqlite3
    import functools

    #### decorator to log SQL queries

    def log_queries(func):
        """
        Decorator that logs SQL queries executed by any function.

        This decorator wraps a function and logs the SQL query parameter
        before executing the function.
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract the query from arguments
            # Assuming the query is the first argument or a named parameter
            query = None

            # Check if query is in kwargs
            if 'query' in kwargs:
                query = kwargs['query']
            # Check if query is in args (assuming it's the first argument)
            elif args:
                query = args[0]

            # Log the query
            if query:
                print(f"Executing query: {query}")

            # Execute the original function
            return func(*args, **kwargs)

        return wrapper

    @log_queries
    def fetch_all_users(query):
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results

    #### fetch users while logging the query
    users = fetch_all_users(query="SELECT * FROM users")
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