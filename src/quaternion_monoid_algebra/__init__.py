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
from .tables import (
    make_mod_add_table,
    make_mod_mul_table,
    make_max_table,
    make_min_table,
    make_and_table,
    make_or_table,
)
from .topology import (
    pairwise_quaternion_distance,
    distance_to_identity,
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
    "make_mod_add_table",
    "make_mod_mul_table",
    "make_max_table",
    "make_min_table",
    "make_and_table",
    "make_or_table",
    "pairwise_quaternion_distance",
    "distance_to_identity",
]
__version__ = "0.3.0"
