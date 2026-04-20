"""
LLM Responder module using GroqAPI.
Handles scheme-matching queries and eligibility assessment.
"""

import logging
import os
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class LLMResponder:
    """LLM-powered responder using GroqAPI."""
    
    def __init__(self, model: str = "mixtral-8x7b-32768"):
        """
        Initialize LLM responder.
        
        Args:
            model: Groq model to use
        """
        self.model = model
        self.client = None
        self.api_key = os.getenv('GROQ_API_KEY')
        self.initialized = False
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found in environment")
            logger.info("Set GROQ_API_KEY in .env or environment variables")
        
        try:
            from groq import Groq
            self.groq_client = Groq
            self._initialize()
        except ImportError:
            logger.error("groq library not installed. Install with: pip install groq")
            self.groq_client = None
    
    def _initialize(self):
        """Initialize Groq client."""
        try:
            if not self.api_key:
                logger.error("Cannot initialize Groq client without API key")
                return False
            
            logger.info(f"Initializing Groq client with model: {self.model}")
            self.client = self.groq_client(api_key=self.api_key)
            self.initialized = True
            logger.info("Groq client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            return False
    
    def answer_eligibility_question(self, user_criteria: str, 
                                   question_id: str) -> str:
        """
        Get LLM response for eligibility question.
        
        Args:
            user_criteria: User's input/criteria
            question_id: ID of the question being answered
            
        Returns:
            LLM response or empty string if failed
        """
        if not self.initialized or self.client is None:
            logger.warning("LLM not initialized, returning empty response")
            return ""
        
        try:
            prompt = f"""Based on the following user input, extract the relevant information clearly:

User input: {user_criteria}
Question being answered: {question_id}

Please:
1. Extract the relevant value from the user's input
2. Be concise and clear
3. If the input is unclear, ask for clarification

Keep your response to 1-2 sentences."""
            
            logger.debug(f"Sending query to Groq (question: {question_id})")
            
            message = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                max_tokens=150,
                temperature=0.3
            )
            
            response = message.choices[0].message.content.strip()
            logger.debug(f"LLM response: {response}")
            return response
            
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            return ""
    
    def match_schemes_to_criteria(self, user_criteria: str, 
                                 available_schemes: list) -> str:
        """
        Use LLM to match schemes to user criteria.
        
        Args:
            user_criteria: User's eligibility criteria
            available_schemes: List of available schemes
            
        Returns:
            LLM recommendation or empty string if failed
        """
        if not self.initialized or self.client is None:
            logger.warning("LLM not initialized")
            return ""
        
        try:
            # Format schemes for context
            schemes_text = "\n".join([
                f"- {scheme.get('scheme_name', 'Unknown')}: "
                f"{scheme.get('benefit_type', 'N/A')} "
                f"(₹{scheme.get('benefit_amount', 'N/A')})"
                for scheme in available_schemes[:10]  # Limit to 10 for token efficiency
            ])
            
            prompt = f"""Based on the user's eligibility criteria, recommend suitable schemes:

User Criteria: {user_criteria}

Available Schemes:
{schemes_text}

Please:
1. Recommend the most suitable schemes
2. Explain why each scheme matches the criteria
3. Mention any documents or additional steps needed
4. Be clear and concise

Keep your response to 3-4 sentences."""
            
            logger.debug("Sending scheme matching query to Groq")
            
            message = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                max_tokens=300,
                temperature=0.3
            )
            
            response = message.choices[0].message.content.strip()
            logger.debug(f"Scheme matching response: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Scheme matching failed: {e}")
            return ""
    
    def generate_explanation(self, scheme: dict, matching_criteria: list) -> str:
        """
        Generate explanation for why scheme matches user.
        
        Args:
            scheme: Scheme information
            matching_criteria: List of matching criteria
            
        Returns:
            Explanation text
        """
        criteria_str = "\n".join([f"  • {c}" for c in matching_criteria[:5]])
        
        explanation = f"""
Scheme: {scheme.get('scheme_name', 'Unknown')}
Category: {scheme.get('category', 'N/A')}
Benefit: {scheme.get('benefit_type', 'N/A')} - ₹{scheme.get('benefit_amount', 'N/A')}

Why you match:
{criteria_str}

Application Mode: {scheme.get('application_mode', 'Contact official office')}
Official Portal: {scheme.get('official_portal', 'Contact your local office')}
Documents Required: {scheme.get('documents_required', 'Check official website')}
"""
        return explanation
    
    def translate_response(self, text: str, target_language: str = 'en') -> str:
        """
        Translate response to target language using LLM.
        
        Args:
            text: Text to translate
            target_language: Target language code ('en' or 'ta')
            
        Returns:
            Translated text
        """
        if not self.initialized or self.client is None:
            logger.warning("LLM not initialized for translation")
            return text
        
        try:
            lang_map = {'en': 'English', 'ta': 'Tamil'}
            target_lang = lang_map.get(target_language, 'English')
            
            prompt = f"""Translate the following text to {target_lang}. 
Keep formatting and structure. Return only the translated text:

{text}"""
            
            logger.debug(f"Requesting translation to {target_lang}")
            
            message = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                max_tokens=500,
                temperature=0.2
            )
            
            translation = message.choices[0].message.content.strip()
            logger.debug("Translation completed")
            return translation
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text
