import os


class Config:
    MYSQL_URI = os.getenv("MYSQL_URI", "mysql+pymysql://root:sriram@localhost/mba_ecommerce")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    DEFAULT_MIN_SUPPORT = float(os.getenv("DEFAULT_MIN_SUPPORT", "0.02"))
    DEFAULT_MIN_CONFIDENCE = float(os.getenv("DEFAULT_MIN_CONFIDENCE", "0.30"))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    JWT_ACCESS_TOKEN_EXPIRES_HOURS = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "8"))
