"""
Orchestrator Agent - Routes user requests to the appropriate tool.

This is the main entry point for handling user requests. It:
1. Classifies intent using IntentClassifier (small model)
2. Checks confidence and handles fallback if needed
3. Routes to the appropriate tool from the registry
4. Returns a standardized AgentResponse

WORKSHOP OBJECTIVES DEMONSTRATED:
- Tool discovery via ToolRegistry
- Intent classification with confidence scoring
- Prompt rewriting and entity extraction
- Fallback handling for low confidence
"""

from ..models.agent_models import AgentResponse
from ..models.classification import ClassificationResponse
from ..models.context import AgentContext
from ..models.faq import FAQRequest, FAQResponse
from ..memory import IMemoryStore, ConversationTurn
from ..services.intent_classifier import IntentClassifier
from ..services.llm_service import LLMService
from ..services.prompt_template_service import PromptTemplateService
from ..tools.tool_registry import ToolRegistry


# Confidence thresholds
CONFIDENCE_THRESHOLD_EXECUTE = 0.7   # Above this: execute the tool
CONFIDENCE_THRESHOLD_CLARIFY = 0.4   # Above this but below execute: ask clarification
# Below CLARIFY: fallback to human/general response


class OrchestratorAgent:
    """
    Routes user requests to the appropriate tool.
    
    DEBUGGING:
    Set a breakpoint on handle() and step through to see:
    1. Classification result (intent, confidence, entities)
    2. Confidence-based routing decision
    3. Tool instantiation from registry
    4. Tool execution
    
    This is the main orchestration loop that ties everything together.
    """
    
    def __init__(
        self,
        registry: ToolRegistry,
        llm_service: LLMService,
        template_service: PromptTemplateService,
        memory_store: IMemoryStore
    ):
        self._registry = registry
        self._llm = llm_service
        self._templates = template_service
        self._memory = memory_store
        
        # Create the intent classifier (uses the small/fast model)
        self._classifier = IntentClassifier(llm_service, template_service)
        print(f"[OrchestratorAgent] Initialized")
    
    def handle(
        self, 
        user_input: str, 
        context: AgentContext
    ) -> AgentResponse:
        """
        Handle a user request end-to-end.
        
        Args:
            user_input: The raw user message
            context: Conversation context (customer info, turn count, etc.)
        
        Returns:
            AgentResponse with the final answer and metadata
        
        DEBUGGING: This is the main entry point - set breakpoint here.
        """
        print(f"\n[Orchestrator] Received: {user_input}")
        
        # =================================================================
        # STEP 1: CLASSIFY INTENT
        # -----------------------------------------------------------------
        # Calls IntentClassifier with:
        #   - user_input: raw message from user
        #   - available_tools: list of registered tools for LLM to pick from
        #
        # Returns ClassificationResponse:
        #   - intent: "faq", "booking", etc. (which tool to use)
        #   - confidence: 0.0-1.0 (how certain the model is)
        #   - reasoning: why this intent was chosen
        #   - rewritten_prompt: cleaned/focused version of user input
        #   - entities: extracted info (dates, locations, etc.)
        # =================================================================
        available_tools = self._registry.get_routing_descriptions()
        classification = self._classifier.classify(user_input, available_tools)
        
        # =================================================================
        # BREAKPOINT 3: RECEIVE + VALIDATE CLASSIFICATION FROM INTENT
        # -----------------------------------------------------------------
        # DETERMINISTIC PATTERN: Validate inputs at every boundary.
        # Even though IntentClassifier validated before returning,
        # we validate again here. Defense in depth.
        # =================================================================
        assert isinstance(classification, ClassificationResponse), \
            f"Expected ClassificationResponse, got {type(classification)}"
        assert classification.intent, "Classification must have an intent"
        assert 0.0 <= classification.confidence <= 1.0, \
            f"Confidence must be 0.0-1.0, got {classification.confidence}"
        print(f"[Orchestrator] ✓ Received valid ClassificationResponse")
        
        # =================================================================
        # STEP 2: CONFIDENCE-BASED ROUTING DECISION
        # -----------------------------------------------------------------
        # Three-tier decision based on confidence score:
        #
        #   confidence < 0.4  → FALLBACK
        #       Model is very uncertain. Don't guess - apologize and
        #       ask user to rephrase. Avoids wrong tool execution.
        #
        #   confidence 0.4-0.7 → CLARIFY  
        #       Model has some idea but not confident. Ask user to
        #       confirm before executing. "Did you mean...?"
        #
        #   confidence >= 0.7 → EXECUTE
        #       Model is confident. Proceed to tool execution.
        #
        # =================================================================
        if classification.confidence < CONFIDENCE_THRESHOLD_CLARIFY:
            # Very low confidence (< 0.4) - don't even guess
            response = self._handle_fallback(user_input, classification)
            self._save_turn(context, user_input, response, classification)
            return response
        
        if classification.confidence < CONFIDENCE_THRESHOLD_EXECUTE:
            # Medium confidence (0.4 - 0.7) - ask for confirmation
            response = self._handle_clarification(user_input, classification)
            self._save_turn(context, user_input, response, classification)
            return response
        
        # =================================================================
        # STEP 3: VERIFY TOOL EXISTS IN REGISTRY
        # -----------------------------------------------------------------
        # Safety check: classifier might return an intent that doesn't
        # match any registered tool (e.g., hallucinated tool name).
        # If so, fall back gracefully rather than crash.
        # =================================================================
        if not self._registry.has_tool(classification.intent):
            print(f"[Orchestrator] WARNING: Unknown intent '{classification.intent}'")
            response = self._handle_fallback(user_input, classification)
            self._save_turn(context, user_input, response, classification)
            return response
        
        # =================================================================
        # STEP 4: GET TOOL FROM REGISTRY AND EXECUTE
        # -----------------------------------------------------------------
        # High confidence (>= 0.7) - execute the tool.
        # Uses the REWRITTEN prompt (cleaner, more focused).
        # Returns standardized AgentResponse.
        # NOTE: _execute_tool handles its own _save_turn call since it
        # has access to tool_reasoning from FAQResponse.
        # =================================================================
        response = self._execute_tool(user_input, classification, context)
        return response
    
    def _execute_tool(
        self,
        original_input: str,
        classification: ClassificationResponse,
        context: AgentContext
    ) -> AgentResponse:
        """
        Get the tool from registry and execute it.
        
        Called when confidence >= 0.7 (high confidence routing).
        Uses rewritten_prompt instead of original for cleaner input.
        """
        print(f"[Orchestrator] Routing to: {classification.intent}")
        
        # Get tool instance from registry (injects llm_service, template_service)
        tool = self._registry.get(
            classification.intent,
            llm_service=self._llm,
            template_service=self._templates
        )
        
        # =================================================================
        # BREAKPOINT 4: BUILD STRUCTURED REQUEST FOR TOOL
        # -----------------------------------------------------------------
        # Create FAQRequest using the REWRITTEN prompt (cleaner, focused).
        # Pydantic validates on construction - if 'question' is empty
        # or wrong type, this will raise ValidationError.
        #
        # NOTE: In production, each tool would have its own request type.
        # We'd use a factory pattern to build the right request type
        # based on classification.intent.
        # =================================================================
        request = FAQRequest(question=classification.rewritten_prompt)
        
        # =================================================================
        # BREAKPOINT 5: VALIDATE STRUCTURED REQUEST BEFORE SENDING
        # -----------------------------------------------------------------
        # DETERMINISTIC PATTERN: Explicit validation at boundaries.
        # Verify the request object is properly formed before passing
        # to the tool. This catches issues early.
        # =================================================================
        assert isinstance(request, FAQRequest), \
            f"Expected FAQRequest, got {type(request)}"
        assert request.question, "FAQRequest.question cannot be empty"
        print(f"[Orchestrator] ✓ Built valid FAQRequest: '{request.question[:50]}...'")
        
        # Execute the tool (this is where the main LLM work happens)
        tool_response = tool.execute(request, context)
        
        # =================================================================
        # BREAKPOINT 12: RECEIVE + VALIDATE RESPONSE FROM TOOL
        # -----------------------------------------------------------------
        # DETERMINISTIC PATTERN: Validate all responses from external calls.
        # The tool should have returned a valid FAQResponse.
        # Verify structure before using the data.
        # =================================================================
        assert isinstance(tool_response, FAQResponse), \
            f"Expected FAQResponse, got {type(tool_response)}"
        assert tool_response.answer, "FAQResponse.answer cannot be empty"
        print(f"[Orchestrator] ✓ Received valid FAQResponse")
        
        # =================================================================
        # BREAKPOINT 13: ORCHESTRATOR REASONS + BUILDS FINAL RESPONSE
        # -----------------------------------------------------------------
        # Wrap the tool response in a standardized AgentResponse.
        # This is the final output that goes back to the user.
        # In a more complex system, the orchestrator might:
        # - Chain to another tool
        # - Request clarification
        # - Add follow-up suggestions
        # =================================================================
        final_response = AgentResponse(
            answer=tool_response.answer,
            routed_to=classification.intent,
            confidence=classification.confidence,
            original_input=original_input,
            rewritten_input=classification.rewritten_prompt
        )
        print(f"[Orchestrator] ✓ Built AgentResponse, returning to user")
        
        # Save with tool reasoning for visibility
        self._save_turn(
            context, original_input, final_response, classification,
            tool_reasoning=tool_response.reasoning
        )
        return final_response
    
    def _handle_clarification(
        self,
        original_input: str,
        classification: ClassificationResponse
    ) -> AgentResponse:
        """
        Handle medium-confidence (0.4 - 0.7) by asking for clarification.
        
        The model has some idea what the user wants, but isn't confident.
        Ask the user to confirm before executing the wrong tool.
        """
        print(f"[Orchestrator] Medium confidence ({classification.confidence:.2f}) - asking clarification")
        
        return AgentResponse(
            answer=f"I'm not quite sure I understand. Could you rephrase your question? "
                   f"I think you might be asking about {classification.intent}, but I want to make sure.",
            routed_to="clarification",
            confidence=classification.confidence,
            original_input=original_input,
            rewritten_input=classification.rewritten_prompt
        )
    
    def _handle_fallback(
        self,
        original_input: str,
        classification: ClassificationResponse
    ) -> AgentResponse:
        """
        Handle very low confidence (< 0.4) or unknown intent.
        
        The model is too uncertain to even guess. Don't risk executing
        the wrong tool - apologize and list what we CAN help with.
        """
        print(f"[Orchestrator] Fallback - confidence too low ({classification.confidence:.2f})")
        
        return AgentResponse(
            answer="I'm sorry, I'm not sure how to help with that. "
                   "I can help you with questions about baggage, policies, booking, or refunds. "
                   "Could you try rephrasing your question?",
            routed_to="fallback",
            confidence=classification.confidence,
            original_input=original_input,
            rewritten_input=classification.rewritten_prompt
        )
    
    def _save_turn(
        self,
        context: AgentContext,
        user_input: str,
        response: AgentResponse,
        classification: ClassificationResponse,
        tool_reasoning: str | None = None
    ) -> None:
        """
        Save this conversation turn to memory.
        
        Called after every response, regardless of routing path.
        Uses customer_name as session_id for demo purposes.
        
        Args:
            context: Current conversation context
            user_input: Raw user input
            response: Final AgentResponse sent to user
            classification: Classification result (contains intent reasoning)
            tool_reasoning: Optional reasoning from the executed tool
        """
        # Convert entities list to dict for storage
        entities_dict = {e.type: e.value for e in classification.entities}
        
        turn = ConversationTurn(
            user_input=user_input,
            agent_response=response.answer,
            intent=classification.intent,
            confidence=classification.confidence,
            rewritten_prompt=classification.rewritten_prompt,
            entities=entities_dict,
            classification_reasoning=classification.reasoning,
            tool_reasoning=tool_reasoning
        )
        
        # Use customer_name as session_id (in production, use a real session ID)
        session_id = context.customer_name
        self._memory.save_turn(session_id, turn)
