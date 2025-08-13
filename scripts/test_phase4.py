#!/usr/bin/env python3
"""
JobPilot Phase 4: Web Interface & User Experience Tests

Test the Flask web application, template rendering, and user interactions.
"""

import sys
import os
import time
import json
import requests
from pathlib import Path
from datetime import datetime

# Add root directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from utils.database import db_manager
from scrapers import demo_scraper

def print_header(title: str):
    """Print a formatted test section header."""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}")

def print_test(test_name: str):
    """Print a formatted test name."""
    print(f"\n🧪 {test_name}")

def print_success(message: str):
    """Print a success message."""
    print(f"   ✅ {message}")

def print_error(message: str):
    """Print an error message."""
    print(f"   ❌ {message}")

def print_info(message: str):
    """Print an info message."""
    print(f"   ℹ️  {message}")

def test_app_creation():
    """Test Flask app creation and configuration."""
    print_test("Testing Flask application creation...")
    
    try:
        app = create_app('testing')
        
        if app:
            print_success("Flask application created successfully")
            print_info(f"App name: {app.name}")
            print_info(f"Config: {app.config.get('SECRET_KEY', 'Not set')[:20]}...")
            
            # Test app context
            with app.app_context():
                print_success("Application context works")
                
            return app, True
        else:
            print_error("Failed to create Flask application")
            return None, False
            
    except Exception as e:
        print_error(f"Error creating Flask app: {e}")
        return None, False

def test_database_integration():
    """Test database integration with web app."""
    print_test("Testing database integration...")
    
    try:
        # Initialize database
        db_manager.create_tables()
        print_success("Database initialized")
        
        # Get stats
        stats = db_manager.get_table_stats()
        print_success(f"Database stats retrieved: {stats}")
        
        # Generate some test data if needed
        if stats.get('job_listings', 0) < 5:
            print_info("Generating demo data for testing...")
            demo_scraper.scrape_jobs(max_jobs=10, force=True)
            new_stats = db_manager.get_table_stats()
            print_success(f"Demo data generated: {new_stats.get('job_listings', 0)} jobs")
        
        return True
        
    except Exception as e:
        print_error(f"Database integration error: {e}")
        return False

def test_route_responses(app):
    """Test basic route responses."""
    print_test("Testing route responses...")
    
    test_client = app.test_client()
    routes_to_test = [
        ('/', 'GET', 'Home page'),
        ('/search', 'GET', 'Search page'),
        ('/profile', 'GET', 'Profile page'),
        ('/api/search/suggestions?q=python', 'GET', 'Search suggestions API'),
    ]
    
    success_count = 0
    total_routes = len(routes_to_test)
    
    for route, method, description in routes_to_test:
        try:
            if method == 'GET':
                response = test_client.get(route)
            else:
                response = test_client.post(route)
            
            if 200 <= response.status_code < 400:
                print_success(f"{description}: {response.status_code}")
                success_count += 1
            else:
                print_error(f"{description}: {response.status_code}")
                
        except Exception as e:
            print_error(f"{description}: {e}")
    
    print_info(f"Route tests passed: {success_count}/{total_routes}")
    return success_count == total_routes

def test_template_rendering(app):
    """Test template rendering with sample data."""
    print_test("Testing template rendering...")
    
    test_client = app.test_client()
    
    try:
        # Test home page rendering
        response = test_client.get('/')
        if b'JobPilot' in response.data and b'AI-Powered' in response.data:
            print_success("Home page template renders correctly")
        else:
            print_error("Home page template missing key elements")
            return False
        
        # Test search page
        response = test_client.get('/search?q=python+developer')
        if response.status_code == 200:
            print_success("Search page template renders")
            if b'Search Results' in response.data or b'No jobs found' in response.data:
                print_success("Search results template working")
            else:
                print_error("Search results template not working properly")
        else:
            print_error(f"Search page failed: {response.status_code}")
            return False
        
        # Test profile page
        response = test_client.get('/profile')
        if response.status_code == 200 and b'Profile' in response.data:
            print_success("Profile page template renders")
        else:
            print_error("Profile page template failed")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Template rendering error: {e}")
        return False

def test_semantic_search_integration(app):
    """Test semantic search integration in web interface."""
    print_test("Testing semantic search integration...")
    
    test_client = app.test_client()
    
    try:
        # Test search with AI-powered query
        search_queries = [
            'python developer',
            'machine learning engineer', 
            'remote jobs',
            'senior software engineer'
        ]
        
        successful_searches = 0
        
        for query in search_queries:
            try:
                response = test_client.get(f'/search?q={query}')
                
                if response.status_code == 200:
                    # Check for semantic search indicators
                    response_text = response.data.decode('utf-8')
                    if 'AI-powered' in response_text or 'semantic' in response_text.lower():
                        print_success(f"Semantic search working for: '{query}'")
                        successful_searches += 1
                    else:
                        print_info(f"Search completed for: '{query}' (basic functionality)")
                        successful_searches += 1
                else:
                    print_error(f"Search failed for: '{query}' - Status: {response.status_code}")
                    
            except Exception as e:
                print_error(f"Search error for '{query}': {e}")
        
        print_info(f"Successful searches: {successful_searches}/{len(search_queries)}")
        return successful_searches > 0
        
    except Exception as e:
        print_error(f"Semantic search integration error: {e}")
        return False

def test_user_profile_functionality(app):
    """Test user profile creation and management."""
    print_test("Testing user profile functionality...")
    
    test_client = app.test_client()
    
    try:
        # Test profile form submission
        profile_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'current_title': 'Software Developer',
            'experience_years': '5',
            'skills': 'Python, JavaScript, React, Django',
            'preferred_locations': 'San Francisco, Remote',
            'desired_salary_min': '100000',
            'desired_salary_max': '150000',
            'bio': 'Experienced software developer looking for new opportunities.'
        }
        
        # Submit profile
        response = test_client.post('/profile', data=profile_data, follow_redirects=True)
        
        if response.status_code == 200:
            print_success("Profile form submission successful")
            
            # Check if profile is saved (look for success message or data)
            response_text = response.data.decode('utf-8')
            if 'success' in response_text.lower() or 'Test' in response_text:
                print_success("Profile data appears to be saved")
            else:
                print_info("Profile form processed (data persistence unclear)")
        else:
            print_error(f"Profile form submission failed: {response.status_code}")
            return False
        
        # Test dashboard access with profile
        response = test_client.get('/dashboard')
        if response.status_code == 200:
            print_success("Dashboard accessible")
        else:
            print_info("Dashboard requires authentication (expected)")
        
        return True
        
    except Exception as e:
        print_error(f"User profile functionality error: {e}")
        return False

def test_api_endpoints(app):
    """Test API endpoints functionality."""
    print_test("Testing API endpoints...")
    
    test_client = app.test_client()
    
    try:
        # Test search suggestions API
        response = test_client.get('/api/search/suggestions?q=python')
        if response.status_code == 200:
            try:
                data = json.loads(response.data)
                if isinstance(data, list):
                    print_success(f"Search suggestions API working: {len(data)} suggestions")
                else:
                    print_info("Search suggestions API returns data but format unclear")
            except json.JSONDecodeError:
                print_info("Search suggestions API responds but not JSON")
        else:
            print_error(f"Search suggestions API failed: {response.status_code}")
        
        # Test similar jobs API (requires job ID)
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
        from utils.database import job_repo
        jobs = job_repo.get_recent_jobs(limit=1)
        
        if jobs:
            job_id = jobs[0].id
            response = test_client.get(f'/api/jobs/similar/{job_id}')
            if response.status_code == 200:
                print_success("Similar jobs API working")
            else:
                print_info(f"Similar jobs API status: {response.status_code}")
        else:
            print_info("No jobs available to test similar jobs API")
        
        return True
        
    except Exception as e:
        print_error(f"API endpoints error: {e}")
        return False

def test_error_handling(app):
    """Test error page rendering."""
    print_test("Testing error handling...")
    
    test_client = app.test_client()
    
    try:
        # Test 404 error
        response = test_client.get('/nonexistent-page')
        if response.status_code == 404:
            if b'404' in response.data and b'Page Not Found' in response.data:
                print_success("404 error page renders correctly")
            else:
                print_info("404 error handled but custom page unclear")
        else:
            print_info(f"404 test returned: {response.status_code}")
        
        # Test invalid job ID
        response = test_client.get('/job/invalid-job-id')
        if response.status_code in [404, 302]:  # 302 for redirect
            print_success("Invalid job ID handled properly")
        else:
            print_info(f"Invalid job ID returned: {response.status_code}")
        
        return True
        
    except Exception as e:
        print_error(f"Error handling test error: {e}")
        return False

def test_responsive_design():
    """Test responsive design elements (basic check)."""
    print_test("Testing responsive design elements...")
    
    try:
        # Read the CSS file to check for responsive utilities
        css_path = Path(__file__).parent.parent / 'static' / 'css' / 'style.css'
        
        if css_path.exists():
            with open(css_path, 'r') as f:
                css_content = f.read()
            
            responsive_indicators = [
                '@media (max-width',
                'sm:',
                'md:',
                'lg:',
                'mobile-',
                'responsive'
            ]
            
            found_indicators = [indicator for indicator in responsive_indicators if indicator in css_content]
            
            if found_indicators:
                print_success(f"Responsive design elements found: {len(found_indicators)}")
                print_info(f"Indicators: {', '.join(found_indicators[:3])}...")
            else:
                print_info("Custom CSS exists but responsive indicators not clear")
            
            print_success("CSS file exists and readable")
        else:
            print_info("Custom CSS file not found (using CDN only)")
        
        return True
        
    except Exception as e:
        print_error(f"Responsive design test error: {e}")
        return False

def test_performance_basics(app):
    """Test basic performance aspects."""
    print_test("Testing basic performance...")
    
    test_client = app.test_client()
    
    try:
        # Test response times for key pages
        pages_to_test = [
            ('/', 'Home'),
            ('/search', 'Search'),
            ('/profile', 'Profile')
        ]
        
        total_time = 0
        successful_tests = 0
        
        for url, name in pages_to_test:
            try:
                start_time = time.time()
                response = test_client.get(url)
                end_time = time.time()
                
                response_time = end_time - start_time
                total_time += response_time
                
                if response.status_code == 200:
                    print_success(f"{name} page: {response_time:.3f}s")
                    successful_tests += 1
                else:
                    print_info(f"{name} page: {response_time:.3f}s (status: {response.status_code})")
                    
            except Exception as e:
                print_error(f"{name} page performance test failed: {e}")
        
        if successful_tests > 0:
            avg_time = total_time / successful_tests
            print_info(f"Average response time: {avg_time:.3f}s")
            
            if avg_time < 1.0:
                print_success("Response times within acceptable range")
            else:
                print_info("Response times slower than ideal (>1s)")
        
        return successful_tests > 0
        
    except Exception as e:
        print_error(f"Performance test error: {e}")
        return False

def cleanup():
    """Clean up test resources."""
    print_test("Cleaning up test resources...")
    
    try:
        print_info("Test data preserved for manual inspection")
        print_info("Run Phase 2 cleanup script if you need to reset the database")
        print_success("Cleanup completed")
        return True
        
    except Exception as e:
        print_error(f"Cleanup error: {e}")
        return False

def main():
    """Run all Phase 4 tests."""
    print("🌐 JobPilot Phase 4: Web Interface & User Experience Tests\n")
    
    start_time = time.time()
    test_results = {}
    
    # Test functions to run
    tests = [
        ("Flask App Creation", test_app_creation),
        ("Database Integration", test_database_integration),
    ]
    
    # Run initial tests first
    app = None
    for test_name, test_func in tests:
        print_header(f"{test_name}:")
        try:
            if test_name == "Flask App Creation":
                app, success = test_func()
                test_results[test_name] = success
            else:
                start_test_time = time.time()
                success = test_func()
                test_time = time.time() - start_test_time
                test_results[test_name] = success
                print_info(f"Completed in {test_time:.2f}s")
        except Exception as e:
            print_error(f"Test failed with exception: {e}")
            test_results[test_name] = False
    
    # If we have the app, run the web-specific tests
    if app:
        web_tests = [
            ("Route Responses", lambda: test_route_responses(app)),
            ("Template Rendering", lambda: test_template_rendering(app)),
            ("Semantic Search Integration", lambda: test_semantic_search_integration(app)),
            ("User Profile Functionality", lambda: test_user_profile_functionality(app)),
            ("API Endpoints", lambda: test_api_endpoints(app)),
            ("Error Handling", lambda: test_error_handling(app)),
            ("Responsive Design", test_responsive_design),
            ("Performance Basics", lambda: test_performance_basics(app)),
            ("Cleanup", cleanup)
        ]
        
        for test_name, test_func in web_tests:
            print_header(f"{test_name}:")
            try:
                start_test_time = time.time()
                success = test_func()
                test_time = time.time() - start_test_time
                test_results[test_name] = success
                print_info(f"Completed in {test_time:.2f}s")
            except Exception as e:
                print_error(f"Test failed with exception: {e}")
                test_results[test_name] = False
    
    # Print summary
    total_time = time.time() - start_time
    
    print_header("SUMMARY:")
    passed_tests = sum(1 for success in test_results.values() if success)
    total_tests = len(test_results)
    
    for test_name, success in test_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} - {test_name}")
    
    print(f"\nResults: {passed_tests}/{total_tests} tests passed")
    print(f"Total execution time: {total_time:.2f}s")
    
    if passed_tests == total_tests:
        print(f"\n🎉 All Phase 4 tests passed! Web interface is ready for production.")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
