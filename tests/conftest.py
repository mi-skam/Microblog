"""
Shared test fixtures and configuration for the microblog test suite.

This module provides common fixtures used across all test modules including
temporary files, mock configuration data, and test utilities.
"""

import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_path = Path(f.name)

    yield config_path

    # Cleanup
    if config_path.exists():
        config_path.unlink()


@pytest.fixture
def valid_config_data() -> dict[str, Any]:
    """Provide valid configuration data for testing."""
    return {
        'site': {
            'title': 'Test Blog',
            'url': 'https://test.example.com',
            'author': 'Test Author',
            'description': 'A test blog for testing purposes'
        },
        'build': {
            'output_dir': 'test_build',
            'backup_dir': 'test_build.bak',
            'posts_per_page': 5
        },
        'server': {
            'host': '127.0.0.1',
            'port': 8080,
            'hot_reload': True
        },
        'auth': {
            'jwt_secret': 'test-secret-key-that-is-long-enough-for-testing-purposes',
            'session_expires': 3600
        }
    }


@pytest.fixture
def invalid_config_data() -> dict[str, Any]:
    """Provide invalid configuration data for testing validation."""
    return {
        'site': {
            'title': '',  # Invalid: empty title
            'url': 'not-a-valid-url',  # Invalid: malformed URL
            'author': 'Test Author'
            # Missing description is OK (optional)
        },
        'build': {
            'output_dir': 'test_build',
            'backup_dir': 'test_build.bak',
            'posts_per_page': 0  # Invalid: must be >= 1
        },
        'server': {
            'host': '127.0.0.1',
            'port': 99999,  # Invalid: port too high
            'hot_reload': True
        },
        'auth': {
            'jwt_secret': 'short',  # Invalid: too short
            'session_expires': 30  # Invalid: too short
        }
    }


@pytest.fixture
def valid_config_file(temp_config_file, valid_config_data):
    """Create a temporary config file with valid configuration."""
    with open(temp_config_file, 'w') as f:
        yaml.dump(valid_config_data, f, default_flow_style=False)
    return temp_config_file


@pytest.fixture
def invalid_config_file(temp_config_file, invalid_config_data):
    """Create a temporary config file with invalid configuration."""
    with open(temp_config_file, 'w') as f:
        yaml.dump(invalid_config_data, f, default_flow_style=False)
    return temp_config_file


@pytest.fixture
def empty_config_file(temp_config_file):
    """Create an empty config file for testing."""
    with open(temp_config_file, 'w') as f:
        f.write('')
    return temp_config_file


@pytest.fixture
def malformed_yaml_file(temp_config_file):
    """Create a config file with malformed YAML."""
    with open(temp_config_file, 'w') as f:
        f.write("""
site:
  title: Test Blog
  url: https://test.example.com
  author: Test Author
build:
  output_dir: test_build
  - invalid_yaml_structure
""")
    return temp_config_file


@pytest.fixture
def minimal_valid_config_data() -> dict[str, Any]:
    """Provide minimal valid configuration data."""
    return {
        'site': {
            'title': 'Minimal Blog',
            'url': 'https://minimal.example.com',
            'author': 'Minimal Author'
        },
        'auth': {
            'jwt_secret': 'minimal-test-secret-key-that-is-long-enough-for-testing'
        }
    }


@pytest.fixture
def minimal_config_file(temp_config_file, minimal_valid_config_data):
    """Create a config file with minimal valid configuration."""
    with open(temp_config_file, 'w') as f:
        yaml.dump(minimal_valid_config_data, f, default_flow_style=False)
    return temp_config_file


@pytest.fixture
def temp_content_dir():
    """Create a temporary content directory structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        content_dir = Path(temp_dir) / 'content'
        data_dir = content_dir / '_data'
        data_dir.mkdir(parents=True)
        yield content_dir


@pytest.fixture
def mock_config_callback():
    """Create a mock callback function for config reload testing."""
    class MockCallback:
        def __init__(self):
            self.called = False
            self.old_config = None
            self.new_config = None

        def __call__(self, old_config, new_config):
            self.called = True
            self.old_config = old_config
            self.new_config = new_config

        def reset(self):
            self.called = False
            self.old_config = None
            self.new_config = None

    return MockCallback()
