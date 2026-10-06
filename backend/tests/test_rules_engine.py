"""
Tests for the Phase 2 Rules Engine.
Pure unit tests (no DB, no HTTP).
"""
import pytest
from decimal import Decimal
from app.rules_engine.engine import translate


def test_translate_fx_only():
    """Test basic currency conversion with no tax or special rounding."""
    res = translate(
        amount=Decimal("100.00"),
        base_currency="USD",
        target_currency="EUR",
        fx_rate=Decimal("0.85"),
        tax_rate=Decimal("0"),
        tax_mode="exclusive",
        rounding_strategy="none",
        psychological_pricing=False,
        rule_set_version="1",
        compliance_note="Test note",
    )
    assert res.translated_amount == Decimal("85.00")
    assert res.tax_label == "No tax applied"
    assert res.regulation_notes == "Test note"
    assert res.rule_set_version == "1"


def test_translate_tax_exclusive():
    """Test tax_mode=exclusive adds tax on top of the converted amount."""
    # 100 * 0.85 = 85.00
    # 85 * 1.20 = 102.00
    res = translate(
        amount=Decimal("100.00"),
        base_currency="USD",
        target_currency="EUR",
        fx_rate=Decimal("0.85"),
        tax_rate=Decimal("20.0"),  # 20%
        tax_mode="exclusive",
        rounding_strategy="none",
        psychological_pricing=False,
        rule_set_version="1",
    )
    assert res.translated_amount == Decimal("102.00")
    assert res.tax_label == "+ 20.0% tax"


def test_translate_tax_inclusive():
    """Test tax_mode=inclusive does not add tax on top; it assumes price is already gross."""
    # 100 * 0.85 = 85.00
    # Inclusive means 85 is the final price shown.
    res = translate(
        amount=Decimal("100.00"),
        base_currency="USD",
        target_currency="EUR",
        fx_rate=Decimal("0.85"),
        tax_rate=Decimal("20.0"),
        tax_mode="inclusive",
        rounding_strategy="none",
        psychological_pricing=False,
        rule_set_version="1",
    )
    assert res.translated_amount == Decimal("85.00")
    assert res.tax_label == "incl. 20.0% tax"


def test_rounding_whole():
    """Test rounding_strategy=whole (rounds to nearest integer)."""
    # 100 * 0.855 = 85.50 -> rounded to 86.00
    res = translate(
        amount=Decimal("100.00"),
        base_currency="USD",
        target_currency="EUR",
        fx_rate=Decimal("0.855"),
        tax_rate=Decimal("0"),
        tax_mode="exclusive",
        rounding_strategy="whole",
        psychological_pricing=False,
        rule_set_version="1",
    )
    assert res.translated_amount == Decimal("86.00")

    # 100 * 0.854 = 85.40 -> rounded to 85.00
    res2 = translate(
        amount=Decimal("100.00"),
        base_currency="USD",
        target_currency="EUR",
        fx_rate=Decimal("0.854"),
        tax_rate=Decimal("0"),
        tax_mode="exclusive",
        rounding_strategy="whole",
        psychological_pricing=False,
        rule_set_version="1",
    )
    assert res2.translated_amount == Decimal("85.00")


def test_rounding_nearest_99():
    """Test rounding_strategy=nearest_99."""
    # 100 * 0.855 = 85.50 -> nearest whole is 86, subtract 0.01 = 85.99
    res = translate(
        amount=Decimal("100.00"),
        base_currency="USD",
        target_currency="EUR",
        fx_rate=Decimal("0.855"),
        tax_rate=Decimal("0"),
        tax_mode="exclusive",
        rounding_strategy="nearest_99",
        psychological_pricing=False,
        rule_set_version="1",
    )
    assert res.translated_amount == Decimal("85.99")


def test_psychological_pricing_override():
    """Test psychological_pricing forces a .99 ending by ceiling."""
    # 34.10 -> 34.99
    res = translate(
        amount=Decimal("34.10"),
        base_currency="USD",
        target_currency="EUR",
        fx_rate=Decimal("1.0"),
        tax_rate=Decimal("0"),
        tax_mode="exclusive",
        rounding_strategy="none",
        psychological_pricing=True,
        rule_set_version="1",
    )
    assert res.translated_amount == Decimal("34.99")

    # 34.90 -> 34.99
    res2 = translate(
        amount=Decimal("34.90"),
        base_currency="USD",
        target_currency="EUR",
        fx_rate=Decimal("1.0"),
        tax_rate=Decimal("0"),
        tax_mode="exclusive",
        rounding_strategy="none",
        psychological_pricing=True,
        rule_set_version="1",
    )
    assert res2.translated_amount == Decimal("34.99")

    # 34.00 -> 33.99
    res3 = translate(
        amount=Decimal("34.00"),
        base_currency="USD",
        target_currency="EUR",
        fx_rate=Decimal("1.0"),
        tax_rate=Decimal("0"),
        tax_mode="exclusive",
        rounding_strategy="none",
        psychological_pricing=True,
        rule_set_version="1",
    )
    assert res3.translated_amount == Decimal("33.99")
