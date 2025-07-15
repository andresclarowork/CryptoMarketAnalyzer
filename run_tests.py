#!/usr/bin/env python3
"""
Test runner for the Crypto Market Sentiment Analyzer.
"""

import sys
import subprocess
from pathlib import Path


def run_tests():
    """Run the test suite."""
    print("🧪 Running Crypto Market Sentiment Analyzer tests...")
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("❌ pytest not found. Please install it with: pip install pytest")
        return False
    
    # Run tests
    test_dir = Path("tests")
    if not test_dir.exists():
        print("❌ Tests directory not found")
        return False
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All tests passed!")
            return True
        else:
            print("❌ Some tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def run_quick_test():
    """Run a quick functionality test."""
    print("🔍 Running quick functionality test...")
    
    try:
        from src.main import CryptoMarketSentimentAnalyzer
        
        analyzer = CryptoMarketSentimentAnalyzer(debug_mode=True)
        success = analyzer.run_quick_test()
        
        if success:
            print("✅ Quick test passed!")
            return True
        else:
            print("❌ Quick test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error in quick test: {e}")
        return False


def main():
    """Main test runner."""
    print("🚀 Crypto Market Sentiment Analyzer - Test Suite")
    print("=" * 50)
    
    # Run unit tests
    print("\n1. Running unit tests...")
    unit_tests_passed = run_tests()
    
    # Run quick functionality test
    print("\n2. Running quick functionality test...")
    quick_test_passed = run_quick_test()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Unit Tests: {'✅ PASSED' if unit_tests_passed else '❌ FAILED'}")
    print(f"   Quick Test: {'✅ PASSED' if quick_test_passed else '❌ FAILED'}")
    
    if unit_tests_passed and quick_test_passed:
        print("\n🎉 All tests passed! The system is ready to use.")
        return True
    else:
        print("\n⚠️ Some tests failed. Please check the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 