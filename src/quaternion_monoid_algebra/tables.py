"""A library of alternative sub-field constructions (Cayley tables).

Every constructor returns a monoid table usable as ``form_table`` /
``spin_table`` in :func:`~quaternion_monoid_algebra.algebra.packet_product`
(and the batch equivalents). Each is verified associative-with-identity by
the test suite via :func:`~quaternion_monoid_algebra.algebra.validate_monoid_table`.

Trade-offs between the families:

======================  =========  ==============  ================================
constructor             identity   structure       behavior under iteration
======================  =========  ==============  ================================
``make_xor_table``      0          group (Z_2^n)   information-preserving, mixing
``make_mod_add_table``  0          group (Z/nZ)    information-preserving, mixing
``make_mod_mul_table``  1          monoid          0 is absorbing: one zero packet
                                                   permanently zeroes the field
``make_max_table``      0          band (lattice)  saturates upward to n-1;
                                                   a one-way "high-water mark"
``make_min_table``      n-1        band (lattice)  saturates downward to 0
``make_and_table``      2^n - 1    band (lattice)  bits can only be cleared;
                                                   monotone "capability revoked"
``make_or_table``       0          band (lattice)  bits can only be set;
                                                   monotone "event seen" flags
======================  =========  ==============  ================================

Groups (XOR, mod-add) are invertible, so every stimulus remains recoverable
in principle and long chains spread over the whole value space — the right
choice for avalanche/distinguishability behavior. Bands (max, min, AND, OR)
are idempotent and monotone: they forget, by design, everything except a
running extremum or bit-union — the right choice for one-way flags. The
mod-mul monoid sits in between: invertible on units, absorbing at zero.

IMPORTANT: a table whose identity element is not 0 (``make_min_table``,
``make_and_table``, ``make_mod_mul_table``) changes the identity element of
the packet monoid. Build the matching identity with, e.g.,
``identity_packet(field_a=15)`` when using an AND table for field_a — the
default ``identity_packet()`` assumes identity 0 for the lookup sub-fields.
"""

from __future__ import annotations
import numpy as np

from .algebra import make_xor_table, validate_monoid_table

__all__ = [
    "make_xor_table",
    "make_mod_add_table",
    "make_mod_mul_table",
    "make_max_table",
    "make_min_table",
    "make_and_table",
    "make_or_table",
    "validate_monoid_table",
]


def make_mod_add_table(n: int) -> np.ndarray:
    """T[i, j] = (i + j) mod n over {0,...,n-1}: the cyclic group Z/nZ.
    Identity 0. Information-preserving (every element invertible)."""
    idx = np.arange(n, dtype=np.int64)
    return (idx[:, None] + idx[None, :]) % n


def make_mod_mul_table(n: int) -> np.ndarray:
    """T[i, j] = (i * j) mod n over {0,...,n-1}: the multiplicative monoid of
    Z/nZ. Identity 1 (NOT 0 — see the module docstring). Zero is absorbing:
    once a chain has seen field value 0, the field stays 0 forever."""
    idx = np.arange(n, dtype=np.int64)
    return (idx[:, None] * idx[None, :]) % n


def make_max_table(n: int) -> np.ndarray:
    """T[i, j] = max(i, j) over {0,...,n-1}: an idempotent commutative band.
    Identity 0. Saturates upward: a chain's value is the running maximum."""
    idx = np.arange(n, dtype=np.int64)
    return np.maximum(idx[:, None], idx[None, :])


def make_min_table(n: int) -> np.ndarray:
    """T[i, j] = min(i, j) over {0,...,n-1}: the dual band of max.
    Identity n-1 (NOT 0 — see the module docstring). Saturates downward."""
    idx = np.arange(n, dtype=np.int64)
    return np.minimum(idx[:, None], idx[None, :])


def make_and_table(n_bits: int) -> np.ndarray:
    """T[i, j] = i AND j over {0,...,2^n - 1}: bitwise conjunction band.
    Identity 2^n - 1 (all ones, NOT 0). Bits can only be cleared — a
    monotone "capabilities remaining" register."""
    idx = np.arange(1 << n_bits, dtype=np.int64)
    return np.bitwise_and.outer(idx, idx)


def make_or_table(n_bits: int) -> np.ndarray:
    """T[i, j] = i OR j over {0,...,2^n - 1}: bitwise disjunction band.
    Identity 0. Bits can only be set — a monotone "events seen" register."""
    idx = np.arange(1 << n_bits, dtype=np.int64)
    return np.bitwise_or.outer(idx, idx)
