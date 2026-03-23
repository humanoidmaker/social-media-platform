#!/usr/bin/env python3
"""Seed sample data for development."""
import asyncio
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SAMPLE_USERS = [
    {"username": "johndoe", "display_name": "John Doe", "email": "john@example.com", "bio": "Software developer and tech enthusiast"},
    {"username": "janedoe", "display_name": "Jane Doe", "email": "jane@example.com", "bio": "Designer & creative thinker"},
    {"username": "techguru", "display_name": "Tech Guru", "email": "tech@example.com", "bio": "Sharing the latest in tech"},
    {"username": "photographer", "display_name": "Alex Photo", "email": "alex@example.com", "bio": "Capturing moments one click at a time"},
    {"username": "foodie", "display_name": "Chef Maria", "email": "maria@example.com", "bio": "Food lover and recipe creator"},
    {"username": "traveler", "display_name": "World Walker", "email": "walker@example.com", "bio": "Exploring the world one city at a time"},
    {"username": "musicfan", "display_name": "Beat Master", "email": "beats@example.com", "bio": "Music is life"},
    {"username": "bookworm", "display_name": "Avid Reader", "email": "reader@example.com", "bio": "Lost in books"},
]

SAMPLE_POSTS = [
    "Just launched my new project! Check it out #coding #webdev",
    "Beautiful sunset today at the beach. Nature never disappoints.",
    "Working on something exciting. Stay tuned! #comingsoon",
    "Coffee and code - the perfect morning combo #developer",
    "Just finished reading an amazing book. Highly recommend!",
    "New recipe alert! This pasta is absolutely divine #foodie #cooking",
    "Exploring the streets of Tokyo. What an incredible city! #travel",
    "Music recommendation: check out this amazing new album #music",
    "Hot take: TypeScript is better than JavaScript. Fight me.",
    "Grateful for this community. You all are amazing! #thankful",
    "Who else is excited about the new tech announcements? #tech",
    "Morning workout done. Feeling energized! #fitness #health",
    "Just adopted a puppy! Meet my new best friend #pets #dogs",
    "Learning something new every day. Never stop growing. #motivation",
    "Friday vibes! What are your plans for the weekend? #friday",
]

SAMPLE_HASHTAGS = [
    "coding", "webdev", "tech", "travel", "foodie", "music",
    "photography", "fitness", "motivation", "design", "startup",
    "ai", "python", "react", "javascript", "nature", "art",
]


async def seed_data():
    from app.database import get_db_session
    from app.models.user import User
    from app.models.post import Post
    from app.models.hashtag import Hashtag
    from app.utils.hashing import hash_password

    async with get_db_session() as session:
        # Create users
        users = []
        for u in SAMPLE_USERS:
            user = User(
                username=u["username"],
                display_name=u["display_name"],
                email=u["email"],
                password_hash=hash_password("Password123!"),
                bio=u["bio"],
                is_verified=random.choice([True, False]),
            )
            session.add(user)
            users.append(user)
        await session.flush()

        # Create hashtags
        hashtags = []
        for tag in SAMPLE_HASHTAGS:
            ht = Hashtag(name=tag, post_count=random.randint(10, 1000))
            session.add(ht)
            hashtags.append(ht)
        await session.flush()

        # Create posts
        for content in SAMPLE_POSTS:
            post = Post(
                content=content,
                author_id=random.choice(users).id,
                like_count=random.randint(0, 500),
                comment_count=random.randint(0, 50),
                repost_count=random.randint(0, 30),
            )
            session.add(post)
        await session.flush()

        # Create some follows
        for user in users:
            follow_targets = random.sample(
                [u for u in users if u.id != user.id],
                k=random.randint(1, len(users) - 1)
            )
            for target in follow_targets:
                from app.models.follow import Follow
                follow = Follow(follower_id=user.id, following_id=target.id)
                session.add(follow)

        await session.commit()
        print(f"Seeded {len(users)} users, {len(SAMPLE_POSTS)} posts, {len(hashtags)} hashtags")


if __name__ == "__main__":
    asyncio.run(seed_data())
