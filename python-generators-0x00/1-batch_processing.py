#!/usr/bin/python3
"""
Batch processing module for streaming and filtering users from database
"""

import mysql.connector
from typing import Generator, Dict, Any


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


def stream_users_in_batches(batch_size: int) -> Generator[list, None, None]:
    """
    Generator function that fetches users from database in batches
    
    Args:
        batch_size (int): Number of rows to fetch per batch
        
    Yields:
        list: Batch of user records as dictionaries
    """
    connection = connect_db()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT user_id, name, email, age FROM user_data")
        
        # Loop 1: Fetch and yield batches
        while True:
            batch = cursor.fetchmany(batch_size)
            if not batch:
                break
            yield batch
                
    except mysql.connector.Error as e:
        print(f"Error fetching data: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def batch_processing(batch_size: int) -> None:
    """
    Process batches of users and filter those over age 25
    
    Args:
        batch_size (int): Size of each batch to process
    """
    # Loop 2: Process each batch
    for batch in stream_users_in_batches(batch_size):
        # Loop 3: Filter users in current batch
        for user in batch:
            if user['age'] > 25:
                print(user)