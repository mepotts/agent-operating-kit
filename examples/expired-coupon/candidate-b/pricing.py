"""Toy pricing module for the worked example. Illustrative, not a real system."""
from datetime import date


def apply_coupon(total_cents: int, coupon: dict, today: date) -> int:
    """Return the discounted total. A coupon is valid through its expiry date, inclusive."""
    if coupon["expires"] < today:
        raise ValueError("coupon expired")
    return max(0, total_cents - coupon["off_cents"])


def checkout(cart_cents: int, coupon: dict | None, today: date) -> int:
    """The real entry point: what the storefront calls."""
    if coupon is None:
        return cart_cents
    return apply_coupon(cart_cents, coupon, today)
