#!/usr/bin/python3
"""
Lazy pagination module for streaming paginated user data from database
"""

import seed
from typing import Generator, List, Dict, Any


def paginate_users(page_size: int, offset: int) -> List[Dict[str, Any]]:
    """
    Fetch a single page of users from the database
    
    Args:
        page_size (int): Number of users to fetch per page
        offset (int): Starting position in the database
        
    Returns:
        List[Dict[str, Any]]: List of user records as dictionaries
    """
    connection = seed.connect_to_prodev()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM user_data LIMIT {page_size} OFFSET {offset}")
    rows = cursor.fetchall()
    connection.close()
    return rows


def lazy_pagination(page_size: int) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Generator function that lazily fetches paginated data from the users database
    
    Args:
        page_size (int): Number of records to fetch per page
        
    Yields:
        List[Dict[str, Any]]: A page of user records
    """
    offset = 0
    
    # Single loop that continues until no more data is available
    while True:
        page = paginate_users(page_size, offset)
        
        # If no rows returned, we've reached the end
        if not page:
            break
            
        yield page
        offset += page_size