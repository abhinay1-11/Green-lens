import pytest
from app.utils.confidence import normalize_confidence, format_confidence_percentage

def test_confidence_required_values():
    assert normalize_confidence(0.0) == 0.0
    assert normalize_confidence(0.25) == 0.25
    assert normalize_confidence(0.50) == 0.50
    assert normalize_confidence(0.87) == 0.87
    assert normalize_confidence(0.99) == 0.99
    assert normalize_confidence(1.0) == 1.0

def test_confidence_formatting():
    assert format_confidence_percentage(0.0) == "0%"
    assert format_confidence_percentage(0.25) == "25%"
    assert format_confidence_percentage(0.50) == "50%"
    assert format_confidence_percentage(0.87) == "87%"
    assert format_confidence_percentage(0.99) == "99%"
    assert format_confidence_percentage(1.0) == "100%"

def test_confidence_bounds_clamping():
    assert normalize_confidence(1.5) == 1.0
    assert normalize_confidence(-0.5) == 0.0
