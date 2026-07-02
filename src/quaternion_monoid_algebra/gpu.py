"""GPU-accelerated batched compositional algebra via CuPy.

If CuPy is not installed, the module exports HAS_GPU = False and stub
implementations that raise on use. Tests detect this and report a clean skip.
"""

from __future__ import annotations
import numpy as np

try:
    import cupy as cp
    HAS_GPU = True
except Exception:
    cp = None
    HAS_GPU = False


def hamilton_product_batch_gpu(q1, q2):
    """Batched Hamilton product on GPU.
    q1, q2: shape (N, 4) FP32 arrays on GPU.
    Returns: shape (N, 4) FP32 array on GPU, bit-exact to NumPy reference
    when both sides use the same FP32 ordering.
    """
    if not HAS_GPU:
        raise RuntimeError("CuPy not available")
    w1, x1, y1, z1 = q1[:, 0], q1[:, 1], q1[:, 2], q1[:, 3]
    w2, x2, y2, z2 = q2[:, 0], q2[:, 1], q2[:, 2], q2[:, 3]
    out = cp.empty_like(q1)
    out[:, 0] = w1*w2 - x1*x2 - y1*y2 - z1*z2
    out[:, 1] = w1*x2 + x1*w2 + y1*z2 - z1*y2
    out[:, 2] = w1*y2 - x1*z2 + y1*w2 + z1*x2
    out[:, 3] = w1*z2 + x1*y2 - y1*x2 + z1*w2
    return out


def hamilton_product_batch_cpu(q1, q2):
    """Bit-exact CPU reference for the GPU batched Hamilton product.
    Same arithmetic, same FP32 precision, same operation order."""
    w1, x1, y1, z1 = q1[:, 0], q1[:, 1], q1[:, 2], q1[:, 3]
    w2, x2, y2, z2 = q2[:, 0], q2[:, 1], q2[:, 2], q2[:, 3]
    out = np.empty_like(q1)
    out[:, 0] = w1*w2 - x1*x2 - y1*y2 - z1*z2
    out[:, 1] = w1*x2 + x1*w2 + y1*z2 - z1*y2
    out[:, 2] = w1*y2 - x1*z2 + y1*w2 + z1*x2
    out[:, 3] = w1*z2 + x1*y2 - y1*x2 + z1*w2
    return out
