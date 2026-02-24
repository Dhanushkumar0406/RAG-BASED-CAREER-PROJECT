import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Callable
from urllib import robotparser
from urllib.parse import urlparse, urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_WEWORK_URL = "https://weworkremotely.com/remote-jobs"
# Second vetted source (Remotive lists remote roles with API/HTML allowed for scraping per robots.txt)
BASE_REMOTIVE_URL = "https://remotive.com/remote-jobs"
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
        # cache robots.txt parsers keyed by domain
        self._robots_cache: Dict[str, robotparser.RobotFileParser] = {}

    def _robots_allowed(self, url: str) -> bool:
        """Check robots.txt allowance for the given URL."""
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        rp = self._robots_cache.get(base)
        if not rp:
            rp = robotparser.RobotFileParser()
            rp.set_url(urljoin(base, "/robots.txt"))
            try:
                rp.read()
            except Exception:
                # If robots cannot be fetched, default to disallow to be safe.
                return False
            self._robots_cache[base] = rp
        allowed = rp.can_fetch(self.session.headers.get("User-Agent", "*"), url)
        if not allowed:
            print(f"robots.txt disallows: {url}")
        return allowed

    def _fetch_source(
        self,
        name: str,
        page_iter: Callable[[], List[str]],
        parse_listing: Callable[[str], Optional[JobPost]],
        limit: int,
    ) -> List[JobPost]:
        """Generic fetch helper with robots check and exclusion logging."""
        jobs: List[JobPost] = []
        seen_urls = set()
        for item_url in page_iter():
            if item_url in seen_urls:
                continue
            seen_urls.add(item_url)
            if not self._robots_allowed(item_url):
                continue
            job = parse_listing(item_url)
            if job:
                jobs.append(job)
            if len(jobs) >= limit:
                break
            time.sleep(self.delay)
        print(f"{name}: collected {len(jobs)} items (limit {limit})")
        return jobs

    def fetch_weworkremotely(
        self, max_pages: int = 20, limit: int = 500
    ) -> List[JobPost]:
        """Iterate paginated listings until we collect the desired amount."""
        def page_iter():
            for page in range(1, max_pages + 1):
                page_url = f"{BASE_WEWORK_URL}?page={page}"
                print(f"Scraping listing page: {page_url}")
                if not self._robots_allowed(page_url):
                    continue
                resp = self.session.get(page_url, timeout=15)
                if resp.status_code != 200:
                    print(f"Skipping page {page}, status: {resp.status_code}")
                    return

                soup = BeautifulSoup(resp.text, "lxml")
                anchors = soup.select("section.jobs li a[href^='/remote-jobs/']")
                if not anchors:
                    print("No more listings found; stopping.")
                    return
                for a in anchors:
                    href = a.get("href")
                    if not href:
                        continue
                    yield f"https://weworkremotely.com{href}"
                time.sleep(self.delay)

        def parse_listing(url: str) -> Optional[JobPost]:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                print(f"Failed detail fetch {url} ({resp.status_code})")
                return None
            soup = BeautifulSoup(resp.text, "lxml")
            # Detail page selectors
            title_node = soup.select_one("h1.listing-header-container") or soup.select_one(
                "div.listing-header-container h1"
            )
            company_node = soup.select_one("div.listing-company h2") or soup.select_one(
                "div.listing-header-container h2"
            )
            location_node = soup.select_one("div.listing-header-container span.location") or soup.select_one(
                "div.listing-header-container span.region"
            )
            title = title_node.get_text(strip=True) if title_node else ""
            company = company_node.get_text(strip=True) if company_node else ""
            location = location_node.get_text(strip=True) if location_node else ""
            description, skills = self._extract_detail_from_soup(soup)
            if not description:
                description = soup.get_text(separator=" ", strip=True)
            return JobPost(
                title=title or "",
                company=company or "",
                location=location or "",
                skills=", ".join(skills),
                description=description or "",
                source="weworkremotely",
                url=url,
            )

        return self._fetch_source(
            name="weworkremotely",
            page_iter=page_iter,
            parse_listing=parse_listing,
            limit=limit,
        )

    def fetch_remotive(self, max_pages: int = 10, limit: int = 400) -> List[JobPost]:
        """Scrape Remotive HTML listings (vetted remote board)."""
        def page_iter():
            for page in range(1, max_pages + 1):
                page_url = f"{BASE_REMOTIVE_URL}?page={page}"
                print(f"Scraping Remotive page: {page_url}")
                if not self._robots_allowed(page_url):
                    continue
                resp = self.session.get(page_url, timeout=15)
                if resp.status_code != 200:
                    print(f"Skip page {page} (status {resp.status_code})")
                    return
                soup = BeautifulSoup(resp.text, "lxml")
                anchors = soup.select("a.job-tile[href]")
                if not anchors:
                    print("No more Remotive listings; stopping.")
                    return
                for a in anchors:
                    href = a.get("href")
                    if not href:
                        continue
                    full = href if href.startswith("http") else urljoin("https://remotive.com", href)
                    yield full
                time.sleep(self.delay)

        def parse_listing(url: str) -> Optional[JobPost]:
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                print(f"Failed Remotive detail {url} ({resp.status_code})")
                return None
            soup = BeautifulSoup(resp.text, "lxml")
            title_node = soup.select_one("h1")
            company_node = soup.select_one("[data-testid='job-company-name']")
            location_node = soup.select_one("[data-testid='job-location']")
            title = title_node.get_text(strip=True) if title_node else ""
            company = company_node.get_text(strip=True) if company_node else ""
            location = location_node.get_text(strip=True) if location_node else ""
            description, skills = self._extract_detail_from_soup(soup)
            if not description:
                description = soup.get_text(separator=" ", strip=True)
            return JobPost(
                title=title,
                company=company,
                location=location,
                skills=", ".join(skills),
                description=description,
                source="remotive",
                url=url,
            )

        return self._fetch_source(
            name="remotive",
            page_iter=page_iter,
            parse_listing=parse_listing,
            limit=limit,
        )

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
    def _extract_detail_from_soup(soup: BeautifulSoup) -> tuple[Optional[str], List[str]]:
        """Shared detail extractor for parsed soup objects."""
        desc_node = soup.select_one("div.listing-container") or soup.select_one(
            "div.listing-body"
        ) or soup.select_one("[data-testid='job-description']")
        description = desc_node.get_text(separator=" ", strip=True) if desc_node else ""
        tags = [
            tag.get_text(strip=True)
            for tag in soup.select("span.listing-tag, .tag, [data-testid='job-tag']")
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
    ww_jobs = scraper.fetch_weworkremotely(limit=target_count)
    remaining = max(target_count - len(ww_jobs), 0)
    rm_jobs: List[JobPost] = []
    if remaining > 0:
        rm_jobs = scraper.fetch_remotive(limit=remaining)
    jobs = ww_jobs + rm_jobs
    print(f"Total jobs scraped: {len(jobs)} (WeworkRemotely {len(ww_jobs)}, Remotive {len(rm_jobs)})")
    data = [asdict(job) for job in jobs]
    df = pd.DataFrame(data)
    output_path = output_path or RAW_DATA_PATH
    df.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    run_scraper()
