"""Quaternion-monoid algebra: compositional algebra over fixed-width
quaternionic-symbolic state packets."""

from .algebra import (
    Packet,
    packet_product,
    identity_packet,
    packet_power,
    hamilton_product,
    normalize_quaternion,
)

__all__ = [
    "Packet",
    "packet_product",
    "identity_packet",
    "packet_power",
    "hamilton_product",
    "normalize_quaternion",
]
__version__ = "0.1.0"
