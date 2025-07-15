#!/usr/bin/env python3
"""
Setup script for the Crypto Market Sentiment Analyzer.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True


def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")
    
    directories = [
        "reports",
        "logs", 
        "data",
        "tests"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"  ✅ Created {directory}/")
    
    return True


def run_initial_test():
    """Run initial test to verify setup."""
    print("🧪 Running initial test...")
    
    try:
        # Test configuration loading
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from src.utils.config import get_config
        
        config = get_config()
        print("  ✅ Configuration loaded successfully")
        
        # Test sentiment analyzers
        from src.sentiment_analyzers import TextBlobAnalyzer, VADERAnalyzer
        
        textblob = TextBlobAnalyzer()
        vader = VADERAnalyzer()
        
        if textblob.is_configured():
            print("  ✅ TextBlob analyzer configured")
        else:
            print("  ❌ TextBlob analyzer not configured")
        
        if vader.is_configured():
            print("  ✅ VADER analyzer configured")
        else:
            print("  ❌ VADER analyzer not configured")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Initial test failed: {e}")
        return False


def show_usage_examples():
    """Show usage examples."""
    print("\n📚 Usage Examples:")
    print("=" * 50)
    
    print("\n1. Run the main analysis:")
    print("   python src/main.py")
    
    print("\n2. Run with debug mode:")
    print("   python src/main.py --debug")
    
    print("\n3. Run quick test:")
    print("   python src/main.py --test")
    
    print("\n4. Check system status:")
    print("   python src/main.py --status")
    
    print("\n5. Run the example script:")
    print("   python example.py")
    
    print("\n6. Run tests:")
    print("   python run_tests.py")
    
    print("\n7. Quick demo:")
    print("   python example.py --quick")


def main():
    """Main setup function."""
    print("🚀 Crypto Market Sentiment Analyzer - Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Create directories
    if not create_directories():
        return False
    
    # Run initial test
    if not run_initial_test():
        print("⚠️ Initial test failed, but setup may still work")
    
    # Show usage examples
    show_usage_examples()
    
    print("\n🎉 Setup completed!")
    print("📖 Check the README.md file for detailed documentation")
    print("🔧 Edit config.yaml to customize settings")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 