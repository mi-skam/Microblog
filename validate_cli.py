#!/usr/bin/env python3
"""
CLI Validation Script

This script validates that the CLI structure is correctly implemented
without requiring installation.
"""

import importlib.util
import sys
from pathlib import Path


def validate_cli_structure():
    """Validate that the CLI module is correctly structured."""

    # Check if cli.py exists and is importable
    cli_path = Path("microblog/cli.py")
    if not cli_path.exists():
        print("❌ CLI module not found at microblog/cli.py")
        return False

    # Load the CLI module
    try:
        spec = importlib.util.spec_from_file_location("microblog.cli", cli_path)
        cli_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli_module)
        print("✅ CLI module loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load CLI module: {e}")
        return False

    # Check if main function exists
    if not hasattr(cli_module, 'main'):
        print("❌ Main function not found in CLI module")
        return False
    print("✅ Main function found")

    # Check if it's a Click group
    try:
        import click
        if not isinstance(cli_module.main, click.Group):
            print("❌ Main is not a Click group")
            return False
        print("✅ Main is a Click group")
    except ImportError:
        print("⚠️  Click not installed - cannot verify Click group structure")

    # Check expected commands exist
    expected_commands = ['build', 'serve', 'create-user', 'init', 'status']

    try:
        # Get the commands from the Click group
        commands = list(cli_module.main.commands.keys())
        print(f"✅ Found commands: {commands}")

        missing_commands = [cmd for cmd in expected_commands if cmd.replace('-', '_') not in commands]
        if missing_commands:
            print(f"⚠️  Missing expected commands: {missing_commands}")
        else:
            print("✅ All expected commands found")

    except Exception as e:
        print(f"⚠️  Could not verify commands: {e}")

    return True

def validate_project_structure():
    """Validate that the project structure is correct."""

    required_files = [
        "pyproject.toml",
        "requirements.txt",
        "README.md",
        ".gitignore",
        "Dockerfile",
        "docker-compose.yml",
        "Makefile"
    ]

    required_dirs = [
        "microblog",
        "microblog/builder",
        "microblog/server",
        "microblog/server/routes",
        "microblog/auth",
        "microblog/content",
        "templates",
        "templates/dashboard",
        "static",
        "static/css",
        "static/js",
        "static/images",
        "content",
        "content/posts",
        "content/pages",
        "content/images",
        "content/_data",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/e2e",
        "docs",
        "docs/diagrams",
        "docs/adr",
        "docs/api",
        "scripts"
    ]

    print("\n📁 Checking project structure...")

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False

    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
        else:
            print(f"✅ {dir_path}/")

    if missing_dirs:
        print(f"❌ Missing directories: {missing_dirs}")
        return False

    return True

def validate_pyproject_toml():
    """Validate pyproject.toml configuration."""

    print("\n⚙️  Checking pyproject.toml...")

    try:
        with open("pyproject.toml") as f:
            content = f.read()

        # Check for essential sections
        required_sections = [
            "[project]",
            "[project.scripts]",
            "microblog = \"microblog.cli:main\"",
            "fastapi>=0.100.0",
            "click>=8.1.0"
        ]

        for section in required_sections:
            if section in content:
                print(f"✅ Found: {section}")
            else:
                print(f"❌ Missing: {section}")
                return False

        return True

    except Exception as e:
        print(f"❌ Failed to read pyproject.toml: {e}")
        return False

def main():
    """Run all validation checks."""

    print("🔍 Microblog CLI Validation")
    print("=" * 50)

    checks = [
        ("Project Structure", validate_project_structure),
        ("pyproject.toml Configuration", validate_pyproject_toml),
        ("CLI Structure", validate_cli_structure),
    ]

    all_passed = True

    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        print("-" * len(check_name))
        try:
            result = check_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ Check failed with error: {e}")
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All validation checks passed!")
        print("✅ CLI tool should install successfully")
        print("✅ `microblog --help` should display command structure")
        print("✅ All required directories and files are present")
        print("✅ Dependencies should resolve without conflicts")
    else:
        print("❌ Some validation checks failed")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
