"""
Configuration management for Agente_Perfilamiento.

This module handles environment variables, settings, and provides
configured instances of external services like LLM models.
"""

import os
from pathlib import Path
from typing import Optional, Union, List
from dotenv import load_dotenv, find_dotenv

from agente_perfilamiento.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


def load_environment_variables() -> None:
    """
    Load environment variables from a single .env file.
    
    This simplified approach loads only one .env file from the project root,
    allowing users to configure their LLM provider, API keys, and model parameters.
    """
    # Get the project root directory (where .env file should be located)
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    
    # Load the single .env file
    env_file = project_root / ".env"
    
    if env_file.exists():
        try:
            load_dotenv(env_file, override=True)
            logger.info(f"Environment variables loaded from: {env_file.name}")
        except Exception as e:
            logger.warning(f"Failed to load environment file {env_file}: {e}")
    else:
        # Try to find and load any .env file in current directory or parents as fallback
        try:
            fallback_env = find_dotenv()
            if fallback_env:
                load_dotenv(fallback_env)
                logger.info(f"Loaded environment file: {Path(fallback_env).name}")
            else:
                logger.info("No .env file found. Using system environment variables only.")
        except Exception as e:
            logger.info("No .env file found. Using system environment variables only.")


# Load environment variables using enhanced loading
load_environment_variables()


class Settings:
    """
    Application settings and configuration.
    """
    
    def __init__(self):
        """Initialize settings from environment variables."""
        # Generic LLM Configuration
        self.llm_api_key: str = os.getenv("LLM_API_KEY", "")
        self.llm_model_name: str = os.getenv("LLM_MODEL", os.getenv("LLM_MODEL_NAME", "gpt-4o-mini"))
        self.llm_provider: str = os.getenv("LLM_PROVIDER", "openai").lower()
        self.llm_base_url: Optional[str] = os.getenv("LLM_BASE_URL")
        
        # Provider-specific configurations (fallback support)
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", self.llm_api_key)
        self.openai_model: str = os.getenv("OPENAI_MODEL", self.llm_model_name)
        self.anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", self.llm_api_key)
        self.anthropic_model: str = os.getenv("ANTHROPIC_MODEL", self.llm_model_name)
        self.google_api_key: str = os.getenv("GOOGLE_API_KEY", self.llm_api_key)
        self.google_model: str = os.getenv("GOOGLE_MODEL", self.llm_model_name)
        
        # AWS Configuration (optional)
        self.aws_region_name: Optional[str] = os.getenv("AWS_REGION_NAME")
        self.aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_session_token: Optional[str] = os.getenv("AWS_SESSION_TOKEN")
        
        # Application Configuration
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.environment: str = os.getenv("ENVIRONMENT", "development")
        
        # Data directories
        self.data_dir: str = os.getenv("DATA_DIR", "data")
        self.conversations_dir: str = f"{self.data_dir}/conversations"
        self.memory_dir: str = f"{self.data_dir}/memory"
        
        self._validate_settings()
    
    def _validate_settings(self) -> None:
        """Validate required settings."""
        if not self.llm_api_key:
            raise ValueError("LLM_API_KEY environment variable is required")
        
        supported_providers = ["openai", "anthropic", "google", "custom"]
        if self.llm_provider not in supported_providers:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}. Supported: {supported_providers}")
        
        logger.info(f"Settings loaded for environment: {self.environment}")
        logger.info(f"Using LLM provider: {self.llm_provider} with model: {self.llm_model_name}")


# Global settings instance
settings = Settings()


def get_llm_model(temperature: float = 0.1) -> Union:
    """
    Get configured LLM model instance based on the provider setting.
    
    Args:
        temperature: Model temperature for response randomness
        
    Returns:
        Configured LLM instance (provider-specific)
    """
    try:
        if settings.llm_provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=settings.llm_model_name,
                temperature=temperature,
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url
            )
        
        elif settings.llm_provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=settings.llm_model_name,
                temperature=temperature,
                api_key=settings.llm_api_key
            )
        
        elif settings.llm_provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=settings.llm_model_name,
                temperature=temperature,
                google_api_key=settings.llm_api_key
            )
        
        elif settings.llm_provider == "custom":
            # For custom providers, try to use OpenAI-compatible interface
            from langchain_openai import ChatOpenAI
            if not settings.llm_base_url:
                raise ValueError("LLM_BASE_URL is required for custom provider")
            return ChatOpenAI(
                model=settings.llm_model_name,
                temperature=temperature,
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url
            )
        
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
            
    except ImportError as e:
        logger.error(f"Failed to import LLM provider {settings.llm_provider}: {e}")
        logger.error("Make sure you have installed the required package for your LLM provider")
        raise
    except Exception as e:
        logger.error(f"Error creating LLM model: {e}")
        raise


def ensure_data_directories() -> None:
    """
    Ensure data directories exist.
    """
    os.makedirs(settings.conversations_dir, exist_ok=True)
    os.makedirs(settings.memory_dir, exist_ok=True)
    logger.info("Data directories ensured")