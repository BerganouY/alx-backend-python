import sqlite3
import functools
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#### decorator to manage database transactions

def transactional(func):
    """
    Decorator that manages database transactions.

    This decorator ensures that all database operations within the function
    are executed as a single transaction, with automatic commit on success
    and rollback on failure.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Assume the first argument is the database connection
        conn = args[0] if args else None

        if conn is None:
            raise ValueError("Database connection is required as the first argument")

        try:
            # Execute the function (transaction starts implicitly)
            result = func(*args, **kwargs)

            # Commit transaction on success
            conn.commit()
            logger.info("Transaction committed successfully")
            return result

        except Exception as e:
            # Rollback transaction on error
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise  # Re-raise the exception

    return wrapper


# Helper decorator to combine with connection handling
def with_db_connection(func):
    """
    Decorator that automatically handles database connections.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect('users.db')
        try:
            result = func(conn, *args, **kwargs)
            return result
        finally:
            conn.close()

    return wrapper


# Example usage
@with_db_connection
@transactional
def create_user(conn, name, email):
    """
    Create a new user in the database.

    Args:
        conn: Database connection
        name: User's name
        email: User's email

    Returns:
        ID of the newly created user
    """
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
    return cursor.lastrowid


@with_db_connection
@transactional
def update_user_email(conn, user_id, new_email):
    """
    Update a user's email address.

    Args:
        conn: Database connection
        user_id: ID of the user to update
        new_email: New email address

    Raises:
        ValueError: If user is not found
    """
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, user_id))

    if cursor.rowcount == 0:
        raise ValueError(f"User with id {user_id} not found")


@with_db_connection
@transactional
def delete_user(conn, user_id):
    """
    Delete a user from the database.

    Args:
        conn: Database connection
        user_id: ID of the user to delete

    Raises:
        ValueError: If user is not found
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

    if cursor.rowcount == 0:
        raise ValueError(f"User with id {user_id} not found")


@with_db_connection
@transactional
def transfer_booking(conn, from_user_id, to_user_id, booking_id):
    """
    Transfer a booking from one user to another.
    This demonstrates a more complex transaction that could fail.

    Args:
        conn: Database connection
        from_user_id: ID of the current booking owner
        to_user_id: ID of the new booking owner
        booking_id: ID of the booking to transfer
    """
    cursor = conn.cursor()

    # Check if the booking exists and belongs to from_user
    cursor.execute("SELECT * FROM bookings WHERE id = ? AND user_id = ?",
                   (booking_id, from_user_id))
    booking = cursor.fetchone()

    if not booking:
        raise ValueError(f"Booking {booking_id} not found for user {from_user_id}")

    # Check if the target user exists
    cursor.execute("SELECT * FROM users WHERE id = ?", (to_user_id,))
    target_user = cursor.fetchone()

    if not target_user:
        raise ValueError(f"Target user {to_user_id} not found")

    # Update the booking
    cursor.execute("UPDATE bookings SET user_id = ? WHERE id = ?",
                   (to_user_id, booking_id))

    # Log the transfer
    cursor.execute("""
        INSERT INTO booking_transfers (booking_id, from_user_id, to_user_id, transfer_date)
        VALUES (?, ?, ?, datetime('now'))
    """, (booking_id, from_user_id, to_user_id))


# Test the transaction decorator
if __name__ == "__main__":
    # Initialize database with sample tables
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            property_id INTEGER,
            start_date DATE,
            end_date DATE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS booking_transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER,
            from_user_id INTEGER,
            to_user_id INTEGER,
            transfer_date TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings (id)
        )
    ''')

    conn.commit()
    conn.close()

    # Test successful transaction
    try:
        user_id = create_user("John Doe", "john@example.com")
        print(f"Successfully created user with ID: {user_id}")
    except Exception as e:
        print(f"Error creating user: {e}")

    # Test failed transaction (duplicate email)
    try:
        user_id = create_user("Jane Doe", "john@example.com")  # Same email
        print(f"Created user with ID: {user_id}")
    except Exception as e:
        print(f"Expected error (duplicate email): {e}")

    # Test update
    try:
        update_user_email(1, "john.updated@example.com")
        print("Successfully updated user email")
    except Exception as e:
        print(f"Error updating email: {e}")

    # Test update with non-existent user (should rollback)
    try:
        update_user_email(999, "nonexistent@example.com")
        print("Updated non-existent user")
    except Exception as e:
        print(f"Expected error (user not found): {e}")