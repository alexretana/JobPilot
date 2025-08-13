"""
Logging configuration for JobPilot.
Provides structured logging with file rotation and different log levels.
"""

import sys
import logging
from pathlib import Path
from loguru import logger
from typing import Dict, Any
from .config import settings


class InterceptHandler(logging.Handler):
    """Intercept standard logging messages toward Loguru sinks."""
    
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    """Configure logging for the application."""
    
    # Remove default loguru logger
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Add file handler with rotation
    log_file = Path(settings.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",  # Always log everything to file
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression="zip",
        backtrace=True,
        diagnose=True,
    )
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Set levels for third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    

def get_logger(name: str) -> "logger":
    """Get a logger instance for the specified name."""
    return logger.bind(name=name)


class LoggerMixin:
    """Mixin class to add logging capabilities to other classes."""
    
    @property
    def logger(self):
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


def log_function_call(func_name: str, **kwargs) -> None:
    """Log a function call with its parameters."""
    logger.debug(f"Calling {func_name} with params: {kwargs}")


def log_api_call(service: str, endpoint: str, method: str = "GET", **kwargs) -> None:
    """Log an API call."""
    logger.debug(f"API Call: {method} {service}/{endpoint}", extra=kwargs)


def log_scraping_action(action: str, url: str, **kwargs) -> None:
    """Log a web scraping action."""
    logger.info(f"Scraping: {action} on {url}", extra=kwargs)


def log_job_processing(action: str, job_id: str, **kwargs) -> None:
    """Log job processing actions."""
    logger.info(f"Job Processing: {action} for job {job_id}", extra=kwargs)


def log_error(error: Exception, context: str = "", **kwargs) -> None:
    """Log an error with context."""
    logger.error(f"Error in {context}: {str(error)}", extra=kwargs)
    if settings.is_development:
        logger.exception("Full traceback:")


# Initialize logging when module is imported
setup_logging()
