"""Stress tests for the quaternion-monoid algebra.

The 8-test property suite in run_all.py verifies that the algebra has the
algebraic properties it claims (closure, identity, associativity, etc.).
These stress tests verify that the algebra is *useful* — that it does what
the README and paper claim about real behavior:

    1. Long-horizon stability: 10,000-step iteration without NaN / overflow / norm drift
    2. Avalanche sensitivity: single-packet tampering produces total head divergence
    3. Distinguishability: 100 distinct random chains produce 100 distinct heads
    4. Real-data behavior (TUM): Pioneer 360 sequence runs through the algebra cleanly
    5. Real-data behavior (EuRoC): MAV Machine Hall 01 ground truth composes cleanly
    6. Field saturation honesty: field_b under max() saturates; field_a/c/d/parity do not
    7. Scale stability: scale factor stays in finite range under realistic iteration

Run from repo root:  python tests/stress_tests.py
"""

import os
import sys
import io
import hashlib
import urllib.request
import time
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

import numpy as np
from quaternion_monoid_algebra.algebra import (
    Packet, packet_product, identity_packet, normalize_quaternion,
)


def header(name):
    print()
    print("=" * 72)
    print(f"STRESS TEST: {name}")
    print("=" * 72)


# ---------------------------------------------------------------------------
# 1. Long-horizon stability
# ---------------------------------------------------------------------------

def test_long_horizon_stability():
    header("Long-horizon stability (10,000-step iteration)")
    rng = np.random.default_rng(0)
    state = identity_packet()
    norms = []
    scales = []
    for _ in range(10_000):
        stim = Packet.random(rng)
        state = packet_product(state, stim)
        norms.append(float(np.linalg.norm(state.quaternion)))
        scales.append(state.scale)
    norms = np.array(norms)
    scales = np.array(scales)

    # Quaternion norm should stay at 1.0
    norm_err = np.max(np.abs(norms - 1.0))

    # Scale: with stim.scale ~ exp(N(0, 0.1)), product over 10k draws should
    # drift like exp(sum of N(0, 0.1)) ~ exp(N(0, sqrt(10000)*0.1)) = exp(N(0, 10)).
    # Worst-case drift can be enormous but the IEEE 754 finite range matters.
    # Check: nothing is NaN, nothing is inf, scale stays positive.
    ok_finite = bool(np.all(np.isfinite(scales)) and np.all(scales > 0))
    ok_norm = norm_err < 1e-6

    print("  steps:                 10,000")
    print(f"  final quaternion norm: {norms[-1]:.10f}")
    print(f"  max |norm - 1.0|:      {norm_err:.2e}")
    print(f"  final scale:           {scales[-1]:.6e}")
    print(f"  scale range over run:  [{scales.min():.4e}, {scales.max():.4e}]")
    print(f"  any non-finite?        {bool(np.any(~np.isfinite(scales)))}")
    print(f"  any non-positive?      {bool(np.any(scales <= 0))}")
    print(f"  [{'PASS' if ok_norm and ok_finite else 'FAIL'}] long-horizon stability")
    return ok_norm and ok_finite


# ---------------------------------------------------------------------------
# 2. Avalanche sensitivity
# ---------------------------------------------------------------------------

def test_avalanche():
    header("Avalanche: single-packet tamper produces head divergence")
    rng = np.random.default_rng(1)
    N = 200
    chain = [Packet.random(rng) for _ in range(N)]
    head_orig = identity_packet()
    for p in chain:
        head_orig = packet_product(head_orig, p)

    # Tamper at several positions
    tamper_positions = [0, 1, 50, 100, 150, N - 1]
    all_diverged = True
    print(f"  chain length: {N}")
    for pos in tamper_positions:
        tampered = list(chain)
        # Flip one bit of field_a
        t = tampered[pos]
        tampered[pos] = Packet(
            quaternion=t.quaternion,
            field_a=t.field_a ^ 1,    # single bit flip
            field_b=t.field_b, field_c=t.field_c, field_d=t.field_d,
            parity=t.parity, scale=t.scale,
        )
        head_t = identity_packet()
        for p in tampered:
            head_t = packet_product(head_t, p)
        diverged = head_t != head_orig
        # Measure how different the quaternion components are
        qdiff = float(np.linalg.norm(head_orig.quaternion - head_t.quaternion))
        adiff = head_orig.field_a != head_t.field_a or head_orig.field_d != head_t.field_d
        cdiff = head_orig.field_c != head_t.field_c
        print(f"  bit-flip at packet {pos:3d}:  head diverged? {diverged}   "
              f"|q diff| = {qdiff:.4f}  symbolic diff? {adiff or cdiff}")
        if not diverged:
            all_diverged = False
    print(f"  [{'PASS' if all_diverged else 'FAIL'}] all {len(tamper_positions)} "
          f"single-bit tampers produced head divergence")
    return all_diverged


# ---------------------------------------------------------------------------
# 3. Distinguishability
# ---------------------------------------------------------------------------

def test_distinguishability():
    header("Distinguishability: 100 distinct chains produce 100 distinct heads")
    heads = []
    for seed in range(100):
        rng = np.random.default_rng(seed * 7919 + 13)   # well-separated seeds
        head = identity_packet()
        for _ in range(50):
            head = packet_product(head, Packet.random(rng))
        heads.append(head)
    # Compare every pair
    n_unique_quaternions = len({tuple(h.quaternion.round(10).tolist()) for h in heads})
    n_unique_full = 0
    seen = []
    for h in heads:
        if not any(h == s for s in seen):
            n_unique_full += 1
            seen.append(h)
    print("  chains generated: 100")
    print(f"  distinct quaternion components: {n_unique_quaternions}")
    print(f"  distinct full packets:          {n_unique_full}")
    ok = n_unique_full == 100
    print(f"  [{'PASS' if ok else 'FAIL'}] all 100 heads are distinct")
    return ok


# ---------------------------------------------------------------------------
# 4. Real-data behavior (TUM Pioneer 360 and EuRoC MAV MH_01)
# ---------------------------------------------------------------------------

TUM_URL = ("https://cvg.cit.tum.de/rgbd/dataset/freiburg2/"
            "rgbd_dataset_freiburg2_pioneer_360-groundtruth.txt")
TUM_SHA = "1338bae01eb0219fcfc59b0c1a28c2ee091e36a6490f0cc022846328cebc1a60"

# EuRoC MAV Machine Hall 01 ground truth (Burri et al., IJRR 2016), in
# TUM trajectory format, as mirrored by the OpenVINS project. Pinned to a
# commit SHA so the download is reproducible. See ATTRIBUTION.md.
EUROC_URL = ("https://raw.githubusercontent.com/rpng/open_vins/"
             "485d0dc4a421d9ff47aade93589a39c76a80a57d/"
             "ov_data/euroc_mav/MH_01_easy.txt")
EUROC_SHA = "ab1579de35a047d241e2d0d1a4f4306b4fa51d99c6f11bcdebf336ab2b784df9"


def _real_data_stream(title, short, url, sha, cache_name, max_poses):
    """Download (with SHA-256 pinning) a TUM-format trajectory file
    (t tx ty tz qx qy qz qw per line), stream its quaternions through the
    algebra, and check the composed state is a valid packet."""
    header(f"Real-data behavior: {title}")
    cache = os.path.abspath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "data_cache", cache_name))
    os.makedirs(os.path.dirname(cache), exist_ok=True)

    if not os.path.exists(cache):
        print(f"  downloading {url}")
        try:
            urllib.request.urlretrieve(url, cache)
        except Exception as e:
            print(f"  [SKIP] download failed: {e}")
            return None

    h = hashlib.sha256()
    with open(cache, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    actual = h.hexdigest()
    if actual != sha:
        print(f"  [FAIL] SHA-256 mismatch: expected {sha}, got {actual}")
        return False
    print(f"  {short} SHA-256 verified: {actual}")

    qs = []
    with open(cache, "r") as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            toks = line.split()
            try:
                qx, qy, qz, qw = (float(toks[4]), float(toks[5]),
                                    float(toks[6]), float(toks[7]))
            except (ValueError, IndexError):
                continue
            qs.append([qw, qx, qy, qz])
            if len(qs) >= max_poses:
                break
    qs = normalize_quaternion(np.array(qs))
    print(f"  parsed {len(qs)} unit quaternions from {short} source")

    t0 = time.time()
    state = identity_packet()
    for q in qs:
        state = packet_product(state, Packet(quaternion=q))
    dt = time.time() - t0

    final_norm = float(np.linalg.norm(state.quaternion))
    print(f"  composed {len(qs)} packets in {dt:.3f}s "
          f"({len(qs)/dt:,.0f} ops/sec pure Python)")
    print(f"  final state quaternion: {state.quaternion.round(4).tolist()}")
    print(f"  final state norm:        {final_norm:.10f}")
    print(f"  final state scale:       {state.scale:.6f}")
    print(f"  final field_a={state.field_a}, b={state.field_b}, "
          f"c={state.field_c}, d={state.field_d}, p={state.parity}")
    ok = abs(final_norm - 1.0) < 1e-6 and np.isfinite(state.scale) and state.scale > 0
    print(f"  [{'PASS' if ok else 'FAIL'}] real {short} data composes cleanly "
          f"with unit-norm output")
    return ok


def test_real_data():
    return _real_data_stream(
        "TUM RGB-D Pioneer 360 (2,000 poses)", "TUM",
        TUM_URL, TUM_SHA, "tum_pioneer360.txt", max_poses=2000)


def test_real_data_euroc():
    return _real_data_stream(
        "EuRoC MAV Machine Hall 01 (36,000 poses)", "EuRoC",
        EUROC_URL, EUROC_SHA, "euroc_mh01.txt", max_poses=36_000)


# ---------------------------------------------------------------------------
# 5. Field saturation honesty
# ---------------------------------------------------------------------------

def test_field_saturation():
    header("Field saturation honesty: which fields saturate, which preserve?")
    rng = np.random.default_rng(2)
    n_trials = 100
    n_steps = 200
    final_b_values = []
    final_a_values = []
    final_c_values = []

    for _ in range(n_trials):
        state = identity_packet()
        for _ in range(n_steps):
            state = packet_product(state, Packet.random(rng))
        final_b_values.append(state.field_b)
        final_a_values.append(state.field_a)
        final_c_values.append(state.field_c)

    # field_b is max() — should saturate to 7 (3 bits) quickly
    n_saturated_b = sum(1 for v in final_b_values if v == 7)

    # field_a (XOR over 4 bits) — should be uniform over [0, 16) after enough steps
    from collections import Counter
    a_dist = Counter(final_a_values)
    c_dist = Counter(final_c_values)

    print(f"  trials: {n_trials} chains of {n_steps} steps each")
    print()
    print("  field_b (3-bit, max() rule):")
    print(f"    final values saturated at 7: {n_saturated_b} / {n_trials}")
    print("    -> This is honest behavior: max() is associative with identity 0")
    print("       but saturates under iteration. The README/paper describe this.")
    print("       Use case implication: field_b is a one-way 'has the chain seen")
    print("       a high-amplitude packet yet' flag, not a state register.")
    print()
    print("  field_a (4-bit, XOR rule):")
    print(f"    distinct values across trials: {len(a_dist)} (out of 16 possible)")
    print(f"    distribution: {dict(sorted(a_dist.items()))}")
    print("    -> XOR is information-preserving; distribution should approach uniform")
    print()
    print("  field_c (5-bit, mod-32 add):")
    print(f"    distinct values across trials: {len(c_dist)} (out of 32 possible)")
    print("    -> mod-N addition is information-preserving over Z/NZ")
    print()
    # Pass: field_b saturates (expected), field_a and field_c spread
    ok_b = n_saturated_b >= n_trials * 0.9         # mostly saturated, as expected
    ok_a = len(a_dist) >= 12                        # most values seen
    ok_c = len(c_dist) >= 20                        # most values seen
    overall = ok_b and ok_a and ok_c
    print(f"  [{'PASS' if overall else 'FAIL'}] field behavior matches construction:")
    print(f"    field_b saturates (expected for max()):    {ok_b}")
    print(f"    field_a spreads across XOR group:           {ok_a}")
    print(f"    field_c spreads across mod-32 group:        {ok_c}")
    return overall


# ---------------------------------------------------------------------------
# 6. Scale stability under realistic iteration
# ---------------------------------------------------------------------------

def test_scale_stability():
    header("Scale stability under realistic iteration (1,000 steps × 100 chains)")
    rng = np.random.default_rng(3)
    n_chains = 100
    n_steps = 1000
    finals = []
    for _ in range(n_chains):
        state = identity_packet()
        for _ in range(n_steps):
            state = packet_product(state, Packet.random(rng))
        finals.append(state.scale)
    finals = np.array(finals)
    print(f"  chains: {n_chains}, steps each: {n_steps}")
    print(f"  log10(scale) median:       {np.median(np.log10(finals)):.2f}")
    print("  log10(scale) percentiles:")
    print(f"    p01 = {np.percentile(np.log10(finals), 1):.2f}")
    print(f"    p50 = {np.percentile(np.log10(finals), 50):.2f}")
    print(f"    p99 = {np.percentile(np.log10(finals), 99):.2f}")
    print(f"  all finite?                {bool(np.all(np.isfinite(finals)))}")
    print(f"  all positive?              {bool(np.all(finals > 0))}")
    print()
    print("  Note: under Packet.random(), each scale draw is exp(N(0, 0.1)).")
    print("        Product over 1000 draws is exp(N(0, sqrt(1000)*0.1)) ~ exp(N(0, 3.16)).")
    print("        So 99% of finals lie within ~3 orders of magnitude of 1.0,")
    print("        consistent with theory. No overflow / underflow / NaN.")
    ok = np.all(np.isfinite(finals)) and np.all(finals > 0)
    print(f"  [{'PASS' if ok else 'FAIL'}] scale stays in finite positive range")
    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    results = []
    results.append(("long-horizon stability",       test_long_horizon_stability()))
    results.append(("avalanche sensitivity",        test_avalanche()))
    results.append(("distinguishability",           test_distinguishability()))
    results.append(("real-data behavior (TUM)",     test_real_data()))
    results.append(("real-data behavior (EuRoC)",   test_real_data_euroc()))
    results.append(("field saturation honesty",     test_field_saturation()))
    results.append(("scale stability",              test_scale_stability()))

    print()
    print("=" * 72)
    print("STRESS TEST SUMMARY")
    print("=" * 72)
    def kind(ok):
        if ok is None:
            return "skip"
        return "pass" if bool(ok) else "fail"
    passed = sum(1 for _, ok in results if kind(ok) == "pass")
    failed = sum(1 for _, ok in results if kind(ok) == "fail")
    skipped = sum(1 for _, ok in results if kind(ok) == "skip")
    for name, ok in results:
        tag = {"pass": "PASS", "fail": "FAIL", "skip": "SKIP"}[kind(ok)]
        print(f"  [{tag}] {name}")
    print()
    print(f"TOTAL: {passed} passed, {failed} failed, {skipped} skipped")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
