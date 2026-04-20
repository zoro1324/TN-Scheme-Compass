#!/usr/bin/env python3
"""
Setup script for TN Welfare Schemes Chatbot.
Installs dependencies, downloads models, and validates setup.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a shell command and report status."""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=False)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with error code {e.returncode}")
        return False


def install_dependencies():
    """Install Python dependencies."""
    print("\n" + "="*60)
    print("🔧 TN Welfare Schemes Chatbot - Setup")
    print("="*60)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8+ is required")
        sys.exit(1)
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install main requirements
    if not run_command(
        f"{sys.executable} -m pip install --upgrade pip setuptools wheel",
        "Upgrading pip, setuptools, wheel"
    ):
        print("⚠️  Warning: pip upgrade may have failed, continuing anyway...")
    
    # Install chatbot dependencies
    chatbot_requirements = Path("chatbot/requirements_chatbot.txt")
    if not chatbot_requirements.exists():
        print(f"✗ {chatbot_requirements} not found")
        return False
    
    if not run_command(
        f"{sys.executable} -m pip install -r {chatbot_requirements}",
        "Installing chatbot dependencies"
    ):
        print("✗ Failed to install chatbot dependencies")
        return False
    
    return True


def download_whisper_model(model_size="base"):
    """Download Whisper model."""
    print(f"\n{'='*60}")
    print(f"🎤 Downloading Whisper model ({model_size})")
    print('='*60)
    print(f"This will download ~{{'tiny': 39, 'base': 140, 'small': 400, 'medium': 1400, 'large': 2900}.get(model_size, 140)}MB\n")
    
    try:
        import whisper
        print(f"Loading Whisper model: {model_size}...")
        whisper.load_model(model_size)
        print(f"✓ Whisper model ({model_size}) downloaded successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to download Whisper model: {e}")
        print("⚠️  You can try again later or run: python -c \"import whisper; whisper.load_model('base')\"")
        return False


def setup_env_file():
    """Create .env file if it doesn't exist."""
    env_file = Path(".env")
    
    if env_file.exists():
        print("\n✓ .env file already exists")
        return True
    
    print(f"\n{'='*60}")
    print("⚙️  Setting up .env configuration")
    print('='*60)
    
    groq_key = input("\nEnter your GroqAPI key (or press Enter to skip): ").strip()
    
    env_content = f"""# TN Welfare Schemes Chatbot Configuration

# Required: GroqAPI key for LLM processing
# Get your key from: https://console.groq.com/
GROQ_API_KEY={groq_key or "YOUR_GROQ_API_KEY_HERE"}

# Chatbot Settings
GROQ_MODEL=mixtral-8x7b-32768
WHISPER_MODEL_SIZE=base

# Speech Settings
SPEECH_DURATION_SECONDS=10
ENABLE_SPEECH_MODE=true
ENABLE_TTS=true
SPEECH_RATE=150
SPEECH_VOLUME=0.9

# Optional: Data Pipeline Settings (for data collection)
TAVILY_API_KEY=
LLM_PROVIDER=groq
OLLAMA_MODEL=llama3:8b
OLLAMA_BASE_URL=http://localhost:11434
REQUEST_TIMEOUT_SECONDS=30
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✓ .env file created successfully")
        
        if not groq_key:
            print("\n⚠️  You need to add your GroqAPI key to .env before using the chatbot")
            print("   Get a free key at: https://console.groq.com/")
        
        return True
    except Exception as e:
        print(f"✗ Failed to create .env file: {e}")
        return False


def verify_excel_file():
    """Check if Excel file exists."""
    excel_file = Path("tn_welfare_schemes.xlsx")
    
    print(f"\n{'='*60}")
    print("📊 Verifying data file")
    print('='*60)
    
    if excel_file.exists():
        print(f"✓ Excel file found: {excel_file}")
        try:
            import pandas as pd
            df = pd.read_excel(excel_file)
            print(f"✓ Excel file readable: {len(df)} schemes loaded")
            print(f"✓ Columns: {len(df.columns)}")
            return True
        except Exception as e:
            print(f"✗ Error reading Excel file: {e}")
            return False
    else:
        print(f"✗ Excel file not found: {excel_file}")
        print("   Ensure tn_welfare_schemes.xlsx is in the project root")
        return False


def test_audio_device():
    """Test if audio device is available."""
    print(f"\n{'='*60}")
    print("🎤 Testing audio device")
    print('='*60)
    
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        device_count = p.get_device_count()
        p.terminate()
        
        if device_count > 0:
            print(f"✓ Audio device found ({device_count} device(s))")
            return True
        else:
            print("⚠️  No audio devices detected")
            print("   Speech mode will fall back to text input")
            return False
    except Exception as e:
        print(f"⚠️  Could not initialize audio: {e}")
        print("   Speech mode will fall back to text input")
        return False


def test_imports():
    """Test if all modules can be imported."""
    print(f"\n{'='*60}")
    print("✓ Testing module imports")
    print('='*60)
    
    modules = [
        ("whisper", "OpenAI Whisper (for speech-to-text)"),
        ("pyttsx3", "pyttsx3 (for text-to-speech)"),
        ("chromadb", "ChromaDB (for vector storage)"),
        ("pandas", "Pandas (for data handling)"),
        ("groq", "Groq (for LLM)"),
        ("langdetect", "Langdetect (for language detection)"),
    ]
    
    all_ok = True
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"✓ {description}")
        except ImportError:
            print(f"✗ {description} - NOT INSTALLED")
            all_ok = False
    
    return all_ok


def main():
    """Run full setup."""
    print("\n🚀 TN Welfare Schemes Chatbot - Setup Wizard\n")
    
    steps = [
        ("Install Dependencies", install_dependencies),
        ("Download Whisper Model", lambda: download_whisper_model("base")),
        ("Setup Configuration", setup_env_file),
        ("Verify Excel Data", verify_excel_file),
        ("Test Audio Device", test_audio_device),
        ("Test Module Imports", test_imports),
    ]
    
    results = []
    
    for step_name, step_func in steps:
        try:
            success = step_func()
            results.append((step_name, success))
        except Exception as e:
            print(f"\n✗ Error during {step_name}: {e}")
            results.append((step_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📋 Setup Summary")
    print('='*60)
    
    for step_name, success in results:
        status = "✓" if success else "✗"
        print(f"{status} {step_name}")
    
    all_success = all(success for _, success in results)
    
    if all_success:
        print(f"\n{'='*60}")
        print("✅ Setup completed successfully!")
        print('='*60)
        print("\n🚀 You can now run the chatbot:")
        print("   python run_chatbot.py")
        print("\n📖 For more help, see CHATBOT_README.md")
    else:
        print(f"\n{'='*60}")
        print("⚠️  Setup completed with some warnings")
        print('='*60)
        print("\n⚠️  Some optional components may not work:")
        print("   • Text mode will still work")
        print("   • Speech mode may be unavailable")
        print("\n📖 See CHATBOT_README.md for troubleshooting")
    
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)
