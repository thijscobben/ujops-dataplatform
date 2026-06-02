from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime
import time


def scrape_data_jobs():
    keywords = [
        "Senior Data Engineer", "Senior Data Scientist", "Lead Data Engineer",
        "Lead Data Scientist", "Head of Data", "Chief Data Officer", "CTO",
        "Chief Technology Officer", "Data Architect", "Principal Data"
    ]

    all_jobs = []

    for keyword in keywords:
        try:
            jobs = scrape_jobs(
                site_name=["linkedin"],  # of ["linkedin", "indeed"]
                search_term=keyword,
                location="Netherlands",  # of "Amsterdam", "Randstad"
                results_wanted=50,  # max ~1000 voor LinkedIn
                hours_old=720,  # laatste 30 dagen (voor lang openstaande)
                country_indeed="Netherlands",
            )
            all_jobs.extend(jobs)
            print(f"✓ {len(jobs)} jobs gevonden voor: {keyword}")
            time.sleep(5)  # Respect rate limits
        except Exception as e:
            print(f"Fout bij {keyword}: {e}")

    # Naar DataFrame
    df = pd.DataFrame(all_jobs)

    # Handige kolommen toevoegen voor "lang openstaande"
    if not df.empty:
        df['scrape_date'] = datetime.now()
        df['days_open_estimate'] = (df['scrape_date'] - pd.to_datetime(df['date_posted'])).dt.days

        # Filter op senior / lang open
        senior_df = df[df['title'].str.contains('Senior|Lead|Head|Chief|Principal|CTO|CDO', case=False, na=False)]
        long_open = senior_df[senior_df['days_open_estimate'] > 30]  # >1 maand open

        # Opslaan
        timestamp = datetime.now().strftime("%Y%m%d")
        senior_df.to_csv(f"data_jobs_{timestamp}.csv", index=False)
        long_open.to_csv(f"long_open_data_jobs_{timestamp}.csv", index=False)

        print(f"Totaal jobs: {len(df)} | Lang open (>30d): {len(long_open)}")

    return long_open


if __name__ == "__main__":
    long_open = scrape_data_jobs()
    if not long_open.empty:
        print(long_open[['title', 'company', 'location', 'date_posted', 'days_open_estimate', 'link']].head(10))