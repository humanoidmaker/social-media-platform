#!/usr/bin/env python3
"""Seed the admin user for Social Media Platform."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def seed_admin():
    from app.database import get_db_session
    from app.models.user import User
    from app.utils.hashing import hash_password

    async with get_db_session() as session:
        from sqlalchemy import select
        existing = await session.execute(
            select(User).where(User.email == "admin@social_media.io")
        )
        if existing.scalar_one_or_none():
            print("Admin user already exists.")
            return

        admin = User(
            username="admin",
            email="admin@social_media.io",
            display_name="Social Media Platform Admin",
            password_hash=hash_password("Admin123!@#"),
            is_admin=True,
            is_verified=True,
            bio="Platform administrator",
        )
        session.add(admin)
        await session.commit()
        print("Admin user created: admin@social_media.io / Admin123!@#")


if __name__ == "__main__":
    asyncio.run(seed_admin())
