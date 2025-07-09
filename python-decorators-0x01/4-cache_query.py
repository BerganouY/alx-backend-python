import sqlite3
import functools
import time
import logging
import hashlib
import json
import pickle
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global cache for storing query results
query_cache = {}


#### decorator to cache database query results

def cache_query(expiration_time=60):
    """
    Decorator that caches query results to optimize database performance.

    Args:
        expiration_time (int): Cache expiration time in seconds (default: 60)

    Returns:
        Function decorator that implements caching logic
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key based on function name and arguments
            cache_key = _generate_cache_key(func.__name__, args, kwargs)

            # Check if result is in cache and not expired
            if cache_key in query_cache:
                cached_result, timestamp = query_cache[cache_key]
                if time.time() - timestamp < expiration_time:
                    logger.info(f"Cache hit for query: {func.__name__}")
                    return cached_result
                else:
                    # Remove expired cache entry
                    del query_cache[cache_key]
                    logger.info(f"Cache expired for query: {func.__name__}")

            # Execute function and cache result
            logger.info(f"Cache miss for query: {func.__name__} - executing query")
            result = func(*args, **kwargs)

            # Cache the result
            query_cache[cache_key] = (result, time.time())
            logger.info(f"Query result cached for: {func.__name__}")

            return result

        return wrapper

    return decorator


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Generate a unique cache key based on function name and arguments.

    Args:
        func_name: Name of the function
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Unique cache key string
    """
    # Create a string representation of arguments
    args_str = str(args)
    kwargs_str = str(sorted(kwargs.items()))

    # Combine function name and arguments
    key_data = f"{func_name}:{args_str}:{kwargs_str}"

    # Generate hash for consistent key length
    return hashlib.md5(key_data.encode()).hexdigest()


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


# Cache management functions
def clear_cache():
    """Clear all cached query results."""
    global query_cache
    query_cache.clear()
    logger.info("Cache cleared")


def get_cache_stats():
    """Get cache statistics."""
    total_entries = len(query_cache)
    current_time = time.time()
    expired_entries = 0

    for key, (result, timestamp) in query_cache.items():
        if current_time - timestamp > 60:  # Assuming default expiration
            expired_entries += 1

    return {
        "total_entries": total_entries,
        "expired_entries": expired_entries,
        "active_entries": total_entries - expired_entries
    }


def remove_expired_cache_entries():
    """Remove expired cache entries."""
    global query_cache
    current_time = time.time()
    expired_keys = []

    for key, (result, timestamp) in query_cache.items():
        if current_time - timestamp > 60:  # Assuming default expiration
            expired_keys.append(key)

    for key in expired_keys:
        del query_cache[key]

    logger.info(f"Removed {len(expired_keys)} expired cache entries")


# Example cached functions

@with_db_connection
@cache_query(expiration_time=30)
def get_user_by_id(conn, user_id):
    """
    Get a user by ID with 30-second cache.

    Args:
        conn: Database connection
        user_id: ID of the user to retrieve

    Returns:
        User record or None if not found
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()

    # Simulate some processing time
    time.sleep(0.1)

    return result


@with_db_connection
@cache_query(expiration_time=60)
def get_users_by_domain(conn, domain):
    """
    Get users by email domain with 60-second cache.

    Args:
        conn: Database connection
        domain: Email domain to filter by

    Returns:
        List of users with matching domain
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email LIKE ?", (f"%@{domain}%",))
    result = cursor.fetchall()

    # Simulate some processing time
    time.sleep(0.2)

    return result


@with_db_connection
@cache_query(expiration_time=120)
def get_user_statistics(conn):
    """
    Get user statistics with 2-minute cache.

    Args:
        conn: Database connection

    Returns:
        Dictionary with user statistics
    """
    cursor = conn.cursor()

    # Count total users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # Count users by domain
    cursor.execute("""
        SELECT SUBSTR(email, INSTR(email, '@') + 1) as domain, COUNT(*) as count
        FROM users
        GROUP BY domain
        ORDER BY count DESC
    """)
    domain_stats = cursor.fetchall()

    # Get recent users
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 5")
    recent_users = cursor.fetchall()

    # Simulate heavy processing
    time.sleep(0.5)

    return {
        "total_users": total_users,
        "domain_stats": domain_stats,
        "recent_users": recent_users,
        "generated_at": time.time()
    }


@with_db_connection
@cache_query(expiration_time=300)  # 5-minute cache
def get_user_bookings(conn, user_id):
    """
    Get user bookings with 5-minute cache.

    Args:
        conn: Database connection
        user_id: ID of the user

    Returns:
        List of user bookings
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.*, u.name as user_name
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        WHERE b.user_id = ?
        ORDER BY b.start_date DESC
    """, (user_id,))

    result = cursor.fetchall()

    # Simulate processing time
    time.sleep(0.3)

    return result


# Advanced caching decorator with different strategies
def smart_cache(expiration_time=60, max_size=100, strategy="lru"):
    """
    Advanced caching decorator with size limits and different eviction strategies.

    Args:
        expiration_time (int): Cache expiration time in seconds
        max_size (int): Maximum number of cache entries
        strategy (str): Eviction strategy ('lru', 'fifo', 'lfu')
    """

    def decorator(func):
        # Create function-specific cache
        func_cache = {}
        access_times = {}
        access_counts = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = _generate_cache_key(func.__name__, args, kwargs)
            current_time = time.time()

            # Check if result is in cache and not expired
            if cache_key in func_cache:
                cached_result, timestamp = func_cache[cache_key]
                if current_time - timestamp < expiration_time:
                    # Update access tracking
                    access_times[cache_key] = current_time
                    access_counts[cache_key] = access_counts.get(cache_key, 0) + 1

                    logger.info(f"Cache hit for {func.__name__}")
                    return cached_result
                else:
                    # Remove expired entry
                    del func_cache[cache_key]
                    access_times.pop(cache_key, None)
                    access_counts.pop(cache_key, None)

            # Execute function
            result = func(*args, **kwargs)

            # Check if we need to evict entries
            if len(func_cache) >= max_size:
                _evict_cache_entry(func_cache, access_times, access_counts, strategy)

            # Cache the result
            func_cache[cache_key] = (result, current_time)
            access_times[cache_key] = current_time
            access_counts[cache_key] = 1

            logger.info(f"Cached result for {func.__name__}")
            return result

        return wrapper

    return decorator


def _evict_cache_entry(cache, access_times, access_counts, strategy):
    """
    Evict a cache entry based on the specified strategy.

    Args:
        cache: Cache dictionary
        access_times: Access time tracking
        access_counts: Access count tracking
        strategy: Eviction strategy
    """
    if not cache:
        return

    if strategy == "lru":  # Least Recently Used
        oldest_key = min(access_times.items(), key=lambda x: x[1])[0]
    elif strategy == "fifo":  # First In, First Out
        oldest_key = next(iter(cache))
    elif strategy == "lfu":  # Least Frequently Used
        oldest_key = min(access_counts.items(), key=lambda x: x[1])[0]
    else:
        oldest_key = next(iter(cache))

    # Remove the selected entry
    del cache[oldest_key]
    access_times.pop(oldest_key, None)
    access_counts.pop(oldest_key, None)

    logger.info(f"Evicted cache entry using {strategy} strategy")


# Example with smart cache
@with_db_connection
@smart_cache(expiration_time=30, max_size=10, strategy="lru")
def get_user_profile(conn, user_id):
    """
    Get user profile with smart caching.

    Args:
        conn: Database connection
        user_id: ID of the user

    Returns:
        User profile dictionary
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if user:
        return {
            "id": user[0],
            "name": user[1],
            "email": user[2],
            "created_at": user[3]
        }

    return None


# Test the caching mechanism
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
        ('Charlie Brown', 'charlie@example.com'),
        ('Diana Prince', 'diana@example.com'),
        ('Eve Wilson', 'eve@test.com')
    ]

    cursor.executemany('INSERT OR IGNORE INTO users (name, email) VALUES (?, ?)', sample_users)

    # Insert sample bookings
    sample_bookings = [
        (1, 101, '2024-01-15', '2024-01-20'),
        (2, 102, '2024-01-22', '2024-01-25'),
        (1, 103, '2024-02-01', '2024-02-05')
    ]

    cursor.executemany(
        'INSERT OR IGNORE INTO bookings (user_id, property_id, start_date, end_date) VALUES (?, ?, ?, ?)',
        sample_bookings)

    conn.commit()
    conn.close()

    print("=== Testing Basic Cache Functionality ===")

    # Test cache miss and hit
    start_time = time.time()
    user1 = get_user_by_id(1)
    first_call_time = time.time() - start_time
    print(f"First call (cache miss): {first_call_time:.3f}s - {user1}")

    start_time = time.time()
    user2 = get_user_by_id(1)
    second_call_time = time.time() - start_time
    print(f"Second call (cache hit): {second_call_time:.3f}s - {user2}")

    print(f"Speed improvement: {first_call_time / second_call_time:.2f}x")

    print("\n=== Testing Different Cache Durations ===")

    # Test domain query caching
    domain_users = get_users_by_domain("example.com")
    print(f"Users with example.com domain: {len(domain_users)}")

    # Test statistics caching
    stats = get_user_statistics()
    print(f"User statistics: {stats}")

    print("\n=== Testing Cache Management ===")

    # Show cache statistics
    cache_stats = get_cache_stats()
    print(f"Cache stats: {cache_stats}")

    # Test cache expiration
    print("Waiting for cache to expire...")
    time.sleep(2)

    # This should be a cache miss due to expiration
    user3 = get_user_by_id(1)
    print(f"After expiration: {user3}")

    # Clear cache
    clear_cache()
    print("Cache cleared")

    # Test smart cache
    print("\n=== Testing Smart Cache ===")

    profile = get_user_profile(1)
    print(f"User profile: {profile}")

    # Test multiple users to trigger eviction
    for i in range(1, 15):
        profile = get_user_profile(i)
        if profile:
            print(f"Profile {i}: {profile['name']}")

    print("\n=== Cache Performance Demonstration ===")

    # Demonstrate performance benefit
    print("Testing performance without cache...")


    def get_user_without_cache(user_id):
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        time.sleep(0.1)  # Simulate processing time
        return result


    # Multiple calls without cache
    start_time = time.time()
    for _ in range(5):
        get_user_without_cache(1)
    no_cache_time = time.time() - start_time

    # Multiple calls with cache
    start_time = time.time()
    for _ in range(5):
        get_user_by_id(1)
    cache_time = time.time() - start_time

    print(f"Without cache: {no_cache_time:.3f}s")
    print(f"With cache: {cache_time:.3f}s")
    print(f"Performance improvement: {no_cache_time / cache_time:.2f}x")