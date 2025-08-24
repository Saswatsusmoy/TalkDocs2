#!/usr/bin/env python3
"""
Setup script for the LLM Benchmarking Suite.
"""

import os
import sys
import subprocess
from pathlib import Path


def install_requirements():
    """Install required packages."""
    print("Installing required packages...")
    
    # Install from requirements.txt
    requirements_file = Path(__file__).parent / "requirements.txt"
    if requirements_file.exists():
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
    else:
        print("Warning: requirements.txt not found")
    
    # Install additional packages that might be missing
    additional_packages = [
        "nltk",
        "scikit-learn",
        "psutil"
    ]
    
    for package in additional_packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError:
            print(f"Warning: Failed to install {package}")


def setup_directories():
    """Create necessary directories."""
    print("Creating directories...")
    
    base_dir = Path(__file__).parent
    directories = [
        "results",
        "logs",
        "datasets",
        "models_cache"
    ]
    
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(exist_ok=True)
        print(f"Created: {dir_path}")


def setup_database():
    """Initialize the database."""
    print("Setting up database...")
    
    try:
        from database import db_manager
        print("Database initialized successfully")
    except Exception as e:
        print(f"Warning: Database setup failed: {e}")


def download_nltk_data():
    """Download required NLTK data."""
    print("Downloading NLTK data...")
    
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        print("NLTK data downloaded successfully")
    except Exception as e:
        print(f"Warning: NLTK data download failed: {e}")


def create_config_file():
    """Create a sample configuration file."""
    print("Creating sample configuration...")
    
    config_content = """# LLM Benchmarking Suite Configuration
# Copy this to .env and modify as needed

# Database settings
DATABASE_URL=sqlite:///benchmark_results.db

# HuggingFace settings
HF_TOKEN=your_huggingface_token_here
HF_CACHE_DIR=~/.cache/huggingface

# Model settings
DEVICE=auto
MAX_LENGTH=512
BATCH_SIZE=1

# Benchmark settings
NUM_SAMPLES=100
TIMEOUT_SECONDS=300
MAX_RETRIES=3

# Metrics settings
ENABLE_ROUGE=true
ENABLE_BLEU=true
ENABLE_BLEURT=true
ENABLE_LATENCY=true

# Web interface settings
WEB_PORT=8501
WEB_HOST=localhost

# Logging settings
LOG_LEVEL=INFO
LOG_FILE=logs/benchmark.log

# Output settings
RESULTS_DIR=./results
SAVE_PREDICTIONS=true
"""
    
    config_file = Path(__file__).parent / ".env.example"
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"Sample configuration created: {config_file}")


def run_tests():
    """Run basic tests to verify installation."""
    print("Running basic tests...")
    
    try:
        # Test imports
        from config import config
        from models.model_loader import ModelLoader
        from utils.metrics import MetricsCalculator
        from utils.evaluator import BenchmarkEvaluator
        
        print("✅ All imports successful")
        
        # Test model loader
        loader = ModelLoader()
        print("✅ Model loader initialized")
        
        # Test metrics calculator
        calculator = MetricsCalculator()
        print("✅ Metrics calculator initialized")
        
        # Test evaluator
        evaluator = BenchmarkEvaluator()
        print("✅ Evaluator initialized")
        
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True


def main():
    """Main setup function."""
    print("🤖 LLM Benchmarking Suite Setup")
    print("=" * 40)
    
    # Install requirements
    install_requirements()
    
    # Setup directories
    setup_directories()
    
    # Setup database
    setup_database()
    
    # Download NLTK data
    download_nltk_data()
    
    # Create config file
    create_config_file()
    
    # Run tests
    if run_tests():
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and configure your settings")
        print("2. Set your HuggingFace token in .env if needed")
        print("3. Run the web interface: streamlit run web_interface/app.py")
        print("4. Or use the CLI: python main.py --help")
    else:
        print("\n❌ Setup completed with errors. Please check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
