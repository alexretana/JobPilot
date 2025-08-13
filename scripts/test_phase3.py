#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 test script for JobPilot Semantic Matching Engine.
Tests embedding generation, semantic search, LLM analysis, and job matching.
"""

import sys
import os
from pathlib import Path
import time
import json

# Ensure UTF-8 encoding for Windows
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


def test_embedding_service():
    """Test embedding generation and similarity calculations."""
    print("🧠 Testing embedding service...")
    
    try:
        from semantic.embeddings import embedding_service
        
        # Test model initialization
        model_info = embedding_service.get_model_info()
        print(f"   📊 Model info: {model_info}")
        
        if not model_info['embedding_dimension']:
            print("   ❌ Embedding model not properly initialized")
            return False
        
        print(f"   ✅ Embedding model loaded: {model_info['model_name']}")
        print(f"   📐 Embedding dimension: {model_info['embedding_dimension']}")
        
        # Test single text embedding
        print("   🔍 Testing single text embedding...")
        test_text = "Python software engineer with machine learning experience"
        embedding = embedding_service.embed_text(test_text)
        
        if embedding is not None and len(embedding) == model_info['embedding_dimension']:
            print(f"   ✅ Single embedding generated: shape {embedding.shape}")
        else:
            print("   ❌ Failed to generate single embedding")
            return False
        
        # Test batch embedding
        print("   🔍 Testing batch text embedding...")
        test_texts = [
            "Senior Python Developer",
            "Data Scientist with ML expertise", 
            "Frontend React Developer",
            "DevOps Engineer with AWS experience"
        ]
        
        embeddings = embedding_service.embed_texts(test_texts, use_cache=False)
        
        if len(embeddings) == len(test_texts):
            print(f"   ✅ Batch embeddings generated: {len(embeddings)} embeddings")
        else:
            print("   ❌ Failed to generate batch embeddings")
            return False
        
        # Test similarity calculation
        print("   🔍 Testing similarity calculation...")
        similarity = embedding_service.calculate_similarity(embeddings[0], embeddings[1])
        print(f"   📊 Similarity between 'Python Developer' and 'Data Scientist': {similarity:.3f}")
        
        if 0.0 <= similarity <= 1.0:
            print("   ✅ Similarity calculation working")
        else:
            print("   ❌ Invalid similarity score")
            return False
        
        # Test job description embedding
        print("   🔍 Testing job description embedding...")
        test_job = {
            'title': 'Senior Python Developer',
            'description': 'We are looking for an experienced Python developer to join our team...',
            'skills_required': ['Python', 'Django', 'PostgreSQL'],
            'skills_preferred': ['AWS', 'Docker'],
            'requirements': ['5+ years Python experience', 'Strong problem solving skills']
        }
        
        job_embedding = embedding_service.embed_job_description(test_job)
        if job_embedding is not None and len(job_embedding) == model_info['embedding_dimension']:
            print("   ✅ Job description embedding generated")
        else:
            print("   ❌ Failed to generate job description embedding")
            return False
        
        # Test user profile embedding
        print("   🔍 Testing user profile embedding...")
        test_profile = {
            'current_title': 'Python Developer',
            'skills': ['Python', 'Django', 'REST APIs', 'PostgreSQL'],
            'preferred_titles': ['Senior Python Developer', 'Backend Developer'],
            'industry': 'Technology'
        }
        
        profile_embedding = embedding_service.embed_user_profile(test_profile)
        if profile_embedding is not None and len(profile_embedding) == model_info['embedding_dimension']:
            print("   ✅ User profile embedding generated")
            
            # Calculate profile-job similarity
            profile_job_similarity = embedding_service.calculate_similarity(profile_embedding, job_embedding)
            print(f"   📊 Profile-Job similarity: {profile_job_similarity:.3f}")
        else:
            print("   ❌ Failed to generate user profile embedding")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Embedding service test failed: {e}")
        return False


def test_semantic_search_engine():
    """Test semantic job search and matching."""
    print("🔍 Testing semantic search engine...")
    
    try:
        from semantic.search_engine import search_engine, SearchFilters
        from scrapers.demo_scraper import DemoScraper
        from utils.database import job_repo, db_manager
        from utils.models import JobStatus
        
        # Generate and store some test jobs if needed
        stats = db_manager.get_table_stats()
        if stats.get('job_listings', 0) < 10:
            print("   📊 Generating test jobs for search...")
            demo_scraper = DemoScraper()
            jobs = demo_scraper.search_jobs("python developer", "remote", max_pages=1)
            
            for job in jobs[:10]:  # Limit to 10 jobs
                job_data = {
                    'title': job.title,
                    'company': job.company,
                    'location': job.location,
                    'description': job.description,
                    'skills_required': job.skills_required,
                    'skills_preferred': job.skills_preferred,
                    'requirements': job.requirements,
                    'responsibilities': job.responsibilities,
                    'salary_min': job.salary_min,
                    'salary_max': job.salary_max,
                    'source': job.source,
                    'source_url': str(job.source_url) if job.source_url else None,
                    'status': JobStatus.DISCOVERED.value
                }
                job_repo.create_job(job_data)
            
            print(f"   ✅ Generated {len(jobs)} test jobs")
        
        # Test basic semantic search
        print("   🔍 Testing basic semantic search...")
        query = "python developer with machine learning experience"
        matches = search_engine.search_jobs_semantic(query, limit=5)
        
        if matches:
            print(f"   ✅ Found {len(matches)} job matches")
            
            # Display top match details
            top_match = matches[0]
            print(f"   🏆 Top match: {top_match.job_title} at {top_match.company}")
            print(f"   📊 Overall score: {top_match.overall_score:.3f}")
            print(f"   🧠 Semantic score: {top_match.semantic_score:.3f}")
            print(f"   💡 Match reasons: {top_match.match_reasons[:2]}")
        else:
            print("   ❌ No job matches found")
            return False
        
        # Test search with user profile
        print("   🔍 Testing personalized search with user profile...")
        user_profile = {
            'current_title': 'Software Developer',
            'experience_years': 3,
            'skills': ['Python', 'JavaScript', 'SQL', 'Git'],
            'preferred_titles': ['Senior Developer', 'Python Developer'],
            'preferred_locations': ['remote', 'san francisco'],
            'desired_salary_min': 80000,
            'desired_salary_max': 120000,
            'industry': 'Technology'
        }
        
        personalized_matches = search_engine.search_jobs_semantic(
            query="senior python developer", 
            user_profile=user_profile,
            limit=5
        )
        
        if personalized_matches:
            print(f"   ✅ Found {len(personalized_matches)} personalized matches")
            
            top_personal = personalized_matches[0]
            print(f"   🏆 Top personalized match: {top_personal.job_title}")
            print(f"   📊 Overall: {top_personal.overall_score:.3f}, Skills: {top_personal.skills_match_score:.3f}")
            print(f"   📊 Experience: {top_personal.experience_match_score:.3f}, Salary: {top_personal.salary_match_score:.3f}")
        else:
            print("   ❌ No personalized matches found")
            return False
        
        # Test search with filters
        print("   🔍 Testing search with filters...")
        filters = SearchFilters(
            min_salary=70000,
            remote_types=['remote', 'hybrid'],
            max_age_days=60
        )
        
        filtered_matches = search_engine.search_jobs_semantic(
            query="developer",
            user_profile=user_profile,
            filters=filters,
            limit=3
        )
        
        print(f"   ✅ Found {len(filtered_matches)} matches with filters")
        
        # Test similar jobs functionality
        if matches:
            print("   🔍 Testing similar jobs search...")
            job_id = matches[0].job_id
            similar_jobs = search_engine.find_similar_jobs(job_id, limit=3)
            
            if similar_jobs:
                print(f"   ✅ Found {len(similar_jobs)} similar jobs")
                print(f"   📊 Most similar: {similar_jobs[0].job_title} (similarity: {similar_jobs[0].semantic_score:.3f})")
            else:
                print("   ⚠️  No similar jobs found (this is normal with limited data)")
        
        # Test search engine stats
        print("   📊 Getting search engine statistics...")
        stats = search_engine.get_search_stats()
        print(f"   📊 Search stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Semantic search engine test failed: {e}")
        return False


def test_llm_analyzer():
    """Test LLM-powered job analysis."""
    print("🤖 Testing LLM analyzer...")
    
    try:
        from semantic.llm_analyzer import llm_analyzer
        
        # Check if LLM is available
        provider_info = llm_analyzer.get_provider_info()
        print(f"   📊 LLM Provider: {provider_info}")
        
        if not llm_analyzer.is_available():
            print("   ⚠️  No LLM provider available, testing fallback methods only")
        else:
            print(f"   ✅ LLM available: {provider_info['provider']} - {provider_info['model']}")
        
        # Test job analysis
        print("   🔍 Testing job requirements analysis...")
        test_job = {
            'title': 'Senior Python Developer',
            'company': 'TechCorp',
            'location': 'San Francisco, CA',
            'description': '''We are seeking a Senior Python Developer to join our growing team. 
            You will be responsible for developing scalable web applications using Django and Flask,
            working with PostgreSQL databases, and deploying applications on AWS. Strong problem-solving
            skills and experience with agile development are essential.''',
            'requirements': [
                '5+ years Python development experience',
                'Experience with Django or Flask',
                'Knowledge of SQL and database design',
                'AWS deployment experience preferred'
            ],
            'responsibilities': [
                'Design and implement scalable Python applications',
                'Collaborate with cross-functional teams',
                'Write clean, maintainable code',
                'Mentor junior developers'
            ],
            'skills_required': ['Python', 'Django', 'PostgreSQL', 'REST APIs'],
            'skills_preferred': ['AWS', 'Docker', 'Redis']
        }
        
        job_analysis = llm_analyzer.analyze_job_requirements(test_job)
        
        if job_analysis and 'required_skills' in job_analysis:
            print("   ✅ Job analysis completed")
            print(f"   🛠️  Required skills: {job_analysis.get('required_skills', [])[:3]}")
            print(f"   📈 Difficulty level: {job_analysis.get('difficulty_level', 'Unknown')}")
            print(f"   🎯 Key responsibilities: {len(job_analysis.get('key_responsibilities', []))}")
        else:
            print("   ❌ Job analysis failed")
            return False
        
        # Test match explanation generation
        print("   🔍 Testing match explanation generation...")
        user_profile = {
            'current_title': 'Python Developer',
            'experience_years': 4,
            'skills': ['Python', 'Django', 'PostgreSQL', 'JavaScript'],
            'industry': 'Technology'
        }
        
        match_scores = {
            'overall_score': 0.85,
            'semantic_score': 0.82,
            'skills_match_score': 0.90,
            'experience_match_score': 0.75,
            'salary_match_score': 0.80,
            'location_match_score': 0.60
        }
        
        explanation = llm_analyzer.generate_match_explanation(test_job, user_profile, match_scores)
        
        if explanation and len(explanation) > 50:  # Should be a substantial explanation
            print("   ✅ Match explanation generated")
            print(f"   💭 Preview: {explanation[:100]}...")
        else:
            print("   ❌ Match explanation generation failed")
            return False
        
        # Test skill gap analysis
        print("   🔍 Testing skill gap analysis...")
        skill_gaps = llm_analyzer.identify_skill_gaps(test_job, user_profile)
        
        if skill_gaps and 'missing_skills' in skill_gaps:
            print("   ✅ Skill gap analysis completed")
            missing = skill_gaps.get('missing_skills', [])
            matching = skill_gaps.get('matching_skills', [])
            print(f"   ❌ Missing skills: {missing[:3]}")
            print(f"   ✅ Matching skills: {matching[:3]}")
        else:
            print("   ❌ Skill gap analysis failed")
            return False
        
        # Test application strategy generation
        print("   🔍 Testing application strategy generation...")
        strategy = llm_analyzer.generate_application_strategy(test_job, user_profile)
        
        if strategy and 'key_selling_points' in strategy:
            print("   ✅ Application strategy generated")
            selling_points = strategy.get('key_selling_points', [])
            print(f"   🎯 Key selling points: {selling_points[:2]}")
            interview_prep = strategy.get('interview_prep', [])
            print(f"   📝 Interview prep areas: {len(interview_prep)}")
        else:
            print("   ❌ Application strategy generation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ LLM analyzer test failed: {e}")
        return False


def test_integrated_workflow():
    """Test the complete integrated semantic matching workflow."""
    print("⚡ Testing integrated semantic matching workflow...")
    
    try:
        from semantic import search_engine, llm_analyzer
        from scrapers.demo_scraper import DemoScraper
        
        # Define user profile
        user_profile = {
            'first_name': 'Alex',
            'last_name': 'Developer', 
            'current_title': 'Software Developer',
            'experience_years': 5,
            'skills': ['Python', 'JavaScript', 'React', 'Django', 'PostgreSQL', 'AWS'],
            'preferred_titles': ['Senior Developer', 'Full Stack Developer', 'Python Developer'],
            'preferred_locations': ['remote', 'san francisco', 'seattle'],
            'desired_salary_min': 90000,
            'desired_salary_max': 140000,
            'industry': 'Technology'
        }
        
        # Step 1: Semantic job search
        print("   🔍 Step 1: Performing semantic job search...")
        search_query = "senior full stack developer with python and react experience"
        job_matches = search_engine.search_jobs_semantic(
            query=search_query,
            user_profile=user_profile,
            limit=3
        )
        
        if not job_matches:
            print("   ❌ No job matches found for integrated workflow")
            return False
        
        print(f"   ✅ Found {len(job_matches)} job matches")
        
        # Step 2: Detailed analysis of top match
        print("   🔍 Step 2: Analyzing top job match...")
        top_match = job_matches[0]
        
        print(f"   🏆 Top match: {top_match.job_title} at {top_match.company}")
        print(f"   📊 Match scores:")
        print(f"      • Overall: {top_match.overall_score:.3f}")
        print(f"      • Semantic: {top_match.semantic_score:.3f}")
        print(f"      • Skills: {top_match.skills_match_score:.3f}")
        print(f"      • Experience: {top_match.experience_match_score:.3f}")
        
        # Step 3: Generate detailed analysis with LLM
        print("   🔍 Step 3: Generating AI-powered analysis...")
        
        # Job analysis
        job_analysis = llm_analyzer.analyze_job_requirements(top_match.raw_job_data)
        if job_analysis:
            print(f"   🛠️  Required skills: {', '.join(job_analysis.get('required_skills', [])[:4])}")
            print(f"   📊 Difficulty level: {job_analysis.get('difficulty_level', 'Unknown')}/10")
        
        # Match explanation
        match_explanation = llm_analyzer.generate_match_explanation(
            top_match.raw_job_data, 
            user_profile, 
            {
                'overall_score': top_match.overall_score,
                'semantic_score': top_match.semantic_score,
                'skills_match_score': top_match.skills_match_score,
                'experience_match_score': top_match.experience_match_score,
                'salary_match_score': top_match.salary_match_score,
                'location_match_score': top_match.location_match_score
            }
        )
        
        if match_explanation:
            print(f"   💭 AI Explanation: {match_explanation[:150]}...")
        
        # Skill gap analysis
        skill_gaps = llm_analyzer.identify_skill_gaps(top_match.raw_job_data, user_profile)
        if skill_gaps:
            missing_skills = skill_gaps.get('missing_skills', [])
            if missing_skills:
                print(f"   📚 Skills to develop: {', '.join(missing_skills[:3])}")
            else:
                print("   ✅ No significant skill gaps identified")
        
        # Application strategy
        app_strategy = llm_analyzer.generate_application_strategy(top_match.raw_job_data, user_profile)
        if app_strategy:
            selling_points = app_strategy.get('key_selling_points', [])
            print(f"   🎯 Key selling points: {', '.join(selling_points[:2])}")
        
        # Step 4: Find similar jobs
        print("   🔍 Step 4: Finding similar opportunities...")
        similar_jobs = search_engine.find_similar_jobs(top_match.job_id, limit=2)
        
        if similar_jobs:
            print(f"   ✅ Found {len(similar_jobs)} similar opportunities")
            for i, similar_job in enumerate(similar_jobs, 1):
                print(f"      {i}. {similar_job.job_title} (similarity: {similar_job.semantic_score:.3f})")
        else:
            print("   ℹ️  No similar jobs found (normal with limited data)")
        
        # Step 5: Generate summary report
        print("   📊 Step 5: Generating match summary report...")
        
        summary_report = {
            'user_profile': {
                'name': f"{user_profile['first_name']} {user_profile['last_name']}",
                'experience': f"{user_profile['experience_years']} years",
                'key_skills': user_profile['skills'][:5]
            },
            'top_match': {
                'title': top_match.job_title,
                'company': top_match.company,
                'location': top_match.location,
                'overall_score': top_match.overall_score,
                'match_reasons': top_match.match_reasons[:3]
            },
            'analysis': {
                'difficulty_level': job_analysis.get('difficulty_level') if job_analysis else None,
                'missing_skills': skill_gaps.get('missing_skills', [])[:3] if skill_gaps else [],
                'key_selling_points': app_strategy.get('key_selling_points', [])[:3] if app_strategy else []
            },
            'similar_jobs_count': len(similar_jobs),
            'total_matches': len(job_matches)
        }
        
        print("   ✅ Integrated workflow completed successfully!")
        print("   📋 Summary Report:")
        print(f"      👤 User: {summary_report['user_profile']['name']}")
        print(f"      🎯 Top Match: {summary_report['top_match']['title']} ({summary_report['top_match']['overall_score']:.3f})")
        print(f"      📊 Total Matches: {summary_report['total_matches']}")
        print(f"      🔄 Similar Jobs: {summary_report['similar_jobs_count']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Integrated workflow test failed: {e}")
        return False


def cleanup_test_data():
    """Clean up test data."""
    print("🧹 Cleaning up test data...")
    
    try:
        from utils.database import db_manager
        
        # We could reset the database, but let's keep the job data 
        # for potential manual testing
        print("   ℹ️  Test data preserved for manual inspection")
        print("   ℹ️  Run Phase 2 cleanup script if you need to reset the database")
        return True
        
    except Exception as e:
        print(f"   ❌ Cleanup failed: {e}")
        return False


def main():
    """Run all Phase 3 tests."""
    print("🧠 JobPilot Phase 3: Semantic Matching Engine Tests\n")
    print("=" * 70)
    
    tests = [
        ("Embedding Service", test_embedding_service),
        ("Semantic Search Engine", test_semantic_search_engine), 
        ("LLM Analyzer", test_llm_analyzer),
        ("Integrated Workflow", test_integrated_workflow),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            start_time = time.time()
            success = test_func()
            end_time = time.time()
            
            duration = end_time - start_time
            results.append((test_name, success, duration))
            
            if success:
                print(f"   ⏱️  Completed in {duration:.2f}s")
            
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            results.append((test_name, False, 0))
    
    # Always run cleanup
    print(f"\nCleanup:")
    cleanup_success = cleanup_test_data()
    
    print("\n" + "=" * 70)
    print("📋 SUMMARY:")
    
    passed = 0
    total_duration = 0
    for test_name, success, duration in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} - {test_name} ({duration:.2f}s)")
        if success:
            passed += 1
        total_duration += duration
    
    cleanup_status = "✅ PASS" if cleanup_success else "❌ FAIL"
    print(f"   {cleanup_status} - Cleanup")
    
    print(f"\nResults: {passed}/{len(results)} tests passed")
    print(f"Total execution time: {total_duration:.2f}s")
    
    if passed == len(results):
        print("\n🎉 All Phase 3 tests passed! Semantic Matching Engine is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
