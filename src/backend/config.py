"""
Configuration and logging setup for MTL Finder backend
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings
from uvicorn.logging import ColourizedFormatter

# Path to .env file in project root
current_folder = Path(__file__).parent
env_path = current_folder.parent.parent / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Configuration
    api_url: str = Field(default="http://localhost:8000", alias="API_URL")
    api_port: int = Field(default=8000, alias="API_PORT")

    # Mistral AI Configuration
    mistral_api_key: Optional[str] = Field(default=None, alias="MISTRAL_API_KEY")
    mistral_model: str = Field(default="mistral-small-latest", alias="MISTRAL_MODEL")

    # STM API Configuration
    stm_api_key: Optional[str] = Field(default=None, alias="STM_API_KEY")

    # Photon Geocoder Configuration
    photon_url: str = Field(default="http://localhost:2322", alias="PHOTON_URL")

    # OpenTripPlanner Configuration
    otp_url: str = Field(default="http://localhost:8080/otp/gtfs/v1", alias="OTP_URL")

    # Logging Configuration
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Chat Configuration
    max_chat_iterations: int = Field(default=10)

    # CORS Configuration
    cors_origins: str = Field(
        default="http://localhost:8501,http://127.0.0.1:8501",
        alias="CORS_ORIGINS",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS string into a list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

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
    Configure logging with specified level using uvicorn's colored formatter

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        logging.Logger: Configured logger instance
    """
    # Convert log level string to logging level
    level = logging.getLevelName(log_level.upper())
    if not isinstance(level, int):
        level = logging.INFO  # Default to INFO if level is invalid

    # Create colored formatter (same as uvicorn)
    formatter = ColourizedFormatter(
        "{levelprefix} {name} - {message}",
        style="{",
        use_colors=True
    )

    # Create console handler with colored formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()  # Clear existing handlers
    root_logger.addHandler(console_handler)

    # Configure uvicorn loggers to use same level
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.error").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(level)

    # Create logger for this module
    logger = logging.getLogger(__name__)
    logger.info(f"✅ Logging configured with level: {log_level}")

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
