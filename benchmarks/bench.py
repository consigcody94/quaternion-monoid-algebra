"""Throughput benchmarks for the packet algebra.

Measures the three implementation tiers on this machine:
    1. Scalar Python  — packet_product() in a loop
    2. Vectorized CPU — packet_product_batch() over a PacketArray
    3. GPU (optional) — batched Hamilton product via CuPy, if installed

Run from repo root:  python benchmarks/bench.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import numpy as np
from quaternion_monoid_algebra import (
    Packet, PacketArray, packet_product, packet_product_batch, reduce_packets,
)
from quaternion_monoid_algebra.gpu import HAS_GPU


def bench_scalar(n=20_000):
    rng = np.random.default_rng(0)
    pairs = [(Packet.random(rng), Packet.random(rng)) for _ in range(n)]
    t0 = time.perf_counter()
    for a, b in pairs:
        packet_product(a, b)
    dt = time.perf_counter() - t0
    print(f"scalar packet_product:      {n:>12,} ops in {dt:8.3f}s  "
          f"= {n/dt:>14,.0f} ops/sec")


def bench_batch(n=2_000_000):
    rng = np.random.default_rng(1)
    pa = PacketArray.random(n, rng)
    pb = PacketArray.random(n, rng)
    packet_product_batch(pa, pb)                    # warm-up
    t0 = time.perf_counter()
    packet_product_batch(pa, pb)
    dt = time.perf_counter() - t0
    print(f"batch packet_product:       {n:>12,} ops in {dt:8.3f}s  "
          f"= {n/dt:>14,.0f} ops/sec")


def bench_tree_reduce(n=1_000_000):
    rng = np.random.default_rng(2)
    pa = PacketArray.random(n, rng)
    t0 = time.perf_counter()
    reduce_packets(pa)
    dt = time.perf_counter() - t0
    print(f"tree-reduce chain head:     {n:>12,} pkts in {dt:8.3f}s  "
          f"= {n/dt:>14,.0f} pkts/sec")


def bench_gpu(n=10_000_000):
    if not HAS_GPU:
        print("GPU Hamilton product:       (CuPy not available, skipped)")
        return
    import cupy as cp
    from quaternion_monoid_algebra.gpu import hamilton_product_batch_gpu
    rng = np.random.default_rng(3)
    q1 = cp.asarray(rng.standard_normal((n, 4)).astype(np.float32))
    q2 = cp.asarray(rng.standard_normal((n, 4)).astype(np.float32))
    hamilton_product_batch_gpu(q1, q2)              # warm-up + JIT
    cp.cuda.Stream.null.synchronize()
    t0 = time.perf_counter()
    hamilton_product_batch_gpu(q1, q2)
    cp.cuda.Stream.null.synchronize()
    dt = time.perf_counter() - t0
    print(f"GPU Hamilton product:       {n:>12,} ops in {dt:8.3f}s  "
          f"= {n/dt:>14,.0f} ops/sec")


if __name__ == "__main__":
    print("=" * 72)
    print("BENCHMARKS: quaternion-monoid algebra")
    print("=" * 72)
    bench_scalar()
    bench_batch()
    bench_tree_reduce()
    bench_gpu()
