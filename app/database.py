import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT", "5432")

# SSL Configuration
# RDS often requires SSL. We check for the cert file.
ssl_args = {}
cert_path = os.path.join(os.getcwd(), "global-bundle.pem")
if os.path.exists(cert_path):
    print(f"🔒 SSL Certificate found at {cert_path}")
    ssl_args = {
        "sslmode": "verify-full",
        "sslrootcert": cert_path
    }
else:
    print("⚠️  SSL Certificate not found. Connection might fail if RDS requires SSL.")

# Construct connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine with SSL args
engine = create_engine(
    DATABASE_URL, 
    echo=False,
    connect_args=ssl_args
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
