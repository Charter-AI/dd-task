## Ascentra Survey Analytics Agent (Candidate README)

### What this repository is

This repository is a minimal but working "survey analytics agent" used in consulting due diligence workflows.
Consultants need to ask questions like:

- "Show NPS by region"
- "Define a segment of enterprise customers and compare satisfaction"
- "What is the distribution of plan types?"

The system aims to translate these natural language requests into **structured analysis specifications** and then compute results **deterministically** from the dataset.

### What success looks like

When a user asks a question, the agent should:

- **Understand intent**: decide whether the user is chatting, asking for a plan, defining a segment, or requesting an analysis cut.
- **Avoid assumptions**: if the request is ambiguous or underspecified, ask a clarification question rather than guessing.
- **Produce structured objects**: represent "what to compute" as explicit domain objects (cuts, segments, filters).
- **Compute numbers deterministically**: all metrics and tables are computed in Python, not by the LLM.
- **Remain safe and helpful**: never crash, never show stack traces, never leak internal errors to the user.

---

## Core principles (why this design matters for consultants)

### 1) Separation of concerns (semantic planning vs deterministic computation)

We split the system into two responsibilities:

- **LLM responsibilities**: interpret user intent and propose structured specs (for example, a `CutSpec` or `SegmentSpec`).
- **Python responsibilities**: execute those specs against survey data with a deterministic engine (Pandas).

Why this matters for users:

- Consultants need answers they can trust and reproduce.
- If a number changes between runs, it destroys confidence and slows down decisions.
- Deterministic execution means the same spec and dataset always yield the same results.

Example:

- User: "Show NPS by region"
- LLM: proposes a `CutSpec` describing metric `nps` on `Q_NPS` with dimension `Q_REGION`
- Engine: computes NPS and base sizes per region deterministically

### 2) Structured objects control the data flow

Natural language is flexible but ambiguous.
Structured domain objects give you control over what the system is allowed to do.

In this repo, the important objects are:

- `Question`: describes what columns exist and how to interpret them
- `CutSpec`: describes an analysis cut (metric, question, dimensions, optional filter)
- `SegmentSpec`: describes a segment (a named filter expression)
- Filter AST nodes: `PredicateEq`, `PredicateIn`, `PredicateRange`, logical `And`/`Or`/`Not`, etc.

Why this matters for users:

- It prevents the LLM from "hand-waving" an answer.
- It allows deterministic validation of requests before execution.
- It makes analysis auditable: you can show the user exactly what was computed.

Example: collision between a command and a question ID

- The dataset contains a question `Q_PLAN` ("Which plan are you on?")
- The system also supports a high-level "analysis plan" tool
- User: "Analyse plan"

An agent that guesses will sometimes do the wrong thing.
A well-designed agent treats this as ambiguous, asks a question, and only proceeds after clarification.

### 3) Deterministic flow of analysis

The numbers must come from the data, not from the LLM.
The LLM proposes what to compute, but the engine computes the result.

Why this matters for users:

- The system should behave like a calculator with a natural language interface.
- Consultants must be able to rerun the same analysis and get the same table.

### 4) The agent should never assume what the user wants

An LLM will often try to be helpful by "making something work" even when the request is invalid.
That is dangerous in analytics.

Bad example (silent correction risk):

- User: "Show gender distribution while filtering for Age = UK"
- Age is numeric and UK is not a valid age.
- A naive system might silently change the filter to Region = UK (or something else) to avoid failing.

Correct behavior:

- Do not execute.
- Ask a clarification question or explain what is invalid and offer valid alternatives.

---

## How the system works (end to end)

At a high level, one chat turn should follow this flow:

1. Load dataset context (`questions.json`, `responses.csv`)
2. Classify the user message intent (chat vs plan vs segment vs cut)
3. If the request is ambiguous or underspecified:
   - ask a clarification question
   - do not create objects
   - do not execute analysis
4. If the request is a segment definition:
   - build a `SegmentSpec` (filter AST)
   - validate it deterministically (candidate work)
   - store it in memory for later cuts
5. If the request is a cut:
   - build a `CutSpec`
   - validate it deterministically (candidate work)
   - execute it via the pandas engine
6. Format a user-facing response:
   - include the computed base size
   - include a readable rendering of the `CutSpec`
   - include a preview of the table

---

## Repository layout (where to look first)

### The Ascentra agent (the area you will work in)

- `src/ascentra_agent/cli.py`
  - CLI entrypoint and chat loop (`uv run ascentra chat`)
- `src/ascentra_agent/orchestrator/agent.py`
  - The core routing logic
  - Where ambiguity handling, retries, and safe error handling should live
- `src/ascentra_agent/tools/`
  - LLM-backed tools and routing logic
  - `intent_classifier.py` is the first step in the task
  - `cut_planner.py`, `segment_builder.py`, `high_level_planner.py`, `chat_responder.py`
- `src/ascentra_agent/contracts/`
  - Typed domain objects for questions, cuts, segments, filters
  - This is where deterministic validation can be implemented
- `src/ascentra_agent/engine/`
  - Deterministic execution engine (Pandas)
  - This is intentionally not the focus of the task
- `src/ascentra_agent/llm/`
  - Azure OpenAI client and structured output helper
  - Prompt templates are under `src/ascentra_agent/llm/prompts/`

### Validation suites (how you measure progress)

The `ascentra_validation/` folder contains stepwise tests that guide development:

- `ascentra_validation/test_intent_classifier.py`
  - Step 1: improve intent classification using the question catalog
- `ascentra_validation/test_ambiguity_handling.py`
  - Step 2: detect ambiguity and ask clarifying questions, do not assume
- `ascentra_validation/test_invalid_requests_no_artifacts.py`
  - Step 3a: invalid requests must not create objects or execute
- `ascentra_validation/test_graceful_failure_handling.py`
  - Step 3b: invalid requests must not leak internal errors or crash

---

## How to run

### Run the chat CLI

```bash
uv run ascentra chat --data data/demo
```

Type `quit` to exit.

### Run the validation suites

The repo uses `uv`. To run the validation tests without installing dev dependencies:

```bash
uv run pytest ascentra_validation/test_intent_classifier.py
```

You can swap the filename to run each step's test suite.

---

## Candidate guidance

More detailed task iinstructions and goals and be found in `TASK.md`

### Where to start

Start with:

- `src/ascentra_agent/tools/intent_classifier.py`
- `src/ascentra_agent/orchestrator/agent.py`
- `data/demo/questions.json` (to understand the catalog you need to ground to)

### Constraints to keep in mind

- Prefer deterministic validation of structured objects over prompt-only rules.
- Do not assume user intent when multiple interpretations exist.
- Keep the system safe and conversational even when requests are invalid.

### Suggested extension ideas (after the required steps)

If you finish the required steps early, strong extensions include:

- Better grounding from user phrases to question IDs and option codes (lightweight search or ranking)
- A retry strategy when tool outputs fail validation (with error context)
- Simple tracing: an internal per-turn record of tool calls and outcomes (without forcing any specific architecture)
- Scaling prompts: avoid dumping the full question catalog when it is large by retrieving relevant questions first


