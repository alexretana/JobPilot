#!/usr/bin/env python3
"""
JobPilot Web Application
Main Flask application entry point with semantic job matching capabilities.
"""

import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import traceback

# Import JobPilot modules
from utils.config import settings
from utils.database import db_manager, job_repo
from utils.logger import setup_logging, get_logger
from utils.models import JobStatus
from semantic import search_engine, llm_analyzer
from semantic.search_engine import SearchFilters
from scrapers import demo_scraper

# Initialize logging
setup_logging()
logger = get_logger(__name__)

def create_app(config_name='development'):
    """Create and configure Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    
    # Initialize database
    db_manager.create_tables()
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        return render_template('errors/500.html'), 500
    
    # Context processors
    @app.context_processor
    def inject_user():
        """Inject user data into all templates."""
        return {
            'current_user': session.get('user_profile'),
            'is_authenticated': 'user_profile' in session
        }
    
    @app.context_processor
    def inject_stats():
        """Inject application statistics into templates."""
        try:
            stats = db_manager.get_table_stats()
            search_stats = search_engine.get_search_stats()
            return {
                'app_stats': {
                    'total_jobs': stats.get('job_listings', 0),
                    'total_applications': stats.get('applications', 0),
                    'embedding_model': search_stats.get('embedding_model', 'Unknown'),
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
            }
        except Exception as e:
            logger.error(f"Error getting stats for context: {e}")
            return {'app_stats': {}}
    
    # Routes
    @app.route('/')
    def index():
        """Home page with search interface."""
        try:
            # Get recent jobs for showcase
            recent_jobs = job_repo.get_recent_jobs(limit=6)
            
            # Get some sample search suggestions
            search_suggestions = [
                "Python Developer Remote",
                "Machine Learning Engineer",
                "Full Stack JavaScript",
                "DevOps Cloud Engineer",
                "Product Manager Tech",
                "Data Scientist AI"
            ]
            
            return render_template('index.html', 
                                 recent_jobs=recent_jobs,
                                 search_suggestions=search_suggestions)
        except Exception as e:
            logger.error(f"Error loading home page: {e}")
            flash('Error loading homepage. Please try again.', 'error')
            return render_template('index.html', recent_jobs=[], search_suggestions=[])
    
    @app.route('/search')
    def search():
        """Job search page with semantic search."""
        try:
            query = request.args.get('q', '').strip()
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            
            # Search filters
            filters = SearchFilters(
                min_salary=request.args.get('min_salary', type=float),
                max_salary=request.args.get('max_salary', type=float),
                job_types=request.args.getlist('job_type'),
                remote_types=request.args.getlist('remote_type'),
                experience_levels=request.args.getlist('experience_level'),
                locations=request.args.getlist('location'),
                companies=request.args.getlist('company'),
                max_age_days=request.args.get('max_age_days', 30, type=int)
            )
            
            matches = []
            search_time = 0
            
            if query:
                start_time = datetime.now()
                
                # Get user profile if logged in
                user_profile = session.get('user_profile')
                
                # Perform semantic search
                all_matches = search_engine.search_jobs_semantic(
                    query=query,
                    user_profile=user_profile,
                    filters=filters,
                    limit=per_page * 5  # Get more results for pagination
                )
                
                # Paginate results
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                matches = all_matches[start_idx:end_idx]
                
                search_time = (datetime.now() - start_time).total_seconds()
                
                logger.info(f"Search query: '{query}' returned {len(all_matches)} results in {search_time:.3f}s")
            
            # Get filter options for the sidebar
            filter_options = {
                'job_types': ['Full-time', 'Part-time', 'Contract', 'Freelance', 'Internship'],
                'remote_types': ['On-site', 'Remote', 'Hybrid'],
                'experience_levels': ['entry_level', 'associate', 'mid_level', 'senior_level', 'director', 'executive'],
                'salary_ranges': [
                    {'label': 'Under $50k', 'min': 0, 'max': 50000},
                    {'label': '$50k - $75k', 'min': 50000, 'max': 75000},
                    {'label': '$75k - $100k', 'min': 75000, 'max': 100000},
                    {'label': '$100k - $150k', 'min': 100000, 'max': 150000},
                    {'label': '$150k+', 'min': 150000, 'max': None}
                ]
            }
            
            return render_template('search.html', 
                                 query=query,
                                 matches=matches,
                                 search_time=search_time,
                                 page=page,
                                 per_page=per_page,
                                 filters=filters,
                                 filter_options=filter_options,
                                 total_results=len(matches))
            
        except Exception as e:
            logger.error(f"Error in search: {e}")
            logger.error(traceback.format_exc())
            flash('Search error occurred. Please try again.', 'error')
            return render_template('search.html', query='', matches=[], search_time=0)
    
    @app.route('/job/<job_id>')
    def job_detail(job_id):
        """Job detail page with AI analysis."""
        try:
            job = job_repo.get_job(job_id)
            if not job:
                flash('Job not found.', 'error')
                return redirect(url_for('index'))
            
            # Get user profile for personalized analysis
            user_profile = session.get('user_profile')
            
            # Generate AI analysis if LLM is available
            ai_analysis = None
            similar_jobs = []
            
            try:
                # Job analysis
                job_dict = {
                    'title': job.title,
                    'description': job.description,
                    'requirements': job.requirements,
                    'responsibilities': job.responsibilities,
                    'skills_required': job.skills_required,
                    'skills_preferred': job.skills_preferred,
                    'experience_level': job.experience_level,
                    'salary_min': job.salary_min,
                    'salary_max': job.salary_max
                }
                
                ai_analysis = llm_analyzer.analyze_job_requirements(job_dict)
                
                # Generate match explanation if user is logged in
                if user_profile:
                    # Calculate match scores for this specific job
                    from semantic.search_engine import SemanticSearchEngine
                    temp_engine = SemanticSearchEngine()
                    query_embedding = temp_engine.embedding_service.embed_text(f"{job.title} {job.description}"[:200])
                    job_match = temp_engine._calculate_job_match(job, query_embedding, None, user_profile)
                    
                    if job_match:
                        match_scores = {
                            'overall': job_match.overall_score,
                            'skills': job_match.skills_match_score,
                            'experience': job_match.experience_match_score,
                            'salary': job_match.salary_match_score
                        }
                        
                        ai_analysis['match_explanation'] = llm_analyzer.generate_match_explanation(
                            job_dict, user_profile, match_scores
                        )
                
                # Get similar jobs
                similar_jobs = search_engine.find_similar_jobs(job_id, limit=5)
                
            except Exception as e:
                logger.warning(f"AI analysis failed for job {job_id}: {e}")
            
            return render_template('job_detail.html', 
                                 job=job,
                                 ai_analysis=ai_analysis,
                                 similar_jobs=similar_jobs,
                                 user_profile=user_profile)
            
        except Exception as e:
            logger.error(f"Error loading job {job_id}: {e}")
            flash('Error loading job details.', 'error')
            return redirect(url_for('index'))
    
    @app.route('/profile', methods=['GET', 'POST'])
    def profile():
        """User profile management."""
        if request.method == 'POST':
            try:
                # Save user profile to session
                profile_data = {
                    'first_name': request.form.get('first_name', ''),
                    'last_name': request.form.get('last_name', ''),
                    'email': request.form.get('email', ''),
                    'current_title': request.form.get('current_title', ''),
                    'experience_years': int(request.form.get('experience_years', 0)),
                    'skills': [skill.strip() for skill in request.form.get('skills', '').split(',') if skill.strip()],
                    'preferred_locations': [loc.strip() for loc in request.form.get('preferred_locations', '').split(',') if loc.strip()],
                    'desired_salary_min': int(request.form.get('desired_salary_min', 0)) if request.form.get('desired_salary_min') else None,
                    'desired_salary_max': int(request.form.get('desired_salary_max', 0)) if request.form.get('desired_salary_max') else None,
                    'bio': request.form.get('bio', ''),
                    'updated_at': datetime.now().isoformat()
                }
                
                session['user_profile'] = profile_data
                session.permanent = True
                
                flash('Profile updated successfully!', 'success')
                logger.info(f"Profile updated for user: {profile_data.get('email', 'unknown')}")
                
            except Exception as e:
                logger.error(f"Error updating profile: {e}")
                flash('Error updating profile. Please try again.', 'error')
        
        user_profile = session.get('user_profile', {})
        return render_template('profile.html', user_profile=user_profile)
    
    @app.route('/dashboard')
    def dashboard():
        """User dashboard with job recommendations."""
        user_profile = session.get('user_profile')
        if not user_profile:
            flash('Please complete your profile to get personalized recommendations.', 'info')
            return redirect(url_for('profile'))
        
        try:
            # Get personalized job recommendations
            recommendations = search_engine.search_jobs_semantic(
                query=f"{user_profile.get('current_title', '')} {' '.join(user_profile.get('skills', []))}",
                user_profile=user_profile,
                limit=10
            )
            
            # Get user's job applications (mock data for now)
            applications = []  # TODO: Implement job application tracking
            
            # Calculate profile completion
            required_fields = ['first_name', 'last_name', 'current_title', 'skills', 'experience_years']
            completed_fields = sum(1 for field in required_fields if user_profile.get(field))
            profile_completion = int((completed_fields / len(required_fields)) * 100)
            
            return render_template('dashboard.html',
                                 recommendations=recommendations,
                                 applications=applications,
                                 profile_completion=profile_completion)
            
        except Exception as e:
            logger.error(f"Error loading dashboard: {e}")
            flash('Error loading dashboard. Please try again.', 'error')
            return render_template('dashboard.html', recommendations=[], applications=[])
    
    @app.route('/api/jobs/similar/<job_id>')
    def api_similar_jobs(job_id):
        """API endpoint for similar jobs."""
        try:
            similar_jobs = search_engine.find_similar_jobs(job_id, limit=5)
            return jsonify([{
                'id': job.job_id,
                'title': job.job_title,
                'company': job.company,
                'location': job.location,
                'similarity_score': job.semantic_score
            } for job in similar_jobs])
        except Exception as e:
            logger.error(f"Error getting similar jobs: {e}")
            return jsonify({'error': 'Failed to get similar jobs'}), 500
    
    @app.route('/api/search/suggestions')
    def api_search_suggestions():
        """API endpoint for search suggestions."""
        query = request.args.get('q', '').lower()
        suggestions = []
        
        if len(query) >= 2:
            # Get job titles and skills from recent jobs
            try:
                recent_jobs = job_repo.get_recent_jobs(limit=100)
                titles = set()
                for job in recent_jobs:
                    if query in job.title.lower():
                        titles.add(job.title)
                    if job.skills_required:
                        for skill in job.skills_required:
                            if query in skill.lower():
                                titles.add(skill)
                
                suggestions = list(titles)[:8]
            except Exception as e:
                logger.error(f"Error getting search suggestions: {e}")
        
        return jsonify(suggestions)
    
    @app.route('/admin/demo-data')
    def admin_demo_data():
        """Generate demo data for testing."""
        try:
            demo_scraper.scrape_jobs(max_jobs=20, force=True)
            flash('Demo data generated successfully!', 'success')
            logger.info("Demo data generated via admin interface")
        except Exception as e:
            logger.error(f"Error generating demo data: {e}")
            flash('Error generating demo data.', 'error')
        
        return redirect(url_for('index'))
    
    @app.route('/logout')
    def logout():
        """Clear user session."""
        session.clear()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))
    
    logger.info("JobPilot Flask application created successfully")
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Development server configuration
    debug = os.environ.get('FLASK_ENV') == 'development'
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    
    logger.info(f"Starting JobPilot server on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)
