import sqlite3
import functools


#### decorator to handle database connections

def with_db_connection(func):
    """
    Decorator that automatically handles database connections.

    This decorator opens a database connection before executing the function
    and ensures it's properly closed afterward, eliminating boilerplate code.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Open database connection
        conn = sqlite3.connect('users.db')
        try:
            # Pass the connection as the first argument to the function
            result = func(conn, *args, **kwargs)
            return result
        finally:
            # Ensure connection is always closed, even if an exception occurs
            conn.close()

    return wrapper


# Example usage
@with_db_connection
def get_user_by_id(conn, user_id):
    """
    Retrieve a user by their ID.

    Args:
        conn: Database connection (automatically provided by decorator)
        user_id: ID of the user to retrieve

    Returns:
        User record or None if not found
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()


@with_db_connection
def get_all_users(conn):
    """
    Retrieve all users from the database.

    Args:
        conn: Database connection (automatically provided by decorator)

    Returns:
        List of all user records
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()


# Test the decorator
if __name__ == "__main__":
    # These functions will automatically get a database connection
    user = get_user_by_id(1)
    print(f"User: {user}")

    all_users = get_all_users()
    print(f"Total users: {len(all_users)}")