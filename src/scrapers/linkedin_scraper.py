from .base_scraper import BaseScraper
from jobspy import scrape_jobs
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class LinkedInScraper(BaseScraper):
    """LinkedIn job scraper with jobspy library"""

    def __init__(self, rate_limit_config: Dict[str, Any]):
        super().__init__("linkedin", rate_limit_config)

    def scrape(self, keyword: str, location: str) -> List[Dict[str, Any]]:
        """
        Scrape LinkedIn using jobspy
        Returns raw jobs in jobspy format
        """
        try:
            jobs = scrape_jobs(
                site_name=["linkedin"],
                search_term=keyword,
                location=location,
                results_wanted=50,
                hours_old=720,
                country_indeed="Netherlands"
            )

            # Convert DataFrame to list of dicts if needed
            if hasattr(jobs, 'to_dict'):
                return jobs.to_dict('records')
            return jobs if jobs else []

        except Exception as e:
            logger.error(f"LinkedIn scrape failed for '{keyword}': {e}")
            raise