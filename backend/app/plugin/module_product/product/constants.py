from enum import IntEnum


class ProductStatus(IntEnum):
    """Product lifecycle used by both Admin and the public Mall projection."""

    ON_SALE = 0
    OFF_SALE = 1


__all__ = ["ProductStatus"]
