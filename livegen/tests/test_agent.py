"""Tests for BPO Service agent."""

import pytest

from src.agent import BPOServiceAgent
from src.models import SessionState, CallMetrics, CallEndReason, CollectedInfo
from src.prompts import SYSTEM_PROMPT, GREETING, SalesPrompts, RetentionPrompts


def test_session_state_defaults():
    """Test SessionState has proper defaults."""
    state = SessionState()
    assert state.session_id == ""
    assert state.caller_id is None


def test_call_metrics_defaults():
    """Test CallMetrics has proper defaults."""
    import time

    metrics = CallMetrics(session_id="test-123", call_start=time.time())
    assert metrics.session_id == "test-123"
    assert metrics.service_type == "support"


def test_service_type_in_metrics():
    """Test service type is tracked in metrics."""
    import time

    metrics = CallMetrics(
        session_id="test", call_start=time.time(), service_type="sales"
    )
    assert metrics.service_type == "sales"


def test_collected_info_defaults():
    """Test CollectedInfo has proper defaults."""
    info = CollectedInfo()
    assert info.phone is None
    assert info.intent is None


def test_call_end_reason():
    """Test CallEndReason enum."""
    assert CallEndReason.COMPLETED.value == "completed"
    assert CallEndReason.ERROR.value == "error"


def test_bpo_agent_support():
    """Test BPO agent for support."""
    agent = BPOServiceAgent(room_sid="test-room", service_type="support")
    assert agent is not None
    assert agent._service_type == "support"


def test_bpo_agent_sales():
    """Test BPO agent for sales."""
    agent = BPOServiceAgent(room_sid="test-room", service_type="sales")
    assert agent._service_type == "sales"
    assert SalesPrompts.GREETING in agent._greeting


def test_bpo_agent_retention():
    """Test BPO agent for retention."""
    agent = BPOServiceAgent(room_sid="test-room", service_type="retention")
    assert agent._service_type == "retention"
    assert RetentionPrompts.GREETING in agent._greeting


def test_sales_prompts():
    """Test sales prompts exist."""
    assert SalesPrompts.GREETING is not None
    assert SalesPrompts.INSTRUCTIONS is not None


def test_retention_prompts():
    """Test retention prompts exist."""
    assert RetentionPrompts.GREETING is not None
    assert RetentionPrompts.INSTRUCTIONS is not None
