"""
Base scraper class for JobPilot.
Provides common functionality for all job board scrapers.
"""

import time
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import json
import re

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import LoggerMixin, log_scraping_action, log_error
from utils.config import settings
from utils.models import JobListing, JobStatus, RemoteType, JobType, ExperienceLevel


class RateLimiter:
    """Simple rate limiter for web scraping."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self.last_request_time = 0
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            # Add some randomness to avoid being too predictable
            sleep_time += random.uniform(0, 0.5)
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()


class BaseScraper(ABC, LoggerMixin):
    """Base class for all job board scrapers."""
    
    def __init__(self, source_name: str, base_url: str, rate_limit: int = 60):
        """Initialize base scraper."""
        self.source_name = source_name
        self.base_url = base_url
        self.rate_limiter = RateLimiter(rate_limit)
        self.session = requests.Session()
        self.scraped_urls: Set[str] = set()
        
        # Setup session headers
        self.session.headers.update({
            'User-Agent': settings.browser_user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        self.logger.info(f"Initialized {source_name} scraper")
    
    def make_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Make a rate-limited HTTP request."""
        self.rate_limiter.wait_if_needed()
        
        try:
            log_scraping_action("HTTP Request", url)
            response = self.session.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            return response
            
        except requests.RequestException as e:
            log_error(e, f"making request to {url}")
            return None
    
    def get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Get BeautifulSoup object for a URL."""
        response = self.make_request(url)
        if response:
            return BeautifulSoup(response.content, 'html.parser')
        return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        
        return text.strip()
    
    def extract_salary_info(self, text: str) -> tuple[Optional[float], Optional[float], str]:
        """Extract salary information from text."""
        if not text:
            return None, None, "USD"
        
        # Common salary patterns
        patterns = [
            r'\$(\d+(?:,\d+)*(?:\.\d+)?)\s*-\s*\$(\d+(?:,\d+)*(?:\.\d+)?)',  # $50,000 - $70,000
            r'\$(\d+(?:,\d+)*(?:\.\d+)?)k\s*-\s*\$(\d+(?:,\d+)*(?:\.\d+)?)k',  # $50k - $70k
            r'\$(\d+(?:,\d+)*(?:\.\d+)?)',  # $50,000
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    min_sal = float(match.group(1).replace(',', ''))
                    max_sal = float(match.group(2).replace(',', ''))
                    
                    # Handle k notation
                    if 'k' in text.lower():
                        min_sal *= 1000
                        max_sal *= 1000
                    
                    return min_sal, max_sal, "USD"
                else:
                    salary = float(match.group(1).replace(',', ''))
                    if 'k' in text.lower():
                        salary *= 1000
                    return salary, None, "USD"
        
        return None, None, "USD"
    
    def detect_remote_type(self, text: str) -> Optional[RemoteType]:
        """Detect remote work type from text."""
        text = text.lower()
        
        if any(keyword in text for keyword in ['remote', 'work from home', 'wfh']):
            if any(keyword in text for keyword in ['hybrid', 'flexible', 'part remote']):
                return RemoteType.HYBRID
            return RemoteType.REMOTE
        elif any(keyword in text for keyword in ['on-site', 'onsite', 'office', 'in-person']):
            return RemoteType.ON_SITE
        
        return None
    
    def detect_job_type(self, text: str) -> Optional[JobType]:
        """Detect job type from text."""
        text = text.lower()
        
        if 'full-time' in text or 'full time' in text:
            return JobType.FULL_TIME
        elif 'part-time' in text or 'part time' in text:
            return JobType.PART_TIME
        elif 'contract' in text:
            return JobType.CONTRACT
        elif 'freelance' in text:
            return JobType.FREELANCE
        elif 'intern' in text:
            return JobType.INTERNSHIP
        elif 'temporary' in text or 'temp' in text:
            return JobType.TEMPORARY
        
        return None
    
    def detect_experience_level(self, text: str) -> Optional[ExperienceLevel]:
        """Detect experience level from text."""
        text = text.lower()
        
        if any(keyword in text for keyword in ['senior', 'sr.', 'lead', 'principal']):
            return ExperienceLevel.SENIOR_LEVEL
        elif any(keyword in text for keyword in ['junior', 'jr.', 'entry', 'graduate']):
            return ExperienceLevel.ENTRY_LEVEL
        elif any(keyword in text for keyword in ['mid', 'intermediate', 'associate']):
            return ExperienceLevel.MID_LEVEL
        elif any(keyword in text for keyword in ['director', 'head of', 'vp', 'vice president']):
            return ExperienceLevel.DIRECTOR
        elif any(keyword in text for keyword in ['executive', 'ceo', 'cto', 'cfo']):
            return ExperienceLevel.EXECUTIVE
        
        return None
    
    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extract technical skills from job description text."""
        # Common tech skills (this could be expanded or made configurable)
        skill_patterns = [
            # Programming languages
            r'\b(python|java|javascript|typescript|c\+\+|c#|php|ruby|go|rust|swift|kotlin)\b',
            # Frameworks
            r'\b(react|vue|angular|django|flask|spring|laravel|express|fastapi)\b',
            # Databases
            r'\b(postgresql|mysql|mongodb|redis|elasticsearch|cassandra|dynamodb)\b',
            # Cloud platforms
            r'\b(aws|azure|gcp|google cloud|docker|kubernetes|terraform)\b',
            # Tools
            r'\b(git|jenkins|jira|confluence|slack|figma|adobe)\b',
        ]
        
        skills = set()
        text_lower = text.lower()
        
        for pattern in skill_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                skills.add(match.group(1).title())
        
        return list(skills)
    
    def create_job_listing(self, job_data: Dict[str, Any]) -> JobListing:
        """Create a JobListing object from scraped data."""
        # Set defaults and source info
        job_data.setdefault('source', self.source_name)
        job_data.setdefault('status', JobStatus.DISCOVERED)
        job_data.setdefault('created_at', datetime.utcnow())
        
        # Clean text fields, but only if they have content
        for field in ['title', 'company', 'location', 'description']:
            if field in job_data and job_data[field]:
                cleaned = self.clean_text(job_data[field])
                # Only replace if cleaned version is not empty
                if cleaned:
                    job_data[field] = cleaned
        
        # Auto-detect properties from description if not provided
        description = job_data.get('description', '')
        
        if not job_data.get('remote_type') and description:
            job_data['remote_type'] = self.detect_remote_type(description)
        
        if not job_data.get('job_type') and description:
            job_data['job_type'] = self.detect_job_type(description)
        
        if not job_data.get('experience_level') and description:
            job_data['experience_level'] = self.detect_experience_level(description)
        
        # Extract skills if not provided
        if not job_data.get('skills_required') and description:
            job_data['skills_required'] = self.extract_skills_from_text(description)
        
        return JobListing(**job_data)
    
    @abstractmethod
    def search_jobs(self, 
                   query: str = "", 
                   location: str = "", 
                   max_pages: int = 5) -> List[JobListing]:
        """Search for jobs. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def scrape_job_details(self, job_url: str) -> Optional[Dict[str, Any]]:
        """Scrape detailed job information. Must be implemented by subclasses."""
        pass
    
    def scrape_jobs(self, 
                   queries: List[str] = None, 
                   locations: List[str] = None,
                   max_pages: int = 5) -> List[JobListing]:
        """Scrape jobs for multiple queries and locations."""
        all_jobs = []
        
        queries = queries or ["python", "software engineer", "data scientist"]
        locations = locations or ["remote", "san francisco", "new york"]
        
        for query in queries:
            for location in locations:
                self.logger.info(f"Scraping {self.source_name} for '{query}' in '{location}'")
                
                try:
                    jobs = self.search_jobs(query, location, max_pages)
                    all_jobs.extend(jobs)
                    
                    self.logger.info(f"Found {len(jobs)} jobs for '{query}' in '{location}'")
                    
                    # Small delay between different search combinations
                    time.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    log_error(e, f"scraping {query} in {location}")
        
        self.logger.info(f"Total jobs scraped from {self.source_name}: {len(all_jobs)}")
        return all_jobs
