"""
Configuration management system with YAML parsing, validation, and hot-reload support.

This module provides configuration loading, validation, and hot-reload capabilities
for the microblog application.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, validator
from watchfiles import awatch

from microblog.utils import ensure_directory, get_content_dir

logger = logging.getLogger(__name__)


class SiteConfig(BaseModel):
    """Site-level configuration settings."""
    title: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., pattern=r'^https?://.+')
    author: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)


class BuildConfig(BaseModel):
    """Build-related configuration settings."""
    output_dir: str = Field(default='build', max_length=100)
    backup_dir: str = Field(default='build.bak', max_length=100)
    posts_per_page: int = Field(default=10, ge=1, le=100)


class ServerConfig(BaseModel):
    """Server configuration settings."""
    host: str = Field(default='127.0.0.1', max_length=100)
    port: int = Field(default=8000, ge=1024, le=65535)
    hot_reload: bool = Field(default=False)


class AuthConfig(BaseModel):
    """Authentication configuration settings."""
    jwt_secret: str = Field(..., min_length=32, max_length=255)
    session_expires: int = Field(default=7200, ge=60)  # seconds


class AppConfig(BaseModel):
    """Main application configuration model."""
    site: SiteConfig
    build: BuildConfig = Field(default_factory=BuildConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    auth: AuthConfig

    @validator('auth')
    def validate_jwt_secret_length(cls, v):
        if len(v.jwt_secret) < 32:
            raise ValueError('JWT secret must be at least 32 characters long')
        return v


class ConfigManager:
    """
    Configuration manager with YAML loading, validation, and hot-reload support.

    Features:
    - YAML configuration file parsing
    - Pydantic-based validation
    - Hot-reload in development mode
    - Error handling and logging
    """

    def __init__(self, config_path: Path | None = None, dev_mode: bool = False):
        """
        Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file. Defaults to content/_data/config.yaml
            dev_mode: Enable development mode with hot-reload
        """
        self.config_path = config_path or get_content_dir() / "_data" / "config.yaml"
        self.dev_mode = dev_mode
        self._config: AppConfig | None = None
        self._watcher_task: asyncio.Task | None = None
        self._callbacks: list = []

    @property
    def config(self) -> AppConfig:
        """Get the current configuration. Loads if not already loaded."""
        if self._config is None:
            self.load_config()
        return self._config

    def load_config(self) -> AppConfig:
        """
        Load and validate configuration from YAML file.

        Returns:
            Validated configuration object

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValidationError: If config validation fails
            yaml.YAMLError: If YAML parsing fails
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, encoding='utf-8') as file:
                raw_config = yaml.safe_load(file)

            if raw_config is None:
                raise ValueError("Configuration file is empty or invalid")

            self._config = AppConfig(**raw_config)
            logger.info(f"Configuration loaded successfully from {self.config_path}")
            return self._config

        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {self.config_path}: {e}")
            raise
        except ValidationError as e:
            logger.error(f"Configuration validation error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading configuration: {e}")
            raise

    def reload_config(self) -> bool:
        """
        Reload configuration from file.

        Returns:
            True if reload successful, False if error occurred
        """
        try:
            old_config = self._config
            self.load_config()
            logger.info("Configuration reloaded successfully")

            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(old_config, self._config)
                except Exception as e:
                    logger.error(f"Error in config reload callback: {e}")

            return True
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False

    def add_reload_callback(self, callback):
        """
        Add a callback function to be called when configuration is reloaded.

        Args:
            callback: Function that takes (old_config, new_config) as arguments
        """
        self._callbacks.append(callback)

    def remove_reload_callback(self, callback):
        """Remove a reload callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def start_watcher(self):
        """Start file watcher for hot-reload in development mode."""
        if not self.dev_mode:
            logger.warning("File watcher requested but not in development mode")
            return

        if self._watcher_task is not None:
            logger.warning("File watcher already running")
            return

        self._watcher_task = asyncio.create_task(self._watch_config_file())
        logger.info(f"Started configuration file watcher for {self.config_path}")

    async def stop_watcher(self):
        """Stop the file watcher."""
        if self._watcher_task is not None:
            self._watcher_task.cancel()
            try:
                await self._watcher_task
            except asyncio.CancelledError:
                pass
            self._watcher_task = None
            logger.info("Stopped configuration file watcher")

    async def _watch_config_file(self):
        """Internal method to watch configuration file for changes."""
        config_dir = self.config_path.parent

        try:
            async for changes in awatch(config_dir):
                for change_type, changed_path in changes:
                    # Normalize paths for comparison
                    changed_path_obj = Path(changed_path).resolve()
                    config_path_obj = self.config_path.resolve()

                    if changed_path_obj == config_path_obj:
                        logger.info(f"Configuration file changed: {change_type}")
                        await asyncio.sleep(0.1)  # Brief delay to ensure file write is complete

                        if self.reload_config():
                            logger.info("Configuration hot-reload completed")
                        else:
                            logger.error("Configuration hot-reload failed")
                        break
        except asyncio.CancelledError:
            logger.debug("Configuration file watcher cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in configuration file watcher: {e}")

    def validate_config_file(self, config_path: Path | None = None) -> tuple[bool, str | None]:
        """
        Validate a configuration file without loading it.

        Args:
            config_path: Path to config file to validate. Uses default if None.

        Returns:
            Tuple of (is_valid, error_message)
        """
        file_path = config_path or self.config_path

        try:
            with open(file_path, encoding='utf-8') as file:
                raw_config = yaml.safe_load(file)

            if raw_config is None:
                return False, "Configuration file is empty or invalid"

            AppConfig(**raw_config)
            return True, None

        except FileNotFoundError:
            return False, f"Configuration file not found: {file_path}"
        except yaml.YAMLError as e:
            return False, f"YAML parsing error: {e}"
        except ValidationError as e:
            return False, f"Validation error: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"

    def get_config_dict(self) -> dict[str, Any]:
        """Get configuration as a dictionary."""
        return self.config.model_dump()

    def get_json_schema(self) -> dict[str, Any]:
        """Get JSON schema for the configuration."""
        return AppConfig.model_json_schema()


# Global configuration manager instance
_config_manager: ConfigManager | None = None


def get_config_manager(dev_mode: bool = False) -> ConfigManager:
    """
    Get the global configuration manager instance.

    Args:
        dev_mode: Enable development mode with hot-reload

    Returns:
        ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(dev_mode=dev_mode)
    return _config_manager


def get_config() -> AppConfig:
    """Get the current configuration."""
    return get_config_manager().config


def create_default_config_file(config_path: Path | None = None) -> Path:
    """
    Create a default configuration file.

    Args:
        config_path: Path where to create the config file

    Returns:
        Path to the created configuration file
    """
    if config_path is None:
        config_path = get_content_dir() / "_data" / "config.yaml"

    # Ensure the directory exists
    ensure_directory(config_path.parent)

    # Default configuration
    default_config = {
        'site': {
            'title': 'My Microblog',
            'url': 'https://example.com',
            'author': 'Blog Author',
            'description': 'A personal blog powered by Microblog'
        },
        'build': {
            'output_dir': 'build',
            'backup_dir': 'build.bak',
            'posts_per_page': 10
        },
        'server': {
            'host': '127.0.0.1',
            'port': 8000,
            'hot_reload': False
        },
        'auth': {
            'jwt_secret': 'your-super-secret-jwt-key-must-be-at-least-32-characters-long',
            'session_expires': 7200
        }
    }

    with open(config_path, 'w', encoding='utf-8') as file:
        yaml.dump(default_config, file, default_flow_style=False, sort_keys=False)

    logger.info(f"Created default configuration file at {config_path}")
    return config_path
