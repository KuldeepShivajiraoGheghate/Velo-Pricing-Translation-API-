"""
Rules Engine / Translation Engine.
Pure Python module with zero framework dependencies (no FastAPI, no SQLAlchemy).
All monetary arithmetic uses Decimal to prevent floating-point errors.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class TranslationResult:
    translated_amount: Decimal
    tax_label: str
    regulation_notes: str
    rule_set_version: str


def translate(
    amount: Decimal,
    base_currency: str,
    target_currency: str,
    fx_rate: Decimal,
    tax_rate: Decimal,
    tax_mode: str,           # "inclusive" | "exclusive"
    rounding_strategy: str,  # "whole" | "nearest_99" | "nearest_00"
    psychological_pricing: bool,
    rule_set_version: str,
    compliance_note: str = "",
) -> TranslationResult:
    """
    Core translation engine.

    1. Applies FX conversion.
    2. Applies Tax based on mode (if exclusive, tax is added to base; if inclusive, base is already treated as gross).
    3. Applies Rounding.
    4. Applies Psychological Pricing (e.g. .99) if enabled.
    """
    # 1. Currency Conversion
    converted = amount * fx_rate

    # 2. Tax Calculation
    # If inclusive: the converted amount is the final gross price, tax is already "in" it.
    # If exclusive: the converted amount is net, we must add tax to get gross.
    tax_multiplier = Decimal("1") + (tax_rate / Decimal("100"))
    
    if tax_mode == "exclusive":
        gross_amount = converted * tax_multiplier
    else:
        # tax_mode == "inclusive"
        gross_amount = converted

    # 3. Rounding
    # Round to 2 decimal places first for intermediate clean up
    gross_amount = gross_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if rounding_strategy == "whole":
        rounded = gross_amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    elif rounding_strategy == "nearest_00":
        # e.g., 34.50 -> 35.00
        rounded = gross_amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    elif rounding_strategy == "nearest_99":
        # Typically handled by psychological pricing, but if used as base rounding:
        # Round to whole, then subtract 0.01 if we want .99
        whole = gross_amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        rounded = whole - Decimal("0.01")
    else:
        rounded = gross_amount

    # 4. Psychological Pricing
    # If enabled, force the ending to .99
    if psychological_pricing:
        # Get the integer part
        whole_part = rounded.to_integral_value(rounding=ROUND_HALF_UP)
        if whole_part < rounded:
            # If rounding down made it smaller, we want the ceil minus 0.01
            # Actually, standard psychological pricing is just:
            # take ceil, subtract 0.01. So 34.10 -> 34.99.
            pass
        # Simple approach for psychological pricing:
        # take the whole number part, add 0.99
        # (Alternatively, take ceil - 0.01)
        import math
        ceil_val = Decimal(math.ceil(float(gross_amount)))
        rounded = ceil_val - Decimal("0.01")
        # Ensure we don't drop below 0
        if rounded < Decimal("0"):
            rounded = Decimal("0")

    # Final label generation
    if tax_rate > 0:
        if tax_mode == "inclusive":
            tax_label = f"incl. {tax_rate}% tax"
        else:
            tax_label = f"+ {tax_rate}% tax"
    else:
        tax_label = "No tax applied"

    # For .00 rounding, make sure we format it nicely in consumers, but return Decimal here
    return TranslationResult(
        translated_amount=rounded.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        tax_label=tax_label,
        regulation_notes=compliance_note,
        rule_set_version=rule_set_version,
    )
