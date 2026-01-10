"""
Phase 1 Test Runner - Comprehensive validation suite.

This script runs all Phase 1 prototype validation tests:
1. LMstudio SDK connection tests
2. Adapter implementation tests
3. Integration readiness checks

Usage:
    python -m graphrag_local.tests.run_phase1_tests
"""

import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def print_header(title: str) -> None:
    """Print a formatted header."""
    print("\n")
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()


def run_connection_tests() -> bool:
    """Run LMstudio SDK connection tests."""
    print_header("PHASE 1.1: LMstudio SDK Connection Tests")

    try:
        from graphrag_local.tests.test_connection import run_all_tests
        return run_all_tests()
    except Exception as e:
        print(f"✗ Failed to run connection tests: {e}")
        return False


def run_adapter_tests() -> bool:
    """Run adapter implementation tests."""
    print_header("PHASE 1.2: Adapter Implementation Tests")

    try:
        from graphrag_local.tests.test_adapters import run_all_tests
        return run_all_tests()
    except Exception as e:
        print(f"✗ Failed to run adapter tests: {e}")
        return False


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    print_header("Dependency Check")

    dependencies = {
        "Python": sys.version,
    }

    print("Installed dependencies:")
    for name, version in dependencies.items():
        print(f"  ✓ {name}: {version}")

    # Check optional dependencies
    optional_deps = []

    try:
        import lmstudio
        optional_deps.append(("lmstudio", getattr(lmstudio, "__version__", "unknown")))
    except ImportError:
        print("\n  ! lmstudio SDK not installed (install with: pip install lmstudio)")

    if optional_deps:
        print("\nOptional dependencies:")
        for name, version in optional_deps:
            print(f"  ✓ {name}: {version}")

    return True


def generate_phase1_report(results: dict) -> None:
    """Generate a summary report of Phase 1 testing."""
    print_header("PHASE 1 VALIDATION REPORT")

    total_passed = sum(1 for v in results.values() if v)
    total_tests = len(results)

    print("Test Results:")
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")

    print()
    print(f"Overall: {total_passed}/{total_tests} test suites passed")
    print()

    if total_passed == total_tests:
        print("🎉 Phase 1 Validation Complete!")
        print()
        print("Next Steps:")
        print("  1. Install LMstudio and load a chat model")
        print("  2. Install LMstudio Python SDK: pip install lmstudio")
        print("  3. Run connection tests again to verify SDK integration")
        print("  4. Proceed to Phase 2: Core Adapter Integration")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        print()
        print("Common issues:")
        print("  - Missing dependencies: Install required packages")
        print("  - Import errors: Check Python path and package structure")
        print("  - LMstudio SDK: Install when available from official sources")


def main() -> int:
    """Run all Phase 1 tests and generate report."""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  GraphRAG Local - Phase 1: Prototype Validation".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    results = {}

    # Run dependency check
    results["Dependency Check"] = check_dependencies()

    # Run connection tests
    results["LMstudio SDK Connection"] = run_connection_tests()

    # Run adapter tests
    results["Adapter Implementation"] = run_adapter_tests()

    # Generate report
    generate_phase1_report(results)

    # Return exit code
    all_passed = all(results.values())
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
