def shipping_fee(amount):
    """Return shipping fee in KRW for a non-negative integer subtotal."""
    if amount < 0:
        raise ValueError("amount must be non-negative")
    return 0 if amount >= 30000 else 3000
