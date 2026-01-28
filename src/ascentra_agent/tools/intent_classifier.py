"""Intent classification tool for routing user input."""

from ascentra_agent.contracts.specs import UserIntent
from ascentra_agent.contracts.tool_output import ToolOutput, err
from ascentra_agent.llm.structured import build_messages, chat_structured_pydantic
from ascentra_agent.tools.base import Tool, ToolContext


class IntentClassifier(Tool):
    """Tool for classifying user intent from natural language input.

    Determines whether the user wants to:
    - Have a general chat (greetings, questions about capabilities)
    - Generate a high-level analysis plan
    - Execute a specific cut/analysis
    - Define a segment
    - Needs clarification (ambiguous input)
    """

    @property
    def name(self) -> str:
        return "intent_classifier"

    @property
    def description(self) -> str:
        return "Classifies user input into intent types for routing"

    def run(self, ctx: ToolContext) -> ToolOutput[UserIntent]:
        """Classify the intent of the user's input.

        Args:
            ctx: Tool context with questions and the user prompt

        Returns:
            ToolOutput containing a UserIntent or errors
        """
        if not ctx.prompt:
            return ToolOutput.failure(
                errors=[err("missing_prompt", "No user input provided")]
            )

        try:
            intent = self._classify_intent(ctx.prompt, ctx.questions)
            
            trace = {
                "model": None,
                "temperature": 0.0,
                "latency_s": 0.0,
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                "finish_reason": None,
            }

            return ToolOutput.success(data=intent, trace=trace)

        except Exception as e:
            return ToolOutput.failure(
                errors=[err("tool_error", f"Intent classification failed: {str(e)}")],
            )

    def _build_user_content(self, ctx: ToolContext) -> str:
        """Build the user message content."""
        return ctx.prompt
    
    def _classify_intent(self, prompt: str, questions: list) -> UserIntent:
        """Classify user intent using pattern matching and question catalog.
        
        Args:
            prompt: User input text
            questions: Question catalog for grounding
            
        Returns:
            UserIntent with classified type
        """
        text = prompt.lower().strip()
        
        # Build question reference sets for matching
        question_ids = set()
        question_labels = set()
        
        for q in questions:
            question_ids.add(q.question_id.lower())
            # Add tokens from label for fuzzy matching
            label_tokens = q.label.lower().split()
            question_labels.update(label_tokens)
        
        # 1. HIGH-LEVEL PLAN - Analysis planning (NOT casual "plan" mentions)
        plan_verbs = [
            'create an analysis plan', 'create analysis plan',
            'plan the analysis', 'plan an analysis',
            'suggest a plan', 'suggest an analysis plan',
            'suggest a plan for',
            'what should we analyze', 'what should i analyze',
            'give me a roadmap', 'roadmap of analyses',
        ]
        
        for verb in plan_verbs:
            if verb in text:
                return UserIntent(
                    intent_type="high_level_plan",
                    confidence=0.95,
                    reasoning=f"Analysis planning phrase detected: '{verb}'"
                )
        
        
        # 2. MULTI-INTENT PRIORITY - Check for analysis verbs that override segment creation
        # If "analyze" or "show" appears with segment words, prioritize cut_analysis
        analysis_action_verbs = ['analyze', 'show', 'display']
        has_analysis_action = any(verb in text for verb in analysis_action_verbs)
        segment_words = ['segment', 'cohort', 'audience']
        has_segment_word = any(word in text for word in segment_words)
        
        if has_analysis_action and has_segment_word:
            return UserIntent(
                intent_type="cut_analysis",
                confidence=0.9,
                reasoning="Multi-intent detected: analysis action takes priority"
            )
        
        # 3. SEGMENT DEFINITION - Explicit creation verbs
        segment_verbs = [
            'define segment', 'create segment', 'build segment',
            'define a segment', 'create a segment', 'build a segment',
            'define cohort', 'create cohort', 'build cohort',
            'build a cohort for', 'build cohort for',
            'define audience', 'create audience', 'build audience',
            'create an audience', 'build an audience',
            'filter to customers', 'filter to users',
        ]
        
        # Special pattern: "users who are" or "customers aged"
        segment_patterns = ['users who are', 'users aged', 'customers aged', 'customers who']
        
        for verb in segment_verbs:
            if verb in text:
                return UserIntent(
                    intent_type="segment_definition",
                    confidence=0.95,
                    reasoning=f"Segment creation verb detected: '{verb}'"
                )
        
        for pattern in segment_patterns:
            if pattern in text:
                return UserIntent(
                    intent_type="segment_definition",
                    confidence=0.9,
                    reasoning=f"Segment filter pattern detected: '{pattern}'"
                )
        
        # 4. CHAT - Conversational patterns (highest priority to avoid false positives)
        chat_patterns = [
            'hello', 'hi', 'hey', 'help', 'thanks', 'thank you',
            'what can you do', 'how does this work', 'what is a',
            'how do i', 'can you explain', 'tell me about',
        ]
        
        # Casual mentions that should NOT trigger other intents
        casual_phrases = [
            'my plan is', 'our plan is', 'the plan is',
            'what is a segment', 'what is a cut', 'explain segment',
            'pricing plan', 'subscription plan', 'plan problem',
        ]
        
        for pattern in chat_patterns:
            if pattern in text:
                return UserIntent(
                    intent_type="chat",
                    confidence=0.9,
                    reasoning=f"Conversational pattern detected: '{pattern}'"
                )
        
        for phrase in casual_phrases:
            if phrase in text:
                return UserIntent(
                    intent_type="chat",
                    confidence=0.9,
                    reasoning=f"Casual mention detected: '{phrase}'"
                )
        
        
        # 5. CUT ANALYSIS - Data analysis requests
        
        # Check for question references (IDs or labels)
        has_question_reference = False
        matched_question = None
        
        for qid in question_ids:
            if qid in text:
                has_question_reference = True
                matched_question = qid
                break
        
        # Check for common analysis verbs
        analysis_verbs = [
            'show', 'analyze', 'display', 'break down', 'breakdown',
            'distribution', 'frequency', 'compare', 'average',
            'mean', 'count', 'percentage', 'what is the',
        ]
        
        has_analysis_verb = any(verb in text for verb in analysis_verbs)
        
        # Strong signal: question reference + analysis verb
        if has_question_reference and has_analysis_verb:
            return UserIntent(
                intent_type="cut_analysis",
                confidence=0.95,
                reasoning=f"Analysis verb + question reference ({matched_question})"
            )
        
        # Medium signal: question reference alone (e.g., "show Q_PLAN")
        if has_question_reference:
            return UserIntent(
                intent_type="cut_analysis",
                confidence=0.85,
                reasoning=f"Question reference detected: {matched_question}"
            )
        
        # Check for metric keywords with "by" (e.g., "nps by region")
        if ' by ' in text and has_analysis_verb:
            return UserIntent(
                intent_type="cut_analysis",
                confidence=0.8,
                reasoning="Analysis pattern with 'by' dimension detected"
            )
        
        # Weak signal: analysis verb with potential question label tokens
        label_matches = [token for token in text.split() if token in question_labels]
        if has_analysis_verb and label_matches:
            return UserIntent(
                intent_type="cut_analysis",
                confidence=0.75,
                reasoning=f"Analysis verb + question label tokens: {label_matches}"
            )
        
        # 6. DEFAULT - Ambiguous or unclear, default to chat
        return UserIntent(
            intent_type="chat",
            confidence=0.5,
            reasoning="No clear intent pattern detected, defaulting to chat"
        )