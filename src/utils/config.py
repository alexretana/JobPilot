"""
Configuration management for JobPilot.
Handles environment variables, settings, and configuration validation.
"""

import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Core Settings
    project_name: str = Field(default="JobPilot", env="PROJECT_NAME")
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    data_dir: str = Field(default="./data", env="DATA_DIR")
    
    # AI Provider Settings
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-sonnet-20240229", env="ANTHROPIC_MODEL")
    
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama2:latest", env="OLLAMA_MODEL")
    
    # Vector Database Settings
    qdrant_url: str = Field(default="http://localhost:6333", env="QDRANT_URL")
    qdrant_api_key: Optional[str] = Field(default=None, env="QDRANT_API_KEY")
    
    pinecone_api_key: Optional[str] = Field(default=None, env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(default=None, env="PINECONE_ENVIRONMENT")
    
    chroma_persist_directory: str = Field(default="./data/chroma", env="CHROMA_PERSIST_DIRECTORY")
    
    # Job Board API Settings
    linkedin_client_id: Optional[str] = Field(default=None, env="LINKEDIN_CLIENT_ID")
    linkedin_client_secret: Optional[str] = Field(default=None, env="LINKEDIN_CLIENT_SECRET")
    linkedin_access_token: Optional[str] = Field(default=None, env="LINKEDIN_ACCESS_TOKEN")
    
    indeed_publisher_id: Optional[str] = Field(default=None, env="INDEED_PUBLISHER_ID")
    
    glassdoor_partner_id: Optional[str] = Field(default=None, env="GLASSDOOR_PARTNER_ID")
    glassdoor_api_key: Optional[str] = Field(default=None, env="GLASSDOOR_API_KEY")
    
    # Communication API Settings
    gmail_client_id: Optional[str] = Field(default=None, env="GMAIL_CLIENT_ID")
    gmail_client_secret: Optional[str] = Field(default=None, env="GMAIL_CLIENT_SECRET")
    gmail_refresh_token: Optional[str] = Field(default=None, env="GMAIL_REFRESH_TOKEN")
    
    sendgrid_api_key: Optional[str] = Field(default=None, env="SENDGRID_API_KEY")
    from_email: Optional[str] = Field(default=None, env="FROM_EMAIL")
    
    # Browser Settings
    browser_headless: bool = Field(default=True, env="BROWSER_HEADLESS")
    browser_timeout: int = Field(default=30000, env="BROWSER_TIMEOUT")
    browser_user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        env="BROWSER_USER_AGENT"
    )
    
    # Proxy Settings
    proxy_host: Optional[str] = Field(default=None, env="PROXY_HOST")
    proxy_port: Optional[int] = Field(default=None, env="PROXY_PORT")
    proxy_username: Optional[str] = Field(default=None, env="PROXY_USERNAME")
    proxy_password: Optional[str] = Field(default=None, env="PROXY_PASSWORD")
    
    # Database Settings
    database_url: str = Field(default="sqlite:///./data/jobpilot.db", env="DATABASE_URL")
    
    # Rate Limiting
    linkedin_rate_limit: int = Field(default=60, env="LINKEDIN_RATE_LIMIT")
    indeed_rate_limit: int = Field(default=100, env="INDEED_RATE_LIMIT")
    glassdoor_rate_limit: int = Field(default=50, env="GLASSDOOR_RATE_LIMIT")
    default_rate_limit: int = Field(default=120, env="DEFAULT_RATE_LIMIT")
    
    # Security
    jwt_secret_key: str = Field(default="change-me-in-production", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=30, env="JWT_EXPIRE_MINUTES")
    
    # User Preferences
    default_location: str = Field(default="Remote", env="DEFAULT_LOCATION")
    default_radius_miles: int = Field(default=50, env="DEFAULT_RADIUS_MILES")
    default_salary_min: int = Field(default=75000, env="DEFAULT_SALARY_MIN")
    default_job_types: str = Field(default="Full-time,Contract", env="DEFAULT_JOB_TYPES")
    
    default_resume_path: str = Field(default="./data/profiles/default_resume.pdf", env="DEFAULT_RESUME_PATH")
    default_cover_letter_template: str = Field(default="./data/profiles/cover_letter_template.txt", env="DEFAULT_COVER_LETTER_TEMPLATE")
    
    # Development Settings
    debug_mode: bool = Field(default=False, env="DEBUG_MODE")
    mock_external_apis: bool = Field(default=False, env="MOCK_EXTERNAL_APIS")
    save_screenshots: bool = Field(default=True, env="SAVE_SCREENSHOTS")
    save_page_sources: bool = Field(default=False, env="SAVE_PAGE_SOURCES")
    
    # Logging
    log_file: str = Field(default="./logs/jobpilot.log", env="LOG_FILE")
    log_rotation: str = Field(default="10 MB", env="LOG_ROTATION")
    log_retention: str = Field(default="30 days", env="LOG_RETENTION")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    @validator("environment")
    def validate_environment(cls, v):
        if v not in ["development", "staging", "production"]:
            raise ValueError("Environment must be one of: development, staging, production")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        if v not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("Log level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        return v
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def job_types_list(self) -> List[str]:
        return [job_type.strip() for job_type in self.default_job_types.split(",")]
    
    def get_proxy_config(self) -> Optional[Dict[str, Any]]:
        """Get proxy configuration if available."""
        if not self.proxy_host or not self.proxy_port:
            return None
            
        config = {
            "server": f"{self.proxy_host}:{self.proxy_port}"
        }
        
        if self.proxy_username and self.proxy_password:
            config["username"] = self.proxy_username
            config["password"] = self.proxy_password
            
        return config
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.data_dir,
            Path(self.data_dir) / "profiles",
            Path(self.data_dir) / "jobs", 
            Path(self.data_dir) / "contacts",
            Path(self.data_dir) / "chroma",
            Path(self.log_file).parent,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)


def load_settings() -> Settings:
    """Load and validate application settings."""
    # Try to load .env file
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
    
    settings = Settings()
    settings.ensure_directories()
    
    return settings


# Global settings instance
settings = load_settings()
