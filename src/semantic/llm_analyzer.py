"""
LLM integration service for JobPilot AI-powered analysis.
Handles job analysis, match reasoning, and content generation.
"""

from typing import List, Dict, Optional, Any
import json
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import LoggerMixin, log_error
from utils.config import settings


class LLMAnalyzer(LoggerMixin):
    """AI-powered job analysis using Large Language Models."""
    
    def __init__(self):
        """Initialize LLM analyzer."""
        self.client = None
        self.model_name = "gpt-3.5-turbo"  # Default model
        self._initialize_client()
        
        self.logger.info("LLMAnalyzer initialized")
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client based on configuration."""
        try:
            # Try OpenAI first
            if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
                import openai
                self.client = openai.OpenAI(api_key=settings.openai_api_key)
                self.provider = "openai"
                self.logger.info("Using OpenAI for LLM analysis")
                return
            
            # Try Anthropic
            if hasattr(settings, 'anthropic_api_key') and settings.anthropic_api_key:
                import anthropic
                self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
                self.provider = "anthropic"
                self.model_name = "claude-3-haiku-20240307"
                self.logger.info("Using Anthropic Claude for LLM analysis")
                return
            
            # Try local Ollama
            try:
                import ollama
                # Test connection
                ollama.list()
                self.client = ollama
                self.provider = "ollama"
                self.model_name = "llama2"  # Default local model
                self.logger.info("Using Ollama for LLM analysis")
                return
            except Exception:
                pass
            
            # No LLM available
            self.provider = None
            self.logger.warning("No LLM provider available - AI analysis will be limited")
            
        except Exception as e:
            log_error(e, "initializing LLM client")
            self.client = None
            self.provider = None
    
    def _make_llm_request(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """Make a request to the configured LLM."""
        if not self.client:
            return None
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=kwargs.get('max_tokens', 500),
                    temperature=kwargs.get('temperature', 0.7),
                )
                return response.choices[0].message.content
            
            elif self.provider == "anthropic":
                # Convert messages format for Anthropic
                system_msg = ""
                user_messages = []
                
                for msg in messages:
                    if msg['role'] == 'system':
                        system_msg = msg['content']
                    else:
                        user_messages.append(msg)
                
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=kwargs.get('max_tokens', 500),
                    system=system_msg,
                    messages=user_messages
                )
                return response.content[0].text
            
            elif self.provider == "ollama":
                # Combine messages for Ollama
                prompt = ""
                for msg in messages:
                    if msg['role'] == 'system':
                        prompt += f"System: {msg['content']}\n\n"
                    elif msg['role'] == 'user':
                        prompt += f"Human: {msg['content']}\n\n"
                    elif msg['role'] == 'assistant':
                        prompt += f"Assistant: {msg['content']}\n\n"
                
                prompt += "Assistant: "
                
                response = self.client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    options={
                        'num_predict': kwargs.get('max_tokens', 500),
                        'temperature': kwargs.get('temperature', 0.7),
                    }
                )
                return response['response']
            
            return None
            
        except Exception as e:
            log_error(e, f"making {self.provider} LLM request")
            return None
    
    def analyze_job_requirements(self, job_dict: Dict) -> Dict[str, Any]:
        """
        Analyze job requirements and extract key information.
        
        Args:
            job_dict: Job dictionary containing description, requirements, etc.
            
        Returns:
            Dictionary with analyzed job information
        """
        if not self.client:
            return self._fallback_job_analysis(job_dict)
        
        try:
            # Prepare job text
            job_text = self._prepare_job_text(job_dict)
            
            system_prompt = """You are an expert job market analyzer. Analyze the job posting and extract structured information.
            
            Focus on:
            1. Required technical skills (specific technologies, tools, frameworks)
            2. Soft skills and competencies
            3. Experience level requirements
            4. Company culture indicators
            5. Growth opportunities
            6. Key responsibilities
            7. Nice-to-have vs must-have requirements
            
            Respond in valid JSON format with these keys:
            - required_skills: list of essential technical skills
            - soft_skills: list of soft skills and competencies
            - experience_level: estimated years of experience needed
            - key_responsibilities: list of main job duties
            - growth_opportunities: list of career development aspects
            - culture_indicators: list of company culture signals
            - nice_to_have: list of preferred but not required skills
            - difficulty_level: score 1-10 (1=entry level, 10=expert level)
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this job posting:\n\n{job_text}"}
            ]
            
            response = self._make_llm_request(messages, max_tokens=800)
            
            if response:
                try:
                    # Try to parse JSON response
                    analysis = json.loads(response)
                    self.logger.info(f"Successfully analyzed job: {job_dict.get('title', 'Unknown')}")
                    return analysis
                except json.JSONDecodeError:
                    self.logger.warning("Failed to parse LLM JSON response, using fallback")
                    return self._fallback_job_analysis(job_dict)
            else:
                return self._fallback_job_analysis(job_dict)
                
        except Exception as e:
            log_error(e, "analyzing job requirements with LLM")
            return self._fallback_job_analysis(job_dict)
    
    def generate_match_explanation(self, job_dict: Dict, user_profile: Dict, match_scores: Dict) -> str:
        """
        Generate human-readable explanation for job match.
        
        Args:
            job_dict: Job information
            user_profile: User profile information
            match_scores: Dictionary of various match scores
            
        Returns:
            Human-readable match explanation
        """
        if not self.client:
            return self._fallback_match_explanation(job_dict, match_scores)
        
        try:
            job_text = self._prepare_job_text(job_dict)
            profile_text = self._prepare_profile_text(user_profile)
            scores_text = self._prepare_scores_text(match_scores)
            
            system_prompt = """You are a career advisor AI helping users understand why a job might be a good match for them.
            
            Analyze the job posting, user profile, and match scores to provide a personalized explanation.
            
            Your response should be:
            1. Conversational and encouraging
            2. Specific about skills and experience alignment
            3. Honest about potential challenges or gaps
            4. Include actionable advice if relevant
            5. Keep it concise (2-3 paragraphs max)
            
            Focus on the most important factors that make this a good (or not so good) match.
            """
            
            user_content = f"""Job Posting:
{job_text}

User Profile:
{profile_text}

Match Scores:
{scores_text}

Please explain why this job is or isn't a good match for this user, and provide any relevant advice."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            response = self._make_llm_request(messages, max_tokens=400, temperature=0.6)
            
            if response:
                return response.strip()
            else:
                return self._fallback_match_explanation(job_dict, match_scores)
                
        except Exception as e:
            log_error(e, "generating match explanation with LLM")
            return self._fallback_match_explanation(job_dict, match_scores)
    
    def identify_skill_gaps(self, job_dict: Dict, user_profile: Dict) -> Dict[str, Any]:
        """
        Identify skill gaps between user profile and job requirements.
        
        Args:
            job_dict: Job information
            user_profile: User profile information
            
        Returns:
            Dictionary with skill gap analysis
        """
        if not self.client:
            return self._fallback_skill_gaps(job_dict, user_profile)
        
        try:
            job_text = self._prepare_job_text(job_dict)
            profile_text = self._prepare_profile_text(user_profile)
            
            system_prompt = """You are a career development advisor. Analyze the gap between a user's current skills and a job's requirements.
            
            Provide specific, actionable advice on:
            1. Skills the user is missing
            2. Skills the user has that are relevant
            3. Recommended learning priorities
            4. Estimated time to bridge key gaps
            5. Alternative ways to gain experience
            
            Respond in valid JSON format with these keys:
            - missing_skills: list of skills user lacks
            - matching_skills: list of user skills that align with job
            - learning_priorities: list of skills to focus on first
            - time_estimates: dict mapping skills to learning time estimates
            - learning_suggestions: dict mapping skills to learning resources/methods
            - transferable_skills: list of user skills that could transfer to job needs
            """
            
            user_content = f"""Job Requirements:
{job_text}

User Skills and Experience:
{profile_text}

Please analyze the skill gap between this user and this job opportunity."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            response = self._make_llm_request(messages, max_tokens=600)
            
            if response:
                try:
                    analysis = json.loads(response)
                    return analysis
                except json.JSONDecodeError:
                    return self._fallback_skill_gaps(job_dict, user_profile)
            else:
                return self._fallback_skill_gaps(job_dict, user_profile)
                
        except Exception as e:
            log_error(e, "analyzing skill gaps with LLM")
            return self._fallback_skill_gaps(job_dict, user_profile)
    
    def generate_application_strategy(self, job_dict: Dict, user_profile: Dict) -> Dict[str, Any]:
        """
        Generate personalized application strategy for a job.
        
        Args:
            job_dict: Job information
            user_profile: User profile information
            
        Returns:
            Dictionary with application strategy recommendations
        """
        if not self.client:
            return self._fallback_application_strategy(job_dict)
        
        try:
            job_text = self._prepare_job_text(job_dict)
            profile_text = self._prepare_profile_text(user_profile)
            
            system_prompt = """You are an expert career strategist helping users optimize their job applications.
            
            Analyze the job and user profile to provide:
            1. Key selling points to highlight
            2. Potential concerns to address
            3. Resume customization suggestions
            4. Cover letter talking points
            5. Interview preparation topics
            6. Company research suggestions
            
            Respond in valid JSON format with these keys:
            - key_selling_points: list of user strengths to emphasize
            - concerns_to_address: list of potential weaknesses to overcome
            - resume_highlights: list of experiences/skills to feature prominently
            - cover_letter_themes: list of main points for cover letter
            - interview_prep: list of topics to prepare for
            - company_research: list of areas to research about the company
            - application_timing: recommendation on when/how to apply
            """
            
            user_content = f"""Job Opportunity:
{job_text}

Candidate Profile:
{profile_text}

Please provide a personalized application strategy for this candidate and job."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            response = self._make_llm_request(messages, max_tokens=700)
            
            if response:
                try:
                    strategy = json.loads(response)
                    return strategy
                except json.JSONDecodeError:
                    return self._fallback_application_strategy(job_dict)
            else:
                return self._fallback_application_strategy(job_dict)
                
        except Exception as e:
            log_error(e, "generating application strategy with LLM")
            return self._fallback_application_strategy(job_dict)
    
    def _prepare_job_text(self, job_dict: Dict) -> str:
        """Prepare job information as text for LLM processing."""
        parts = []
        
        if job_dict.get('title'):
            parts.append(f"Title: {job_dict['title']}")
        
        if job_dict.get('company'):
            parts.append(f"Company: {job_dict['company']}")
        
        if job_dict.get('location'):
            parts.append(f"Location: {job_dict['location']}")
        
        if job_dict.get('description'):
            parts.append(f"Description: {job_dict['description']}")
        
        if job_dict.get('requirements'):
            if isinstance(job_dict['requirements'], list):
                parts.append(f"Requirements: {'; '.join(job_dict['requirements'])}")
            else:
                parts.append(f"Requirements: {job_dict['requirements']}")
        
        if job_dict.get('responsibilities'):
            if isinstance(job_dict['responsibilities'], list):
                parts.append(f"Responsibilities: {'; '.join(job_dict['responsibilities'])}")
            else:
                parts.append(f"Responsibilities: {job_dict['responsibilities']}")
        
        if job_dict.get('skills_required'):
            if isinstance(job_dict['skills_required'], list):
                parts.append(f"Required Skills: {', '.join(job_dict['skills_required'])}")
        
        if job_dict.get('skills_preferred'):
            if isinstance(job_dict['skills_preferred'], list):
                parts.append(f"Preferred Skills: {', '.join(job_dict['skills_preferred'])}")
        
        return "\n".join(parts)
    
    def _prepare_profile_text(self, user_profile: Dict) -> str:
        """Prepare user profile as text for LLM processing."""
        parts = []
        
        if user_profile.get('current_title'):
            parts.append(f"Current Role: {user_profile['current_title']}")
        
        if user_profile.get('experience_years'):
            parts.append(f"Years of Experience: {user_profile['experience_years']}")
        
        if user_profile.get('industry'):
            parts.append(f"Industry: {user_profile['industry']}")
        
        if user_profile.get('skills'):
            if isinstance(user_profile['skills'], list):
                parts.append(f"Skills: {', '.join(user_profile['skills'])}")
        
        if user_profile.get('preferred_titles'):
            if isinstance(user_profile['preferred_titles'], list):
                parts.append(f"Preferred Roles: {', '.join(user_profile['preferred_titles'])}")
        
        if user_profile.get('preferred_locations'):
            if isinstance(user_profile['preferred_locations'], list):
                parts.append(f"Preferred Locations: {', '.join(user_profile['preferred_locations'])}")
        
        return "\n".join(parts) if parts else "Limited profile information available"
    
    def _prepare_scores_text(self, match_scores: Dict) -> str:
        """Prepare match scores as text for LLM processing."""
        parts = []
        
        for key, value in match_scores.items():
            if isinstance(value, float):
                percentage = int(value * 100)
                parts.append(f"{key.replace('_', ' ').title()}: {percentage}%")
        
        return "\n".join(parts)
    
    # Fallback methods for when LLM is not available
    
    def _fallback_job_analysis(self, job_dict: Dict) -> Dict[str, Any]:
        """Fallback job analysis when LLM is not available."""
        skills = []
        if job_dict.get('skills_required'):
            skills.extend(job_dict['skills_required'] if isinstance(job_dict['skills_required'], list) else [])
        if job_dict.get('skills_preferred'):
            skills.extend(job_dict['skills_preferred'] if isinstance(job_dict['skills_preferred'], list) else [])
        
        return {
            "required_skills": skills[:5],  # Limit to top 5
            "soft_skills": ["Communication", "Problem Solving", "Teamwork"],
            "experience_level": "3-5 years",
            "key_responsibilities": job_dict.get('responsibilities', [])[:3],
            "growth_opportunities": ["Skill development", "Career advancement"],
            "culture_indicators": ["Collaborative environment"],
            "nice_to_have": skills[5:] if len(skills) > 5 else [],
            "difficulty_level": 5
        }
    
    def _fallback_match_explanation(self, job_dict: Dict, match_scores: Dict) -> str:
        """Fallback match explanation when LLM is not available."""
        overall_score = match_scores.get('overall_score', 0)
        
        if overall_score >= 0.7:
            return f"This looks like a strong match for the {job_dict.get('title', 'position')} role at {job_dict.get('company', 'this company')}. Your skills and experience align well with their requirements."
        elif overall_score >= 0.5:
            return f"This could be a good opportunity for the {job_dict.get('title', 'position')} role. There are some areas of alignment, though you may want to highlight specific relevant experiences in your application."
        else:
            return f"This {job_dict.get('title', 'position')} role might be a stretch, but could offer growth opportunities. Consider whether you're ready to take on new challenges in areas where you have less experience."
    
    def _fallback_skill_gaps(self, job_dict: Dict, user_profile: Dict) -> Dict[str, Any]:
        """Fallback skill gap analysis when LLM is not available."""
        job_skills = set()
        if job_dict.get('skills_required'):
            job_skills.update(job_dict['skills_required'] if isinstance(job_dict['skills_required'], list) else [])
        
        user_skills = set()
        if user_profile.get('skills'):
            user_skills.update(user_profile['skills'] if isinstance(user_profile['skills'], list) else [])
        
        missing = list(job_skills - user_skills)
        matching = list(job_skills.intersection(user_skills))
        
        return {
            "missing_skills": missing[:5],
            "matching_skills": matching,
            "learning_priorities": missing[:3],
            "time_estimates": {skill: "2-3 months" for skill in missing[:3]},
            "learning_suggestions": {skill: "Online courses and practice projects" for skill in missing[:3]},
            "transferable_skills": matching
        }
    
    def _fallback_application_strategy(self, job_dict: Dict) -> Dict[str, Any]:
        """Fallback application strategy when LLM is not available."""
        return {
            "key_selling_points": ["Relevant experience", "Technical skills", "Problem-solving abilities"],
            "concerns_to_address": ["Any experience gaps", "Salary expectations"],
            "resume_highlights": ["Recent projects", "Key achievements", "Relevant skills"],
            "cover_letter_themes": ["Passion for the role", "Relevant experience", "Cultural fit"],
            "interview_prep": ["Technical questions", "Behavioral scenarios", "Company knowledge"],
            "company_research": ["Company mission", "Recent news", "Team structure"],
            "application_timing": "Apply within 1-2 weeks for best visibility"
        }
    
    def is_available(self) -> bool:
        """Check if LLM service is available."""
        return self.client is not None
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current LLM provider."""
        return {
            "provider": self.provider,
            "model": self.model_name,
            "available": self.is_available()
        }


# Global LLM analyzer instance
llm_analyzer = LLMAnalyzer()
