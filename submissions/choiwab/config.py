"""
Configuration management for Banking Client.
Supports environment-based configuration.
"""

import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class BankingConfig:
    """Configuration settings for the Banking Client."""

    # API Settings
    api_base_url: str = "http://localhost:8123"
    api_timeout: int = 10

    # Authentication Settings
    default_username: str = "alice"
    default_password: str = "secret"
    default_scope: str = "transfer"

    # Retry Settings
    max_retries: int = 3
    backoff_factor: float = 1.0

    # Connection Pool Settings
    pool_connections: int = 10
    pool_maxsize: int = 20

    # Logging Settings
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> 'BankingConfig':
        """
        Load configuration from environment variables.

        Environment variables:
        - BANKING_API_URL: Base URL of the banking API
        - BANKING_API_TIMEOUT: Request timeout in seconds
        - BANKING_USERNAME: Default username
        - BANKING_PASSWORD: Default password
        - BANKING_SCOPE: Default token scope
        - LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)

        Returns:
            BankingConfig instance with values from environment
        """
        return cls(
            api_base_url=os.getenv("BANKING_API_URL", "http://localhost:8123"),
            api_timeout=int(os.getenv("BANKING_API_TIMEOUT", "10")),
            default_username=os.getenv("BANKING_USERNAME", "alice"),
            default_password=os.getenv("BANKING_PASSWORD", "secret"),
            default_scope=os.getenv("BANKING_SCOPE", "transfer"),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            backoff_factor=float(os.getenv("BACKOFF_FACTOR", "1.0")),
            pool_connections=int(os.getenv("POOL_CONNECTIONS", "10")),
            pool_maxsize=int(os.getenv("POOL_MAXSIZE", "20")),
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )

    @classmethod
    def load_from_file(cls, filepath: Optional[str] = None) -> 'BankingConfig':
        """
        Load configuration from .env file.

        Args:
            filepath: Path to .env file (defaults to .env in current directory)

        Returns:
            BankingConfig instance
        """
        if filepath is None:
            filepath = Path.cwd() / ".env"

        if Path(filepath).exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(filepath)
            except ImportError:
                print("Warning: python-dotenv not installed, skipping .env file")

        return cls.from_env()


# Singleton instance
_config: Optional[BankingConfig] = None


def get_config() -> BankingConfig:
    """
    Get the global configuration instance.

    Returns:
        BankingConfig singleton instance
    """
    global _config
    if _config is None:
        _config = BankingConfig.from_env()
    return _config


def set_config(config: BankingConfig) -> None:
    """
    Set the global configuration instance.

    Args:
        config: BankingConfig instance to set as global
    """
    global _config
    _config = config
