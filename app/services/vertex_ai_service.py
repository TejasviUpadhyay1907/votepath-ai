"""Google Vertex AI integration service

This module integrates Google Vertex AI for AI-powered features.
Vertex AI provides access to Google's generative AI models.

Features:
- Intent validation using AI
- Response quality enhancement
- Query understanding improvement
- Confidence scoring validation

Why Vertex AI?
- Access to Google's latest AI models (Gemini)
- Generous free tier
- Serverless (no infrastructure)
- Integration with Google Cloud
- Production-ready AI capabilities

Free Tier:
- Gemini 1.5 Flash: Free tier available
- Perfect for intent validation
- No API key required (uses project auth)
"""

import logging
import os
from typing import Optional, Dict

# Vertex AI is optional - gracefully degrade if not available
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False

logger = logging.getLogger(__name__)


class VertexAIService:
    """Service for integrating with Google Vertex AI"""

    def __init__(self):
        """Initialize Vertex AI client"""
        self.model: Optional[GenerativeModel] = None
        self.enabled = False
        self.project_id: Optional[str] = None

    def initialize(self) -> bool:
        """
        Initialize Vertex AI integration.

        Returns:
            bool: True if successfully initialized, False otherwise
        """
        # Only enable in production (Cloud Run environment)
        if not os.getenv("K_SERVICE"):
            logger.info("Vertex AI disabled (not running on Cloud Run)")
            return False

        if not VERTEX_AI_AVAILABLE:
            logger.warning("vertexai not installed, skipping")
            return False

        try:
            # Get project ID from environment
            self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            if not self.project_id:
                logger.warning("GOOGLE_CLOUD_PROJECT not set, Vertex AI disabled")
                return False

            # Initialize Vertex AI
            vertexai.init(project=self.project_id, location="us-central1")

            # Initialize Gemini model (free tier)
            self.model = GenerativeModel("gemini-1.5-flash")

            self.enabled = True
            logger.info("Vertex AI initialized successfully with Gemini 1.5 Flash")
            return True

        except Exception as exc:
            # Graceful degradation - continue without Vertex AI
            logger.warning("Failed to initialize Vertex AI: %s", exc)
            return False

    def validate_intent(
        self,
        question: str,
        detected_intent: str,
        confidence: str
    ) -> Dict[str, any]:
        """
        Use AI to validate detected intent and confidence.

        Args:
            question: User's question
            detected_intent: Intent detected by keyword matching
            confidence: Confidence level from keyword matching

        Returns:
            Dict with ai_validation, ai_confidence, ai_reasoning
        """
        if not self.enabled or not self.model:
            return {
                "ai_validation": "unavailable",
                "ai_confidence": confidence,
                "ai_reasoning": "Vertex AI not available"
            }

        try:
            # Construct prompt for intent validation
            prompt = f"""You are an election information assistant. Validate if the detected intent is correct.

Question: "{question}"
Detected Intent: {detected_intent}
Keyword Confidence: {confidence}

Valid intents are:
- first_time_voter: Questions from 18-year-olds or new voters
- registration: Voter registration process
- documents: Required documents for voting
- correction: Correcting voter list errors
- status_check: Checking registration status
- polling_day: Polling booth location and voting day
- timeline: Election schedule and deadlines
- faq: General election questions
- out_of_scope: Non-election questions

Respond in this exact format:
VALIDATION: [correct/incorrect/uncertain]
CONFIDENCE: [high/medium/low]
REASONING: [one sentence explanation]"""

            # Generate response (with timeout)
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": 200,
                    "temperature": 0.1,  # Low temperature for consistent validation
                }
            )

            # Parse response
            text = response.text.strip()
            lines = text.split("\n")

            validation = "uncertain"
            ai_confidence = confidence
            reasoning = "Unable to parse AI response"

            for line in lines:
                if line.startswith("VALIDATION:"):
                    validation = line.split(":", 1)[1].strip().lower()
                elif line.startswith("CONFIDENCE:"):
                    ai_confidence = line.split(":", 1)[1].strip().lower()
                elif line.startswith("REASONING:"):
                    reasoning = line.split(":", 1)[1].strip()

            return {
                "ai_validation": validation,
                "ai_confidence": ai_confidence,
                "ai_reasoning": reasoning
            }

        except Exception as exc:
            # Don't fail requests due to AI issues
            logger.debug("Failed to validate intent with Vertex AI: %s", exc)
            return {
                "ai_validation": "error",
                "ai_confidence": confidence,
                "ai_reasoning": f"AI validation error: {str(exc)[:100]}"
            }

    def enhance_response(
        self,
        question: str,
        intent: str,
        response_text: str
    ) -> Optional[str]:
        """
        Use AI to enhance response quality (optional feature).

        Args:
            question: User's question
            intent: Detected intent
            response_text: Original response text

        Returns:
            Enhanced response text or None if unavailable
        """
        if not self.enabled or not self.model:
            return None

        try:
            prompt = (
                f"You are an election information assistant. "
                f"Make this response more natural and helpful "
                f"while keeping all factual information.\n\n"
                f'Question: "{question}"\n'
                f"Intent: {intent}\n"
                f'Original Response: "{response_text[:500]}"\n\n'
                f"Provide a more natural, conversational version while:\n"
                f"1. Keeping all factual information\n"
                f"2. Making it easier to understand\n"
                f"3. Being concise (max 3 sentences)\n"
                f"4. Maintaining professional tone"
            )

            response = self.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": 300,
                    "temperature": 0.3,
                }
            )

            enhanced = response.text.strip()
            return enhanced if enhanced else None

        except Exception as exc:
            logger.debug("Failed to enhance response with Vertex AI: %s", exc)
            return None

    def is_enabled(self) -> bool:
        """
        Check if Vertex AI is enabled.

        Returns:
            bool: True if Vertex AI is active
        """
        return self.enabled


# Global instance
_vertex_ai_service: Optional[VertexAIService] = None


def get_vertex_ai_service() -> VertexAIService:
    """
    Get global Vertex AI service instance (singleton pattern).

    Returns:
        VertexAIService: Global Vertex AI service instance
    """
    global _vertex_ai_service
    if _vertex_ai_service is None:
        _vertex_ai_service = VertexAIService()
    return _vertex_ai_service
