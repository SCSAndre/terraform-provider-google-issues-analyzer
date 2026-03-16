"""Tests for service scope definitions."""

from service_definitions import (
    get_critical_keywords,
    get_service_terms,
    get_supported_service_categories,
)


def test_supported_categories_are_cloud_armor_only() -> None:
    """Service scope must remain Cloud Armor-only for phase-1 architecture split."""
    assert get_supported_service_categories() == ["Cloud Armor"]


def test_service_terms_are_cloud_armor_only() -> None:
    """Expanded service terms should expose a single Cloud Armor category."""
    terms = get_service_terms()
    assert list(terms.keys()) == ["Cloud Armor"]
    assert "cloud armor" in " ".join(terms["Cloud Armor"]).lower()


def test_critical_keywords_are_cloud_armor_only() -> None:
    """Critical keywords should expose a single Cloud Armor category."""
    keywords = get_critical_keywords()
    assert list(keywords.keys()) == ["Cloud Armor"]
    assert "cloud armor" in " ".join(keywords["Cloud Armor"]).lower()

