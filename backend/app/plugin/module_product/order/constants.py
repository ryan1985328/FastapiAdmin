from enum import Enum


class ProductOrderStatus(str, Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


__all__ = ["ProductOrderStatus"]
