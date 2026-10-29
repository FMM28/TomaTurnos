import os
from dotenv import load_dotenv

load_dotenv()

def env_int(name, default):
    value = os.getenv(name)
    return default if not value or value.lower() == "none" else int(value)

def env_str(name, default=None):
    value = os.getenv(name)
    return default if value is None or value.lower() == "none" else value

class Config:
    DB_USER = env_str("DB_USER")
    DB_PASSWORD = env_str("DB_PASSWORD")
    DB_HOST = env_str("DB_HOST", "localhost")
    DB_PORT = env_int("DB_PORT", 3306)
    DB_NAME = env_str("DB_NAME", "turnos")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        "?charset=utf8mb4"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": env_int("DB_POOL_SIZE", 5),
        "max_overflow": env_int("DB_MAX_OVERFLOW", 5),
        "pool_timeout": env_int("DB_POOL_TIMEOUT", 30),
        "pool_recycle": env_int("DB_POOL_RECYCLE", 1800),
        "pool_pre_ping": True,
        "echo": False,
        "echo_pool": False,
    }

    SECRET_KEY = env_str("SECRET_KEY")

    MAX_TURNO = env_int("MAX_TURNO", 999)

    PRINT_MODE = env_str("PRINT_MODE", "mock")
