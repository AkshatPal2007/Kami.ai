"""
Unit tests for SchemeService: data loading, search heuristics, and eligibility assessment.
"""

import os
import pytest
from services.scheme_service import SchemeService


@pytest.fixture
def service():
    return SchemeService()


def test_schemes_loaded(service):
    schemes = service.get_all_schemes()
    assert len(schemes) >= 2
    scheme_ids = [s["id"] for s in schemes]
    assert "pm_kisan" in scheme_ids
    assert "pmfby" in scheme_ids


def test_myscheme_portal_loaded(service):
    portal = service.get_myscheme_info()
    assert "official_url" in portal
    assert "myscheme.gov.in" in portal["official_url"]


def test_scenario_a_crop_damage_search(service):
    """
    Scenario A: "मेरी फसल बारिश से खराब हो गई है। मुझे सरकारी मदद चाहिए।"
    Must rank PMFBY at the top.
    """
    query = "मेरी फसल बारिश से खराब हो गई है। मुझे सरकारी मदद चाहिए।"
    results = service.search_schemes(query)
    assert len(results) > 0
    top_scheme, score = results[0]
    assert top_scheme["id"] == "pmfby"
    assert score > 0


def test_scenario_b_farmer_support_search(service):
    """
    Scenario B: "मैं किसान हूँ। मुझे खेती के लिए सरकारी सहायता चाहिए।"
    Must find PM-KISAN.
    """
    query = "मैं किसान हूँ। मुझे खेती के लिए सरकारी सहायता चाहिए।"
    results = service.search_schemes(query)
    assert len(results) > 0
    matched_ids = [r[0]["id"] for r in results]
    assert "pm_kisan" in matched_ids


def test_scenario_c_unknown_problem(service):
    """
    Scenario C: An unrelated query such as shop theft should not falsely match farming schemes with high score.
    """
    query = "मेरी दुकान में रात को चोरी हो गई है और गहने गायब हैं।"
    results = service.search_schemes(query)
    # Either empty or negligible score
    if results:
        top_scheme, score = results[0]
        assert score < 3.0


def test_pm_kisan_eligibility_assessment(service):
    pm_kisan = service.get_scheme_by_id("pm_kisan")
    assert pm_kisan is not None

    # Case 1: Landowner, has Aadhaar, not taxpayer -> potentially eligible
    facts = {"is_landowner": True, "has_aadhaar": True, "is_taxpayer": False}
    assessment = service.assess_eligibility(pm_kisan, facts)
    assert assessment["status"] == "potentially_eligible"
    assert len(assessment["reasons_hi"]) > 0

    # Case 2: Taxpayer -> apparently ineligible
    taxpayer_facts = {"is_landowner": True, "is_taxpayer": True}
    assessment_ineligible = service.assess_eligibility(pm_kisan, taxpayer_facts)
    assert assessment_ineligible["status"] == "apparently_ineligible"

    # Case 3: Insufficient info
    empty_facts = {}
    assessment_empty = service.assess_eligibility(pm_kisan, empty_facts)
    assert assessment_empty["status"] == "insufficient_information"
    assert len(assessment_empty["missing_info_hi"]) > 0


def test_pmfby_72_hour_rule(service):
    pmfby = service.get_scheme_by_id("pmfby")
    assert pmfby is not None

    # Check 72 hour requirement exists in eligibility text
    eligibility_str = " ".join(pmfby["eligibility_hi"])
    assert "72 घंटे" in eligibility_str
