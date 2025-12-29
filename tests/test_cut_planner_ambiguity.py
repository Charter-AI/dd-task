# test_cut_planner_ambiguity.py
import json
from unittest.mock import MagicMock, patch
from pathlib import Path

from dd_agent.tools.cut_planner import CutPlanner, CutPlanResult, AmbiguityOption
from dd_agent.contracts.specs import CutSpec, MetricSpec, DimensionSpec
from dd_agent.contracts.questions import Question, QuestionType, Option
from dd_agent.tools.base import ToolContext

def test_ambiguity_detection():
    """Test that the cut planner detects ambiguity correctly."""
    
    # Create ambiguous questions (multiple satisfaction questions)
    questions = [
        Question(
            question_id="Q_OVERALL_SAT",
            label="Overall, how satisfied are you with our product?",
            type=QuestionType.likert_1_5,
            options=[
                Option(code=1, label="Very Dissatisfied"),
                Option(code=2, label="Dissatisfied"),
                Option(code=3, label="Neutral"),
                Option(code=4, label="Satisfied"),
                Option(code=5, label="Very Satisfied")
            ]
        ),
        Question(
            question_id="Q_SUPPORT_SAT",
            label="How satisfied are you with our customer support?",
            type=QuestionType.likert_1_5,
            options=[
                Option(code=1, label="Very Dissatisfied"),
                Option(code=2, label="Dissatisfied"),
                Option(code=3, label="Neutral"),
                Option(code=4, label="Satisfied"),
                Option(code=5, label="Very Satisfied")
            ]
        ),
        Question(
            question_id="Q_REGION",
            label="In which region do you live?",
            type=QuestionType.single_choice,
            options=[
                Option(code="NORTH", label="North"),
                Option(code="SOUTH", label="South"),
                Option(code="EAST", label="East"),
                Option(code="WEST", label="West")
            ]
        )
    ]
    
    # Create mock LLM response with ambiguity
    mock_ambiguity_options = [
        AmbiguityOption(
            question_id="Q_OVERALL_SAT",
            label="Overall, how satisfied are you with our product?",
            match_reason="User said 'satisfaction', this is overall satisfaction question",
            confidence=0.8,
            question_type="likert_1_5"
        ),
        AmbiguityOption(
            question_id="Q_SUPPORT_SAT",
            label="How satisfied are you with our customer support?",
            match_reason="User said 'satisfaction', this is support satisfaction question",
            confidence=0.6,
            question_type="likert_1_5"
        )
    ]
    
    mock_cut_plan = CutPlanResult(
        ok=True,
        cut=None,  # No cut until ambiguity resolved
        resolution_map={"satisfaction": "multiple_possible", "region": "Q_REGION"},
        ambiguity_options=mock_ambiguity_options,
        requires_user_resolution=True,
        errors=[]
    )
    
    # Mock the chat_structured_pydantic function
    with patch('dd_agent.tools.cut_planner.chat_structured_pydantic') as mock_llm:
        mock_llm.return_value = (mock_cut_plan, {"model": "test", "latency_s": 0.5})
        
        # Create CutPlanner
        planner = CutPlanner()
        
        # Create context
        ctx = ToolContext(
            questions=questions,
            segments=[],
            prompt="Show satisfaction by region"
        )
        
        # Run the planner
        result = planner.run(ctx)
        
        # Assertions
        assert not result.ok  # Should not be ok because needs user input
        assert result.requires_user_input  # Should require user input
        assert len(result.user_input_options) == 2  # Should have 2 options
        assert result.user_input_options[0]["question_id"] == "Q_OVERALL_SAT"  # Higher confidence first
        assert result.user_input_options[1]["question_id"] == "Q_SUPPORT_SAT"
        
        print("✅ Ambiguity detection test passed!")
        print(f"User input required: {result.requires_user_input}")
        print(f"Options: {[opt['question_id'] for opt in result.user_input_options]}")
        
def test_clear_request():
    """Test that clear requests don't trigger ambiguity."""
    
    # Create clear question (only one NPS question)
    questions = [
        Question(
            question_id="Q_NPS",
            label="How likely are you to recommend our product?",
            type=QuestionType.nps_0_10
        ),
        Question(
            question_id="Q_REGION",
            label="In which region do you live?",
            type=QuestionType.single_choice,
            options=[
                Option(code="NORTH", label="North"),
                Option(code="SOUTH", label="South"),
                Option(code="EAST", label="East"),
                Option(code="WEST", label="West")
            ]
        )
    ]
    
    # Create expected cut
    expected_cut = CutSpec(
        cut_id="cut_nps_by_region",
        metric=MetricSpec(type="nps", question_id="Q_NPS"),
        dimensions=[DimensionSpec(kind="question", id="Q_REGION")],
        filter=None
    )
    
    mock_cut_plan = CutPlanResult(
        ok=True,
        cut=expected_cut,
        resolution_map={"nps": "Q_NPS", "region": "Q_REGION"},
        ambiguity_options=[],
        requires_user_resolution=False,
        errors=[]
    )
    
    # Mock the chat_structured_pydantic function
    with patch('dd_agent.tools.cut_planner.chat_structured_pydantic') as mock_llm:
        mock_llm.return_value = (mock_cut_plan, {"model": "test", "latency_s": 0.5})
        
        # Create CutPlanner
        planner = CutPlanner()
        
        # Create context
        ctx = ToolContext(
            questions=questions,
            segments=[],
            prompt="Show NPS by region"
        )
        
        # Run the planner
        result = planner.run(ctx)
        
        # Assertions
        assert result.ok  # Should be ok
        assert not result.requires_user_input  # Should not require user input
        assert result.data is not None  # Should have a cut
        assert result.data.cut_id == "cut_nps_by_region"
        
        print("Clear request test passed!")
        print(f"Cut ID: {result.data.cut_id}")
        print(f"Metric: {result.data.metric.type} on {result.data.metric.question_id}")

if __name__ == "__main__":
    print("Testing CutPlanner ambiguity resolution...")
    print("=" * 60)
    
    test_ambiguity_detection()
    print()
    test_clear_request()
    
    print("\n" + "=" * 60)
    print("All tests passed!")