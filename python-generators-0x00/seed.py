import mysql.connector
from mysql.connector import Error
import csv
import uuid
import os
from decimal import Decimal


def connect_db():
    """
    Connects to the MySQL database server.
    
    Returns:
        connection: MySQL connection object or None if connection fails
    """
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            port=3306
        )
        
        if connection.is_connected():
            print("Successfully connected to MySQL server")
            return connection
            
    except Error as e:
        print(f"Error connecting to MySQL server: {e}")
        return None


def create_database(connection):
    """
    Creates the database 'ALX_prodev' if it does not exist.
    
    Args:
        connection: MySQL connection object
        
    Returns:
        bool: True if database creation is successful, False otherwise
    """
    try:
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS ALX_prodev")
        print("Database 'ALX_prodev' created successfully or already exists")
        
        cursor.close()
        return True
        
    except Error as e:
        print(f"Error creating database: {e}")
        return False


def connect_to_prodev():
    """
    Connects to the ALX_prodev database in MySQL.
    
    Returns:
        connection: MySQL connection object to ALX_prodev database or None if connection fails
    """
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='ALX_prodev',
            port=3306
        )
        
        if connection.is_connected():
            print("Successfully connected to ALX_prodev database")
            return connection
            
    except Error as e:
        print(f"Error connecting to ALX_prodev database: {e}")
        return None


def create_table(connection):
    """
    Creates a table 'user_data' if it does not exist with the required fields.
    
    Args:
        connection: MySQL connection object
        
    Returns:
        bool: True if table creation is successful, False otherwise
    """
    try:
        cursor = connection.cursor()
        
        # Create table with specified schema
        create_table_query = """
        CREATE TABLE IF NOT EXISTS user_data (
            user_id CHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            age DECIMAL(5,2) NOT NULL,
            INDEX idx_user_id (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        cursor.execute(create_table_query)
        print("Table 'user_data' created successfully or already exists")
        
        cursor.close()
        return True
        
    except Error as e:
        print(f"Error creating table: {e}")
        return False


def insert_data(connection, data):
    """
    Inserts data into the database if it does not exist.
    
    Args:
        connection: MySQL connection object
        data: Either a CSV filename (string) or list of tuples containing (user_id, name, email, age)
        
    Returns:
        bool: True if data insertion is successful, False otherwise
    """
    try:
        # Check if data is a string (CSV filename) or actual data
        if isinstance(data, str):
            # It's a CSV filename, read the data first
            csv_file_path = data
            if os.path.exists(csv_file_path):
                data = read_csv_data(csv_file_path)
            else:
                print(f"CSV file not found: {csv_file_path}")
                return False
        
        # If no data to insert
        if not data:
            print("No data to insert")
            return False
        
        cursor = connection.cursor()
        
        # Insert query with ON DUPLICATE KEY UPDATE to avoid duplicates
        insert_query = """
        INSERT INTO user_data (user_id, name, email, age) 
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        name = VALUES(name),
        email = VALUES(email),
        age = VALUES(age)
        """
        
        # Execute batch insert
        cursor.executemany(insert_query, data)
        connection.commit()
        
        print(f"Successfully inserted/updated {cursor.rowcount} records")
        cursor.close()
        return True
        
    except Error as e:
        print(f"Error inserting data: {e}")
        connection.rollback()
        return False


def read_csv_data(csv_file_path):
    """
    Reads user data from CSV file and returns formatted data for database insertion.
    
    Args:
        csv_file_path: Path to the CSV file
        
    Returns:
        list: List of tuples containing user data
    """
    data = []
    
    try:
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                # Generate UUID if not provided in CSV
                user_id = row.get('user_id', str(uuid.uuid4()))
                name = row['name']
                email = row['email']
                age = Decimal(str(row['age']))
                
                data.append((user_id, name, email, age))
                
        print(f"Successfully read {len(data)} records from CSV file")
        return data
        
    except FileNotFoundError:
        print(f"CSV file not found: {csv_file_path}")
        return []
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return []


def create_sample_data():
    """
    Creates sample data for testing when CSV file is not available.
    
    Returns:
        list: List of tuples containing sample user data
    """
    sample_data = [
        (str(uuid.uuid4()), "John Doe", "john.doe@email.com", Decimal("25.00")),
        (str(uuid.uuid4()), "Jane Smith", "jane.smith@email.com", Decimal("30.50")),
        (str(uuid.uuid4()), "Bob Johnson", "bob.johnson@email.com", Decimal("45.25")),
        (str(uuid.uuid4()), "Alice Brown", "alice.brown@email.com", Decimal("28.75")),
        (str(uuid.uuid4()), "Charlie Wilson", "charlie.wilson@email.com", Decimal("35.00"))
    ]
    
    print("Using sample data (CSV file not found)")
    return sample_data


def main():
    """
    Main function to orchestrate the database setup and data population.
    """
    # Step 1: Connect to MySQL server
    connection = connect_db()
    if not connection:
        print("Failed to connect to MySQL server. Exiting...")
        return
    
    # Step 2: Create database
    if not create_database(connection):
        print("Failed to create database. Exiting...")
        connection.close()
        return
    
    # Close initial connection and connect to specific database
    connection.close()
    
    # Step 3: Connect to ALX_prodev database
    connection = connect_to_prodev()
    if not connection:
        print("Failed to connect to ALX_prodev database. Exiting...")
        return
    
    # Step 4: Create table
    if not create_table(connection):
        print("Failed to create table. Exiting...")
        connection.close()
        return
    
    # Step 5: Read data from CSV or use sample data
    csv_file_path = "user_data.csv"
    
    if os.path.exists(csv_file_path):
        data = read_csv_data(csv_file_path)
    else:
        data = create_sample_data()
    
    # Step 6: Insert data
    if data:
        if insert_data(connection, data):
            print("Database setup and data population completed successfully!")
        else:
            print("Failed to insert data")
    else:
        print("No data to insert")
    
    # Step 7: Close connection
    connection.close()
    print("Connection closed")


# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'port': 3306
}


if __name__ == "__main__":
    main()