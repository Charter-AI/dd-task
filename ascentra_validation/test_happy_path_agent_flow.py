from __future__ import annotations


def test_chat_happy_path(agent) -> None:
    resp = agent.handle_message("hello")
    assert resp.success is True
    assert resp.intent.intent_type == "chat"
    assert resp.message is not None
    assert "stub chat" in resp.message


def test_plan_happy_path(agent) -> None:
    resp = agent.handle_message("create an analysis plan")
    assert resp.success is True
    assert resp.intent.intent_type == "high_level_plan"
    assert resp.message is not None
    assert "Analysis plan:" in resp.message


def test_segment_then_cut_happy_path(agent) -> None:
    seg_resp = agent.handle_message("define segment for something")
    assert seg_resp.success is True
    assert seg_resp.intent.intent_type == "segment_definition"

    cut_resp = agent.handle_message("show a cut")
    assert cut_resp.success is True
    assert cut_resp.intent.intent_type == "cut_analysis"
    assert cut_resp.message is not None

    # Verify readable CutSpec is displayed
    assert "CutSpec:" in cut_resp.message
    assert "Base N:" in cut_resp.message

    # Verify we show a dataframe preview (stringified)
    assert "\n" in cut_resp.message


