# DD Analytics Agent - Technical Challenge 🚀

This is a technical assessment for candidates applying for Senior/Staff AI Engineer roles. It involves completing the implementation of a production-grade analytics agent skeleton.

## 🎯 The Challenge

The objective is to "bring to life" a Planning Analytics Agent. While we have provided the deterministic foundation (engine, validation, contracts), the **agentic orchestration** and **tool logic** are stubbed out for you to implement.

**Please see [TASK.md](./TASK.md) for full instructions and success criteria.**


### Key Principles

1. **LLM does planning + specification**, not computation
2. **All outputs are typed contracts** validated before execution
3. **Execution is deterministic** - same specs always produce same results
4. **Full traceability** - every run saves all artifacts

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Azure OpenAI access (or mock for testing)

### Installation

```bash
# Clone and navigate to the project
cd dd-task

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your Azure OpenAI credentials
```

### Configuration

Create a `.env` file with your Azure OpenAI credentials:

```bash
AZURE_OPENAI_ENDPOINT=https://YOUR_RESOURCE_NAME.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=YOUR_MODEL_DEPLOYMENT_NAME
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

### Running the Demo

```bash
# Run the demo with the sample dataset
dd-agent demo

# Or run a specific analysis
dd-agent run --data data/demo --prompt "Show NPS by region"

# Run the full autoplan flow
dd-agent autoplan --data data/demo

# Validate your data directory
dd-agent validate --data data/demo

# Run interactive query
dd-agent interactive --data data/demo
```

## 📁 Project Structure

```
dd-agent/
├── src/dd_agent/
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Configuration (Azure OpenAI settings)
│   ├── run_store.py        # Run artifact storage
│   │
│   ├── contracts/          # Pydantic models (typed contracts)
│   │   ├── questions.py    # Question, Option, QuestionType
│   │   ├── filters.py      # Boolean expression AST
│   │   ├── specs.py        # CutSpec, SegmentSpec, MetricSpec
│   │   ├── tool_output.py  # ToolOutput envelope
│   │   └── validate.py     # Domain validators (strict)
│   │
│   ├── engine/             # Deterministic execution
│   │   ├── masks.py        # Filter → boolean mask
│   │   ├── metrics.py      # Metric computations
│   │   ├── tables.py       # Table result models
│   │   └── executor.py     # Main executor
│   │
│   ├── llm/                # LLM integration
│   │   ├── azure_client.py # AzureOpenAI wrapper
│   │   ├── structured.py   # Structured outputs helpers
│   │   └── prompts/        # Prompt templates
│   │
│   ├── tools/              # LLM-powered tools
│   │   ├── base.py         # Tool base class
│   │   ├── high_level_planner.py
│   │   ├── cut_planner.py
│   │   └── segment_builder.py
│   │
│   ├── orchestrator/       # Pipeline coordination
│   │   ├── agent.py        # Agent class
│   │   └── pipeline.py     # Pipeline flows
│   │
│   └── util/               # Utilities
│       ├── hashing.py      # Dataset hashing
│       ├── logging.py      # Structured logging
│       └── jsonschema.py   # JSON schema helpers
│
├── data/demo/              # Demo dataset
│   ├── questions.json
│   ├── responses.csv
│   ├── scope.md
│   └── eval_cases.yaml
│
├── tests/                  # Test suite
│   ├── test_metrics.py
│   ├── test_validation.py
│   └── test_end_to_end_mock_llm.py
│
├── pyproject.toml
├── .env.example
└── README.md
```

## 🔧 Architecture

### Design Patterns

**Ports & Adapters (Hexagonal Architecture)**
- Core domain logic is isolated from the LLM provider
- LLM backend is an adapter: can swap AzureOpenAI ↔ mock without touching core logic

**Typed Contracts + JSON Schema**
- All domain objects are Pydantic models
- LLM outputs use Structured Outputs for guaranteed schema compliance

**Tool Interface with Standard Envelope**
Every tool returns:
```python
ToolOutput[T]:
    ok: bool
    data: T | None
    errors: list[ToolMessage]
    warnings: list[ToolMessage]
    trace: dict  # prompts, model, latency, mappings
```

### Data Flow

```
Input Files                 LLM Tools                 Executor              Output
─────────────              ──────────                ──────────            ────────
questions.json  ──┐
responses.csv   ──┼──▶  High-Level Planner ──▶ Cut Planner ──▶ Executor ──▶ Tables
scope.md        ──┘          │                      │              │        Report
                             ▼                      ▼              ▼
                      AnalysisIntents ────▶ CutSpecs (validated) ──▶ Results
```

## 📊 Contracts

### Question Types
- `single_choice` - Single selection from options
- `multi_choice` - Multiple selections (semicolon-separated)
- `likert_1_5` - 5-point Likert scale
- `likert_1_7` - 7-point Likert scale
- `numeric` - Numeric values
- `nps_0_10` - Net Promoter Score (0-10)

### Metric Types
| Metric | Compatible Types |
|--------|------------------|
| `frequency` | single_choice, multi_choice, likert, nps |
| `mean` | likert, numeric, nps |
| `top2box` | likert_1_5, likert_1_7 |
| `bottom2box` | likert_1_5, likert_1_7 |
| `nps` | nps_0_10 only |

### Filter Expression AST
```python
# Predicates
PredicateEq(question_id="Q1", value="option_a")
PredicateIn(question_id="Q1", values=["a", "b", "c"])
PredicateRange(question_id="Q1", min=18, max=65)
PredicateContainsAny(question_id="Q1", values=["x", "y"])  # multi-choice

# Logical Operators
And(children=[...])
Or(children=[...])
Not(child=...)
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_metrics.py -v
pytest tests/test_validation.py -v
pytest tests/test_end_to_end_mock_llm.py -v

# Run with coverage
pytest tests/ --cov=dd_agent --cov-report=html
```

### Test Categories

1. **Unit tests (no LLM)** - Metrics and validation
2. **End-to-end tests (mock LLM)** - Full pipeline with deterministic mocks
3. **Evaluation cases** - `eval_cases.yaml` for regression testing

## 📦 Run Artifacts

Each run creates a directory:
```
runs/<timestamp>_<id>/
├── inputs/
│   ├── questions.json
│   ├── responses.csv
│   └── user_prompt.txt
├── artifacts/
│   ├── high_level_plan.json
│   ├── cuts.json
│   ├── results.json
│   └── table_*.json
├── metadata.json
└── report.md
```

## 🚧 Production Hardening Notes

This skeleton is designed for local development. For production:

- **Authentication**: Use Entra ID instead of API keys
- **Caching**: Add prompt/result caching by hash
- **Observability**: Structured logs, per-tool latency, error rates
- **Safety**: PII scanning + redaction before LLM calls
- **Evals**: Expand `eval/` into regression tests

## 📝 License

MIT License
