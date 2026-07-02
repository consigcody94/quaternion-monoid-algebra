"""Metric utilities backing the topology-preservation results.

The metric used throughout the validation suite is

    d(p, q) = arccos(|<p, q>|)

on unit quaternions, where <.,.> is the Euclidean inner product on R^4.
The absolute value identifies antipodes (q and -q encode the same
rotation), making d a metric on the projective space S^3 / {+-1} = RP^3,
i.e. on the rotation group SO(3).

Formal statements and proofs — including the exact-preservation theorem
for composition with a common packet, and the Lipschitz development bound
for iterated composition — are in ``paper/topology_notes.md``. The
machine-checked counterparts live in ``tests/test_topology.py``.
"""

from __future__ import annotations
import numpy as np


def pairwise_quaternion_distance(qarr: np.ndarray) -> np.ndarray:
    """Pairwise geodesic distances d(p, q) = arccos(|<p, q>|) between unit
    quaternions.

    qarr: shape (N, 4), rows assumed unit norm. Returns an (N, N) symmetric
    matrix with zero diagonal. This is the distance matrix the persistent-
    homology tests build their Vietoris-Rips filtrations on.
    """
    q = np.asarray(qarr, dtype=np.float64)
    if q.ndim != 2 or q.shape[1] != 4:
        raise ValueError(f"expected shape (N, 4), got {q.shape}")
    gram = np.clip(np.abs(q @ q.T), 0.0, 1.0)
    d = np.arccos(gram)
    np.fill_diagonal(d, 0.0)
    return d


def distance_to_identity(qarr: np.ndarray) -> np.ndarray:
    """d(1, q) = arccos(|q_w|) for each row: the rotation half-angle offset
    of q from the identity quaternion [1, 0, 0, 0]."""
    q = np.asarray(qarr, dtype=np.float64)
    if q.ndim == 1:
        return float(np.arccos(np.clip(np.abs(q[0]), 0.0, 1.0)))
    return np.arccos(np.clip(np.abs(q[..., 0]), 0.0, 1.0))
