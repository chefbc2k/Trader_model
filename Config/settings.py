from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

# Django Secret Key
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

# New Relic
NEW_RELIC_LICENSE_KEY = os.getenv("NEW_RELIC_LICENSE_KEY")

# API Keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
APCA_API_KEY_ID = os.getenv("APCA_API_KEY_ID")
APCA_API_SECRET_KEY = os.getenv("APCA_API_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
QUANDL_API_KEY = os.getenv("QUANDL_API_KEY")
MORNINGSTAR_API_KEY = os.getenv("MORNINGSTAR_API_KEY")
MORNINGSTAR_API_ENDPOINT = os.getenv("MORNINGSTAR_API_ENDPOINT")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_BUCKET = os.getenv("S3_BUCKET")

# Redis Configuration (Local)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# FMP API Configuration
FMP_API_BASE_URL = os.getenv("FMP_API_BASE_URL", "https://financialmodelingprep.com/api/v3")
FMP_API_NEWS_SENTIMENT_ENDPOINT = os.getenv("FMP_API_NEWS_SENTIMENT_ENDPOINT", "/news-sentiment")
FMP_API_KEY = os.getenv("FMP_API_KEY")