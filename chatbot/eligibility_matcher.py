"""
Eligibility Matcher module for generating questions and scoring schemes.
Handles user criteria collection and scheme matching logic.
"""

import logging
import re
from typing import Dict, List, Tuple, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class EligibilityMatcher:
    """Generates eligibility questions and matches user criteria to schemes."""
    
    def __init__(self, schemes_df: pd.DataFrame):
        """
        Initialize matcher with schemes data.
        
        Args:
            schemes_df: DataFrame containing welfare schemes
        """
        self.schemes_df = schemes_df
        self.question_pool = self._build_question_pool()
        self.current_question_index = 0
        self.user_responses = {}
        self.asked_questions = set()
    
    def _build_question_pool(self) -> List[Dict]:
        """Build pool of eligibility questions."""
        return [
            {
                'id': 'age',
                'question': 'What is your age?',
                'type': 'numeric',
                'field_mapping': ['eligibility_age_min', 'eligibility_age_max'],
                'unit': 'years'
            },
            {
                'id': 'income',
                'question': 'What is your annual household income (in rupees)?',
                'type': 'numeric',
                'field_mapping': ['income_limit_annual'],
                'unit': 'rupees'
            },
            {
                'id': 'gender',
                'question': 'What is your gender? (Male/Female/Other/Prefer not to say)',
                'type': 'categorical',
                'field_mapping': ['eligible_gender'],
                'options': ['Male', 'Female', 'Other', 'Prefer not to say']
            },
            {
                'id': 'caste',
                'question': 'Which caste category do you belong to? (General/OBC/SC/ST)',
                'type': 'categorical',
                'field_mapping': ['eligible_caste'],
                'options': ['General', 'OBC', 'SC', 'ST']
            },
            {
                'id': 'religion',
                'question': 'What is your religion?',
                'type': 'categorical',
                'field_mapping': ['eligible_religion'],
                'options': ['Hindu', 'Muslim', 'Christian', 'Sikh', 'Buddhist', 'Jain', 'Other']
            },
            {
                'id': 'occupation',
                'question': 'What is your occupation/profession?',
                'type': 'text',
                'field_mapping': ['occupation']
            },
            {
                'id': 'education',
                'question': 'What is your highest education level? (No formal/10th/12th/Graduation/Post-Graduation)',
                'type': 'categorical',
                'field_mapping': ['education_required'],
                'options': ['No formal', '10th', '12th', 'Graduation', 'Post-Graduation']
            },
            {
                'id': 'marital_status',
                'question': 'What is your marital status? (Single/Married/Divorced/Widowed)',
                'type': 'categorical',
                'field_mapping': ['marital_status'],
                'options': ['Single', 'Married', 'Divorced', 'Widowed']
            },
            {
                'id': 'disability',
                'question': 'Do you have any disability? (Yes/No)',
                'type': 'categorical',
                'field_mapping': ['disability_required'],
                'options': ['Yes', 'No']
            },
            {
                'id': 'residence',
                'question': 'How long have you been residing in Tamil Nadu? (in years)',
                'type': 'numeric',
                'field_mapping': ['residence_requirement'],
                'unit': 'years'
            }
        ]
    
    def get_next_question(self) -> Optional[Dict]:
        """
        Get next unanswered question.
        
        Returns:
            Question dictionary or None if all answered
        """
        for question in self.question_pool:
            if question['id'] not in self.asked_questions:
                self.asked_questions.add(question['id'])
                logger.debug(f"Returning question: {question['id']}")
                return question
        
        logger.debug("All questions have been asked")
        return None
    
    def record_response(self, question_id: str, response: str) -> bool:
        """
        Record user response to a question.
        
        Args:
            question_id: ID of the question
            response: User's response
            
        Returns:
            True if response recorded successfully
        """
        try:
            if not response or not response.strip():
                logger.warning(f"Empty response for question {question_id}")
                return False
            
            self.user_responses[question_id] = response.strip()
            logger.debug(f"Recorded response for {question_id}: {response[:50]}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record response: {e}")
            return False
    
    def parse_numeric_response(self, response: str) -> Optional[float]:
        """
        Parse numeric response from user.
        
        Args:
            response: User's text response
            
        Returns:
            Parsed numeric value or None
        """
        try:
            # Extract numbers from response
            import re
            numbers = re.findall(r'\d+', response)
            if numbers:
                return float(numbers[0])
            return None
        except Exception as e:
            logger.error(f"Failed to parse numeric response: {e}")
            return None

    def _parse_limit_value(self, value) -> Optional[float]:
        """Parse a scheme threshold such as income/age/residence from text or numbers.

        Returns:
            A numeric threshold, or None if the field should be treated as unknown.
            Textual non-limits like 'No Limit' are mapped to infinity.
        """
        if value is None or pd.isna(value):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip().lower()
        if not text:
            return None

        unlimited_patterns = [
            'no limit',
            'no income limit',
            'no income limit (government college students)',
            'no income limit (government school students)',
            'no income limit (construction workers)',
            'no income limit (plantation workers)',
            'no income limit (ex-servicemen)',
            'below poverty line',
            'bpl',
            'rural poor households',
        ]
        if any(pattern in text for pattern in unlimited_patterns):
            return float('inf')

        numbers = re.findall(r'\d+(?:\.\d+)?', text.replace(',', ''))
        if numbers:
            return float(numbers[0])

        return None
    
    def score_scheme(self, scheme: pd.Series) -> Tuple[float, List[str]]:
        """
        Score a scheme based on user responses.
        
        Args:
            scheme: Scheme row from DataFrame
            
        Returns:
            Tuple of (score: 0-1, matching_criteria: list of explanations)
        """
        score = 0.0
        max_score = 0.0
        matching_criteria = []
        
        try:
            # Age check
            if 'age' in self.user_responses:
                user_age = self.parse_numeric_response(self.user_responses['age'])
                if user_age is not None:
                    min_age = scheme.get('eligibility_age_min')
                    max_age = scheme.get('eligibility_age_max')
                    
                    min_age = self._parse_limit_value(min_age)
                    max_age = self._parse_limit_value(max_age)

                    if min_age is not None and max_age is not None:
                        max_score += 1.0
                        
                        if min_age <= user_age <= max_age:
                            score += 1.0
                            matching_criteria.append(
                                f"✓ Age {min_age}-{max_age} (your age: {user_age})"
                            )
                        else:
                            matching_criteria.append(
                                f"✗ Age {min_age}-{max_age} (your age: {user_age})"
                            )
            
            # Income check
            if 'income' in self.user_responses:
                user_income = self.parse_numeric_response(self.user_responses['income'])
                if user_income is not None:
                    income_limit = scheme.get('income_limit_annual')
                    
                    income_limit = self._parse_limit_value(income_limit)

                    if income_limit is not None:
                        max_score += 1.0

                        if income_limit == float('inf') or user_income <= income_limit:
                            score += 1.0
                            if income_limit == float('inf'):
                                matching_criteria.append(
                                    f"✓ Income requirement: no effective income limit (your income: ₹{user_income:,.0f})"
                                )
                            else:
                                matching_criteria.append(
                                    f"✓ Income limit ₹{income_limit:,.0f} (your income: ₹{user_income:,.0f})"
                                )
                        else:
                            matching_criteria.append(
                                f"✗ Income limit ₹{income_limit:,.0f} (your income: ₹{user_income:,.0f})"
                            )
            
            # Gender check
            if 'gender' in self.user_responses:
                user_gender = self.user_responses['gender'].lower()
                eligible_gender = scheme.get('eligible_gender')
                
                if pd.notna(eligible_gender):
                    eligible_genders = [g.strip().lower() for g in str(eligible_gender).split(',')]
                    max_score += 1.0
                    
                    if user_gender in eligible_genders or 'all' in eligible_genders:
                        score += 1.0
                        matching_criteria.append(f"✓ Gender: {eligible_gender}")
                    else:
                        matching_criteria.append(f"✗ Gender requirement: {eligible_gender}")
            
            # Caste check
            if 'caste' in self.user_responses:
                user_caste = self.user_responses['caste'].lower()
                eligible_caste = scheme.get('eligible_caste')
                
                if pd.notna(eligible_caste):
                    eligible_castes = [c.strip().lower() for c in str(eligible_caste).split(',')]
                    max_score += 1.0
                    
                    if user_caste in eligible_castes or 'all' in eligible_castes:
                        score += 1.0
                        matching_criteria.append(f"✓ Caste: {eligible_caste}")
                    else:
                        matching_criteria.append(f"✗ Caste requirement: {eligible_caste}")
            
            # Religion check
            if 'religion' in self.user_responses:
                user_religion = self.user_responses['religion'].lower()
                eligible_religion = scheme.get('eligible_religion')
                
                if pd.notna(eligible_religion):
                    eligible_religions = [r.strip().lower() for r in str(eligible_religion).split(',')]
                    max_score += 1.0
                    
                    if user_religion in eligible_religions or 'all' in eligible_religions:
                        score += 1.0
                        matching_criteria.append(f"✓ Religion: {eligible_religion}")
                    else:
                        matching_criteria.append(f"✗ Religion requirement: {eligible_religion}")
            
            # Disability check
            if 'disability' in self.user_responses:
                user_disability = self.user_responses['disability'].lower().startswith('yes')
                disability_required = scheme.get('disability_required')
                
                if pd.notna(disability_required):
                    max_score += 1.0
                    disability_required = str(disability_required).lower()
                    
                    if disability_required == 'no' or (user_disability and disability_required != 'no'):
                        score += 1.0
                        matching_criteria.append(
                            f"✓ Disability requirement: {disability_required}"
                        )
                    else:
                        matching_criteria.append(
                            f"✗ Disability requirement: {disability_required}"
                        )

            # Residence check
            if 'residence' in self.user_responses:
                user_residence = self.parse_numeric_response(self.user_responses['residence'])
                if user_residence is not None:
                    residence_requirement = self._parse_limit_value(scheme.get('residence_requirement'))

                    if residence_requirement is not None:
                        max_score += 1.0

                        if residence_requirement == float('inf') or user_residence >= residence_requirement:
                            score += 1.0
                            if residence_requirement == float('inf'):
                                matching_criteria.append(
                                    f"✓ Residence requirement: no effective minimum (your residence: {user_residence} years)"
                                )
                            else:
                                matching_criteria.append(
                                    f"✓ Residence requirement: {residence_requirement} years+ (your residence: {user_residence} years)"
                                )
                        else:
                            matching_criteria.append(
                                f"✗ Residence requirement: {residence_requirement} years+ (your residence: {user_residence} years)"
                            )
            
            # Calculate final score
            if max_score > 0:
                final_score = score / max_score
            else:
                final_score = 0.5  # Default score if no criteria checked
            
            logger.debug(f"Scheme score: {final_score:.2f} ({score}/{max_score})")
            
            return final_score, matching_criteria
            
        except Exception as e:
            logger.error(f"Error scoring scheme: {e}")
            return 0.0, ["Error calculating match"]
    
    def find_matching_schemes(self) -> List[Dict]:
        """
        Find and rank schemes matching user criteria.
        
        Returns:
            List of matching schemes with scores and explanations
        """
        try:
            if len(self.user_responses) == 0:
                logger.warning("No user responses recorded")
                return []
            
            logger.info(f"Matching schemes against {len(self.user_responses)} criteria...")
            
            matches = []
            
            for idx, scheme in self.schemes_df.iterrows():
                score, criteria = self.score_scheme(scheme)
                
                # Include schemes with score > 0.3 (at least 30% match)
                if score > 0.3:
                    match = {
                        'scheme_id': scheme.get('scheme_id'),
                        'scheme_name': scheme.get('scheme_name'),
                        'category': scheme.get('category'),
                        'sub_category': scheme.get('sub_category'),
                        'benefit_type': scheme.get('benefit_type'),
                        'benefit_amount': scheme.get('benefit_amount'),
                        'application_mode': scheme.get('application_mode'),
                        'official_portal': scheme.get('official_portal'),
                        'documents_required': scheme.get('documents_required'),
                        'score': score,
                        'matching_criteria': criteria
                    }
                    matches.append(match)
            
            # Sort by score (descending)
            matches.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(f"Found {len(matches)} matching schemes")
            return matches
            
        except Exception as e:
            logger.error(f"Error finding matching schemes: {e}")
            return []
    
    def reset(self):
        """Reset matcher state."""
        self.current_question_index = 0
        self.user_responses.clear()
        self.asked_questions.clear()
        logger.debug("Matcher reset")
