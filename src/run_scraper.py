#!/usr/bin/env python3
"""
Main entry point for running the job scraper
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from src.jobs.daily_scraper_job import DailyScraperJob

if __name__ == "__main__":
    print("🚀 Starting Job Market Analytics Scraper")
    print("=" * 50)

    job = DailyScraperJob()
    result = job.run()

    if result:
        print(f"\n✅ Success! Data saved to: {result}")
    else:
        print("\n❌ Job failed - check logs above")