"""
Database management for JobPilot.
Handles database connections, migrations, and CRUD operations.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Type, TypeVar
from sqlalchemy import create_engine, MetaData, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager

from .config import settings
from .logger import LoggerMixin, log_error
from .models import Base, JobListingDB, UserProfileDB, ApplicationDB

T = TypeVar('T')


class DatabaseManager(LoggerMixin):
    """Manages database connections and operations."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager."""
        self.database_url = database_url or settings.database_url
        self.engine = None
        self.SessionLocal = None
        self._setup_database()
    
    def _setup_database(self) -> None:
        """Set up database engine and session factory."""
        try:
            # Create database directory if using SQLite
            if self.database_url.startswith('sqlite'):
                db_path = self.database_url.replace('sqlite:///', '')
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Create engine
            self.engine = create_engine(
                self.database_url,
                echo=settings.debug_mode,  # Log SQL queries in debug mode
                pool_pre_ping=True,  # Verify connections before use
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            self.logger.info(f"Database engine created: {self.database_url}")
            
        except Exception as e:
            log_error(e, "database setup")
            raise
    
    def create_tables(self) -> None:
        """Create all tables in the database."""
        try:
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("Database tables created successfully")
            
            # Log created tables
            inspector = inspect(self.engine)
            table_names = inspector.get_table_names()
            self.logger.info(f"Created tables: {table_names}")
            
        except Exception as e:
            log_error(e, "table creation")
            raise
    
    def drop_tables(self) -> None:
        """Drop all tables in the database."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            self.logger.info("Database tables dropped successfully")
        except Exception as e:
            log_error(e, "table dropping")
            raise
    
    def reset_database(self) -> None:
        """Reset database by dropping and recreating all tables."""
        self.logger.warning("Resetting database - all data will be lost!")
        self.drop_tables()
        self.create_tables()
        self.logger.info("Database reset completed")
    
    @contextmanager
    def get_session(self):
        """Get a database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            log_error(e, "database session")
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            self.logger.info("Database health check passed")
            return True
        except Exception as e:
            log_error(e, "database health check")
            return False
    
    def get_table_stats(self) -> Dict[str, int]:
        """Get row counts for all tables."""
        stats = {}
        try:
            with self.get_session() as session:
                stats['job_listings'] = session.query(JobListingDB).count()
                stats['user_profiles'] = session.query(UserProfileDB).count()
                stats['applications'] = session.query(ApplicationDB).count()
            
            self.logger.info(f"Table statistics: {stats}")
            return stats
            
        except Exception as e:
            log_error(e, "getting table stats")
            return {}


class JobRepository(LoggerMixin):
    """Repository for job listing operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_job(self, job_data: Dict[str, Any]) -> Optional[JobListingDB]:
        """Create a new job listing."""
        try:
            with self.db_manager.get_session() as session:
                job = JobListingDB(**job_data)
                session.add(job)
                session.flush()  # Get the ID
                session.refresh(job)
                
                self.logger.info(f"Created job listing: {job.id} - {job.title}")
                session.expunge(job)  # Detach from session so it can be used outside
                return job
                
        except Exception as e:
            log_error(e, f"creating job listing")
            return None
    
    def get_job(self, job_id: str) -> Optional[JobListingDB]:
        """Get a job listing by ID."""
        try:
            with self.db_manager.get_session() as session:
                job = session.query(JobListingDB).filter(JobListingDB.id == job_id).first()
                if job:
                    session.expunge(job)  # Detach from session so it can be used outside
                return job
        except Exception as e:
            log_error(e, f"getting job {job_id}")
            return None
    
    def get_jobs_by_status(self, status: str, limit: int = 100) -> List[JobListingDB]:
        """Get jobs by status."""
        try:
            with self.db_manager.get_session() as session:
                jobs = (session.query(JobListingDB)
                       .filter(JobListingDB.status == status)
                       .limit(limit)
                       .all())
                return jobs
        except Exception as e:
            log_error(e, f"getting jobs by status {status}")
            return []
    
    def get_jobs_by_source(self, source: str, limit: int = 100) -> List[JobListingDB]:
        """Get jobs by source."""
        try:
            with self.db_manager.get_session() as session:
                jobs = (session.query(JobListingDB)
                       .filter(JobListingDB.source == source)
                       .limit(limit)
                       .all())
                return jobs
        except Exception as e:
            log_error(e, f"getting jobs by source {source}")
            return []
    
    def update_job_status(self, job_id: str, new_status: str) -> bool:
        """Update job status."""
        try:
            with self.db_manager.get_session() as session:
                job = session.query(JobListingDB).filter(JobListingDB.id == job_id).first()
                if job:
                    job.status = new_status
                    self.logger.info(f"Updated job {job_id} status to {new_status}")
                    return True
                else:
                    self.logger.warning(f"Job {job_id} not found for status update")
                    return False
        except Exception as e:
            log_error(e, f"updating job {job_id} status")
            return False
    
    def search_jobs(self, 
                   title_keywords: Optional[List[str]] = None,
                   company_keywords: Optional[List[str]] = None,
                   location_keywords: Optional[List[str]] = None,
                   limit: int = 100) -> List[JobListingDB]:
        """Search jobs with keywords."""
        try:
            with self.db_manager.get_session() as session:
                query = session.query(JobListingDB)
                
                # Add filters
                if title_keywords:
                    for keyword in title_keywords:
                        query = query.filter(JobListingDB.title.contains(keyword))
                
                if company_keywords:
                    for keyword in company_keywords:
                        query = query.filter(JobListingDB.company.contains(keyword))
                
                if location_keywords:
                    for keyword in location_keywords:
                        query = query.filter(JobListingDB.location.contains(keyword))
                
                jobs = query.limit(limit).all()
                return jobs
                
        except Exception as e:
            log_error(e, "searching jobs")
            return []
    
    def get_recent_jobs(self, limit: int = 20) -> List[JobListingDB]:
        """Get most recently posted jobs."""
        try:
            with self.db_manager.get_session() as session:
                jobs = (session.query(JobListingDB)
                       .order_by(JobListingDB.posted_date.desc())
                       .limit(limit)
                       .all())
                
                # Detach from session so they can be used outside
                for job in jobs:
                    session.expunge(job)
                
                return jobs
        except Exception as e:
            log_error(e, "getting recent jobs")
            return []
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job listing."""
        try:
            with self.db_manager.get_session() as session:
                job = session.query(JobListingDB).filter(JobListingDB.id == job_id).first()
                if job:
                    session.delete(job)
                    self.logger.info(f"Deleted job listing: {job_id}")
                    return True
                else:
                    self.logger.warning(f"Job {job_id} not found for deletion")
                    return False
        except Exception as e:
            log_error(e, f"deleting job {job_id}")
            return False


# Global database manager instance
db_manager = DatabaseManager()
job_repo = JobRepository(db_manager)
