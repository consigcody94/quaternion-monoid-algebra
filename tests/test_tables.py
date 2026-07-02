"""Tests for the alternative sub-field constructions in tables.py.

Every constructor must produce a genuine monoid table (checked against
validate_monoid_table with the correct identity element), and the
documented behavioral trade-offs (information-preserving vs saturating vs
absorbing) must actually hold under iteration.
"""

import numpy as np
import pytest

from quaternion_monoid_algebra import (
    Packet, packet_product, identity_packet, validate_monoid_table,
    make_xor_table, make_mod_add_table, make_mod_mul_table,
    make_max_table, make_min_table, make_and_table, make_or_table,
)


@pytest.mark.parametrize("table,identity", [
    (make_xor_table(4), 0),
    (make_mod_add_table(12), 0),
    (make_mod_add_table(16), 0),
    (make_mod_mul_table(16), 1),
    (make_mod_mul_table(7), 1),
    (make_max_table(8), 0),
    (make_min_table(8), 7),
    (make_and_table(4), 15),
    (make_or_table(4), 0),
])
def test_constructors_produce_monoids(table, identity):
    validate_monoid_table(table, identity=identity)


def test_or_table_saturates_upward():
    table = make_or_table(4)
    acc = 0
    for v in [1, 2, 4, 8]:
        acc = int(table[acc, v])
    assert acc == 15          # all bits set, and they can never clear
    assert int(table[15, 3]) == 15


def test_and_table_saturates_downward():
    table = make_and_table(4)
    acc = 15
    for v in [14, 13, 11, 7]:
        acc = int(table[acc, v])
    assert acc == 0           # all bits cleared, and they can never return
    assert int(table[0, 15]) == 0


def test_mod_mul_zero_is_absorbing():
    table = make_mod_mul_table(16)
    assert int(table[0, 7]) == 0 and int(table[7, 0]) == 0
    acc = 3
    for v in [5, 0, 11, 13]:  # one zero anywhere zeroes the chain for good
        acc = int(table[acc, v])
    assert acc == 0


def test_mod_add_is_information_preserving():
    # A group table: composing with any fixed element is a bijection.
    table = make_mod_add_table(16)
    for g in range(16):
        assert sorted(int(table[g, j]) for j in range(16)) == list(range(16))


def test_identity_packet_with_and_table():
    rng = np.random.default_rng(0)
    and_table = make_and_table(4)          # identity element is 15, not 0
    ident = identity_packet(field_a=15)
    for _ in range(20):
        p = Packet.random(rng)
        assert packet_product(ident, p, form_table=and_table) == p
        assert packet_product(p, ident, form_table=and_table) == p


def test_identity_packet_with_min_table_on_spin_field():
    rng = np.random.default_rng(1)
    min_table = make_min_table(8)          # identity element is 7, not 0
    ident = identity_packet(field_d=7)
    for _ in range(20):
        p = Packet.random(rng)
        assert packet_product(ident, p, spin_table=min_table) == p
        assert packet_product(p, ident, spin_table=min_table) == p


def test_default_identity_packet_fails_for_nonzero_identity_table():
    # Documented gotcha: the default identity_packet() is NOT the identity
    # of a packet monoid built on an AND table.
    rng = np.random.default_rng(2)
    and_table = make_and_table(4)
    p = Packet.random(rng)
    while p.field_a == 0:                  # need a packet the default masks
        p = Packet.random(rng)
    assert packet_product(identity_packet(), p, form_table=and_table) != p
