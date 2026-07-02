"""Vectorized batch operations over arrays of packets (struct-of-arrays).

The scalar API in :mod:`.algebra` composes one pair of packets per call and
tops out around 10^5 ops/sec in pure Python. This module holds N packets as
a struct-of-arrays (`PacketArray`) so that N compositions are a handful of
NumPy kernel calls, and chain reduction runs as an O(log N)-depth pairwise
tree — legal because ⊗ is associative, so any parenthesization gives the
same result (integer-exact on the symbolic fields, up to floating-point
rounding on the quaternion and scale).

    pa = PacketArray.random(1_000_000)
    pb = PacketArray.random(1_000_000)
    pc = packet_product_batch(pa, pb)       # 1M compositions, vectorized
    head = reduce_packets(pa)               # chain head, O(log N) passes
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Sequence
import numpy as np

from .algebra import (
    DEFAULT_MOD, _FORM_TABLE, _SPIN_TABLE,
    Packet, hamilton_product, identity_packet, normalize_quaternion,
)

_FIELD_MASKS = {"field_a": 0xF, "field_b": 0x7, "field_c": 0x1F,
                "field_d": 0x7, "parity": 0x1}


@dataclass
class PacketArray:
    """N packets stored as a struct-of-arrays for vectorized composition.

    Same validation contract as :class:`Packet`, applied elementwise:
    quaternions finite and nonzero (renormalized to unit length), symbolic
    fields masked to their bit widths, scales finite and positive.
    """
    quaternion: np.ndarray          # (N, 4) float64, unit rows
    field_a: np.ndarray             # (N,) int64 in [0, 16)
    field_b: np.ndarray             # (N,) int64 in [0, 8)
    field_c: np.ndarray             # (N,) int64 in [0, 32)
    field_d: np.ndarray             # (N,) int64 in [0, 8)
    parity: np.ndarray              # (N,) int64 in {0, 1}
    scale: np.ndarray               # (N,) float64, positive

    def __post_init__(self):
        q = np.asarray(self.quaternion, dtype=np.float64)
        if q.ndim != 2 or q.shape[1] != 4:
            raise ValueError(f"quaternion must have shape (N, 4), got {q.shape}")
        if not np.all(np.isfinite(q)):
            raise ValueError("quaternion array has non-finite components")
        # Pre-scale by the largest component per row before computing the
        # norm, so rows with extreme magnitudes normalize correctly instead
        # of overflowing/underflowing the sum of squares (see
        # normalize_quaternion).
        m = np.max(np.abs(q), axis=1)
        if np.any(m == 0.0):
            raise ValueError(f"{int(np.sum(m == 0.0))} zero quaternion rows")
        qs = q / m[:, None]
        self.quaternion = qs / np.linalg.norm(qs, axis=1)[:, None]
        n = len(q)
        for name, mask in _FIELD_MASKS.items():
            arr = np.asarray(getattr(self, name), dtype=np.int64) & mask
            if arr.shape != (n,):
                raise ValueError(f"{name} must have shape ({n},), got {arr.shape}")
            setattr(self, name, arr)
        s = np.asarray(self.scale, dtype=np.float64)
        if s.shape != (n,):
            raise ValueError(f"scale must have shape ({n},), got {s.shape}")
        if not np.all(np.isfinite(s)) or np.any(s <= 0.0):
            raise ValueError("scale array must be finite and positive")
        self.scale = s

    def __len__(self) -> int:
        return len(self.quaternion)

    def __getitem__(self, i: int) -> Packet:
        return Packet(
            quaternion=self.quaternion[i].copy(),
            field_a=int(self.field_a[i]), field_b=int(self.field_b[i]),
            field_c=int(self.field_c[i]), field_d=int(self.field_d[i]),
            parity=int(self.parity[i]), scale=float(self.scale[i]),
        )

    def _slice(self, idx) -> "PacketArray":
        return PacketArray(
            quaternion=self.quaternion[idx],
            field_a=self.field_a[idx], field_b=self.field_b[idx],
            field_c=self.field_c[idx], field_d=self.field_d[idx],
            parity=self.parity[idx], scale=self.scale[idx],
        )

    @staticmethod
    def from_packets(packets: Sequence[Packet]) -> "PacketArray":
        if not packets:
            raise ValueError("from_packets requires at least one packet")
        return PacketArray(
            quaternion=np.stack([p.quaternion for p in packets]),
            field_a=np.array([p.field_a for p in packets]),
            field_b=np.array([p.field_b for p in packets]),
            field_c=np.array([p.field_c for p in packets]),
            field_d=np.array([p.field_d for p in packets]),
            parity=np.array([p.parity for p in packets]),
            scale=np.array([p.scale for p in packets]),
        )

    def to_packets(self) -> list[Packet]:
        return [self[i] for i in range(len(self))]

    @staticmethod
    def random(n: int, rng: Optional[np.random.Generator] = None) -> "PacketArray":
        """N random packets with the same distribution as Packet.random()."""
        if rng is None:
            rng = np.random.default_rng()
        q = rng.standard_normal((n, 4))
        return PacketArray(
            quaternion=q,   # __post_init__ normalizes
            field_a=rng.integers(0, 16, size=n),
            field_b=rng.integers(0, 8, size=n),
            field_c=rng.integers(0, 32, size=n),
            field_d=rng.integers(0, 8, size=n),
            parity=rng.integers(0, 2, size=n),
            scale=np.exp(rng.standard_normal(n) * 0.1),
        )


def packet_product_batch(pa: PacketArray, pb: PacketArray,
                          form_table: Optional[np.ndarray] = None,
                          spin_table: Optional[np.ndarray] = None) -> PacketArray:
    """Elementwise composition: out[i] = pa[i] ⊗ pb[i], fully vectorized.

    Bit-identical on the symbolic fields to N scalar packet_product calls,
    and equal on the quaternion and scale up to floating-point rounding.
    """
    if len(pa) != len(pb):
        raise ValueError(f"length mismatch: {len(pa)} vs {len(pb)}")
    if form_table is None:
        form_table = _FORM_TABLE
    if spin_table is None:
        spin_table = _SPIN_TABLE
    return PacketArray(
        quaternion=normalize_quaternion(hamilton_product(pa.quaternion, pb.quaternion)),
        field_a=form_table[pa.field_a, pb.field_a],
        field_b=np.maximum(pa.field_b, pb.field_b),
        field_c=(pa.field_c + pb.field_c) % DEFAULT_MOD,
        field_d=spin_table[pa.field_d, pb.field_d],
        parity=pa.parity ^ pb.parity,
        scale=pa.scale * pb.scale,
    )


def reduce_packets(pa: PacketArray,
                    form_table: Optional[np.ndarray] = None,
                    spin_table: Optional[np.ndarray] = None) -> Packet:
    """Compose a whole chain, pa[0] ⊗ pa[1] ⊗ ... ⊗ pa[N-1], as a pairwise
    tree reduction: O(log N) vectorized passes instead of N scalar products.

    Associativity guarantees the same head as the sequential left fold —
    exactly on the symbolic fields, within floating-point tolerance on the
    quaternion and scale. This is the parallel-reduction pattern the scalar
    example in examples/02_swarm_composition.py demonstrates packet by packet.
    """
    if len(pa) == 0:
        return identity_packet()
    while len(pa) > 1:
        n = len(pa)
        even = pa._slice(slice(0, n - (n % 2), 2))
        odd = pa._slice(slice(1, n, 2))
        combined = packet_product_batch(even, odd, form_table, spin_table)
        if n % 2 == 1:
            last = pa._slice(slice(n - 1, n))
            combined = PacketArray(
                quaternion=np.concatenate([combined.quaternion, last.quaternion]),
                field_a=np.concatenate([combined.field_a, last.field_a]),
                field_b=np.concatenate([combined.field_b, last.field_b]),
                field_c=np.concatenate([combined.field_c, last.field_c]),
                field_d=np.concatenate([combined.field_d, last.field_d]),
                parity=np.concatenate([combined.parity, last.parity]),
                scale=np.concatenate([combined.scale, last.scale]),
            )
        pa = combined
    return pa[0]
