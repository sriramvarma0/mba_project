import os


class Config:
    MYSQL_URI = "mysql+pymysql://admin:sriramvarma@database-1.c3ge4a0ya22d.ap-south-2.rds.amazonaws.com:3306/mba_ecommerce"
    JWT_SECRET_KEY = "mba-project-super-secret-jwt-key"
    DEFAULT_MIN_SUPPORT = float(os.getenv("DEFAULT_MIN_SUPPORT", "0.02"))
    DEFAULT_MIN_CONFIDENCE = float(os.getenv("DEFAULT_MIN_CONFIDENCE", "0.30"))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    JWT_ACCESS_TOKEN_EXPIRES_HOURS = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "8"))
