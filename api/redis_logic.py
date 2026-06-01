import redis.asyncio as redis
from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import Optional
from typing import AsyncIterator

# Глобальная переменная для клиента
redis_client: Optional[redis.Redis] = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    print("Подключаемся к Redis...")

    # Создаём клиент и сохраняем его в app.state
    app.state.redis = redis.from_url(
        "redis://localhost:6379",
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_keepalive=True,
        max_connections=50,
    )

    # Проверка соединения
    try:
        await app.state.redis.ping()
        print("✅ Redis успешно подключён")
    except Exception as e:
        print(f"❌ Не удалось подключиться к Redis: {e}")
        raise

    yield  # ← приложение работает

    # Graceful shutdown
    print("Отключаемся от Redis...")
    await app.state.redis.aclose()
    print("Redis отключён")


# Функция для удобного получения клиента в зависимостях (опционально)
def get_redis():
    if redis_client is None:
        raise RuntimeError("Redis client не инициализирован")
    return redis_client