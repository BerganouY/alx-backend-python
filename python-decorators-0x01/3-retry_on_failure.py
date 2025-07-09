#!/usr/bin/env python3
"""
Database Retry Decorator
"""

import time
import sqlite3
import functools
from random import random


def with_db_connection(func):
    """
    Decorator that automatically handles database connections

    Args:
        func: The function to be decorated

    Returns:
        A wrapped function with connection handling
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect('users.db')
        try:
            if 'conn' not in kwargs and not (args and isinstance(args[0], sqlite3.Connection)):
                kwargs['conn'] = conn
            return func(*args, **kwargs)
        finally:
            conn.close()

    return wrapper


def retry_on_failure(retries=3, delay=2):
    """
    Decorator that retries database operations on failure

    Args:
        retries: Number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 2)

    Returns:
        A wrapped function with retry capability
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                    last_exception = e
                    if attempt < retries:
                        # Exponential backoff with jitter
                        sleep_time = delay * (2 ** (attempt - 1)) + (random() * 0.5)
                        print(f"Attempt {attempt} failed. Retrying in {sleep_time:.2f} seconds...")
                        time.sleep(sleep_time)
            print(f"All {retries} attempts failed")
            raise last_exception

        return wrapper

    return decorator


@with_db_connection
@retry_on_failure(retries=3, delay=1)
def fetch_users_with_retry(conn):
    """
    Fetches all users from the database with retry capability

    Args:
        conn: Database connection

    Returns:
        List of all users
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()


if __name__ == "__main__":
    # Example usage
    try:
        users = fetch_users_with_retry()
        print(f"Successfully fetched {len(users)} users")
    except Exception as e:
        print(f"Failed to fetch users: {str(e)}")