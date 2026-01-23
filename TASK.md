### Task V2: Ascentra Survey Analytics Agent (4 hour technical)

This task uses `src/ascentra_agent/` as a starting point for building a production minded analytics agent.

The goal is not to build a chat app. The chat loop, tools, contracts, and deterministic pandas engine already exist.
Your goal is to improve agent behavior so that consultants can trust it in real due diligence workflows.

You will be evaluated on:

- Correctness of routing and behavior on happy paths
- Safety and predictability (no guessing, no silent correction, no internal error leakage)
- Deterministic validation (moving rules from prompts into code where possible)
- Engineering judgment, clarity, and trade-offs

---

### Deliverables (required)

You must produce:

- **Working code changes** in `src/ascentra_agent/`
- **`explanation.md`** (required even if you only complete the required steps)
  - what you changed and why
  - what you intentionally did not do and why
  - the biggest risks you see in the current approach
  - what you would do next with more time

The goal is to assess how you reason about agent behavior, reliability, and product safety, not just whether you can make tests pass.

---

### Assessment criteria

We are evaluating whether you can build a reliable, user trustworthy analytics agent, not whether you can build a demo chatbot. In due diligence, the key requirement is trust: users must be able to rely on outputs, understand what was computed, and avoid silent mistakes.

#### 1) Correct routing and intent handling

- Correctly routes common user requests to the right behavior: chat vs plan vs segment vs cut.
- Does not over-trigger tools on conversational inputs (hello, help, etc.).
- Uses the question catalog (`questions.json`) rather than brittle keyword rules.

#### 2) No assumptions: ambiguity and underspecification

- Detects ambiguous requests (for example collisions like "plan" vs `Q_PLAN`, or "satisfaction" across multiple questions).
- Detects underspecified requests (for example "create a cut" without a target question).
- Asks clarification questions and does not execute analysis until clarified.

#### 3) Deterministic validation (code driven, not prompt driven)

- Prevents invalid objects from being created or executed:
  - unknown question IDs
  - incompatible metric/question combinations
  - invalid filter operations for a question type
  - invalid option codes (for example `Q_REGION = SOUTHEAST`)
- Validation behavior is deterministic and explainable.

#### 4) Safety and UX continuity (consultant friendly)

- The agent never crashes and never leaks internal errors to the user.
- Responses remain helpful even when refusing a request (ask clarifying questions or suggest alternatives).
- The agent does not silently "correct" the user's request to make it executable.

#### 5) Deterministic analysis execution

- Computation is performed by Python, not the LLM.
- Outputs are reproducible: the same validated spec on the same dataset yields the same result.

#### 6) Engineering quality and reasoning

- Clear structure and readable code changes.
- Sensible boundaries between orchestration, validation, and execution.
- `explanation.md` clearly describes what you did, trade-offs, and next steps.

#### 7) Progress against the validation suites (guidance, not a hard requirement)

We provide stepwise suites in `ascentra_validation/` to guide you.
A strong submission typically shows meaningful progress across:

- intent classification
- ambiguity handling
- invalid request handling (no artifacts)
- graceful failure UX safety

We do not expect everything to pass, but we expect you to be deliberate about what you chose to prioritize and why.

#### 8) Extensions (bonus)

If time allows, we reward thoughtful extensions that improve reliability or usability, such as:

- bounded retry loops with validation context
- retrieval of relevant questions instead of dumping the full catalog
- caching, sessions, tracing/event logs
- better grounding from phrases to question IDs and option codes

---

### Mental model (how this system should work)

This system separates responsibilities:

- The LLM is used for semantic interpretation: mapping user language into structured specifications.
- Python executes those specifications deterministically, producing reproducible numerical results.

### Step 1: Improve intent classification (dynamic, grounded)

#### What you are building

Given a user message, decide which high level behavior is required:

- `chat`: user is conversing or asking meta questions
- `high_level_plan`: user wants a plan of analyses
- `segment_definition`: user wants to define a segment or filter
- `cut_analysis`: user wants a concrete analysis

#### Why it matters for consultants

Consultants do not know your internal tool names.
They speak in business language and shorthand.
If the agent routes to the wrong tool, the system feels unpredictable and untrustworthy.

#### Where to look

- `src/ascentra_agent/tools/intent_classifier.py`
- `src/ascentra_agent/tools/base.py` (tool context includes the question catalog)
- `data/demo/questions.json` (the catalog you should ground to)

#### What to implement

Make the classifier more dynamic than keyword matching.
At minimum, it should:

- Recognize question IDs like `Q_PLAN`, `Q_GENDER`, `Q_NPS`
- Recognize question labels like "Region", "Overall Satisfaction"
- Avoid false positives where words like "plan" are used conversationally

#### How to validate

- `ascentra_validation/test_intent_classifier.py`

---

### Step 2: Clarification and ambiguity handling (agent level)

#### What you are building

Detect when a user message could reasonably mean multiple things and ask a clarifying question before calling tools.

Examples:

- "Analyse plan" could mean "create an analysis plan" or analyze the `Q_PLAN` question.
- "Satisfaction" could refer to multiple satisfaction questions (overall vs support).
- "Create a cut" is a syntactically valid request but underspecified.

#### Why it matters for consultants

When the agent guesses, it wastes time and can create incorrect conclusions.
In due diligence, the cost of a wrong assumption is high.

#### Where to look

- `src/ascentra_agent/orchestrator/agent.py` (this is where clarification should be orchestrated)
- `src/ascentra_agent/tools/intent_classifier.py`

#### What to implement

Implement an explicit clarification flow at the agent level:

- If ambiguous, ask a clarification question and do not call planner tools.
- If the user responds with a selection, continue with the intended action.
- Do not create cut or plan objects until clarification is resolved.

#### How to validate

- `ascentra_validation/test_ambiguity_handling.py`

---

### Step 3a: Validation and no artifacts for invalid requests

#### What you are building

When a request is invalid, the system should refuse to create or execute analysis objects.
The important part is determinism: validation should be code driven, not prompt driven.

Invalid examples (based on the demo dataset):

- Invalid ID in cut dimension: "Cut QUNKNOWN"
- Invalid metric compatibility: "mean gender"
- Unsupported metric: "median age"
- Invalid ID in filter: "UNKNOWN = 10"
- Invalid filter operation: "Region > North"
- Invalid filter criteria: "Region = SOUTHEAST"

Also repeat the same invalid filter patterns for segments.

#### Why it matters for consultants

LLMs often try to be helpful by silently rewriting the user request.
That is dangerous in analytics. If the user asked for `UNKNOWN`, the agent must not quietly switch to `Q_REGION`.

#### Where to look

- `src/ascentra_agent/contracts/` (best place for deterministic validation rules)
- `src/ascentra_agent/orchestrator/agent.py` (policy: validate before execute)
- `src/ascentra_agent/engine/` (execution should only accept validated specs)

#### What to implement

Add deterministic validation checks that prevent:

- Creating invalid `CutSpec` or `SegmentSpec` objects
- Executing invalid cuts

You can choose the validation layer:

- Validate at object creation time (preferred for determinism), or
- Validate before execution in the orchestrator

#### How to validate

- `ascentra_validation/test_invalid_requests_no_artifacts.py`

This suite is focused on artifact behavior, not message wording.

---

### Step 3b: Graceful error handling and UX safety

#### What you are building

Even when a request is invalid or a tool fails schema validation, the agent should:

- Not crash
- Return a user facing message
- Avoid leaking stack traces, exception class names, or internal payload dumps

#### Why it matters for consultants

Consultants need a system that feels like a product.
Internal exceptions and raw validation errors destroy trust and slow down adoption.

#### Where to look

- `src/ascentra_agent/orchestrator/agent.py` (top level try/except policy)
- `src/ascentra_agent/tools/*` (tool failure behavior)

#### What to implement

Introduce a safe failure policy:

- Catch unexpected exceptions at the top level of a turn.
- Convert them into a safe response that asks a clarifying question or suggests a valid alternative.
- Keep internal diagnostics out of the user message.

If you implement retries, ensure they are bounded and explainable.

#### How to validate

- `ascentra_validation/test_graceful_failure_handling.py`

---

### After required steps: choose an extension (2 to 2.5 hours)

Pick one extension that improves real world usefulness. Your goal is to strengthen reliability, usability, and trust in the face of ambiguity and LLM unpredictability.

Below are some suggestions, but you are welcome to come up with your own

### Retry strategy when tool outputs fail validation

**What it is:** If the LLM outputs a spec that fails deterministic validation, retry planning with clear error context (for example “metric mean is not compatible with single_choice question Q_GENDER”).

**Why it matters:** Real users will not phrase requests in the exact way your prompts expect. A bounded retry loop improves robustness without sacrificing determinism, as long as validation remains code driven and execution is still gated by passing validation.

### Lightweight retrieval for relevant questions (prompt scaling)

**What it is:** Instead of dumping the full `questions.json` into the prompt every time, retrieve a small subset of relevant questions and options based on the user message (simple keyword match, ranking, or embedding search).

**Why it matters:** This is a practical scaling issue. Larger surveys and consulting datasets will not fit comfortably in the context window. Retrieval also reduces noise, which improves grounding and reduces hallucinated IDs.

### Better grounding from user terms to question IDs and option codes

**What it is:** Improve mapping from user words to question IDs and option codes (for example “North” to `Q_REGION = NORTH`, “plan” to `Q_PLAN`). This can be done with heuristics, ranking, or a small matching index.

**Why it matters:** Grounding is the bridge between semantic language and deterministic execution. Better grounding reduces the need for clarification while keeping the system faithful to what the user asked.

### Request and response caching

**What it is:** Cache intermediate and final results keyed by deterministic inputs (for example dataset hash + validated `CutSpec` and `SegmentSpec` set). Cache either LLM tool outputs, engine results, or both.

**Why it matters:** Consulting workflows repeat the same analyses across sessions and stakeholders. Caching reduces latency and cost, and it improves user experience. It also reduces repeated LLM calls, which reduces variance.

### Data permanence and sessions

**What it is:** Persist conversation state and artifacts such as created segments and prior cuts, so users can resume, reference previous work, and build analyses iteratively.

**Why it matters:** Consultants work in sessions. They define segments once and reuse them across many cuts. Persistence makes the agent behave like an analysis tool, not a stateless chatbot.

### Turn level tracing (event log)

**What it is:** Add per turn tracing that records tool calls, validation outcomes, and decisions in a structured form (for example an event list). This can be printed to console, stored to disk, or both.

**Why it matters:** In agentic systems, debugging is a product feature. Traceability makes it easier to understand why an answer was produced, and it makes the system safer because failures can be investigated rather than guessed.

Your extension must be explained in `explanation.md`:

- What you built
- Why it matters for users
- Key trade-offs and known limitations
- What you would do next with more time

Your extension should be explained in an `explanation.md` style write-up:

- What you built
- Why it matters for users
- What you would do next with more time


