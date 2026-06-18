import redis.asyncio as redis
from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import AsyncIterator

import secrets 
from datetime import datetime


class RedisClient:
    def __init__(self):
        pass

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncIterator[None]:
        print("Trying to connect to Redis...")

        app.state.redis = redis.from_url(
            "redis://localhost:6379",
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
            max_connections=50,
        )

        try:
            await app.state.redis.ping()
            print("-- Connection to Redis was established")

        except Exception as _ex:
            print(f"!! Cant connect to Redis !! Error :: {_ex}")
            raise RuntimeError("Cant connect to Redis") from _ex

        yield  

        print("Turning off Redis...")
        await app.state.redis.aclose()
        print("Redis was shutted down")

    async def create_session(self, user_id: int, redis_client,  is_admin: bool = False) -> str:
        token_len = 64 if is_admin else 32
        session_id: str = secrets.token_urlsafe(token_len)
        key: str = f"session:{session_id}"

        session_data = {
            "user_id": str(user_id),
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
        }

        for field, value in session_data.items():
            await redis_client.hset(key, field, value)

        await redis_client.expire(key, 60 * 24 * 7)
        return session_id

    async def get_session(self, session_id: str, redis_client):
        if not session_id:
            return None
        
        key = f"session:{session_id}"
        data = await redis_client.hgetall(key)
        
        if not data or "user_id" not in data:
            return None

        await redis_client.expire(key, 60 * 24 * 7)
        return int(data["user_id"])

    async def delete_session(self, session_id: str, redis_client):
        SESSION_PREFIX: str = "session:"
        if session_id:
            await redis_client.delete(f"{SESSION_PREFIX}{session_id}")

    # --------------------------------------------------
    #               verification codes
    # --------------------------------------------------

    async def create_email_vercode(self, email: str, code: str, redis_client) -> str:        
        key = f"email_verification:{email}"
        
        verification_data = {
            "code": code,
            "attempts": "0",
            "created_at": datetime.utcnow().isoformat(),
        }

        for field, value in verification_data.items():
            await redis_client.hset(key, field, value)

        await redis_client.expire(key, 60 * 10)

        print(f"Код подтверждения создан для {email}: {code}")
        return code

    async def get_email_verification_code(self, email: str, redis_client):
        key = f"email_verification:{email}"
        data = await redis_client.hgetall(key)
        
        if not data:
            return None
        
        print('data items', data.items())
        return {k: v for k, v in data.items()}

    async def delete_email_vercode(self, email: str, redis_client):
        key = f"email_verification:{email}"
        await redis_client.delete(key)

    async def increment_verification_attempts(self, email: str, redis_client) -> int:
        key = f"email_verification:{email}"
        attempts = await redis_client.hincrby(key, "attempts", 1)
        return attempts

    async def verify_email_code(self, email: str, input_code: str, redis_client):
        data = await self.get_email_verification_code(email, redis_client)
        
        if not data:
            raise RuntimeError("Verification code wasnt found")
        
        if data.get("code") != input_code:
            raise RuntimeError("Wrond VerCode")
        
        print("код подошел")
        await self.delete_email_vercode(email, redis_client)
        return True

    async def can_send_new_code(self, email: str, redis_client) -> bool:
        key = f"email_verification{email}"
        exists = await redis_client.exists(key)
        return not bool(exists)
