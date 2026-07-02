"""Quaternion-monoid algebra: compositional algebra over fixed-width
quaternionic-symbolic state packets."""

from .algebra import (
    Packet,
    packet_product,
    identity_packet,
    packet_power,
    compose,
    hamilton_product,
    normalize_quaternion,
    make_xor_table,
    validate_monoid_table,
)
from .batch import (
    PacketArray,
    packet_product_batch,
    reduce_packets,
)

__all__ = [
    "Packet",
    "packet_product",
    "identity_packet",
    "packet_power",
    "compose",
    "hamilton_product",
    "normalize_quaternion",
    "make_xor_table",
    "validate_monoid_table",
    "PacketArray",
    "packet_product_batch",
    "reduce_packets",
]
__version__ = "0.2.0"
