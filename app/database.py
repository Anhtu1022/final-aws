from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import get_settings

settings = get_settings()
db_url = settings.get_database_url()

# SQLAlchemy connection arguments
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # Production connection pool settings for PostgreSQL / AWS RDS
    connect_args = {
        "connect_timeout": 10
    }

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,  # Automatically reconnect if connection was dropped
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides a database session per request.
    Closes the session when request lifecycle completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
