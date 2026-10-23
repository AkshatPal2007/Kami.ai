"""
Unit tests for AIService focusing on Demo mode fallback, safety, and rural Hindi responses.
"""

import os
import pytest
from services.ai_service import AIService
from services.scheme_service import SchemeService


@pytest.fixture
def ai_service():
    # Force demo mode by ensuring clean environment
    os.environ.pop("GEMINI_API_KEY", None)
    scheme_service = SchemeService()
    return AIService(scheme_service=scheme_service)


def test_scenario_d_demo_mode_without_api_key(ai_service):
    """
    Scenario D: The app must start without an API key, using a clearly labeled demo fallback.
    """
    assert not ai_service.is_ai_available()
    assert "डेमो मोड" in ai_service.get_current_mode()


def test_scenario_a_crop_damage_flow(ai_service):
    """
    Scenario A: User with crop damage from rain.
    Assistant should recommend PMFBY, highlight 72-hour reporting rule, and ask clarifying questions.
    """
    user_msg = "मेरी फसल बारिश से खराब हो गई है। मुझे सरकारी मदद चाहिए।"
    response = ai_service.process_query(user_msg)

    assert response is not None
    assert response.mode.startswith("⚡") or "डेमो" in response.mode
    assert not response.is_unknown_domain
    assert len(response.recommended_schemes) > 0

    top_scheme = response.recommended_schemes[0]
    assert top_scheme["id"] == "pmfby"

    # Should mention 72 hours
    assert "72 घंटे" in response.reply_hi or any("72 घंटे" in s for s in response.checklist)

    # Should provide checklist
    assert len(response.checklist) >= 3

    # Must include disclaimer
    assert "अंतिम पात्रता" in response.disclaimer_hi


def test_scenario_b_farmer_support_flow(ai_service):
    """
    Scenario B: Farmer asking for government agricultural support.
    Should recommend PM-KISAN / KCC and not guarantee approval.
    """
    user_msg = "मैं किसान हूँ। मुझे खेती के लिए सरकारी सहायता चाहिए।"
    response = ai_service.process_query(user_msg)

    assert response is not None
    assert not response.is_unknown_domain
    matched_ids = [s["id"] for s in response.recommended_schemes]
    assert "pm_kisan" in matched_ids

    # Should have follow-up question
    assert response.follow_up_question_hi is not None
    assert len(response.checklist) >= 3


def test_scenario_c_unknown_domain_flow(ai_service):
    """
    Scenario C: User asks about shop theft or private dispute.
    Assistant should admit knowledge limitations and redirect to myScheme portal.
    """
    user_msg = "मेरी दुकान में रात को चोरी हो गई, मुझे मुआवजा चाहिए।"
    response = ai_service.process_query(user_msg)

    assert response is not None
    assert response.is_unknown_domain is True
    assert "myScheme" in response.reply_hi
    assert len(response.recommended_schemes) == 0
    assert any("myScheme" in step or "FIR" in step for step in response.checklist)
