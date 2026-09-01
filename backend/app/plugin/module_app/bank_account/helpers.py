def mask_card_number(card_last4: str | None) -> str:
    """Return the only card-number representation allowed in business responses."""

    last4 = "".join(char for char in str(card_last4 or "") if char.isdigit())[-4:]
    if len(last4) != 4:
        return "**** **** **** ****"
    return f"**** **** **** {last4}"


__all__ = ["mask_card_number"]
