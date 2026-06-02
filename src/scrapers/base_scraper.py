from abc import ABC, abstractmethod
import time
from typing import List, Dict, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """
    Abstract base class for all scrapers.
    Implements rate limiting and standardized output.
    """
    
    def __init__(self, board_name: str, rate_limit_config: Dict[str, Any]):
        self.board_name = board_name
        self.rate_limit_config = rate_limit_config
        self.last_request_time = 0
        self.requests_today = 0
        
    def _apply_throttle(self):
        """Respect rate limits between requests"""
        delay = self.rate_limit_config.get("delay_between_requests_sec", 60)
        elapsed = time.time() - self.last_request_time
        
        if elapsed < delay:
            wait_time = delay - elapsed
            logger.info(f"Throttling {self.board_name}: waiting {wait_time:.1f}s")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
        self.requests_today += 1
    
    def _standardize_record(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert scraper-specific format to standard schema.
        This is where different APIs map to unified model.
        """
        return {
            "source": self.board_name,
            "source_job_id": raw_job.get("id"),
            "title": raw_job.get("title"),
            "company": raw_job.get("company"),
            "location": raw_job.get("location"),
            "job_description": raw_job.get("description"),
            "job_type": raw_job.get("job_type", "unknown"),
            "salary_min": raw_job.get("salary_min"),
            "salary_max": raw_job.get("salary_max"),
            "currency": raw_job.get("currency", "EUR"),
            "job_url": raw_job.get("url"),
            "date_posted": raw_job.get("date_posted"),
            "date_scraped": datetime.utcnow().isoformat(),
            "is_remote": raw_job.get("is_remote", False),
            "raw_data": raw_job  # Store original for debugging
        }
    
    @abstractmethod
    def scrape(self, keyword: str, location: str) -> List[Dict[str, Any]]:
        """
        Scrape jobs for a keyword.
        Subclasses implement board-specific logic.
        """
        pass
    
    def scrape_batch(self, keywords: List[str], location: str) -> List[Dict[str, Any]]:
        """Scrape multiple keywords with throttling"""
        all_jobs = []
        
        for keyword in keywords:
            try:
                logger.info(f"Scraping '{keyword}' from {self.board_name}")
                self._apply_throttle()
                
                jobs = self.scrape(keyword, location)
                standardized = [self._standardize_record(job) for job in jobs]
                all_jobs.extend(standardized)
                
                logger.info(f"✓ Found {len(jobs)} jobs for '{keyword}'")
            
            except Exception as e:
                logger.error(f"✗ Error scraping '{keyword}': {str(e)}")
                # Continue with next keyword instead of failing
                continue
        
        return all_jobs
