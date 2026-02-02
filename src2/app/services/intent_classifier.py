"""
Intent Classifier Service - Handles intent classification, NER, and prompt rewriting.

This service uses a smaller/faster model to:
1. Classify user intent → maps to a registered tool
2. Extract entities (NER) → dates, locations, flight numbers, etc.
3. Rewrite the prompt → clean, concise, focused

All three tasks in one LLM call for efficiency.
"""

from ..models.classification import ClassificationResponse
from .llm_service import LLMService
from .prompt_template_service import PromptTemplateService


class IntentClassifier:
    """
    Classifies user input and prepares it for tool routing.
    
    Uses a smaller model (gpt-4.1-mini) for fast, cheap classification.
    The heavy reasoning is left to the execution model (gpt-5.2).
    
    WORKSHOP NOTE:
    Set a breakpoint in classify() to see:
    - The classification prompt being built
    - The raw user input
    - The structured ClassificationResponse returned
    """
    
    def __init__(
        self, 
        llm_service: LLMService, 
        template_service: PromptTemplateService
    ):
        self._llm = llm_service
        self._templates = template_service
        print(f"[IntentClassifier] Initialized")
    
    def classify(
        self, 
        user_input: str, 
        available_tools: str
    ) -> ClassificationResponse:
        """
        Classify user intent and extract relevant information.
        
        Args:
            user_input: The raw user message
            available_tools: Formatted string of available tools from registry
                            (e.g., "- faq: Handles general questions...")
        
        Returns:
            ClassificationResponse with:
                - intent: which tool to route to
                - confidence: 0.0-1.0
                - reasoning: why this intent
                - rewritten_prompt: cleaned up user message
                - entities: extracted key information
        
        DEBUGGING: Step into this method to see classification in action.
        """
        # =================================================================
        # BREAKPOINT 7a: BUILD CONTEXT WINDOW FOR CLASSIFIER
        # -----------------------------------------------------------------
        # Load the classification prompt template and inject:
        # - available_tools: list of tools the LLM can choose from
        # - user_input: the raw message to classify
        # The prompt tells the LLM to return structured JSON.
        # =================================================================
        system_prompt = self._templates.load(
            "classification",
            {
                "available_tools": available_tools,
                "user_input": user_input
            }
        )
        print(f"[IntentClassifier] Built classification prompt ({len(system_prompt)} chars)")
        
        # =================================================================
        # BREAKPOINT 1: CALL LLM TO BUILD STRUCTURED OUTPUT
        # -----------------------------------------------------------------
        # The LLM will return JSON matching ClassificationResponse schema.
        # LLMService handles: API call → JSON parse → Pydantic validation.
        # use_classifier_model=True uses the fast model (gpt-4.1-mini).
        # =================================================================
        response = self._llm.complete(
            system_prompt=system_prompt,
            user_message=user_input,
            response_model=ClassificationResponse,
            use_classifier_model=True  # Use the fast model
        )
        
        # =================================================================
        # BREAKPOINT 2: VALIDATE STRUCTURED OUTPUT BEFORE RETURNING
        # -----------------------------------------------------------------
        # At this point, 'response' is already a validated Pydantic object
        # (validated in LLMService). But we add an explicit check here
        # for teaching purposes - this is the handoff boundary.
        # 
        # DETERMINISTIC PATTERN: Always verify structure at boundaries.
        # =================================================================
        assert isinstance(response, ClassificationResponse), \
            f"Expected ClassificationResponse, got {type(response)}"
        
        # Verify required fields are populated
        assert response.intent, "Intent cannot be empty"
        assert 0.0 <= response.confidence <= 1.0, \
            f"Confidence must be 0.0-1.0, got {response.confidence}"
        assert response.rewritten_prompt, "Rewritten prompt cannot be empty"
        
        print(f"[IntentClassifier] ✓ Validated ClassificationResponse")
        print(f"[IntentClassifier]   Intent: {response.intent} (confidence: {response.confidence:.2f})")
        print(f"[IntentClassifier]   Reasoning: {response.reasoning}")
        print(f"[IntentClassifier]   Rewritten: {response.rewritten_prompt}")
        if response.entities:
            print(f"[IntentClassifier]   Entities: {[(e.type, e.value) for e in response.entities]}")
        
        return response
