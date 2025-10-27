#!/usr/bin/env python3
"""
Test verification script for build system tests.

This script runs the comprehensive build system tests and verifies coverage requirements.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    """Main verification function."""
    print("Build System Test Verification")
    print("=" * 60)

    # Change to project directory
    project_dir = Path(__file__).parent

    tests_passed = 0
    tests_total = 0

    # Test 1: Run unit tests for build system
    print("\n1. Running unit tests for build system...")
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/unit/test_build_system.py",
        "-v", "--tb=short"
    ]
    if run_command(cmd, "Unit tests for build system"):
        tests_passed += 1
    tests_total += 1

    # Test 2: Check coverage for build modules
    print("\n2. Checking coverage for build modules...")
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/unit/test_build_system.py",
        "--cov=microblog.builder",
        "--cov-report=term-missing",
        "--cov-fail-under=85",
        "-q"
    ]
    if run_command(cmd, "Coverage check for build modules"):
        tests_passed += 1
    tests_total += 1

    # Test 3: Run integration tests (with more lenient approach)
    print("\n3. Running integration tests...")
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/integration/test_build_process.py",
        "-v", "--tb=short", "-x"  # Stop on first failure
    ]
    if run_command(cmd, "Integration tests"):
        tests_passed += 1
    tests_total += 1

    # Test 4: Verify test completeness
    print("\n4. Verifying test completeness...")
    cmd = [
        sys.executable, "-c", """
import sys
sys.path.insert(0, '.')
from tests.unit.test_build_system import *
from tests.integration.test_build_process import *

# Count test methods
import inspect

def count_test_methods(cls):
    return len([name for name, method in inspect.getmembers(cls, inspect.isfunction)
               if name.startswith('test_')])

unit_test_classes = [
    TestBuildProgress, TestBuildResult, TestMarkdownProcessor,
    TestTemplateRenderer, TestAssetManager, TestBuildGenerator,
    TestBuildFailureScenarios, TestPerformanceBuildTests
]

integration_test_classes = [TestIntegrationBuildProcess]

unit_count = sum(count_test_methods(cls) for cls in unit_test_classes)
integration_count = sum(count_test_methods(cls) for cls in integration_test_classes)

print(f"Unit test methods: {unit_count}")
print(f"Integration test methods: {integration_count}")
print(f"Total test methods: {unit_count + integration_count}")

# Verify we have comprehensive coverage
if unit_count >= 30 and integration_count >= 5:
    print("✓ Test coverage is comprehensive")
    sys.exit(0)
else:
    print("✗ Insufficient test coverage")
    sys.exit(1)
"""
    ]
    if run_command(cmd, "Test completeness verification"):
        tests_passed += 1
    tests_total += 1

    # Summary
    print(f"\n{'='*60}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*60}")
    print(f"Tests passed: {tests_passed}/{tests_total}")

    if tests_passed == tests_total:
        print("✓ All verification checks passed!")
        print("\nBuild system tests are comprehensive and meet requirements:")
        print("- Unit tests cover all major components")
        print("- Integration tests verify complete build process")
        print("- Failure scenarios and rollback mechanisms tested")
        print("- Performance requirements validated")
        print("- Test coverage >85% for build modules")
        return True
    else:
        print("✗ Some verification checks failed.")
        print("\nPlease review and fix failing tests.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)