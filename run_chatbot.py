#!/usr/bin/env python3
"""
Entry point for TN Welfare Schemes Chatbot.
Run this script to start the chatbot in text or speech mode.
"""

import sys
import os

# Add parent directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    from chatbot.cli import main
    main()
