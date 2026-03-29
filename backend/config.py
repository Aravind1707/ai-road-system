import os

# Environment-based configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:admin123@localhost:5432/road_ai")

# Email settings for authority reporting
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "your_email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your_password")
AUTHORITY_EMAIL = os.getenv("AUTHORITY_EMAIL", "pwd@yourgov.org")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)

# Prediction thresholds and disclaimers
PREDICTION_DAYS = int(os.getenv("PREDICTION_DAYS", "7"))
CRITICAL_DAMAGE_THRESHOLD = float(os.getenv("CRITICAL_DAMAGE_THRESHOLD", "150.0"))
MODERATE_DAMAGE_THRESHOLD = float(os.getenv("MODERATE_DAMAGE_THRESHOLD", "70.0"))

# JWT Settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change_me_to_a_long_random_secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
