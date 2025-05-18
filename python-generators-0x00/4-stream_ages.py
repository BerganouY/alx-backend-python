#!/usr/bin/python3
"""
Memory-efficient aggregate function module for computing average age
"""

import mysql.connector
from typing import Generator


def connect_db() -> mysql.connector.MySQLConnection:
    """Establish database connection"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='ALX_prodev',
            user='root',
            password='root'
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Error connecting to database: {e}")
        return None


def stream_user_ages() -> Generator[int, None, None]:
    """
    Generator function that yields user ages one by one from the database
    
    Yields:
        int: Individual user age
    """
    connection = connect_db()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT age FROM user_data")
        
        # Loop 1: Fetch and yield ages one by one
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield row[0]  # Yield the age value
                
    except mysql.connector.Error as e:
        print(f"Error fetching data: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def calculate_average_age() -> None:
    """
    Calculate the average age of users without loading entire dataset into memory
    Uses the stream_user_ages generator for memory efficiency
    """
    total_age = 0
    user_count = 0
    
    # Loop 2: Process each age from the generator
    for age in stream_user_ages():
        total_age += age
        user_count += 1
    
    # Calculate and print average
    if user_count > 0:
        average_age = total_age / user_count
        print(f"Average age of users: {average_age}")
    else:
        print("No users found in database")


if __name__ == "__main__":
    calculate_average_age()