#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 test script for JobPilot Discovery Engine.
Tests database setup, job scraping, and storage functionality.
"""

import sys
import os
from pathlib import Path

# Ensure UTF-8 encoding for Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


def test_database_setup():
    """Test database initialization and table creation."""
    print("🗄️  Testing database setup...")
    
    try:
        from utils.database import db_manager, job_repo
        
        # Test database connection
        if db_manager.health_check():
            print("   ✅ Database connection successful")
        else:
            print("   ❌ Database connection failed")
            return False
        
        # Create tables
        db_manager.create_tables()
        print("   ✅ Database tables created successfully")
        
        # Check table stats
        stats = db_manager.get_table_stats()
        print(f"   📊 Table stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database setup failed: {e}")
        return False


def test_scraper_functionality():
    """Test demo scraper functionality."""
    print("🕷️  Testing scraper functionality...")
    
    try:
        from src.scrapers.demo_scraper import DemoScraper
        
        # Initialize scraper
        scraper = DemoScraper()
        print("   ✅ Demo scraper initialized")
        
        # Test stats
        stats = scraper.get_demo_stats()
        print(f"   📊 Demo scraper stats: {stats}")
        
        # Test job generation
        print("   🔍 Testing job search...")
        jobs = scraper.search_jobs("python", "remote", max_pages=1)
        
        if jobs:
            print(f"   ✅ Generated {len(jobs)} test jobs")
            
            # Display first job details
            first_job = jobs[0]
            print(f"   📝 Sample job: {first_job.title} at {first_job.company}")
            print(f"   💰 Salary: ${first_job.salary_min:,} - ${first_job.salary_max:,}")
            print(f"   🏠 Location: {first_job.location}")
            print(f"   🛠️  Skills: {', '.join(first_job.skills_required[:3])}...")
            
            return True
        else:
            print("   ❌ No jobs generated")
            return False
            
    except Exception as e:
        print(f"   ❌ Scraper test failed: {e}")
        return False


def test_job_storage():
    """Test storing scraped jobs in database."""
    print("💾 Testing job storage...")
    
    try:
        from src.scrapers.demo_scraper import DemoScraper
        from utils.database import job_repo
        from utils.models import JobStatus
        
        # Generate a test job
        scraper = DemoScraper()
        jobs = scraper.search_jobs("python", "san francisco", max_pages=1)
        
        if not jobs:
            print("   ❌ No jobs to store")
            return False
        
        test_job = jobs[0]
        
        # Convert to database format
        job_data = {
            'title': test_job.title,
            'company': test_job.company,
            'location': test_job.location,
            'description': test_job.description,
            'remote_type': test_job.remote_type.value if test_job.remote_type and hasattr(test_job.remote_type, 'value') else test_job.remote_type,
            'job_type': test_job.job_type.value if test_job.job_type and hasattr(test_job.job_type, 'value') else test_job.job_type,
            'experience_level': test_job.experience_level.value if test_job.experience_level and hasattr(test_job.experience_level, 'value') else test_job.experience_level,
            'salary_min': test_job.salary_min,
            'salary_max': test_job.salary_max,
            'salary_currency': test_job.salary_currency,
            'posted_date': test_job.posted_date,
            'expires_date': test_job.expires_date,
            'source': test_job.source,
            'source_url': str(test_job.source_url) if test_job.source_url else None,
            'source_id': test_job.source_id,
            'skills_required': test_job.skills_required,
            'skills_preferred': test_job.skills_preferred,
            'requirements': test_job.requirements,
            'responsibilities': test_job.responsibilities,
            'benefits': test_job.benefits,
            'status': JobStatus.DISCOVERED.value
        }
        
        # Store in database
        stored_job = job_repo.create_job(job_data)
        
        if stored_job:
            stored_job_id = stored_job.id
            stored_job_title = stored_job.title
            print(f"   ✅ Job stored successfully: ID {stored_job_id}")
            
            # Test retrieval
            retrieved_job = job_repo.get_job(stored_job_id)
            if retrieved_job:
                print(f"   ✅ Job retrieved successfully: {retrieved_job.title}")
                return True
            else:
                print("   ❌ Job retrieval failed")
                return False
        else:
            print("   ❌ Job storage failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Job storage test failed: {e}")
        return False


def test_job_search_and_filtering():
    """Test job search and filtering capabilities."""
    print("🔍 Testing job search and filtering...")
    
    try:
        from src.scrapers.demo_scraper import DemoScraper
        from utils.database import job_repo
        from utils.models import JobStatus
        
        # Generate and store multiple jobs
        scraper = DemoScraper()
        all_jobs = []
        
        queries = ["python", "javascript", "data science"]
        for query in queries:
            jobs = scraper.search_jobs(query, "remote", max_pages=1)
            all_jobs.extend(jobs[:3])  # Limit to 3 per query
        
        print(f"   📊 Generated {len(all_jobs)} jobs for testing")
        
        # Store all jobs
        stored_count = 0
        for job in all_jobs:
            job_data = {
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'description': job.description,
                'source': job.source,
                'source_url': str(job.source_url) if job.source_url else None,
                'status': JobStatus.DISCOVERED.value
            }
            
            if job_repo.create_job(job_data):
                stored_count += 1
        
        print(f"   ✅ Stored {stored_count} jobs in database")
        
        # Test filtering by source
        demo_jobs = job_repo.get_jobs_by_source("demo", limit=20)
        print(f"   📊 Found {len(demo_jobs)} jobs from demo source")
        
        # Test filtering by status
        discovered_jobs = job_repo.get_jobs_by_status(JobStatus.DISCOVERED.value, limit=20)
        print(f"   📊 Found {len(discovered_jobs)} discovered jobs")
        
        # Test search functionality
        python_jobs = job_repo.search_jobs(title_keywords=["Python"], limit=10)
        print(f"   📊 Found {len(python_jobs)} Python jobs")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Job search test failed: {e}")
        return False


def test_full_pipeline():
    """Test the complete scraping to storage pipeline."""
    print("🚀 Testing full pipeline...")
    
    try:
        from src.scrapers.demo_scraper import DemoScraper
        from utils.database import db_manager, job_repo
        from utils.models import JobStatus
        
        # Get initial stats
        initial_stats = db_manager.get_table_stats()
        initial_count = initial_stats.get('job_listings', 0)
        
        # Scrape some jobs
        scraper = DemoScraper()
        jobs = scraper.scrape_jobs(
            queries=["python", "react"],
            locations=["remote", "san francisco"],
            max_pages=1
        )
        
        print(f"   📊 Scraped {len(jobs)} total jobs")
        
        # Store all scraped jobs
        stored_count = 0
        failed_count = 0
        
        for job in jobs:
            job_data = {
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'description': job.description,
                'remote_type': job.remote_type.value if job.remote_type and hasattr(job.remote_type, 'value') else job.remote_type,
                'job_type': job.job_type.value if job.job_type and hasattr(job.job_type, 'value') else job.job_type,
                'experience_level': job.experience_level.value if job.experience_level and hasattr(job.experience_level, 'value') else job.experience_level,
                'salary_min': job.salary_min,
                'salary_max': job.salary_max,
                'source': job.source,
                'source_url': str(job.source_url) if job.source_url else None,
                'skills_required': job.skills_required,
                'status': JobStatus.DISCOVERED.value
            }
            
            if job_repo.create_job(job_data):
                stored_count += 1
            else:
                failed_count += 1
        
        # Get final stats
        final_stats = db_manager.get_table_stats()
        final_count = final_stats.get('job_listings', 0)
        
        print(f"   ✅ Pipeline completed:")
        print(f"      📊 Jobs scraped: {len(jobs)}")
        print(f"      💾 Jobs stored: {stored_count}")
        print(f"      ❌ Storage failures: {failed_count}")
        print(f"      📈 Database growth: {initial_count} → {final_count} jobs")
        
        return stored_count > 0
        
    except Exception as e:
        print(f"   ❌ Full pipeline test failed: {e}")
        return False


def test_error_handling():
    """Test error handling and edge cases."""
    print("🛡️  Testing error handling...")
    
    try:
        from utils.database import job_repo
        
        # Test retrieving non-existent job
        fake_job = job_repo.get_job("non-existent-id")
        if fake_job is None:
            print("   ✅ Non-existent job handling works")
        else:
            print("   ❌ Non-existent job handling failed")
            return False
        
        # Test empty job data
        empty_result = job_repo.create_job({})
        if empty_result is None:
            print("   ✅ Empty job data handling works")
        else:
            print("   ❌ Empty job data handling failed")
            return False
        
        # Test invalid search
        invalid_jobs = job_repo.search_jobs(title_keywords=[], limit=0)
        print(f"   ✅ Invalid search handled, returned {len(invalid_jobs)} jobs")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
        return False


def cleanup_test_data():
    """Clean up test data."""
    print("🧹 Cleaning up test data...")
    
    try:
        from utils.database import db_manager
        
        # Reset database to clean state
        db_manager.reset_database()
        print("   ✅ Test data cleaned up")
        return True
        
    except Exception as e:
        print(f"   ❌ Cleanup failed: {e}")
        return False


def main():
    """Run all Phase 2 tests."""
    print("🚀 JobPilot Phase 2: Discovery Engine Tests\n")
    print("=" * 60)
    
    tests = [
        ("Database Setup", test_database_setup),
        ("Scraper Functionality", test_scraper_functionality),
        ("Job Storage", test_job_storage),
        ("Job Search & Filtering", test_job_search_and_filtering),
        ("Full Pipeline", test_full_pipeline),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            results.append((test_name, False))
    
    # Always run cleanup
    print(f"\nCleanup:")
    cleanup_success = cleanup_test_data()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if success:
            passed += 1
    
    cleanup_status = "✅ PASS" if cleanup_success else "❌ FAIL"
    print(f"   {cleanup_status} - Cleanup")
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All Phase 2 tests passed! Discovery Engine is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
