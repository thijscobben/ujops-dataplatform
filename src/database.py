import os
import logging
import time
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

logger = logging.getLogger(__name__)


def get_db_connection_string():
    """Get PostgreSQL connection string from environment or defaults"""
    db_user = os.getenv("DB_USER", "jobanalyzer_user")
    db_password = os.getenv("DB_PASSWORD", "jobanalyzer_pass")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "jobanalyzer")

    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def init_db(max_retries: int = 5):
    """Initialize database connection with retry logic"""
    connection_string = get_db_connection_string()

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to PostgreSQL (attempt {attempt + 1}/{max_retries})...")

            engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                echo=False,
                connect_args={'connect_timeout': 5}
            )

            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info("✓ Connected to PostgreSQL successfully")

            # Create schemas and tables
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
                                      url TEXT UNIQUE,
                                      description TEXT,
                                      job_board VARCHAR
                                  (
                                      50
                                  ),
                                      scrape_keyword VARCHAR
                                  (
                                      100
                                  ),
                                      first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                      last_seen_at TIMESTAMP,
                                      is_active BOOLEAN DEFAULT true,
                                      scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                      );

                                  CREATE INDEX IF NOT EXISTS idx_job_listings_url
                                      ON raw.job_listings(url);
                                  CREATE INDEX IF NOT EXISTS idx_job_listings_first_seen_at
                                      ON raw.job_listings(first_seen_at);
                                  CREATE INDEX IF NOT EXISTS idx_job_listings_job_board
                                      ON raw.job_listings(job_board);
                                  CREATE INDEX IF NOT EXISTS idx_job_listings_active
                                      ON raw.job_listings(is_active);
                                  """))

                conn.commit()

            logger.info("Database tables initialized successfully")
            return engine

        except Exception as e:
            logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts")
                raise


@contextmanager
def get_session():
    """Context manager for database sessions"""
    try:
        engine = create_engine(get_db_connection_string(), pool_pre_ping=True)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()