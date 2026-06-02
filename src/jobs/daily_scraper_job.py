import logging
from datetime import datetime
import pandas as pd
from pathlib import Path
from sqlalchemy import text
import json

from src.scrapers import LinkedInScraper, ScraperConfig, JobBoard
from src.database import get_session, init_db

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DailyScraperJob:
    """
    Daily job to scrape job boards and load to PostgreSQL data warehouse.
    """

    def __init__(self, db_enabled: bool = True, data_dir: str = "data/raw", keywords: list = None):
        self.db_enabled = db_enabled
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config = ScraperConfig()
        self.keywords = keywords or self.config.KEYWORDS
        self.run_timestamp = datetime.utcnow().isoformat()

        if self.db_enabled:
            init_db()

    def run(self):
        """Execute daily scraping job"""
        logger.info("=" * 60)
        logger.info(f"Starting daily scraping job: {self.run_timestamp}")
        logger.info(f"Keywords: {self.keywords}")
        logger.info("=" * 60)

        all_jobs = []

        # LinkedIn
        try:
            logger.info("\n[1/1] Scraping LinkedIn...")
            linkedin = LinkedInScraper(self.config.RATE_LIMITS[JobBoard.LINKEDIN.value])
            linkedin_jobs = linkedin.scrape_batch(self.keywords, self.config.LOCATION)
            all_jobs.extend(linkedin_jobs)
            logger.info(f"✓ LinkedIn: {len(linkedin_jobs)} jobs")
        except Exception as e:
            logger.error(f"✗ LinkedIn scraping failed: {e}")

        if not all_jobs:
            logger.warning("No jobs scraped!")
            return None

        # Save to raw layer
        df = pd.DataFrame(all_jobs)
        output_file = self._save_raw_data(df)
        logger.info(f"\n✓ Saved {len(df)} jobs to {output_file}")

        # Load to database if enabled
        if self.db_enabled:
            try:
                self._load_to_database(df)
                logger.info(f"✓ Loaded {len(df)} jobs to PostgreSQL")
            except Exception as e:
                logger.error(f"✗ Database load failed: {e}")

        logger.info(f"\n✓ Job completed successfully")
        return output_file

    def _save_raw_data(self, df: pd.DataFrame) -> str:
        """Save raw scraped data as CSV"""
        date_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"raw_job_listings_{date_str}.csv"
        filepath = self.data_dir / filename

        df.to_csv(filepath, index=False)
        return str(filepath)

    def _load_to_database(self, df: pd.DataFrame):
        """Load data to PostgreSQL raw schema"""
        with get_session() as session:
            for _, row in df.iterrows():
                insert_sql = text("""
                                  INSERT INTO raw.job_listings
                                      (title, company, location, url, description, job_board, scrape_keyword)
                                  VALUES (:title, :company, :location, :url, :description, :job_board, :keyword)
                                  """)

                session.execute(insert_sql, {
                    'title': row.get('title'),
                    'company': row.get('company'),
                    'location': row.get('location'),
                    'url': row.get('url'),
                    'description': row.get('description'),
                    'job_board': 'linkedin',
                    'keyword': row.get('search_term', 'unknown')
                })

            session.commit()


if __name__ == "__main__":
    job = DailyScraperJob()
    job.run()