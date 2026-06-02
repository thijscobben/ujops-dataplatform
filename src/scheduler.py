import logging
import schedule
import time
from datetime import datetime
import json
import os
import sys
from src.jobs.daily_scraper_job import DailyScraperJob
from src.database import init_db

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Setup logging
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class JobScheduler:
    """Manage daily scheduled scraping jobs"""

    def __init__(self, config_file: str = "scheduler_config.json"):
        logger.info("Initializing scheduler...")

        # Wait for database
        try:
            init_db(max_retries=10)
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            sys.exit(1)

        self.config = self._load_config(config_file)
        self.schedule_time = self.config.get("schedule_time", "09:00")
        self.keywords = self.config.get("keywords", [])
        logger.info(f"Scheduler initialized with {len(self.keywords)} keywords")

    def _load_config(self, config_file: str) -> dict:
        """Load scheduler configuration from JSON file"""
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)

        logger.warning(f"Config file {config_file} not found, using defaults")
        return {
            "schedule_time": "09:00",
            "keywords": ["python developer", "data engineer"],
            "db_enabled": True
        }

    def daily_job(self):
        """Execute the daily scraping job"""
        logger.info(f"Executing scheduled job at {datetime.now()}")
        try:
            job = DailyScraperJob(
                db_enabled=self.config.get("db_enabled", True),
                keywords=self.keywords
            )
            job.run()
        except Exception as e:
            logger.error(f"Scheduled job failed: {e}", exc_info=True)

    def start(self):
        """Start the scheduler"""
        logger.info(f"Scheduler started. Jobs will run daily at {self.schedule_time}")
        logger.info(f"Monitoring keywords: {self.keywords}")

        schedule.every().day.at(self.schedule_time).do(self.daily_job)

        # Keep scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


if __name__ == "__main__":
    try:
        scheduler = JobScheduler()
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)