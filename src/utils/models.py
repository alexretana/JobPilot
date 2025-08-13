"""
Core data models for JobPilot.
Defines the structure for jobs, user profiles, applications, and other core entities.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, EmailStr, validator
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

# =============================================================================
# ENUMS
# =============================================================================

class JobStatus(str, Enum):
    """Status of job applications."""
    DISCOVERED = "discovered"
    FILTERED = "filtered"
    MATCHED = "matched"
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    ACCEPTED = "accepted"
    WITHDRAWN = "withdrawn"


class ApplicationStatus(str, Enum):
    """Status of applications."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    COMPLETED = "completed"
    REJECTED = "rejected"
    OFFER_RECEIVED = "offer_received"
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_DECLINED = "offer_declined"


class JobType(str, Enum):
    """Types of employment."""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"


class ExperienceLevel(str, Enum):
    """Experience levels."""
    ENTRY_LEVEL = "entry_level"
    ASSOCIATE = "associate"
    MID_LEVEL = "mid_level"
    SENIOR_LEVEL = "senior_level"
    DIRECTOR = "director"
    EXECUTIVE = "executive"


class RemoteType(str, Enum):
    """Remote work options."""
    ON_SITE = "on_site"
    REMOTE = "remote"
    HYBRID = "hybrid"


# =============================================================================
# PYDANTIC MODELS (for API/serialization)
# =============================================================================

class BaseJobPilotModel(BaseModel):
    """Base model with common configurations."""
    
    class Config:
        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True


class JobListing(BaseJobPilotModel):
    """Represents a job listing from any source."""
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    company: str
    location: Optional[str] = None
    remote_type: Optional[RemoteType] = None
    job_type: Optional[JobType] = None
    experience_level: Optional[ExperienceLevel] = None
    
    description: str
    requirements: Optional[List[str]] = []
    responsibilities: Optional[List[str]] = []
    benefits: Optional[List[str]] = []
    
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = "USD"
    
    posted_date: Optional[datetime] = None
    expires_date: Optional[datetime] = None
    
    source: str  # "linkedin", "indeed", "glassdoor", etc.
    source_url: Optional[HttpUrl] = None
    source_id: Optional[str] = None
    
    skills_required: Optional[List[str]] = []
    skills_preferred: Optional[List[str]] = []
    
    relevance_score: Optional[float] = None
    match_reasons: Optional[List[str]] = []
    
    status: JobStatus = JobStatus.DISCOVERED
    notes: Optional[str] = None
    tags: Optional[List[str]] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = {}


class UserProfile(BaseJobPilotModel):
    """Represents user's profile and preferences."""
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Personal Information
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    
    # Professional Information
    current_title: Optional[str] = None
    experience_years: Optional[int] = None
    industry: Optional[str] = None
    
    # Skills and Preferences
    skills: List[str] = []
    preferred_titles: List[str] = []
    preferred_companies: Optional[List[str]] = []
    preferred_locations: List[str] = []
    preferred_remote_types: List[RemoteType] = []
    preferred_job_types: List[JobType] = []
    
    # Salary Preferences
    desired_salary_min: Optional[float] = None
    desired_salary_max: Optional[float] = None
    salary_currency: str = "USD"
    
    # Documents
    resume_path: Optional[str] = None
    cover_letter_template: Optional[str] = None
    portfolio_url: Optional[HttpUrl] = None
    linkedin_url: Optional[HttpUrl] = None
    
    # Search Preferences
    job_alert_frequency: Optional[str] = "daily"  # daily, weekly, never
    auto_apply: bool = False
    max_applications_per_day: int = 5
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class Company(BaseJobPilotModel):
    """Represents company information."""
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    
    # URLs and Social
    website: Optional[HttpUrl] = None
    linkedin_url: Optional[HttpUrl] = None
    glassdoor_url: Optional[HttpUrl] = None
    
    # Ratings and Reviews
    glassdoor_rating: Optional[float] = None
    glassdoor_reviews_count: Optional[int] = None
    
    # Research Data
    culture_notes: Optional[str] = None
    hiring_process_notes: Optional[str] = None
    recent_news: Optional[List[str]] = []
    
    # Contact Information
    recruiters: Optional[List[str]] = []
    employees: Optional[List[str]] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class Contact(BaseJobPilotModel):
    """Represents a contact (recruiter, employee, etc.)."""
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic Information
    first_name: str
    last_name: str
    title: Optional[str] = None
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    
    # Contact Information
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    linkedin_url: Optional[HttpUrl] = None
    
    # Relationship Information
    contact_type: str = "unknown"  # recruiter, employee, hiring_manager, etc.
    source: str = "manual"  # linkedin, referral, manual, etc.
    
    # Interaction History
    last_contact_date: Optional[datetime] = None
    contact_frequency: Optional[str] = None
    notes: Optional[str] = None
    
    # Metadata
    tags: List[str] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class Application(BaseJobPilotModel):
    """Represents a job application."""
    
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # References
    job_id: str
    user_id: str
    
    # Application Details
    status: ApplicationStatus = ApplicationStatus.PENDING
    applied_date: Optional[datetime] = None
    
    # Documents Used
    resume_used: Optional[str] = None
    cover_letter_used: Optional[str] = None
    
    # Tracking Information
    application_method: Optional[str] = None  # "website", "email", "linkedin", etc.
    confirmation_number: Optional[str] = None
    
    # Follow-up Information
    follow_up_date: Optional[datetime] = None
    interview_dates: Optional[List[datetime]] = []
    
    # Outcome
    rejection_date: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    offer_date: Optional[datetime] = None
    offer_amount: Optional[float] = None
    
    # Notes and Communication
    notes: Optional[str] = None
    communication_log: Optional[List[Dict[str, Any]]] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


# =============================================================================
# SQLAlchemy MODELS (for database)
# =============================================================================

class JobListingDB(Base):
    """Database model for job listings."""
    
    __tablename__ = "job_listings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String)
    remote_type = Column(String)
    job_type = Column(String)
    experience_level = Column(String)
    
    description = Column(Text, nullable=False)
    requirements = Column(JSON)
    responsibilities = Column(JSON)
    benefits = Column(JSON)
    
    salary_min = Column(Float)
    salary_max = Column(Float)
    salary_currency = Column(String, default="USD")
    
    posted_date = Column(DateTime)
    expires_date = Column(DateTime)
    
    source = Column(String, nullable=False)
    source_url = Column(String)
    source_id = Column(String)
    
    skills_required = Column(JSON)
    skills_preferred = Column(JSON)
    
    relevance_score = Column(Float)
    match_reasons = Column(JSON)
    
    status = Column(String, default=JobStatus.DISCOVERED.value)
    notes = Column(Text)
    tags = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    extra_metadata = Column(JSON)


class UserProfileDB(Base):
    """Database model for user profiles."""
    
    __tablename__ = "user_profiles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String)
    location = Column(String)
    
    current_title = Column(String)
    experience_years = Column(Integer)
    industry = Column(String)
    
    skills = Column(JSON)
    preferred_titles = Column(JSON)
    preferred_companies = Column(JSON)
    preferred_locations = Column(JSON)
    preferred_remote_types = Column(JSON)
    preferred_job_types = Column(JSON)
    
    desired_salary_min = Column(Float)
    desired_salary_max = Column(Float)
    salary_currency = Column(String, default="USD")
    
    resume_path = Column(String)
    cover_letter_template = Column(String)
    portfolio_url = Column(String)
    linkedin_url = Column(String)
    
    job_alert_frequency = Column(String, default="daily")
    auto_apply = Column(Boolean, default=False)
    max_applications_per_day = Column(Integer, default=5)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


class ApplicationDB(Base):
    """Database model for applications."""
    
    __tablename__ = "applications"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    job_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    
    status = Column(String, default=ApplicationStatus.PENDING.value)
    applied_date = Column(DateTime)
    
    resume_used = Column(String)
    cover_letter_used = Column(String)
    
    application_method = Column(String)
    confirmation_number = Column(String)
    
    follow_up_date = Column(DateTime)
    interview_dates = Column(JSON)
    
    rejection_date = Column(DateTime)
    rejection_reason = Column(String)
    offer_date = Column(DateTime)
    offer_amount = Column(Float)
    
    notes = Column(Text)
    communication_log = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
