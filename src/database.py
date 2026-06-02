import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

logger = logging.getLogger(__name__)


def get_db_connection_string():
    """Get PostgreSQL connection string from environment or defaults"""
    db_user = os.getenv("DB_USER", "<your_db_user>")
    db_password = os.getenv("DB_PASSWORD", "<your_db_password>")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "jobanalyzer")

    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def init_db():
    """Initialize database connection and create tables if needed"""
    connection_string = get_db_connection_string()
    engine = create_engine(connection_string, echo=False)

    # Create tables if they don't exist
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE SCHEMA IF NOT EXISTS raw;
            CREATE SCHEMA IF NOT EXISTS staging;
            CREATE SCHEMA IF NOT EXISTS warehouse;
        """))

        conn.execute(text("""
                          CREATE TABLE IF NOT EXISTS raw.job_listings
                          (
                              id
                              SERIAL
                              PRIMARY
                              KEY,
                              title
                              VARCHAR
                          (
                              255
                          ),
                              company VARCHAR
                          (
                              255
                          ),
                              location VARCHAR
                          (
                              255
                          ),
                              url TEXT,
                              description TEXT,
                              job_board VARCHAR
                          (
                              50
                          ),
                              scrape_keyword VARCHAR
                          (
                              100
                          ),
                              scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                              );

                          CREATE INDEX IF NOT EXISTS idx_job_listings_scraped_at
                              ON raw.job_listings(scraped_at);
                          CREATE INDEX IF NOT EXISTS idx_job_listings_job_board
                              ON raw.job_listings(job_board);
                          """))

        conn.commit()

    logger.info("Database initialized successfully")
    return engine


@contextmanager
def get_session():
    """Context manager for database sessions"""
    engine = create_engine(get_db_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()