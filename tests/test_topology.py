"""Machine checks for the formal statements in paper/topology_notes.md.

Each test names the statement it certifies. The isometry results are exact
over the reals; assertions use 1e-12/1e-9 tolerances for floating point.
"""

import numpy as np
import pytest

from quaternion_monoid_algebra import (
    Packet, packet_product, pairwise_quaternion_distance,
)
from quaternion_monoid_algebra.algebra import hamilton_product, normalize_quaternion
from quaternion_monoid_algebra.topology import distance_to_identity

try:
    import gudhi
    HAS_GUDHI = True
except ImportError:
    HAS_GUDHI = False

needs_gudhi = pytest.mark.skipif(not HAS_GUDHI, reason="GUDHI not installed")


def random_units(n, seed):
    rng = np.random.default_rng(seed)
    return normalize_quaternion(rng.standard_normal((n, 4)))


def compose_all_with(g_quaternion, qarr, side):
    """Map every configuration point through the actual packet operation
    p -> g (x) p (side='left') or p -> p (x) g (side='right'), returning the
    resulting quaternion components."""
    g = Packet(quaternion=g_quaternion)
    out = []
    for q in qarr:
        p = Packet(quaternion=q)
        composed = packet_product(g, p) if side == "left" else packet_product(p, g)
        out.append(composed.quaternion)
    return np.array(out)


def total_persistence(qarr, dim):
    """Total persistence (sum of finite interval lengths) of the Rips
    filtration over the FULL distance range, in homology dimension dim."""
    d = pairwise_quaternion_distance(qarr)
    rips = gudhi.RipsComplex(distance_matrix=d, max_edge_length=float(d.max()) + 1e-9)
    st = rips.create_simplex_tree(max_dimension=dim + 1)
    st.compute_persistence()
    bars = st.persistence_intervals_in_dimension(dim)
    return float(sum(dth - b for (b, dth) in bars if dth != float("inf")))


# --- Lemma 1 / Theorem 1: common composition is an isometry -------------------

def test_left_composition_preserves_distance_matrix():
    qs = random_units(60, seed=0)
    g = random_units(1, seed=1)[0]
    composed = compose_all_with(g, qs, side="left")
    assert np.allclose(pairwise_quaternion_distance(qs),
                       pairwise_quaternion_distance(composed), atol=1e-12)


def test_right_composition_preserves_distance_matrix():
    qs = random_units(60, seed=2)
    g = random_units(1, seed=3)[0]
    composed = compose_all_with(g, qs, side="right")
    assert np.allclose(pairwise_quaternion_distance(qs),
                       pairwise_quaternion_distance(composed), atol=1e-12)


@needs_gudhi
def test_persistence_diagrams_equal_under_common_composition():
    qs = random_units(40, seed=4)
    g = random_units(1, seed=5)[0]
    composed = compose_all_with(g, qs, side="left")
    for dim in (0, 1):
        orig = np.sort(np.array(
            [(b, d) for (b, d) in _diagram(qs, dim) if d != float("inf")]), axis=0)
        comp = np.sort(np.array(
            [(b, d) for (b, d) in _diagram(composed, dim) if d != float("inf")]), axis=0)
        assert orig.shape == comp.shape
        if orig.size:
            assert np.allclose(orig, comp, atol=1e-9)


def _diagram(qarr, dim):
    d = pairwise_quaternion_distance(qarr)
    rips = gudhi.RipsComplex(distance_matrix=d, max_edge_length=float(d.max()) + 1e-9)
    st = rips.create_simplex_tree(max_dimension=dim + 1)
    st.compute_persistence()
    return st.persistence_intervals_in_dimension(dim)


# --- Lemma 2: subadditivity of the identity offset -----------------------------

def test_subadditivity_of_identity_offset():
    rng = np.random.default_rng(6)
    for _ in range(500):
        a = normalize_quaternion(rng.standard_normal(4))
        b = normalize_quaternion(rng.standard_normal(4))
        ab = normalize_quaternion(hamilton_product(a, b))
        assert distance_to_identity(ab) <= (
            distance_to_identity(a) + distance_to_identity(b) + 1e-12)


# --- Proposition 3: development bound ------------------------------------------

def _trajectory(stimuli):
    state = Packet(quaternion=np.array([1.0, 0.0, 0.0, 0.0]))
    out = []
    for x in stimuli:
        state = packet_product(state, Packet(quaternion=x))
        out.append(state.quaternion)
    return np.array(out)


def test_trajectory_steps_equal_stimulus_offsets():
    stimuli = random_units(200, seed=7)
    traj = _trajectory(stimuli)
    prev = np.array([1.0, 0.0, 0.0, 0.0])
    for x, q in zip(stimuli, traj, strict=True):
        step = float(np.arccos(np.clip(abs(np.dot(prev, q)), 0.0, 1.0)))
        offset = float(distance_to_identity(x))
        assert abs(step - offset) < 1e-9
        prev = q


def test_window_distance_bounded_by_offset_sum():
    stimuli = random_units(120, seed=8)
    traj = _trajectory(stimuli)
    offsets = np.array([distance_to_identity(x) for x in stimuli])
    rng = np.random.default_rng(9)
    for _ in range(200):
        s, t = sorted(rng.integers(0, len(traj), size=2))
        if s == t:
            continue
        dist = float(np.arccos(np.clip(abs(np.dot(traj[s], traj[t])), 0.0, 1.0)))
        assert dist <= float(np.sum(offsets[s + 1:t + 1])) + 1e-9


# --- Section 5: iterated composition can inflate H1 ----------------------------

@needs_gudhi
def test_constant_stream_inflates_h1():
    """A constant stimulus (input set = one point, H1 = 0) develops into a
    geodesic circle whose Rips filtration carries positive H1 persistence:
    the trajectory/input H1 ratio is unbounded, so iterated preservation
    cannot be a theorem. See topology_notes.md section 5."""
    theta = np.pi / 24
    x = np.array([np.cos(theta), np.sin(theta), 0.0, 0.0])
    traj = _trajectory([x] * 48)
    assert total_persistence(traj, dim=1) > 0.0
