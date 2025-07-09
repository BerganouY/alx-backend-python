import sqlite3
import functools
import time
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#### decorator to retry database operations on failure

def retry_on_failure(retries=3, delay=1):
    """
    Decorator that retries database operations on failure.

    Args:
        retries (int): Number of retry attempts (default: 3)
        delay (int): Delay between retries in seconds (default: 1)

    Returns:
        Function decorator that implements retry logic
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt < retries:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {retries + 1} attempts failed. Final error: {e}")

            # Re-raise the last exception if all retries failed
            raise last_exception

        return wrapper

    return decorator


# Helper decorator for database connections
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


# Example usage with different retry configurations

@with_db_connection
@retry_on_failure(retries=3, delay=1)
def fetch_user_by_id(conn, user_id):
    """
    Fetch a user by ID with retry logic.

    Args:
        conn: Database connection
        user_id: ID of the user to fetch

    Returns:
        User record or None if not found
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()


@with_db_connection
@retry_on_failure(retries=5, delay=2)
def create_user_with_retry(conn, name, email):
    """
    Create a user with more aggressive retry policy.

    Args:
        conn: Database connection
        name: User's name
        email: User's email

    Returns:
        ID of the newly created user
    """
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
    conn.commit()
    return cursor.lastrowid


@with_db_connection
@retry_on_failure(retries=2, delay=0.5)
def update_user_with_retry(conn, user_id, name=None, email=None):
    """
    Update user information with retry logic.

    Args:
        conn: Database connection
        user_id: ID of the user to update
        name: New name (optional)
        email: New email (optional)

    Raises:
        ValueError: If user is not found
    """
    cursor = conn.cursor()

    # Build dynamic update query
    updates = []
    params = []

    if name:
        updates.append("name = ?")
        params.append(name)

    if email:
        updates.append("email = ?")
        params.append(email)

    if not updates:
        raise ValueError("At least one field must be provided for update")

    params.append(user_id)
    query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"

    cursor.execute(query, params)

    if cursor.rowcount == 0:
        raise ValueError(f"User with id {user_id} not found")

    conn.commit()


# Advanced retry decorator with exponential backoff
def retry_with_exponential_backoff(max_retries=3, base_delay=1, max_delay=60):
    """
    Decorator that implements exponential backoff retry strategy.

    Args:
        max_retries (int): Maximum number of retry attempts
        base_delay (int): Base delay in seconds
        max_delay (int): Maximum delay in seconds
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt < max_retries:
                        # Calculate exponential backoff delay
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        # Add some jitter to prevent thundering herd
                        jitter = random.uniform(0, 0.1) * delay
                        total_delay = delay + jitter

                        logger.warning(f"Attempt {attempt + 1} failed: {e}. "
                                       f"Retrying in {total_delay:.2f} seconds...")
                        time.sleep(total_delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed. Final error: {e}")

            raise last_exception

        return wrapper

    return decorator


# Example with exponential backoff
@with_db_connection
@retry_with_exponential_backoff(max_retries=4, base_delay=1, max_delay=30)
def complex_database_operation(conn, user_id):
    """
    Example of a complex operation that might fail and need sophisticated retry logic.

    Args:
        conn: Database connection
        user_id: ID of the user

    Returns:
        Dictionary with operation results
    """
    cursor = conn.cursor()

    # Simulate a complex operation that might fail
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        raise ValueError(f"User {user_id} not found")

    # Simulate some processing that might fail
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE user_id = ?", (user_id,))
    booking_count = cursor.fetchone()[0]

    return {
        "user_id": user_id,
        "user_name": user[1],  # Assuming name is in column 1
        "booking_count": booking_count,
        "status": "success"
    }


# Conditional retry decorator
def retry_on_specific_exceptions(exceptions, retries=3, delay=1):
    """
    Decorator that only retries on specific exceptions.

    Args:
        exceptions: Tuple of exception types to retry on
        retries (int): Number of retry attempts
        delay (int): Delay between retries in seconds
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < retries:
                        logger.warning(f"Attempt {attempt + 1} failed with {type(e).__name__}: {e}. "
                                       f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {retries + 1} attempts failed. Final error: {e}")
                except Exception as e:
                    # Don't retry on unexpected exceptions
                    logger.error(f"Non-retryable exception occurred: {type(e).__name__}: {e}")
                    raise

            raise last_exception

        return wrapper

    return decorator


# Example with specific exception handling
@with_db_connection
@retry_on_specific_exceptions((sqlite3.OperationalError, sqlite3.DatabaseError), retries=3, delay=1)
def database_operation_with_specific_retry(conn, query, params=None):
    """
    Execute a database operation with retry only on specific database errors.

    Args:
        conn: Database connection
        query: SQL query to execute
        params: Query parameters (optional)

    Returns:
        Query results
    """
    cursor = conn.cursor()

    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)

    # For SELECT queries, return results
    if query.strip().upper().startswith('SELECT'):
        return cursor.fetchall()

    # For other queries, commit and return affected rows
    conn.commit()
    return cursor.rowcount


# Function to simulate database errors for testing
def simulate_database_error():
    """
    Simulate random database errors for testing retry mechanism.
    """
    error_types = [
        sqlite3.OperationalError("database is locked"),
        sqlite3.DatabaseError("database disk image is malformed"),
        ConnectionError("network connection failed"),
        sqlite3.IntegrityError("UNIQUE constraint failed")
    ]

    if random.random() < 0.7:  # 70% chance of error
        raise random.choice(error_types)

    return "Operation successful"


@retry_on_failure(retries=3, delay=1)
def unreliable_operation():
    """
    Simulate an unreliable operation for testing.
    """
    logger.info("Attempting unreliable operation...")
    return simulate_database_error()


# Test the retry mechanisms
if __name__ == "__main__":
    # Initialize database
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

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

    # Insert sample data
    sample_users = [
        ('Alice Johnson', 'alice@example.com'),
        ('Bob Smith', 'bob@test.com'),
        ('Charlie Brown', 'charlie@example.com')
    ]

    cursor.executemany('INSERT OR IGNORE INTO users (name, email) VALUES (?, ?)', sample_users)
    conn.commit()
    conn.close()

    print("=== Testing Basic Retry Mechanism ===")

    # Test successful operation
    try:
        user = fetch_user_by_id(1)
        print(f"Successfully fetched user: {user}")
    except Exception as e:
        print(f"Error fetching user: {e}")

    # Test create user with retry
    try:
        user_id = create_user_with_retry("John Doe", "john@example.com")
        print(f"Successfully created user with ID: {user_id}")
    except Exception as e:
        print(f"Error creating user: {e}")

    # Test update with retry
    try:
        update_user_with_retry(1, name="Alice Updated")
        print("Successfully updated user")
    except Exception as e:
        print(f"Error updating user: {e}")

    print("\n=== Testing Exponential Backoff ===")

    try:
        result = complex_database_operation(1)
        print(f"Complex operation result: {result}")
    except Exception as e:
        print(f"Error in complex operation: {e}")

    print("\n=== Testing Specific Exception Retry ===")

    try:
        result = database_operation_with_specific_retry("SELECT * FROM users WHERE id = ?", (1,))
        print(f"Query result: {result}")
    except Exception as e:
        print(f"Error in specific retry operation: {e}")

    print("\n=== Testing Unreliable Operation ===")

    try:
        result = unreliable_operation()
        print(f"Unreliable operation result: {result}")
    except Exception as e:
        print(f"Unreliable operation failed: {e}")

    print("\n=== Testing Non-Retryable Error ===")

    try:
        # This should fail immediately without retry (non-existent user)
        update_user_with_retry(999, name="Non-existent User")
    except Exception as e:
        print(f"Expected error for non-existent user: {e}")