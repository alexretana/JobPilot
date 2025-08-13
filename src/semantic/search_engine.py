"""
Semantic search engine for JobPilot.
Handles job-to-user matching, relevance scoring, and semantic search.
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
from pathlib import Path
import json
from datetime import datetime, timedelta
import sqlalchemy

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import LoggerMixin, log_error
from utils.database import db_manager, job_repo
from utils.models import JobStatus
from semantic.embeddings import embedding_service


@dataclass
class JobMatch:
    """Represents a job match with relevance scores and explanations."""
    job_id: str
    job_title: str
    company: str
    location: str
    semantic_score: float
    skills_match_score: float
    experience_match_score: float
    salary_match_score: float
    location_match_score: float
    overall_score: float
    match_reasons: List[str]
    raw_job_data: Dict


@dataclass
class SearchFilters:
    """Search filters for job matching."""
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    job_types: Optional[List[str]] = None
    remote_types: Optional[List[str]] = None
    experience_levels: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    companies: Optional[List[str]] = None
    required_skills: Optional[List[str]] = None
    excluded_skills: Optional[List[str]] = None
    max_age_days: Optional[int] = 30


class SemanticSearchEngine(LoggerMixin):
    """AI-powered job search and matching engine."""
    
    def __init__(self):
        """Initialize the semantic search engine."""
        self.embedding_service = embedding_service
        self.logger.info("SemanticSearchEngine initialized")
    
    def search_jobs_semantic(self, 
                           query: str, 
                           user_profile: Optional[Dict] = None,
                           filters: Optional[SearchFilters] = None,
                           limit: int = 20) -> List[JobMatch]:
        """
        Perform semantic search for jobs based on query and user profile.
        
        Args:
            query: Search query text
            user_profile: User profile for personalized matching
            filters: Additional search filters
            limit: Maximum number of results to return
            
        Returns:
            List of JobMatch objects sorted by relevance
        """
        try:
            # Get all jobs from database that match basic filters
            jobs = self._get_filtered_jobs(filters)
            if not jobs:
                self.logger.info("No jobs found matching filters")
                return []
            
            self.logger.info(f"Found {len(jobs)} jobs matching filters")
            
            # Generate query embedding
            query_embedding = self.embedding_service.embed_text(query)
            
            # Generate user profile embedding if provided
            user_embedding = None
            if user_profile:
                user_embedding = self.embedding_service.embed_user_profile(user_profile)
            
            # Calculate matches for all jobs
            job_matches = []
            for job in jobs:
                try:
                    job_match = self._calculate_job_match(
                        job, query_embedding, user_embedding, user_profile
                    )
                    if job_match:
                        job_matches.append(job_match)
                except Exception as e:
                    log_error(e, f"calculating match for job {job.id}")
                    continue
            
            # Sort by overall score
            job_matches.sort(key=lambda x: x.overall_score, reverse=True)
            
            self.logger.info(f"Generated {len(job_matches)} job matches")
            return job_matches[:limit]
            
        except Exception as e:
            log_error(e, "semantic job search")
            return []
    
    def _get_filtered_jobs(self, filters: Optional[SearchFilters] = None) -> List:
        """Get jobs from database with basic filters applied."""
        try:
            with db_manager.get_session() as session:
                from utils.models import JobListingDB
                
                query = session.query(JobListingDB)
                
                # Apply filters
                if filters:
                    # Salary filter
                    if filters.min_salary is not None:
                        query = query.filter(JobListingDB.salary_max >= filters.min_salary)
                    if filters.max_salary is not None:
                        query = query.filter(JobListingDB.salary_min <= filters.max_salary)
                    
                    # Job type filter
                    if filters.job_types:
                        query = query.filter(JobListingDB.job_type.in_(filters.job_types))
                    
                    # Remote type filter
                    if filters.remote_types:
                        query = query.filter(JobListingDB.remote_type.in_(filters.remote_types))
                    
                    # Experience level filter
                    if filters.experience_levels:
                        query = query.filter(JobListingDB.experience_level.in_(filters.experience_levels))
                    
                    # Location filter
                    if filters.locations:
                        location_filters = []
                        for location in filters.locations:
                            location_filters.append(JobListingDB.location.contains(location))
                        query = query.filter(sqlalchemy.or_(*location_filters))
                    
                    # Company filter
                    if filters.companies:
                        query = query.filter(JobListingDB.company.in_(filters.companies))
                    
                    # Age filter
                    if filters.max_age_days:
                        cutoff_date = datetime.now() - timedelta(days=filters.max_age_days)
                        query = query.filter(JobListingDB.posted_date >= cutoff_date)
                
                jobs = query.all()
                
                # Detach from session
                for job in jobs:
                    session.expunge(job)
                
                return jobs
                
        except Exception as e:
            log_error(e, "filtering jobs from database")
            return []
    
    def _calculate_job_match(self, 
                           job, 
                           query_embedding: np.ndarray,
                           user_embedding: Optional[np.ndarray] = None,
                           user_profile: Optional[Dict] = None) -> Optional[JobMatch]:
        """Calculate comprehensive match score for a job."""
        try:
            # Convert job to dictionary
            job_dict = {
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'description': job.description,
                'requirements': job.requirements,
                'responsibilities': job.responsibilities,
                'skills_required': job.skills_required,
                'skills_preferred': job.skills_preferred,
                'salary_min': job.salary_min,
                'salary_max': job.salary_max,
                'job_type': job.job_type,
                'remote_type': job.remote_type,
                'experience_level': job.experience_level,
                'posted_date': job.posted_date,
            }
            
            # Generate job embedding
            job_embedding = self.embedding_service.embed_job_description(job_dict)
            
            # Calculate semantic similarity with query
            semantic_score = self.embedding_service.calculate_similarity(
                query_embedding, job_embedding
            )
            
            # Calculate other match scores
            skills_match_score = self._calculate_skills_match(job_dict, user_profile)
            experience_match_score = self._calculate_experience_match(job_dict, user_profile)
            salary_match_score = self._calculate_salary_match(job_dict, user_profile)
            location_match_score = self._calculate_location_match(job_dict, user_profile)
            
            # Calculate overall weighted score
            overall_score = self._calculate_overall_score(
                semantic_score, skills_match_score, experience_match_score,
                salary_match_score, location_match_score
            )
            
            # Generate match reasons
            match_reasons = self._generate_match_reasons(
                job_dict, user_profile, semantic_score, skills_match_score,
                experience_match_score, salary_match_score, location_match_score
            )
            
            return JobMatch(
                job_id=job.id,
                job_title=job.title,
                company=job.company,
                location=job.location or "Not specified",
                semantic_score=semantic_score,
                skills_match_score=skills_match_score,
                experience_match_score=experience_match_score,
                salary_match_score=salary_match_score,
                location_match_score=location_match_score,
                overall_score=overall_score,
                match_reasons=match_reasons,
                raw_job_data=job_dict
            )
            
        except Exception as e:
            log_error(e, f"calculating job match for job {job.id}")
            return None
    
    def _calculate_skills_match(self, job_dict: Dict, user_profile: Optional[Dict]) -> float:
        """Calculate skills compatibility score."""
        if not user_profile or not user_profile.get('skills'):
            return 0.5  # Neutral score
        
        try:
            user_skills = set(skill.lower() for skill in user_profile['skills'])
            
            # Get job skills
            job_skills = set()
            if job_dict.get('skills_required'):
                if isinstance(job_dict['skills_required'], list):
                    job_skills.update(skill.lower() for skill in job_dict['skills_required'])
            
            if job_dict.get('skills_preferred'):
                if isinstance(job_dict['skills_preferred'], list):
                    job_skills.update(skill.lower() for skill in job_dict['skills_preferred'])
            
            if not job_skills:
                return 0.5  # Neutral if no job skills listed
            
            # Calculate overlap
            overlap = len(user_skills.intersection(job_skills))
            total_job_skills = len(job_skills)
            
            # Calculate score based on overlap ratio
            if total_job_skills == 0:
                return 0.5
            
            score = overlap / total_job_skills
            return min(score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            log_error(e, "calculating skills match")
            return 0.5
    
    def _calculate_experience_match(self, job_dict: Dict, user_profile: Optional[Dict]) -> float:
        """Calculate experience level match score."""
        if not user_profile or not user_profile.get('experience_years'):
            return 0.5  # Neutral score
        
        try:
            user_years = user_profile['experience_years']
            job_level = (job_dict.get('experience_level') or '').lower()
            
            # Map experience levels to years
            level_to_years = {
                'entry_level': (0, 2),
                'associate': (1, 3),
                'mid_level': (3, 7),
                'senior_level': (5, 12),
                'director': (8, 20),
                'executive': (10, 30)
            }
            
            if job_level not in level_to_years:
                return 0.5  # Neutral if unknown level
            
            min_years, max_years = level_to_years[job_level]
            
            if min_years <= user_years <= max_years:
                return 1.0  # Perfect match
            elif user_years < min_years:
                # Under-qualified, score decreases with gap
                gap = min_years - user_years
                return max(0.0, 1.0 - (gap / 5.0))  # Decrease by 0.2 per year gap
            else:
                # Over-qualified, slight penalty
                gap = user_years - max_years
                return max(0.6, 1.0 - (gap / 10.0))  # Slight decrease for over-qualification
                
        except Exception as e:
            log_error(e, "calculating experience match")
            return 0.5
    
    def _calculate_salary_match(self, job_dict: Dict, user_profile: Optional[Dict]) -> float:
        """Calculate salary expectations match score."""
        if not user_profile:
            return 0.5
        
        try:
            user_min = user_profile.get('desired_salary_min')
            user_max = user_profile.get('desired_salary_max')
            job_min = job_dict.get('salary_min')
            job_max = job_dict.get('salary_max')
            
            # If any salary info is missing, return neutral
            if not any([user_min, user_max, job_min, job_max]):
                return 0.5
            
            # If job has no salary info, slight penalty
            if not job_min and not job_max:
                return 0.4
            
            # If user has no preferences, return neutral
            if not user_min and not user_max:
                return 0.5
            
            # Calculate overlap between ranges
            job_range = (job_min or 0, job_max or float('inf'))
            user_range = (user_min or 0, user_max or float('inf'))
            
            overlap_start = max(job_range[0], user_range[0])
            overlap_end = min(job_range[1], user_range[1])
            
            if overlap_start <= overlap_end:
                # There's an overlap, calculate how good it is
                overlap_size = overlap_end - overlap_start
                job_range_size = job_range[1] - job_range[0]
                user_range_size = user_range[1] - user_range[0]
                
                # Score based on overlap ratio
                if job_range_size > 0 and user_range_size > 0:
                    avg_range_size = (job_range_size + user_range_size) / 2
                    score = overlap_size / avg_range_size
                    return min(score, 1.0)
                else:
                    return 1.0  # Perfect overlap if ranges are points
            else:
                # No overlap, calculate penalty based on gap
                gap = overlap_start - overlap_end
                avg_salary = (sum(filter(None, [job_min, job_max, user_min, user_max])) / 
                             len(list(filter(None, [job_min, job_max, user_min, user_max]))))
                
                if avg_salary > 0:
                    gap_ratio = gap / avg_salary
                    return max(0.0, 1.0 - gap_ratio)
                else:
                    return 0.0
                    
        except Exception as e:
            log_error(e, "calculating salary match")
            return 0.5
    
    def _calculate_location_match(self, job_dict: Dict, user_profile: Optional[Dict]) -> float:
        """Calculate location preferences match score."""
        if not user_profile or not user_profile.get('preferred_locations'):
            return 0.5  # Neutral if no preferences
        
        try:
            user_locations = [loc.lower() for loc in user_profile['preferred_locations']]
            job_location = (job_dict.get('location') or '').lower()
            job_remote = (job_dict.get('remote_type') or '').lower()
            
            # Perfect match for remote if user prefers remote
            if 'remote' in user_locations and job_remote in ['remote', 'hybrid']:
                return 1.0
            
            # Check if job location matches any preferred locations
            for user_loc in user_locations:
                if user_loc in job_location or job_location in user_loc:
                    return 1.0
            
            # Partial match for hybrid work
            if job_remote == 'hybrid':
                return 0.7
            
            # No match
            return 0.2
            
        except Exception as e:
            log_error(e, "calculating location match")
            return 0.5
    
    def _calculate_overall_score(self, 
                               semantic: float,
                               skills: float,
                               experience: float,
                               salary: float,
                               location: float) -> float:
        """Calculate weighted overall match score."""
        # Define weights for different factors
        weights = {
            'semantic': 0.35,    # Most important: semantic similarity
            'skills': 0.25,      # Skills compatibility
            'experience': 0.20,  # Experience level match
            'salary': 0.15,      # Salary expectations
            'location': 0.05     # Location preferences (least important due to remote work)
        }
        
        overall = (
            semantic * weights['semantic'] +
            skills * weights['skills'] +
            experience * weights['experience'] +
            salary * weights['salary'] +
            location * weights['location']
        )
        
        return round(overall, 3)
    
    def _generate_match_reasons(self, 
                              job_dict: Dict,
                              user_profile: Optional[Dict],
                              semantic: float,
                              skills: float,
                              experience: float,
                              salary: float,
                              location: float) -> List[str]:
        """Generate human-readable match explanations."""
        reasons = []
        
        # Semantic similarity reasons
        if semantic > 0.7:
            reasons.append("Excellent match with your search query and interests")
        elif semantic > 0.5:
            reasons.append("Good alignment with your search criteria")
        
        # Skills reasons
        if skills > 0.7 and user_profile and user_profile.get('skills'):
            user_skills = set(skill.lower() for skill in user_profile['skills'])
            job_skills = set()
            
            if job_dict.get('skills_required'):
                if isinstance(job_dict['skills_required'], list):
                    job_skills.update(skill.lower() for skill in job_dict['skills_required'])
            
            matching_skills = user_skills.intersection(job_skills)
            if matching_skills:
                skills_list = list(matching_skills)[:3]  # Show top 3
                reasons.append(f"Strong skills match: {', '.join(skills_list)}")
        
        # Experience reasons
        if experience > 0.8:
            reasons.append("Perfect experience level match")
        elif experience > 0.6:
            reasons.append("Good experience level alignment")
        elif experience < 0.4:
            job_level = job_dict.get('experience_level', '').replace('_', ' ').title()
            if job_level:
                reasons.append(f"Consider this {job_level} opportunity for growth")
        
        # Salary reasons
        if salary > 0.7:
            reasons.append("Salary range aligns with your expectations")
        elif salary < 0.3 and job_dict.get('salary_min'):
            reasons.append("Salary may be below expectations")
        
        # Location reasons
        if location > 0.8:
            if job_dict.get('remote_type') == 'remote':
                reasons.append("Fully remote position")
            else:
                reasons.append("Location matches your preferences")
        elif job_dict.get('remote_type') == 'hybrid':
            reasons.append("Hybrid work arrangement available")
        
        # Company and role specific reasons
        if job_dict.get('company'):
            reasons.append(f"Opportunity at {job_dict['company']}")
        
        return reasons[:5]  # Limit to top 5 reasons
    
    def find_similar_jobs(self, job_id: str, limit: int = 10) -> List[JobMatch]:
        """Find jobs similar to a given job."""
        try:
            # Get the reference job
            ref_job = job_repo.get_job(job_id)
            if not ref_job:
                self.logger.warning(f"Job {job_id} not found")
                return []
            
            # Convert to dict and get embedding
            ref_job_dict = {
                'title': ref_job.title,
                'description': ref_job.description,
                'requirements': ref_job.requirements,
                'responsibilities': ref_job.responsibilities,
                'skills_required': ref_job.skills_required,
                'skills_preferred': ref_job.skills_preferred,
            }
            
            ref_embedding = self.embedding_service.embed_job_description(ref_job_dict)
            
            # Get all other jobs and calculate similarity
            all_jobs = self._get_filtered_jobs()
            similar_jobs = []
            
            for job in all_jobs:
                if job.id == job_id:
                    continue  # Skip the reference job
                
                try:
                    job_dict = {
                        'title': job.title,
                        'description': job.description,
                        'requirements': job.requirements,
                        'responsibilities': job.responsibilities,
                        'skills_required': job.skills_required,
                        'skills_preferred': job.skills_preferred,
                    }
                    
                    job_embedding = self.embedding_service.embed_job_description(job_dict)
                    similarity = self.embedding_service.calculate_similarity(ref_embedding, job_embedding)
                    
                    if similarity > 0.3:  # Only include reasonably similar jobs
                        job_match = JobMatch(
                            job_id=job.id,
                            job_title=job.title,
                            company=job.company,
                            location=job.location or "Not specified",
                            semantic_score=similarity,
                            skills_match_score=0.0,  # Not calculated for similar jobs
                            experience_match_score=0.0,
                            salary_match_score=0.0,
                            location_match_score=0.0,
                            overall_score=similarity,
                            match_reasons=[f"Similar to {ref_job.title} at {ref_job.company}"],
                            raw_job_data=job_dict
                        )
                        similar_jobs.append(job_match)
                        
                except Exception as e:
                    log_error(e, f"calculating similarity for job {job.id}")
                    continue
            
            # Sort by similarity and return top matches
            similar_jobs.sort(key=lambda x: x.semantic_score, reverse=True)
            return similar_jobs[:limit]
            
        except Exception as e:
            log_error(e, f"finding similar jobs to {job_id}")
            return []
    
    def get_search_stats(self) -> Dict:
        """Get statistics about the search engine."""
        try:
            stats = db_manager.get_table_stats()
            embedding_info = self.embedding_service.get_model_info()
            
            return {
                'total_jobs': stats.get('job_listings', 0),
                'embedding_model': embedding_info['model_name'],
                'embedding_dimension': embedding_info['embedding_dimension'],
                'search_engine_version': '1.0.0'
            }
            
        except Exception as e:
            log_error(e, "getting search stats")
            return {}


# Global search engine instance
search_engine = SemanticSearchEngine()
