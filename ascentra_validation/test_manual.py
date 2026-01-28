"""Manual testing script"""
from ascentra_agent.orchestrator.agent import Agent
from ascentra_agent.contracts.questions import Question
import pandas as pd
import json

# Load questions
with open('data/demo/questions.json') as f:
    questions_raw = json.load(f)
    questions = [Question.model_validate(q) for q in questions_raw]

# Load responses
responses_df = pd.read_csv('data/demo/responses.csv')

# Create agent
agent = Agent(questions=questions, responses_df=responses_df)

# Test queries
test_queries = [
    "hello",
    "show nps by region",
    "analyze satisfaction",  # Should ask for clarification
    "analyze sat",  # Should also detect (short form)
    "show support",  # Should detect Q_SUPPORT_SAT ambiguity if exists
    "plan",  # Should ask for clarification
    "break down by region",  # Should ask for clarification
    "show Q_NPS by Q_REGION",  # Should work
]

print("=" * 80)
for query in test_queries:
    print(f"\nQuery: {query}")
    print("-" * 80)
    resp = agent.handle_message(query)
    print(f"Success: {resp.success}")
    print(f"Intent: {resp.intent.intent_type}")
    if resp.message:
        print(f"Message:\n{resp.message}")
    if resp.errors:
        print(f"Errors: {resp.errors}")
    print("=" * 80)