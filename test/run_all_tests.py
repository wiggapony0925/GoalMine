#!/usr/bin/env python3
"""
GoalMine Test Suite Runner
Runs all tests with coverage reporting

Usage:
    python test/run_all_tests.py              # Run all tests
    python test/run_all_tests.py --unit       # Only unit tests
    python test/run_all_tests.py --integration  # Only integration tests
   python test/run_all_tests.py --coverage   # With coverage report
"""

import sys
import subprocess
import os

# Set PYTHONPATH
os.environ["PYTHONPATH"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_tests(test_type="all", with_coverage=False):
    """Run test suite"""

    base_cmd = ["python", "-m", "pytest"]

    # Test selection
    if test_type == "unit":
        base_cmd.extend(["-m", "not integration"])
        print("🧪 Running UNIT TESTS only...")
    elif test_type == "integration":
        base_cmd.extend(["-m", "integration"])
        print("🔄 Running INTEGRATION TESTS only...")
    else:
        print("🎯 Running ALL TESTS...")

    # Coverage
    if with_coverage:
        base_cmd.extend(["--cov=.", "--cov-report=term-missing", "--cov-report=html"])

    # Verbosity and formatting
    base_cmd.extend(["-v", "--tb=short", "--color=yes"])

    # Test paths
    test_files = [
        "test/test_complete_coverage.py",
        "test/integration/test_end_to_end.py",
        "test/unit/",
    ]
    base_cmd.extend(test_files)

    print(f"\n📦 Command: {' '.join(base_cmd)}\n")
    print("=" * 80)

    # Run tests
    result = subprocess.run(base_cmd)

    if result.returncode == 0:
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ SOME TESTS FAILED")
        print("=" * 80)
        sys.exit(1)


def print_coverage_summary():
    """Print test coverage summary"""
    print("\n📊 TEST COVERAGE BREAKDOWN:\n")

    components = {
        "Core Infrastructure": [
            "core/initializer/llm.py",
            "core/initializer/whatsapp.py",
            "core/initializer/database.py",
        ],
        "Big Daddy": ["core/generate_bets.py"],
        "Agents": [
            "agents/gatekeeper/gatekeeper.py",
            "agents/logistics/logistics.py",
            "agents/tactics/tactics.py",
            "agents/market/market.py",
            "agents/narrative/narrative.py",
            "agents/quant/quant.py",
        ],
        "Orchestration": ["services/orchestrator.py"],
        "Conversation Flows": [
            "services/buttonConversationalFlow/button_conversation.py",
            "services/conversationalFlow/conversation.py",
        ],
        "God View System": ["data/scripts/godview_builder.py"],
    }

    for category, files in components.items():
        print(f"  {category}:")
        for file in files:
            print(f"    - {file}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run GoalMine test suite")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument(
        "--integration", action="store_true", help="Run only integration tests"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )

    args = parser.parse_args()

    print_coverage_summary()

    test_type = "all"
    if args.unit:
        test_type = "unit"
    elif args.integration:
        test_type = "integration"

    run_tests(test_type, args.coverage)
