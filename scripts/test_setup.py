#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basic setup validation script for JobPilot.
Tests configuration loading, logging, and basic model functionality.
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
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_imports():
    """Test that all core imports work."""
    print("🔧 Testing imports...")
    
    try:
        from utils.config import settings
        print("   ✅ Config module imported successfully")
    except Exception as e:
        print(f"   ❌ Config import failed: {e}")
        return False
    
    try:
        from utils.logger import get_logger
        print("   ✅ Logger module imported successfully")
    except Exception as e:
        print(f"   ❌ Logger import failed: {e}")
        return False
    
    try:
        from utils.models import JobListing, UserProfile, JobStatus
        print("   ✅ Models module imported successfully")
    except Exception as e:
        print(f"   ❌ Models import failed: {e}")
        return False
    
    return True


def test_configuration():
    """Test configuration loading and validation."""
    print("⚙️  Testing configuration...")
    
    from utils.config import settings
    
    try:
        print(f"   Project Name: {settings.project_name}")
        print(f"   Environment: {settings.environment}")
        print(f"   Log Level: {settings.log_level}")
        print(f"   Data Directory: {settings.data_dir}")
        print(f"   Is Development: {settings.is_development}")
        
        # Test directory creation
        if Path(settings.data_dir).exists():
            print("   ✅ Data directories created successfully")
        else:
            print("   ❌ Data directories not created")
            return False
            
        # Test job types parsing
        job_types = settings.job_types_list
        print(f"   Default Job Types: {job_types}")
        
        print("   ✅ Configuration loaded and validated successfully")
        return True
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False


def test_logging():
    """Test logging functionality."""
    print("📝 Testing logging...")
    
    try:
        from utils.logger import get_logger, log_function_call
        
        logger = get_logger("test_setup")
        
        # Test different log levels
        logger.info("Test info message")
        logger.debug("Test debug message")
        logger.warning("Test warning message")
        
        # Test specialized logging functions
        log_function_call("test_function", param1="value1", param2="value2")
        
        print("   ✅ Logging functionality working")
        return True
    except Exception as e:
        print(f"   ❌ Logging test failed: {e}")
        return False


def test_models():
    """Test data model creation and validation."""
    print("📊 Testing data models...")
    
    try:
        from utils.models import JobListing, UserProfile, JobStatus, RemoteType, JobType
        
        # Test JobListing creation
        job = JobListing(
            title="Senior Python Developer",
            company="TechCorp",
            description="Exciting opportunity for a senior Python developer",
            source="test",
            location="San Francisco, CA",
            remote_type=RemoteType.HYBRID,
            job_type=JobType.FULL_TIME,
            skills_required=["Python", "FastAPI", "PostgreSQL"],
            salary_min=120000,
            salary_max=150000,
        )
        
        print(f"   Job ID: {job.id}")
        print(f"   Job Title: {job.title}")
        print(f"   Job Status: {job.status}")
        print(f"   Skills Required: {job.skills_required}")
        
        # Test UserProfile creation
        user = UserProfile(
            first_name="John",
            last_name="Doe", 
            email="john.doe@example.com",
            skills=["Python", "JavaScript", "SQL"],
            preferred_locations=["Remote", "San Francisco"],
            preferred_job_types=[JobType.FULL_TIME, JobType.CONTRACT],
            desired_salary_min=100000,
            desired_salary_max=140000,
        )
        
        print(f"   User ID: {user.id}")
        print(f"   User Name: {user.first_name} {user.last_name}")
        print(f"   User Skills: {user.skills}")
        
        print("   ✅ Data models working correctly")
        return True
    except Exception as e:
        print(f"   ❌ Models test failed: {e}")
        return False


def test_directories():
    """Test that required directories exist."""
    print("📁 Testing directory structure...")
    
    required_dirs = [
        "src/agents",
        "src/scrapers", 
        "src/knowledge",
        "src/automation",
        "src/apis",
        "src/utils",
        "data/profiles",
        "data/jobs",
        "data/contacts",
        "tests",
        "docs",
        "scripts",
        "web"
    ]
    
    all_good = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ❌ {dir_path} missing")
            all_good = False
    
    return all_good


def main():
    """Run all tests."""
    print("🚀 JobPilot Setup Validation\n")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Configuration Tests", test_configuration), 
        ("Logging Tests", test_logging),
        ("Model Tests", test_models),
        ("Directory Structure", test_directories),
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
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Setup is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
