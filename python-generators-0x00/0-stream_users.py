#!/usr/bin/python3
import mysql.connector
from mysql.connector import Error


def stream_users():
    """
    Generator function that streams rows from the user_data table one by one.
    
    Yields:
        dict: A dictionary containing user data with keys: user_id, name, email, age
    """
    connection = None
    cursor = None
    
    try:
        # Connect to the ALX_prodev database
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='ALX_prodev',
            port=3306
        )
        
        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)  # Use dictionary cursor for dict output
            
            # Execute query to select all users from user_data table
            cursor.execute("SELECT user_id, name, email, age FROM user_data")
            
            # Stream rows one by one using yield
            for row in cursor:
                yield row
                
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        
    finally:
        # Clean up resources
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()