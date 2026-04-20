"""
Main CLI orchestrator for the RAG-powered welfare schemes chatbot.
Handles both text and speech-based interaction modes.
"""

import logging
import sys
import pandas as pd
from pathlib import Path
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chatbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WelfareSchemesChatbot:
    """Main chatbot interface for TN welfare schemes."""
    
    def __init__(self, excel_path: str):
        """
        Initialize chatbot.
        
        Args:
            excel_path: Path to Excel file with schemes data
        """
        self.excel_path = excel_path
        self.schemes_df = None
        self.initialized = False
        
        # Import modules
        try:
            from chatbot.rag_retriever import RAGRetriever
            from chatbot.translator import Translator
            from chatbot.whisper_stt import WhisperSTT
            from chatbot.offline_tts import OfflineTTS
            from chatbot.eligibility_matcher import EligibilityMatcher
            from chatbot.llm_responder import LLMResponder
            
            self.RAGRetriever = RAGRetriever
            self.Translator = Translator
            self.WhisperSTT = WhisperSTT
            self.OfflineTTS = OfflineTTS
            self.EligibilityMatcher = EligibilityMatcher
            self.LLMResponder = LLMResponder
            
            self._load_data()
            self._initialize_components()
            
        except ImportError as e:
            logger.error(f"Failed to import chatbot modules: {e}")
            sys.exit(1)
    
    def _load_data(self) -> bool:
        """Load schemes data from Excel."""
        try:
            logger.info(f"Loading schemes from: {self.excel_path}")
            
            if not Path(self.excel_path).exists():
                logger.error(f"Excel file not found: {self.excel_path}")
                return False
            
            self.schemes_df = pd.read_excel(self.excel_path)
            logger.info(f"Loaded {len(self.schemes_df)} schemes")
            logger.debug(f"Columns: {list(self.schemes_df.columns)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return False
    
    def _initialize_components(self) -> bool:
        """Initialize all chatbot components."""
        try:
            logger.info("Initializing chatbot components...")
            
            # Initialize translator
            self.translator = self.Translator()
            
            # Initialize RAG retriever
            self.rag_retriever = self.RAGRetriever(self.schemes_df)
            if not self.rag_retriever.build_index():
                logger.warning("Failed to build RAG index")
            
            # Initialize eligibility matcher
            self.eligibility_matcher = self.EligibilityMatcher(self.schemes_df)
            
            # Initialize LLM responder
            self.llm_responder = self.LLMResponder()
            
            # Initialize speech components (optional - may fail if no audio device)
            try:
                self.stt = self.WhisperSTT()
                self.tts = self.OfflineTTS()
                logger.info("Speech components initialized")
            except Exception as e:
                logger.warning(f"Speech components not available: {e}")
                self.stt = None
                self.tts = None
            
            self.initialized = True
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            return False
    
    def show_menu(self) -> str:
        """Display main menu and get user choice."""
        print("\n" + "="*60)
        print("🔍 TN Welfare Schemes Eligibility Assistant")
        print("="*60)
        print("\nChoose interaction mode:")
        print("  1) 📝 Text-based (type your responses)")
        print("  2) 🎤 Speech-based (speak your responses)")
        print("  3) ❌ Exit")
        print("\n" + "-"*60)
        
        choice = input("Enter your choice (1/2/3): ").strip()
        return choice
    
    def text_mode(self):
        """Interactive text-based conversation mode."""
        print("\n📝 Text Mode - Scheme Eligibility Assistant")
        print("-"*60)
        print("I'll ask you some questions to find suitable schemes.\n")
        
        self.eligibility_matcher.reset()
        
        while True:
            question = self.eligibility_matcher.get_next_question()
            
            if question is None:
                # All questions answered
                print("\n" + "="*60)
                print("🔍 Finding matching schemes...")
                print("="*60)
                
                matches = self.eligibility_matcher.find_matching_schemes()
                self._display_matches(matches)
                break
            
            print(f"\n❓ {question['question']}")
            response = input("Your answer: ").strip()
            
            if not response:
                print("⚠️  Please provide an answer")
                self.eligibility_matcher.asked_questions.remove(question['id'])
                continue
            
            # Detect language and translate if needed
            input_lang = self.translator.detect_language(response)
            if input_lang == 'ta':
                print(f"🔤 Detected Tamil input, translating to English for processing...")
                english_response = self.translator.translate(response, 'en')
                self.eligibility_matcher.record_response(question['id'], english_response)
                self.last_input_language = 'ta'
            else:
                self.eligibility_matcher.record_response(question['id'], response)
                self.last_input_language = 'en'
            
            print("✓ Response recorded")
    
    def speech_mode(self):
        """Interactive speech-based conversation mode."""
        if self.stt is None or self.tts is None:
            print("\n❌ Speech components not available")
            print("Falling back to text mode...\n")
            self.text_mode()
            return
        
        print("\n🎤 Speech Mode - Scheme Eligibility Assistant")
        print("-"*60)
        print("I'll ask you questions. Speak your answers (in Tamil or English).\n")
        
        self.eligibility_matcher.reset()
        self.last_input_language = 'en'
        
        while True:
            question = self.eligibility_matcher.get_next_question()
            
            if question is None:
                # All questions answered
                print("\n" + "="*60)
                print("🔍 Finding matching schemes...")
                print("="*60)
                
                matches = self.eligibility_matcher.find_matching_schemes()
                self._display_matches(matches)
                break
            
            print(f"\n❓ {question['question']}")
            
            # Record speech
            text, detected_lang = self.stt.transcribe_with_recording(duration=10)
            
            if not text:
                print("❌ Could not record audio. Please try again or switch to text mode.")
                self.eligibility_matcher.asked_questions.remove(question['id'])
                continue
            
            print(f"🔤 You said: {text}")
            
            # Translate if Tamil
            if detected_lang == 'ta':
                print("📢 Detected Tamil speech, translating to English for processing...")
                english_text = self.translator.translate(text, 'en')
                self.eligibility_matcher.record_response(question['id'], english_text)
                self.last_input_language = 'ta'
            else:
                self.eligibility_matcher.record_response(question['id'], text)
                self.last_input_language = 'en'
            
            print("✓ Response recorded")
    
    def _display_matches(self, matches: list):
        """Display matching schemes with explanations."""
        if not matches:
            print("\n❌ No matching schemes found based on your criteria.")
            print("This might mean the schemes available don't match your profile.")
            print("\nPlease contact your local welfare office for more information.")
            return
        
        print(f"\n✅ Found {len(matches)} matching scheme(s):\n")
        
        for i, scheme in enumerate(matches, 1):
            self._display_scheme_details(i, scheme)
            print("\n" + "-"*60)
        
        print("\n💡 Tip: You can visit the official portals above to apply.")
    
    def _display_scheme_details(self, index: int, scheme: dict):
        """Display detailed information for a scheme."""
        print(f"\n{index}. {scheme.get('scheme_name', 'Unknown')}")
        print(f"   Category: {scheme.get('category', 'N/A')}")
        print(f"   Type: {scheme.get('benefit_type', 'N/A')}")
        print(f"   Benefit: ₹{scheme.get('benefit_amount', 'N/A')}")
        print(f"   Match Score: {scheme.get('score', 0):.1%}")
        
        print(f"\n   Why this matches you:")
        criteria = scheme.get('matching_criteria', [])
        for criterion in criteria:
            print(f"   {criterion}")
        
        print(f"\n   Application Mode: {scheme.get('application_mode', 'Contact office')}")
        print(f"   Portal: {scheme.get('official_portal', 'Contact your local office')}")
        
        docs = scheme.get('documents_required')
        if docs:
            print(f"   Documents Needed: {docs}")
    
    def run(self):
        """Main run loop."""
        if not self.initialized:
            logger.error("Chatbot not initialized")
            return
        
        logger.info("Chatbot started")
        
        try:
            while True:
                choice = self.show_menu()
                
                if choice == '1':
                    self.text_mode()
                elif choice == '2':
                    self.speech_mode()
                elif choice == '3':
                    print("\n👋 Thank you for using the Welfare Schemes Assistant!")
                    print("For more information, visit your nearest welfare office.\n")
                    break
                else:
                    print("❌ Invalid choice. Please enter 1, 2, or 3.")
                
                # Ask if user wants to continue
                if choice in ['1', '2']:
                    again = input("\n🔄 Do you want to find more schemes? (yes/no): ").strip().lower()
                    if again not in ['yes', 'y']:
                        print("\n👋 Thank you for using the Welfare Schemes Assistant!\n")
                        break
        
        except KeyboardInterrupt:
            print("\n\n👋 Chatbot interrupted by user")
            logger.info("Chatbot interrupted by user")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print(f"\n❌ An error occurred: {e}")


def main():
    """Main entry point."""
    # Determine Excel file path
    excel_path = "tn_welfare_schemes.xlsx"
    
    # Check if path exists
    if not Path(excel_path).exists():
        logger.error(f"Excel file not found: {excel_path}")
        print(f"❌ Excel file not found at: {excel_path}")
        print("Please ensure tn_welfare_schemes.xlsx is in the current directory.")
        sys.exit(1)
    
    # Initialize and run chatbot
    try:
        chatbot = WelfareSchemesChatbot(excel_path)
        chatbot.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
