## Ascentra validation suite (happy path)

This directory contains a deterministic validation suite for the Ascentra MVP agent.

Goals:
- Verify intent recognition (chat, high_level_plan, segment_definition, cut_analysis)
- Verify happy-path end to end flow:
  - create a segment (in-memory)
  - plan a cut (stubbed)
  - execute cut with pandas engine
  - display response including:
    - human readable CutSpec
    - Base N
    - dataframe preview
- Verify ambiguity handling (expected to fail until implemented):
  - ambiguous/underspecified queries must not trigger planning/execution tools
  - agent should ask a clarification question instead of guessing

Non-goals:
- No live Azure OpenAI calls
- No ambiguity handling
- No retry loops
- No persistence or artifacts

### How to run

From repo root:

```bash
uv run --with pytest pytest -q ascentra_validation
```

To run only the ambiguity-focused checks:

```bash
uv run --with pytest pytest -q ascentra_validation/test_ambiguity_handling.py
```

### Notes

The tests stub the LLM-dependent tools (HighLevelPlanner, SegmentBuilder, CutPlanner, ChatResponder).
This keeps the suite stable while the candidate refines intent classification logic.


