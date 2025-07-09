#!/usr/bin/env python3
"""
Transaction Management Decorator
"""

import sqlite3
import functools


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


def transactional(func):
    """
    Decorator that manages database transactions

    Commits if the function succeeds, rolls back if it raises an exception

    Args:
        func: The function to be decorated

    Returns:
        A wrapped function with transaction handling
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Find the connection in args or kwargs
        conn = None
        for arg in args:
            if isinstance(arg, sqlite3.Connection):
                conn = arg
                break
        if not conn:
            conn = kwargs.get('conn')

        if not conn:
            raise ValueError("No database connection found")

        try:
            result = func(*args, **kwargs)
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            raise e

    return wrapper


@with_db_connection
@transactional
def update_user_email(conn, user_id, new_email):
    """
    Updates a user's email address

    Args:
        conn: Database connection
        user_id: ID of the user to update
        new_email: New email address

    Returns:
        Number of rows affected
    """
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, user_id))
    return cursor.rowcount


if __name__ == "__main__":
    # Example usage
    try:
        rows_updated = update_user_email(
            user_id=1,
            new_email='Crawford_Cartwright@hotmail.com'
        )
        print(f"Successfully updated {rows_updated} row(s)")
    except Exception as e:
        print(f"Transaction failed: {str(e)}")