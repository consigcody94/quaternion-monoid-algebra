"""Run the full validation suite for quaternion-monoid algebra.

Eight tests covering:
    1. Left identity:  I ⊗ p = p
    2. Right identity: p ⊗ I = p
    3. Associativity:  (a ⊗ b) ⊗ c = a ⊗ (b ⊗ c)
    4. Closure:        p1 ⊗ p2 is a valid packet (quaternion unit norm, fields in range)
    5. Stability under iteration: 1000-step self-product stays unit norm
    6. Power consistency: packet_power(p, 5) == p ⊗ p ⊗ p ⊗ p ⊗ p
    7. GPU bit-exact: GPU Hamilton matches CPU reference to 0.0 difference (or SKIP if no CuPy)
    8. Topology preservation: H_1 persistence ratio bounded under iterated composition

Exit code 0 if all pass, 1 otherwise.
"""

import os
import sys
import io
import numpy as np

# Force UTF-8 output so unicode operator symbols render on Windows terminals.
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

# Make the package importable from the repo checkout without installation
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from quaternion_monoid_algebra.algebra import (
    Packet, packet_product, identity_packet, packet_power,
    normalize_quaternion,
)
from quaternion_monoid_algebra.gpu import HAS_GPU


# --- helpers -----------------------------------------------------------------

class Result:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def record(self, ok, name, detail=""):
        if ok is None:
            print(f"  [SKIP] {name}  {detail}")
            self.skipped += 1
        elif ok:
            print(f"  [PASS] {name}  {detail}")
            self.passed += 1
        else:
            print(f"  [FAIL] {name}  {detail}")
            self.failed += 1


def packet_is_valid(p: Packet) -> bool:
    """Closure check: a packet is valid if its quaternion is unit norm,
    its symbolic fields are in their declared ranges, and its scale is finite."""
    return (
        np.isclose(np.linalg.norm(p.quaternion), 1.0, atol=1e-6)
        and 0 <= p.field_a < 16
        and 0 <= p.field_b < 8
        and 0 <= p.field_c < 32
        and 0 <= p.field_d < 8
        and p.parity in (0, 1)
        and np.isfinite(p.scale) and p.scale > 0
    )


# --- the 8 tests -------------------------------------------------------------

def test_left_identity(r: Result, rng):
    I = identity_packet()
    mismatches = 0
    for _ in range(100):
        p = Packet.random(rng)
        if packet_product(I, p) != p:
            mismatches += 1
    r.record(mismatches == 0, "Left identity: I ⊗ p = p across 100 packets",
             f"-- {mismatches} mismatches")


def test_right_identity(r: Result, rng):
    I = identity_packet()
    mismatches = 0
    for _ in range(100):
        p = Packet.random(rng)
        if packet_product(p, I) != p:
            mismatches += 1
    r.record(mismatches == 0, "Right identity: p ⊗ I = p across 100 packets",
             f"-- {mismatches} mismatches")


def test_associativity(r: Result, rng):
    violations = 0
    triples = 0
    for _ in range(512):
        a, b, c = Packet.random(rng), Packet.random(rng), Packet.random(rng)
        lhs = packet_product(packet_product(a, b), c)
        rhs = packet_product(a, packet_product(b, c))
        triples += 1
        if lhs != rhs:
            violations += 1
    r.record(violations == 0,
             f"Associativity across {triples} random triples",
             f"-- {violations} violations")


def test_closure(r: Result, rng):
    invalid = 0
    for _ in range(500):
        p1, p2 = Packet.random(rng), Packet.random(rng)
        out = packet_product(p1, p2)
        if not packet_is_valid(out):
            invalid += 1
    r.record(invalid == 0,
             "Closure: every product is a valid packet (500 random pairs)",
             f"-- {invalid} invalid products")


def test_stability(r: Result, rng):
    p = Packet.random(rng)
    state = p
    for _ in range(1000):
        state = packet_product(state, p)
    final_norm_err = abs(np.linalg.norm(state.quaternion) - 1.0)
    r.record(final_norm_err < 1e-6,
             "Chain of 1000 self-products keeps quaternion unit-norm",
             f"-- final norm err = {final_norm_err:.2e}")


def test_power_consistency(r: Result, rng):
    p = Packet.random(rng)
    expanded = identity_packet()
    for _ in range(5):
        expanded = packet_product(expanded, p)
    powered = packet_power(p, 5)
    r.record(expanded == powered,
             "packet_power(p, 5) == p ⊗ p ⊗ p ⊗ p ⊗ p")


def test_gpu_bit_exact(r: Result, rng):
    if not HAS_GPU:
        r.record(None, "GPU Hamilton matches CPU bit-for-bit", "(CuPy not available)")
        return
    import cupy as cp
    from quaternion_monoid_algebra.gpu import (
        hamilton_product_batch_gpu, hamilton_product_batch_cpu,
    )

    N = 100_000
    q1 = rng.standard_normal((N, 4)).astype(np.float32)
    q2 = rng.standard_normal((N, 4)).astype(np.float32)
    # Normalize on CPU to start from valid unit quaternions
    q1 = q1 / np.linalg.norm(q1, axis=1, keepdims=True)
    q2 = q2 / np.linalg.norm(q2, axis=1, keepdims=True)

    cpu = hamilton_product_batch_cpu(q1, q2)
    gpu = cp.asnumpy(hamilton_product_batch_gpu(cp.asarray(q1), cp.asarray(q2)))
    max_diff = float(np.max(np.abs(cpu - gpu)))
    r.record(max_diff == 0.0,
             "GPU Hamilton matches CPU bit-for-bit",
             f"-- max diff = {max_diff:.2e}")


def test_topology_preservation(r: Result, rng):
    """Iterate state[t+1] = state[t] ⊗ stim[t] and check that the H_1
    persistence ratio of the trajectory vs the input stream is bounded
    in [0.3, 5.0]. Skip cleanly if GUDHI is unavailable."""
    try:
        import gudhi
    except ImportError:
        r.record(None, "Topology preservation (H_1 ratio in [0.3, 5.0])",
                 "(GUDHI not available)")
        return

    # Generate a structured input stream (2-frequency torus walk)
    n = 300
    t = np.linspace(0, 4*np.pi, n)
    qs = np.stack([
        np.cos(t/2)*np.cos(t*1.3/2),
        np.cos(t/2)*np.sin(t*1.3/2),
        np.sin(t/2)*np.cos(t*1.9/2),
        np.sin(t/2)*np.sin(t*1.9/2),
    ], axis=1)
    qs = normalize_quaternion(qs)

    def h1_total_persistence(qarr):
        D = np.arccos(np.clip(np.abs(qarr @ qarr.T), -1.0, 1.0))
        rips = gudhi.RipsComplex(distance_matrix=D, max_edge_length=np.percentile(D, 60))
        st = rips.create_simplex_tree(max_dimension=2)
        st.compute_persistence()
        bars = st.persistence_intervals_in_dimension(1)
        finite = [(b, d) for (b, d) in bars if d != float("inf")]
        if not finite:
            return 0.0
        return float(sum(d - b for (b, d) in finite))

    in_pers = h1_total_persistence(qs)

    # Compose state[t+1] = state[t] ⊗ stim[t] where stim is a packet built from qs[t]
    state = identity_packet()
    out_qs = []
    for q in qs:
        stim = Packet(quaternion=q)
        state = packet_product(state, stim)
        out_qs.append(state.quaternion)
    out_qs = np.array(out_qs)

    out_pers = h1_total_persistence(out_qs)
    if in_pers == 0.0:
        ratio = 0.0 if out_pers == 0.0 else float("inf")
    else:
        ratio = out_pers / in_pers

    ok = 0.3 <= ratio <= 5.0
    r.record(ok, "Topology persists under algebraic composition (ratio in [0.3, 5.0])",
             f"-- ratio = {ratio:.3f}")


# --- main --------------------------------------------------------------------

def main():
    print("=" * 72)
    print("VALIDATION: quaternion-monoid algebra")
    print("=" * 72)
    rng = np.random.default_rng(42)
    r = Result()

    print("\n[Identity laws]")
    test_left_identity(r, rng)
    test_right_identity(r, rng)

    print("\n[Associativity]")
    test_associativity(r, rng)

    print("\n[Closure]")
    test_closure(r, rng)

    print("\n[Stability under iteration]")
    test_stability(r, rng)
    test_power_consistency(r, rng)

    print("\n[GPU vs CPU]")
    test_gpu_bit_exact(r, rng)

    print("\n[Topology preservation]")
    test_topology_preservation(r, rng)

    total = r.passed + r.failed + r.skipped
    print()
    print("=" * 72)
    print(f"TOTAL: {r.passed} passed, {r.failed} failed, {r.skipped} skipped"
          f"  ({total} tests)")
    print("=" * 72)

    return 0 if r.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
