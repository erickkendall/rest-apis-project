"""
blacklist.py

This file just contains the blacklist of the JWT tokens. It will be imported by
app and the logout resource so that tokens can be added to the blacklist when the
user logs out.
"""

# BLOCKLIST = set()

import redis
import os

# Connect to Redis using the container name as hostname
jwt_redis_blocklist = redis.Redis(
    host='redis',  # This matches your Redis container name
    port=6379,
    db=0,
    decode_responses=True
)

def add_to_blocklist(jti, expires):
    jwt_redis_blocklist.set(jti, "", ex=expires)

def is_in_blocklist(jti):
    return jwt_redis_blocklist.exists(jti)
