
import os


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
