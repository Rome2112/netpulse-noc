"""
Configuration management for netpulse-noc.

Environment-based configuration with sensible defaults.
"""

import os
from typing import Optional


class Config:
    """Configuration container for NOC server."""
    
    # Server settings
    HOST: str = os.getenv("NOC_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("NOC_PORT", "8000"))
    DEBUG: bool = os.getenv("NOC_DEBUG", "false").lower() == "true"
    
    # Telemetry store settings
    TELEMETRY_STORE_MAX_SIZE: int = int(os.getenv("NOC_STORE_MAX_SIZE", "1000"))
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("NOC_LOG_LEVEL", "INFO")
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls()
    
    @classmethod
    def get_dsn(cls) -> Optional[str]:
        """Get database DSN if configured (for future persistence layer)."""
        return os.getenv("NOC_DATABASE_URL")


# Global config instance
config = Config.from_env()
