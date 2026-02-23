import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_WEWORK_URL = "https://weworkremotely.com/remote-jobs"
RAW_DATA_PATH = "dataset/raw/jobs_raw.csv"


@dataclass
class JobPost:
    title: str
    company: str
    location: str
    skills: str
    description: str
    source: str
    url: str


class JobScraper:
    """Scrape remote job listings (robots.txt allows /) and persist to CSV."""

    def __init__(self, delay: float = 0.5):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0 Safari/537.36"
                )
            }
        )
        self.delay = delay

    def fetch_weworkremotely(
        self, max_pages: int = 20, limit: int = 500
    ) -> List[JobPost]:
        """Iterate paginated listings until we collect the desired amount."""
        jobs: List[JobPost] = []
        seen_urls = set()

        for page in range(1, max_pages + 1):
            page_url = f"{BASE_WEWORK_URL}?page={page}"
            print(f"Scraping listing page: {page_url}")
            resp = self.session.get(page_url, timeout=15)
            if resp.status_code != 200:
                print(f"Skipping page {page}, status: {resp.status_code}")
                break

            soup = BeautifulSoup(resp.text, "lxml")
            anchors = soup.select("section.jobs li a[href^='/remote-jobs/']")
            if not anchors:
                print("No more listings found; stopping.")
                break

            for a in anchors:
                href = a.get("href")
                if not href or href in seen_urls:
                    continue
                seen_urls.add(href)

                job_url = f"https://weworkremotely.com{href}"
                title, company, location = self._parse_listing_snippet(a)
                description, skills = self._fetch_job_detail(job_url)
                if not description:
                    description = self._fallback_description(a)
                if not skills:
                    skills = self._fallback_skills(a)

                jobs.append(
                    JobPost(
                        title=title or "",
                        company=company or "",
                        location=location or "",
                        skills=", ".join(skills),
                        description=description or "",
                        source="weworkremotely",
                        url=job_url,
                    )
                )

                if len(jobs) >= limit:
                    print(f"Collected {len(jobs)} jobs; stopping.")
                    return jobs

                time.sleep(self.delay)

            time.sleep(self.delay)

        return jobs

    @staticmethod
    def _parse_listing_snippet(anchor) -> tuple:
        """Extract quick fields available on the listing card."""
        title = None
        company = None
        location = None

        title_node = anchor.select_one("span.title") or anchor.select_one(
            "h3.new-listing__header__title"
        )
        company_node = anchor.select_one("span.company") or anchor.select_one(
            "p.new-listing__company-name"
        )
        location_node = anchor.select_one("span.region.company") or anchor.select_one(
            "p.new-listing__company-headquarters"
        )

        if title_node:
            title = title_node.get_text(strip=True)
        if company_node:
            company = company_node.get_text(strip=True)
        if location_node:
            location = location_node.get_text(strip=True)

        # Some cards list categories that often include remote scope.
        if not location:
            categories = [
                p.get_text(strip=True)
                for p in anchor.select("p.new-listing__categories__category")
            ]
            if categories:
                location = categories[-1]

        return title, company, location

    def _fetch_job_detail(self, url: str) -> tuple[Optional[str], List[str]]:
        """Follow the job link to collect full description and skill tags."""
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                print(f"Failed to fetch detail: {url} ({resp.status_code})")
                return None, []
        except requests.RequestException as exc:
            print(f"Request error for {url}: {exc}")
            return None, []

        soup = BeautifulSoup(resp.text, "lxml")
        desc_node = soup.select_one("div.listing-container") or soup.select_one(
            "div.listing-body"
        )
        description = desc_node.get_text(separator=" ", strip=True) if desc_node else ""

        tags = [
            tag.get_text(strip=True)
            for tag in soup.select("span.listing-tag")
            if tag.get_text(strip=True)
        ]
        return description, tags

    @staticmethod
    def _fallback_description(anchor) -> str:
        text = anchor.get_text(separator=" ", strip=True)
        return text

    @staticmethod
    def _fallback_skills(anchor) -> List[str]:
        tags = [
            p.get_text(strip=True)
            for p in anchor.select("p.new-listing__categories__category")
            if p.get_text(strip=True)
        ]
        return tags


def run_scraper(output_path: str = RAW_DATA_PATH, target_count: int = 300):
    """Entrypoint to run from CLI."""
    scraper = JobScraper()
    jobs = scraper.fetch_weworkremotely(limit=target_count)
    print(f"Total jobs scraped: {len(jobs)}")
    data = [asdict(job) for job in jobs]
    df = pd.DataFrame(data)
    output_path = output_path or RAW_DATA_PATH
    df.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    run_scraper()
