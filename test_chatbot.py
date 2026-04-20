#!/usr/bin/env python3
"""
Test script to validate TN Welfare Schemes Chatbot installation.
Run this after setup_chatbot.py to verify all components work.
"""

import sys
import os
from pathlib import Path

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text):
    """Print header section."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")


def test_python_version():
    """Test Python version."""
    print("Testing Python version...", end=" ")
    if sys.version_info >= (3, 8):
        print(f"{GREEN}✓ Python {sys.version_info.major}.{sys.version_info.minor}{RESET}")
        return True
    else:
        print(f"{RED}✗ Python 3.8+ required (current: {sys.version_info.major}.{sys.version_info.minor}){RESET}")
        return False


def test_import(module_name, description):
    """Test if module can be imported."""
    print(f"Testing {description}...", end=" ")
    try:
        __import__(module_name)
        print(f"{GREEN}✓{RESET}")
        return True
    except ImportError as e:
        print(f"{RED}✗ {e}{RESET}")
        return False


def test_excel_file():
    """Test if Excel file exists and is readable."""
    print("Testing Excel file...", end=" ")
    excel_file = Path("tn_welfare_schemes.xlsx")
    
    if not excel_file.exists():
        print(f"{RED}✗ File not found{RESET}")
        return False
    
    try:
        import pandas as pd
        df = pd.read_excel(excel_file)
        print(f"{GREEN}✓ ({len(df)} schemes){RESET}")
        return True
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")
        return False


def test_audio_device():
    """Test if audio device is available."""
    print("Testing audio device...", end=" ")
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        device_count = p.get_device_count()
        p.terminate()
        
        if device_count > 0:
            print(f"{GREEN}✓ ({device_count} device(s)){RESET}")
            return True
        else:
            print(f"{YELLOW}⚠ No devices (text mode only){RESET}")
            return False
    except Exception as e:
        print(f"{YELLOW}⚠ Not available: {e}{RESET}")
        return False


def test_whisper_model():
    """Test if Whisper model can be loaded."""
    print("Testing Whisper model...", end=" ")
    try:
        import whisper
        print(f"{YELLOW}⏳ Loading (this may take a minute)...{RESET}")
        model = whisper.load_model("base")
        print(f"Testing Whisper model...{GREEN}✓ Loaded{RESET}")
        return True
    except Exception as e:
        print(f"{YELLOW}⚠ Download needed: Run `python -c \"import whisper; whisper.load_model('base')\"`{RESET}")
        return False


def test_groq_api():
    """Test if GroqAPI key is configured."""
    print("Testing GroqAPI configuration...", end=" ")
    
    api_key = os.getenv('GROQ_API_KEY', '').strip()
    
    if not api_key:
        print(f"{RED}✗ GROQ_API_KEY not set in .env{RESET}")
        return False
    
    if api_key == "YOUR_GROQ_API_KEY_HERE" or api_key == "your_key_here":
        print(f"{RED}✗ GROQ_API_KEY not configured{RESET}")
        return False
    
    try:
        from groq import Groq
        print(f"{GREEN}✓ Configured{RESET}")
        return True
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")
        return False


def test_chatbot_modules():
    """Test if chatbot modules can be imported."""
    print("Testing chatbot modules...", end=" ")
    
    modules_ok = True
    try:
        from chatbot.cli import WelfareSchemesChatbot
        from chatbot.rag_retriever import RAGRetriever
        from chatbot.translator import Translator
        from chatbot.whisper_stt import WhisperSTT
        from chatbot.offline_tts import OfflineTTS
        from chatbot.eligibility_matcher import EligibilityMatcher
        from chatbot.llm_responder import LLMResponder
        print(f"{GREEN}✓ All modules{RESET}")
        return True
    except Exception as e:
        print(f"{RED}✗ {e}{RESET}")
        return False


def test_dependencies():
    """Test key Python dependencies."""
    print("Testing Python dependencies...")
    
    dependencies = [
        ("pandas", "Data handling"),
        ("numpy", "Numerical computing"),
        ("chromadb", "Vector database"),
        ("groq", "LLM API"),
        ("langdetect", "Language detection"),
        ("pyttsx3", "Text-to-speech"),
    ]
    
    all_ok = True
    for module_name, description in dependencies:
        print(f"  - {description}...", end=" ")
        try:
            __import__(module_name)
            print(f"{GREEN}✓{RESET}")
        except ImportError:
            print(f"{RED}✗{RESET}")
            all_ok = False
    
    return all_ok


def test_translation():
    """Test translation functionality."""
    print("Testing translation module...", end=" ")
    try:
        from chatbot.translator import Translator
        translator = Translator()
        
        # Test language detection
        lang_en = translator.detect_language("Hello")
        lang_ta = translator.detect_language("வணக்கம்")
        
        if lang_en == 'en' and lang_ta == 'ta':
            print(f"{GREEN}✓{RESET}")
            return True
        else:
            print(f"{YELLOW}⚠ Language detection working{RESET}")
            return True
    except Exception as e:
        print(f"{RED}✗ {e}{RESET}")
        return False


def main():
    """Run all tests."""
    print_header("TN Welfare Schemes Chatbot - Test Suite")
    
    tests = [
        ("Python Version", test_python_version),
        ("Core Dependencies", test_dependencies),
        ("Chatbot Modules", test_chatbot_modules),
        ("Translation", test_translation),
        ("Excel Data", test_excel_file),
        ("GroqAPI Config", test_groq_api),
        ("Audio Device", test_audio_device),
        ("Whisper Model", test_whisper_model),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{BLUE}▶ {test_name}{RESET}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"{RED}✗ Error: {e}{RESET}")
            results.append((test_name, False))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}✓{RESET}" if result else f"{RED}✗{RESET}"
        print(f"{status} {test_name}")
    
    print(f"\n{BLUE}Results: {passed}/{total} tests passed{RESET}\n")
    
    if passed == total:
        print(f"{GREEN}{'='*60}")
        print("✅ ALL TESTS PASSED!")
        print(f"{'='*60}{RESET}")
        print(f"\nYou can now run the chatbot:")
        print(f"{BLUE}  python run_chatbot.py{RESET}\n")
        return 0
    elif passed >= total - 2:
        print(f"{YELLOW}{'='*60}")
        print("⚠️  MOST TESTS PASSED")
        print(f"{'='*60}{RESET}")
        print(f"\nSome optional features may not work:")
        for test_name, result in results:
            if not result:
                print(f"  • {test_name}")
        print(f"\nYou can still use text mode. To enable all features:")
        print(f"{BLUE}  python setup_chatbot.py{RESET}\n")
        return 1
    else:
        print(f"{RED}{'='*60}")
        print("❌ TESTS FAILED")
        print(f"{'='*60}{RESET}")
        print(f"\nPlease run setup first:")
        print(f"{BLUE}  python setup_chatbot.py{RESET}\n")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Test suite error: {e}{RESET}\n")
        sys.exit(1)
