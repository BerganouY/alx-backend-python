#!/usr/bin/env python3
"""
Concurrent Asynchronous Database Queries
"""

import asyncio
import aiosqlite

async def async_fetch_users():
    """Fetch all users from database"""
    async with aiosqlite.connect('users.db') as db:
        async with db.execute("SELECT * FROM users") as cursor:
            return await cursor.fetchall()

async def async_fetch_older_users():
    """Fetch users older than 40"""
    async with aiosqlite.connect('users.db') as db:
        async with db.execute("SELECT * FROM users WHERE age > ?", (40,)) as cursor:
            return await cursor.fetchall()

async def fetch_concurrently():
    """Run both queries concurrently"""
    users, older_users = await asyncio.gather(
        async_fetch_users(),
        async_fetch_older_users()
    )
    print("All users:")
    for user in users:
        print(user)
    print("\nUsers older than 40:")
    for user in older_users:
        print(user)

if __name__ == "__main__":
    asyncio.run(fetch_concurrently())