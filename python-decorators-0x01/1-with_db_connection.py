#!/usr/bin/env python3
"""
Database Connection Handler Decorator
"""

import sqlite3
import functools


def with_db_connection(func):
    """
    Decorator that automatically handles database connections

    Opens a connection, passes it to the decorated function,
    and ensures the connection is closed afterward

    Args:
        func: The function to be decorated

    Returns:
        A wrapped function with connection handling
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Open a new database connection
        conn = sqlite3.connect('users.db')
        try:
            # Pass the connection as the first argument if not already provided
            if 'conn' not in kwargs and not (args and isinstance(args[0], sqlite3.Connection)):
                kwargs['conn'] = conn

            # Execute the function
            result = func(*args, **kwargs)

            # Commit any changes
            conn.commit()
            return result
        except Exception as e:
            # Rollback on error
            conn.rollback()
            raise e
        finally:
            # Always close the connection
            conn.close()

    return wrapper


@with_db_connection
def get_user_by_id(conn, user_id):
    """
    Gets a user by their ID

    Args:
        conn: Database connection (automatically provided by decorator)
        user_id: ID of the user to retrieve

    Returns:
        The user record or None if not found
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()


if __name__ == "__main__":
    # Example usage
    user = get_user_by_id(user_id=1)
    print(user)