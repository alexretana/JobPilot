"""
Demo scraper for JobPilot testing and demonstration.
Creates mock job listings to test the scraping and storage pipeline.
"""

import random
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.base_scraper import BaseScraper
from utils.models import JobListing, JobStatus, RemoteType, JobType, ExperienceLevel


class DemoScraper(BaseScraper):
    """Demo scraper that generates realistic mock job listings for testing."""
    
    def __init__(self):
        super().__init__("demo", "https://demo-jobs.example.com", rate_limit=120)
        
        # Mock data for generating realistic jobs
        self.companies = [
            "TechCorp", "InnovateLabs", "DataDriven Inc", "CloudScale Solutions",
            "AI Frontiers", "DevOps Masters", "SecureCode Ltd", "GrowthHackers",
            "QuantumSoft", "NextGen Systems", "CodeCrafters", "ByteBuilders"
        ]
        
        self.job_titles = [
            "Senior Python Developer", "Full Stack Engineer", "Data Scientist",
            "DevOps Engineer", "Machine Learning Engineer", "Backend Developer",
            "Frontend Developer", "Software Architect", "Cloud Engineer",
            "Security Engineer", "Product Manager", "Engineering Manager"
        ]
        
        self.locations = [
            "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX",
            "Boston, MA", "Los Angeles, CA", "Chicago, IL", "Remote",
            "Denver, CO", "Portland, OR", "Atlanta, GA", "Miami, FL"
        ]
        
        self.skills_pool = [
            "Python", "JavaScript", "TypeScript", "Java", "Go", "Rust",
            "React", "Vue", "Angular", "Django", "Flask", "FastAPI",
            "PostgreSQL", "MongoDB", "Redis", "Docker", "Kubernetes",
            "AWS", "Azure", "GCP", "Terraform", "Jenkins", "Git"
        ]
        
        self.description_templates = [
            """We are looking for a {title} to join our dynamic team. You'll be working on cutting-edge projects
            using {skills}. This is a {job_type} position with {remote_type} work options.
            
            Responsibilities:
            • Design and implement scalable software solutions
            • Collaborate with cross-functional teams
            • Write clean, maintainable code
            • Participate in code reviews and technical discussions
            
            Requirements:
            • {experience} years of experience with {primary_skill}
            • Strong knowledge of {skills}
            • Experience with {secondary_skills}
            • Excellent problem-solving skills
            
            We offer competitive salary, comprehensive benefits, and opportunities for growth.""",
            
            """Join {company} as a {title}! We're revolutionizing the tech industry with innovative solutions.
            
            What you'll do:
            • Build and maintain applications using {skills}
            • Work in an agile environment
            • Mentor junior developers
            • Drive technical decisions
            
            What we're looking for:
            • {experience}+ years of experience
            • Expertise in {primary_skill}
            • Experience with {secondary_skills}
            • Strong communication skills
            
            Benefits include competitive salary, stock options, and flexible work arrangements."""
        ]
    
    def generate_mock_job(self, query: str = "", location: str = "") -> Dict[str, Any]:
        """Generate a single mock job listing."""
        
        # Select random data
        company = random.choice(self.companies)
        title = random.choice(self.job_titles)
        
        # Use provided location or random
        job_location = location if location and location != "remote" else random.choice(self.locations)
        
        # Generate skills based on query
        skills = random.sample(self.skills_pool, k=random.randint(3, 8))
        if query and query.lower() in [skill.lower() for skill in self.skills_pool]:
            # Ensure the queried skill is included
            if not any(skill.lower() == query.lower() for skill in skills):
                skills[0] = query.title()
        
        primary_skill = skills[0]
        secondary_skills = ", ".join(skills[1:4])
        
        # Generate job details
        job_type = random.choice(list(JobType))
        remote_type = random.choice(list(RemoteType))
        experience_level = random.choice(list(ExperienceLevel))
        
        # Generate salary
        base_salary = random.randint(60, 200) * 1000
        salary_min = base_salary
        salary_max = base_salary + random.randint(20, 50) * 1000
        
        # Generate experience years
        exp_years = random.randint(2, 10)
        
        # Generate description
        template = random.choice(self.description_templates)
        description = template.format(
            title=title.lower(),
            company=company,
            skills=", ".join(skills[:3]),
            job_type=job_type.value.replace('_', '-'),
            remote_type=remote_type.value.replace('_', ' '),
            experience=exp_years,
            primary_skill=primary_skill,
            secondary_skills=secondary_skills
        )
        
        # Generate timestamps
        posted_date = datetime.now() - timedelta(days=random.randint(1, 30))
        expires_date = posted_date + timedelta(days=random.randint(30, 90))
        
        return {
            'title': title,
            'company': company,
            'location': job_location,
            'description': description,
            'remote_type': remote_type,
            'job_type': job_type,
            'experience_level': experience_level,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'salary_currency': 'USD',
            'posted_date': posted_date,
            'expires_date': expires_date,
            'source_url': f"https://demo-jobs.example.com/job/{random.randint(1000, 9999)}",
            'source_id': f"demo_{random.randint(10000, 99999)}",
            'skills_required': skills[:5],
            'skills_preferred': skills[3:],
            'requirements': [
                f"{exp_years}+ years of experience",
                f"Strong knowledge of {primary_skill}",
                f"Experience with {secondary_skills}",
                "Excellent problem-solving skills"
            ],
            'responsibilities': [
                "Design and implement scalable solutions",
                "Collaborate with cross-functional teams",
                "Write clean, maintainable code",
                "Participate in code reviews"
            ],
            'benefits': [
                "Competitive salary",
                "Health insurance",
                "401k matching",
                "Flexible work hours",
                "Professional development budget"
            ]
        }
    
    def search_jobs(self, 
                   query: str = "", 
                   location: str = "", 
                   max_pages: int = 5) -> List[JobListing]:
        """Generate mock job search results."""
        
        # Simulate search delay
        time.sleep(random.uniform(0.5, 2.0))
        
        # Generate 5-15 jobs per "search"
        num_jobs = random.randint(5, 15)
        jobs = []
        
        for _ in range(num_jobs):
            try:
                job_data = self.generate_mock_job(query, location)
                job_listing = self.create_job_listing(job_data)
                jobs.append(job_listing)
                
            except Exception as e:
                self.logger.error(f"Error generating mock job: {e}")
        
        return jobs
    
    def scrape_job_details(self, job_url: str) -> Optional[Dict[str, Any]]:
        """Generate detailed mock job information."""
        
        # Simulate network delay
        time.sleep(random.uniform(0.2, 1.0))
        
        # For demo purposes, just generate additional details
        return {
            'benefits': [
                "Health, dental, and vision insurance",
                "401k with company matching",
                "Unlimited PTO",
                "Remote work options",
                "Professional development budget",
                "Stock options"
            ],
            'company_info': {
                'size': f"{random.randint(50, 5000)} employees",
                'industry': random.choice(['Technology', 'Finance', 'Healthcare', 'E-commerce']),
                'founded': random.randint(2000, 2020)
            },
            'application_process': "Apply through our careers page with resume and cover letter."
        }
    
    def get_demo_stats(self) -> Dict[str, Any]:
        """Get statistics about the demo scraper."""
        return {
            'companies': len(self.companies),
            'job_titles': len(self.job_titles),
            'locations': len(self.locations),
            'skills': len(self.skills_pool),
            'description_templates': len(self.description_templates)
        }
