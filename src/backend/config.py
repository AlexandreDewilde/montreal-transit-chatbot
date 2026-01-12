"""
Configuration and logging setup for MTL Finder backend
"""

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load environment variables from project root
current_folder = Path(__file__).parent
env_path = current_folder.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Configuration
    api_url: str = Field(default="http://localhost:8000", alias="API_URL")
    api_port: int = Field(default=8000, alias="API_PORT")

    # Mistral AI Configuration
    mistral_api_key: Optional[str] = Field(default=None, alias="MISTRAL_API_KEY")
    mistral_model: str = Field(default="mistral-small-latest", alias="MISTRAL_MODEL")

    # Logging Configuration
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Chat Configuration
    max_chat_iterations: int = Field(default=10)

    class Config:
        env_file = str(env_path)
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create settings instance

    Returns:
        Settings: Application settings
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure logging with specified level

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        logging.Logger: Configured logger instance
    """
    # Convert log level string to logging level
    level = logging.getLevelName(log_level.upper())
    if not isinstance(level, int):
        level = logging.INFO  # Default to INFO if level is invalid

    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    # Create and configure logger for this module
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module

    Args:
        name: Logger name (typically __name__)

    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)
