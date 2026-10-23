"""
Unit tests for AIService focusing on Demo mode fallback, safety, bilingual support (Hindi & English).
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
    assert "डेमो मोड" in ai_service.get_current_mode("hi")
    assert "Demo Mode" in ai_service.get_current_mode("en")


def test_scenario_a_crop_damage_flow_hindi(ai_service):
    """
    Scenario A (Hindi): User with crop damage from rain.
    Assistant should recommend PMFBY, highlight 72-hour reporting rule, and ask clarifying questions.
    """
    user_msg = "मेरी फसल बारिश से खराब हो गई है। मुझे सरकारी मदद चाहिए।"
    response = ai_service.process_query(user_msg, preferred_lang="hi")

    assert response is not None
    assert response.mode.startswith("⚡") or "डेमो" in response.mode
    assert not response.is_unknown_domain
    assert len(response.recommended_schemes) > 0

    top_scheme = response.recommended_schemes[0]
    assert top_scheme["id"] == "pmfby"

    # Should mention 72 hours
    assert "72 घंटे" in response.reply_hi or any("72 घंटे" in s for s in response.checklist_hi)
    assert len(response.checklist) >= 3
    assert "अंतिम पात्रता" in response.disclaimer_hi


def test_scenario_a_crop_damage_flow_english(ai_service):
    """
    Scenario A (English): "My crop was damaged by heavy rainfall. I need government assistance."
    """
    user_msg = "My crop was damaged by heavy rainfall. I need government assistance."
    response = ai_service.process_query(user_msg, preferred_lang="en")

    assert response is not None
    assert not response.is_unknown_domain
    assert len(response.recommended_schemes) > 0
    top_scheme = response.recommended_schemes[0]
    assert top_scheme["id"] == "pmfby"

    # Should mention 72 hours in English
    assert "72 hour" in response.reply_en.lower() or any("72 hour" in s.lower() for s in response.checklist_en)
    assert len(response.checklist_en) >= 3
    assert "advisory guidance" in response.disclaimer_en.lower()


def test_scenario_b_farmer_support_flow_english(ai_service):
    """
    Scenario B (English): "I am a farmer. I need government assistance for farming."
    """
    user_msg = "I am a farmer. I need government assistance for farming."
    response = ai_service.process_query(user_msg, preferred_lang="en")

    assert response is not None
    assert not response.is_unknown_domain
    matched_ids = [s["id"] for s in response.recommended_schemes]
    assert "pm_kisan" in matched_ids
    assert response.follow_up_question_en is not None
    assert len(response.checklist_en) >= 3


def test_scenario_c_unknown_domain_flow_english(ai_service):
    """
    Scenario C (English): "My shop was burglarized, I need compensation."
    """
    user_msg = "My shop was burglarized, I need compensation."
    response = ai_service.process_query(user_msg, preferred_lang="en")

    assert response is not None
    assert response.is_unknown_domain is True
    assert "myScheme" in response.reply_en
    assert len(response.recommended_schemes) == 0
    assert any("myScheme" in step or "FIR" in step for step in response.checklist_en)


def test_scenario_c_unknown_domain_flow_hindi(ai_service):
    user_msg = "मेरी दुकान में रात को चोरी हो गई, मुझे मुआवजा चाहिए।"
    response = ai_service.process_query(user_msg, preferred_lang="hi")

    assert response is not None
    assert response.is_unknown_domain is True
    assert "myScheme" in response.reply_hi
    assert len(response.recommended_schemes) == 0
    assert any("myScheme" in step or "FIR" in step for step in response.checklist_hi)
