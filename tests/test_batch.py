"""Tests for the vectorized batch API: PacketArray, packet_product_batch,
and tree reduction. The invariant throughout: batch results must agree with
the scalar reference implementation (exactly on symbolic fields, within
floating-point tolerance on quaternion and scale)."""

import numpy as np
import pytest

from quaternion_monoid_algebra import (
    Packet, PacketArray, packet_product, packet_product_batch,
    identity_packet, reduce_packets, compose,
)


def test_roundtrip_packets():
    rng = np.random.default_rng(0)
    ps = [Packet.random(rng) for _ in range(37)]
    pa = PacketArray.from_packets(ps)
    assert len(pa) == 37
    back = pa.to_packets()
    assert all(a == b for a, b in zip(ps, back, strict=True))


def test_batch_product_matches_scalar():
    rng = np.random.default_rng(1)
    n = 500
    pa = PacketArray.random(n, rng)
    pb = PacketArray.random(n, rng)
    out = packet_product_batch(pa, pb)
    for i in range(0, n, 37):   # spot-check a spread of indices
        assert out[i] == packet_product(pa[i], pb[i])


def test_batch_product_all_indices_small():
    rng = np.random.default_rng(2)
    pa = PacketArray.random(64, rng)
    pb = PacketArray.random(64, rng)
    out = packet_product_batch(pa, pb)
    for i in range(64):
        assert out[i] == packet_product(pa[i], pb[i])


def test_batch_length_mismatch_rejected():
    rng = np.random.default_rng(3)
    with pytest.raises(ValueError, match="length"):
        packet_product_batch(PacketArray.random(4, rng), PacketArray.random(5, rng))


@pytest.mark.parametrize("n", [1, 2, 3, 7, 8, 100, 257])
def test_tree_reduce_matches_sequential_fold(n):
    rng = np.random.default_rng(4)
    pa = PacketArray.random(n, rng)
    sequential = compose(pa.to_packets())
    assert reduce_packets(pa) == sequential


def test_reduce_empty_returns_identity():
    pa = PacketArray.random(1, np.random.default_rng(5))._slice(slice(0, 0))
    assert reduce_packets(pa) == identity_packet()


def test_custom_tables_flow_through_batch_and_reduce():
    rng = np.random.default_rng(7)
    idx = np.arange(16)
    add16 = (idx[:, None] + idx[None, :]) % 16      # mod-16 add: monoid, identity 0
    jdx = np.arange(8)
    add8 = (jdx[:, None] + jdx[None, :]) % 8        # mod-8 add for the spin field

    n = 40
    pa = PacketArray.random(n, rng)
    pb = PacketArray.random(n, rng)
    out = packet_product_batch(pa, pb, form_table=add16, spin_table=add8)
    for i in range(n):
        expected = packet_product(pa[i], pb[i], form_table=add16, spin_table=add8)
        assert out[i] == expected
        assert out[i].field_a == (pa[i].field_a + pb[i].field_a) % 16

    # And through the tree reduction, against the scalar sequential fold.
    head = reduce_packets(pa, form_table=add16, spin_table=add8)
    sequential = identity_packet()
    for p in pa.to_packets():
        sequential = packet_product(sequential, p, form_table=add16, spin_table=add8)
    assert head == sequential


def test_packet_array_extreme_magnitudes_normalize_correctly():
    q = np.array([[1e155, 1e155, 1e155, 1e155],
                  [1e-320, 0.0, 0.0, 0.0],
                  [0.0, 1.0, 0.0, 0.0]])
    pa = PacketArray(
        quaternion=q,
        field_a=np.zeros(3, dtype=np.int64), field_b=np.zeros(3, dtype=np.int64),
        field_c=np.zeros(3, dtype=np.int64), field_d=np.zeros(3, dtype=np.int64),
        parity=np.zeros(3, dtype=np.int64), scale=np.ones(3),
    )
    assert np.allclose(np.linalg.norm(pa.quaternion, axis=1), 1.0, atol=1e-12)


def test_packet_array_validation():
    with pytest.raises(ValueError, match="zero quaternion"):
        PacketArray(
            quaternion=np.zeros((3, 4)),
            field_a=np.zeros(3, dtype=np.int64), field_b=np.zeros(3, dtype=np.int64),
            field_c=np.zeros(3, dtype=np.int64), field_d=np.zeros(3, dtype=np.int64),
            parity=np.zeros(3, dtype=np.int64), scale=np.ones(3),
        )
    with pytest.raises(ValueError, match="scale"):
        PacketArray(
            quaternion=np.tile([1.0, 0, 0, 0], (2, 1)),
            field_a=np.zeros(2, dtype=np.int64), field_b=np.zeros(2, dtype=np.int64),
            field_c=np.zeros(2, dtype=np.int64), field_d=np.zeros(2, dtype=np.int64),
            parity=np.zeros(2, dtype=np.int64), scale=np.array([1.0, -1.0]),
        )


def test_packet_array_quaternions_unit_norm_after_init():
    pa = PacketArray.random(100, np.random.default_rng(6))
    norms = np.linalg.norm(pa.quaternion, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-12)
