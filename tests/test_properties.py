"""Pytest property suite for the packet monoid.

Covers the algebraic laws (identity, associativity, closure), input
validation at the Packet boundary, the monoid-table validator, and
packet_power. Hypothesis drives the law tests with adversarial inputs
rather than a fixed random sample.
"""

import numpy as np
import pytest
from hypothesis import given, settings, strategies as st

from quaternion_monoid_algebra import (
    Packet, packet_product, identity_packet, packet_power, compose,
    make_xor_table, validate_monoid_table,
)


# --- strategies --------------------------------------------------------------

finite_component = st.floats(min_value=-1e6, max_value=1e6,
                             allow_nan=False, allow_infinity=False)


@st.composite
def packets(draw):
    """A valid random packet: nonzero finite quaternion, in-range fields,
    positive finite scale."""
    q = np.array([draw(finite_component) for _ in range(4)])
    if np.max(np.abs(q)) == 0.0:
        q = np.array([1.0, 0.0, 0.0, 0.0])
    return Packet(
        quaternion=q,
        field_a=draw(st.integers(0, 15)),
        field_b=draw(st.integers(0, 7)),
        field_c=draw(st.integers(0, 31)),
        field_d=draw(st.integers(0, 7)),
        parity=draw(st.integers(0, 1)),
        scale=draw(st.floats(min_value=1e-6, max_value=1e6,
                             allow_nan=False, allow_infinity=False)),
    )


# --- monoid laws -------------------------------------------------------------

@given(p=packets())
@settings(max_examples=200)
def test_left_identity(p):
    assert packet_product(identity_packet(), p) == p


@given(p=packets())
@settings(max_examples=200)
def test_right_identity(p):
    assert packet_product(p, identity_packet()) == p


@given(a=packets(), b=packets(), c=packets())
@settings(max_examples=200)
def test_associativity(a, b, c):
    lhs = packet_product(packet_product(a, b), c)
    rhs = packet_product(a, packet_product(b, c))
    assert lhs == rhs


@given(a=packets(), b=packets())
@settings(max_examples=200)
def test_closure(a, b):
    p = packet_product(a, b)
    assert np.isclose(np.linalg.norm(p.quaternion), 1.0, atol=1e-6)
    assert 0 <= p.field_a < 16
    assert 0 <= p.field_b < 8
    assert 0 <= p.field_c < 32
    assert 0 <= p.field_d < 8
    assert p.parity in (0, 1)
    assert np.isfinite(p.scale) and p.scale > 0


# --- packet_power and compose ------------------------------------------------

@pytest.mark.parametrize("n", [0, 1, 2, 3, 5, 8, 13, 64, 1000])
def test_packet_power_matches_sequential_fold(n):
    rng = np.random.default_rng(7)
    p = Packet.random(rng)
    sequential = identity_packet()
    for _ in range(n):
        sequential = packet_product(sequential, p)
    assert packet_power(p, n) == sequential


def test_packet_power_rejects_negative():
    with pytest.raises(ValueError):
        packet_power(Packet.random(np.random.default_rng(0)), -1)


def test_compose_empty_is_identity():
    assert compose([]) == identity_packet()


def test_compose_matches_manual_fold():
    rng = np.random.default_rng(11)
    ps = [Packet.random(rng) for _ in range(20)]
    manual = identity_packet()
    for p in ps:
        manual = packet_product(manual, p)
    assert compose(ps) == manual


# --- boundary validation -----------------------------------------------------

def test_zero_quaternion_rejected():
    with pytest.raises(ValueError, match="nonzero"):
        Packet(quaternion=np.zeros(4))


def test_nan_quaternion_rejected():
    with pytest.raises(ValueError, match="non-finite"):
        Packet(quaternion=np.array([np.nan, 0.0, 0.0, 1.0]))


def test_wrong_shape_quaternion_rejected():
    with pytest.raises(ValueError, match="shape"):
        Packet(quaternion=np.ones(3))


@pytest.mark.parametrize("bad_scale", [0.0, -1.0, float("nan"), float("inf")])
def test_bad_scale_rejected(bad_scale):
    with pytest.raises(ValueError, match="scale"):
        Packet(quaternion=np.array([1.0, 0, 0, 0]), scale=bad_scale)


def test_extreme_magnitude_quaternions_normalize_correctly():
    # Components this large overflow a naive sum-of-squares to inf, which
    # used to slip past the zero check and store an all-zero quaternion.
    p_huge = Packet(quaternion=np.array([1e155, 1e155, 1e155, 1e155]))
    assert np.isclose(np.linalg.norm(p_huge.quaternion), 1.0, atol=1e-12)
    # Components this small underflow a naive sum-of-squares to 0, which
    # used to be falsely rejected as a zero quaternion.
    p_tiny = Packet(quaternion=np.array([1e-320, 0.0, 0.0, 0.0]))
    assert np.allclose(p_tiny.quaternion, [1.0, 0.0, 0.0, 0.0])
    # Both must compose cleanly (closure holds on accepted packets).
    out = packet_product(p_huge, p_tiny)
    assert np.isclose(np.linalg.norm(out.quaternion), 1.0, atol=1e-12)


def test_eq_scale_tolerance_is_relative():
    q = np.array([1.0, 0.0, 0.0, 0.0])
    assert Packet(quaternion=q, scale=1000.0) == Packet(quaternion=q, scale=1000.0 + 1e-7)
    assert Packet(quaternion=q, scale=1000.0) != Packet(quaternion=q, scale=1000.005)


def test_fields_masked_to_width():
    p = Packet(quaternion=np.array([1.0, 0, 0, 0]),
               field_a=255, field_b=255, field_c=255, field_d=255, parity=255)
    assert p.field_a == 255 & 0xF
    assert p.field_b == 255 & 0x7
    assert p.field_c == 255 & 0x1F
    assert p.field_d == 255 & 0x7
    assert p.parity == 255 & 0x1


# --- monoid-table validator ---------------------------------------------------

@pytest.mark.parametrize("n_bits", [1, 2, 3, 4, 5])
def test_xor_tables_are_monoids(n_bits):
    validate_monoid_table(make_xor_table(n_bits))


def test_mod_add_table_is_monoid():
    n = 12
    idx = np.arange(n)
    table = (idx[:, None] + idx[None, :]) % n
    validate_monoid_table(table)


def test_subtraction_table_fails_left_identity():
    n = 8
    idx = np.arange(n)
    # T[i,j] = (i-j) % n has 0 as a RIGHT identity only: T[0,j] = -j != j.
    # The validator checks identity laws before associativity, so this
    # exercises the left-identity branch.
    table = (idx[:, None] - idx[None, :]) % n
    with pytest.raises(ValueError, match="left identity"):
        validate_monoid_table(table)


def test_corrupted_xor_table_fails_associativity():
    # Corrupt one cell of a valid XOR table, away from row/column 0 so both
    # identity laws still hold — the failure must come from the
    # associativity check itself.
    table = make_xor_table(2).copy()
    table[1, 2] = 1     # correct value is 3
    with pytest.raises(ValueError, match="associativity"):
        validate_monoid_table(table)


def test_shifted_table_fails_identity():
    n = 4
    idx = np.arange(n)
    table = (idx[:, None] + idx[None, :] + 1) % n   # no identity at 0
    with pytest.raises(ValueError, match="identity"):
        validate_monoid_table(table)


def test_non_closed_table_rejected():
    table = np.array([[0, 1], [1, 5]])
    with pytest.raises(ValueError, match="closed"):
        validate_monoid_table(table)


def test_custom_table_flows_through_product():
    rng = np.random.default_rng(3)
    # mod-16 addition instead of XOR for field_a: still a monoid with identity 0
    idx = np.arange(16)
    add_table = (idx[:, None] + idx[None, :]) % 16
    validate_monoid_table(add_table)
    a, b = Packet.random(rng), Packet.random(rng)
    out = packet_product(a, b, form_table=add_table)
    assert out.field_a == (a.field_a + b.field_a) % 16


# --- iteration stability ------------------------------------------------------

def test_thousand_step_chain_stays_unit_norm():
    rng = np.random.default_rng(42)
    p = Packet.random(rng)
    state = p
    for _ in range(1000):
        state = packet_product(state, p)
    assert abs(np.linalg.norm(state.quaternion) - 1.0) < 1e-6
