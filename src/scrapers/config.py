
from dataclasses import dataclass
from typing import List
from enum import Enum

class JobBoard(Enum):
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    UPWORK = "upwork"
    TOPTAL = "toptal"
    FREELANCERCOM = "freelancer.com"

@dataclass
class ScraperConfig:
    """Configuration for scraping jobs"""
    # Keywords for Dutch market
    KEYWORDS = [
        "Data Architect",
        "Chief Data Officer",
        "CTO",
        "Chief Technology Officer",
        "Principal Data Engineer",
        "Lead Data Engineer",
        "Senior Data Architect"
    ]
    
    LOCATION = "Netherlands"
    HOURS_OLD = 720  # 30 days
    RESULTS_PER_KEYWORD = 50
    
    # Rate limiting (requests per source)
    RATE_LIMITS = {
        JobBoard.LINKEDIN.value: {
            "requests_per_hour": 30,
            "delay_between_requests_sec": 120
        },
        JobBoard.INDEED.value: {
            "requests_per_hour": 60,
            "delay_between_requests_sec": 60
        },
        JobBoard.UPWORK.value: {
            "requests_per_hour": 20,
            "delay_between_requests_sec": 180
        },
        JobBoard.TOPTAL.value: {
            "requests_per_hour": 25,
            "delay_between_requests_sec": 150
        }
    }
    
    # Job classification
    JOB_TYPES = {
        "fixed": ["permanent", "fixed", "full-time"],
        "freelance": ["freelance", "contract", "temporary"]
    }
