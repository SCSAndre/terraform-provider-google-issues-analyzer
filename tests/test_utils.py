"""Tests for utility functions."""

from terraform_issues_analyzer.utils import extract_label_names, extract_label_names_lower, has_label

def test_extract_label_names_handles_dicts():
    labels = [{"name": "bug"}, {"name": "enhancement "}, {"other": "value"}]
    assert extract_label_names(labels) == ["bug", "enhancement"]

def test_extract_label_names_handles_strings():
    labels = ["bug ", " enhancement"]
    assert extract_label_names(labels) == ["bug", "enhancement"]

def test_extract_label_names_handles_mixed():
    labels = [{"name": "bug"}, "enhancement", None, 123]
    assert extract_label_names(labels) == ["bug", "enhancement"]

def test_extract_label_names_handles_empty():
    assert extract_label_names([]) == []
    assert extract_label_names(None) == []

def test_extract_label_names_lower():
    labels = [{"name": "Bug"}, "Enhancement "]
    assert extract_label_names_lower(labels) == ["bug", "enhancement"]

def test_has_label_case_insensitive():
    labels = [{"name": "BUG-FIX"}, "Feature"]
    assert has_label(labels, "bug-fix")
    assert has_label(labels, "feature")
    assert not has_label(labels, "enhancement")
