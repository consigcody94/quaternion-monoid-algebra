"""Core compositional algebra over fixed-width quaternionic-symbolic packets.

A packet carries:
    - a unit quaternion (rotation in SO(3) lifted to S^3)
    - K small symbolic fields combined under associative monoid operations
    - a positive scaling factor combined multiplicatively

The construction is parameterized by the choice of symbolic-field combination
rules. Defaults below produce a closed associative binary operation with
two-sided identity, making the packet space a monoid.

A note on floating point: associativity of the quaternion sub-operation holds
exactly over the reals; in IEEE 754 arithmetic it holds up to rounding, which
is why ``Packet.__eq__`` compares with a small tolerance: absolute (1e-9) on
the quaternion, whose components are unit-bounded, and relative (1e-9) on the
scale, which is unbounded under multiplication. The symbolic sub-fields are
integer-exact.

References to "SHD-CCP" or any specific 64-bit field layout do not appear here.
This is the general construction. Concrete deployments choose specific bit
widths and sub-field counts.
"""

from __future__ import annotations
from dataclasses import dataclass
from functools import reduce
from typing import Iterable, Optional
import numpy as np


# ---------------------------------------------------------------------------
# Quaternion utilities
# ---------------------------------------------------------------------------

def normalize_quaternion(q: np.ndarray) -> np.ndarray:
    """Return q / ||q||. Accepts shape (4,) or (N, 4).

    The input is pre-scaled by its largest-magnitude component before the
    norm is computed, so normalization is correct even where a naive
    sum-of-squares would overflow (components above ~1e154) or underflow to
    zero (components below ~1e-162).

    Zero rows are returned unchanged (there is no meaningful direction to
    normalize to). ``Packet`` rejects zero quaternions at construction, so
    inside the algebra this branch is never taken.
    """
    q = np.asarray(q, dtype=np.float64)
    if q.ndim == 1:
        m = np.max(np.abs(q))
        if m == 0 or not np.isfinite(m):
            return q
        qs = q / m                       # components in [-1, 1], norm in [1, 2]
        return qs / np.linalg.norm(qs)
    m = np.max(np.abs(q), axis=-1, keepdims=True)
    safe = np.where((m > 0) & np.isfinite(m), m, 1.0)
    qs = q / safe
    n = np.linalg.norm(qs, axis=-1, keepdims=True)
    n = np.where(n > 0, n, 1.0)
    return qs / n


def hamilton_product(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    """Hamilton product of two quaternions in (w, x, y, z) layout.
    Accepts shape (4,) or (N, 4). Returns the same shape."""
    q1 = np.asarray(q1, dtype=np.float64)
    q2 = np.asarray(q2, dtype=np.float64)
    if q1.ndim == 1:
        w1, x1, y1, z1 = q1
        w2, x2, y2, z2 = q2
        return np.array([
            w1*w2 - x1*x2 - y1*y2 - z1*z2,
            w1*x2 + x1*w2 + y1*z2 - z1*y2,
            w1*y2 - x1*z2 + y1*w2 + z1*x2,
            w1*z2 + x1*y2 - y1*x2 + z1*w2,
        ])
    w1, x1, y1, z1 = q1[..., 0], q1[..., 1], q1[..., 2], q1[..., 3]
    w2, x2, y2, z2 = q2[..., 0], q2[..., 1], q2[..., 2], q2[..., 3]
    out = np.empty_like(q1)
    out[..., 0] = w1*w2 - x1*x2 - y1*y2 - z1*z2
    out[..., 1] = w1*x2 + x1*w2 + y1*z2 - z1*y2
    out[..., 2] = w1*y2 - x1*z2 + y1*w2 + z1*x2
    out[..., 3] = w1*z2 + x1*y2 - y1*x2 + z1*w2
    return out


# ---------------------------------------------------------------------------
# Lookup tables that act as monoid operations on small index sets
# ---------------------------------------------------------------------------

def make_xor_table(n_bits: int) -> np.ndarray:
    """Build a Cayley table T[i, j] = i XOR j over {0,...,2^n - 1}.
    XOR over Z_2^n is associative, commutative, and has 0 as identity."""
    idx = np.arange(1 << n_bits, dtype=np.int64)
    return np.bitwise_xor.outer(idx, idx)


def validate_monoid_table(table: np.ndarray, identity: int = 0) -> None:
    """Check that a Cayley table defines a monoid on {0, ..., size-1}.

    Verifies closure (all entries in range), the two identity laws for the
    given identity element, and full associativity
    T[T[i,j],k] == T[i,T[j,k]] over every triple. Raises ValueError with a
    counterexample on the first violated law. Cost is O(size^3) memory and
    time, fine for the small sub-field tables this library uses.

    Use this to vet a custom ``form_table``/``spin_table`` before passing it
    to :func:`packet_product`, which does not re-validate on every call.
    """
    t = np.asarray(table)
    if t.ndim != 2 or t.shape[0] != t.shape[1]:
        raise ValueError(f"table must be square, got shape {t.shape}")
    size = t.shape[0]
    if not (0 <= identity < size):
        raise ValueError(f"identity {identity} out of range for size {size}")
    if t.min() < 0 or t.max() >= size:
        raise ValueError("table is not closed: entries outside [0, size)")
    idx = np.arange(size)
    if not np.array_equal(t[identity, :], idx):
        j = int(np.argmax(t[identity, :] != idx))
        raise ValueError(f"left identity fails: T[{identity},{j}] = {t[identity, j]} != {j}")
    if not np.array_equal(t[:, identity], idx):
        i = int(np.argmax(t[:, identity] != idx))
        raise ValueError(f"right identity fails: T[{i},{identity}] = {t[i, identity]} != {i}")
    # (i*j)*k vs i*(j*k) for all triples, fully vectorized:
    lhs = t[t, :]           # lhs[i, j, k] = T[T[i,j], k]
    rhs = t[:, t]           # rhs[i, j, k] = T[i, T[j,k]]
    if not np.array_equal(lhs, rhs):
        i, j, k = np.unravel_index(int(np.argmax(lhs != rhs)), lhs.shape)
        raise ValueError(
            f"associativity fails at ({i},{j},{k}): "
            f"T[T[{i},{j}],{k}] = {lhs[i, j, k]} but T[{i},T[{j},{k}]] = {rhs[i, j, k]}")


# ---------------------------------------------------------------------------
# Default sub-field choices
# ---------------------------------------------------------------------------

DEFAULT_SYMBOLIC_BITS = (4, 3, 5, 3)   # widths of the K symbolic sub-fields
DEFAULT_MOD = 32                        # modulus for the additive sub-field

# Pre-built tables under default widths
_FORM_TABLE = make_xor_table(4)        # 16x16
_SPIN_TABLE = make_xor_table(3)        # 8x8


# ---------------------------------------------------------------------------
# Packet data structure and operations
# ---------------------------------------------------------------------------

@dataclass
class Packet:
    """A fixed-width quaternionic-symbolic state packet.

    Fields are deliberately generic. A concrete deployment may bit-pack these
    into a specific layout; the algebra is defined on the unpacked values.

    Construction validates the packet: the quaternion must be finite and
    nonzero (it is renormalized to unit length), the symbolic fields are
    masked into their declared bit widths, and the scale must be a finite
    positive number. Rejecting degenerate inputs at the boundary is what
    makes the closure property hold unconditionally inside the algebra.
    """
    quaternion: np.ndarray              # shape (4,), unit norm
    field_a: int = 0                    # 4-bit, default XOR lookup
    field_b: int = 0                    # 3-bit, default max
    field_c: int = 0                    # 5-bit, default add mod 32
    field_d: int = 0                    # 3-bit, default XOR lookup
    parity: int = 0                     # 1-bit, default XOR
    scale: float = 1.0                  # positive float, multiplicative

    def __post_init__(self):
        q = np.asarray(self.quaternion, dtype=np.float64)
        if q.shape != (4,):
            raise ValueError(f"quaternion must have shape (4,), got {q.shape}")
        if not np.all(np.isfinite(q)):
            raise ValueError(f"quaternion has non-finite components: {q.tolist()}")
        if np.max(np.abs(q)) == 0.0:
            raise ValueError("quaternion must be nonzero (zero has no direction to normalize)")
        self.quaternion = normalize_quaternion(q)
        self.field_a = int(self.field_a) & 0xF
        self.field_b = int(self.field_b) & 0x7
        self.field_c = int(self.field_c) & 0x1F
        self.field_d = int(self.field_d) & 0x7
        self.parity = int(self.parity) & 0x1
        scale = float(self.scale)
        if not np.isfinite(scale) or scale <= 0.0:
            raise ValueError(f"scale must be a finite positive number, got {scale}")
        self.scale = scale

    @staticmethod
    def random(rng: Optional[np.random.Generator] = None) -> "Packet":
        if rng is None:
            rng = np.random.default_rng()
        q = rng.standard_normal(4)
        q = q / np.linalg.norm(q)
        return Packet(
            quaternion=q,
            field_a=int(rng.integers(0, 16)),
            field_b=int(rng.integers(0, 8)),
            field_c=int(rng.integers(0, 32)),
            field_d=int(rng.integers(0, 8)),
            parity=int(rng.integers(0, 2)),
            scale=float(np.exp(rng.standard_normal() * 0.1)),  # positive
        )

    def __eq__(self, other: object) -> bool:
        """Tolerant equality: quaternion within absolute 1e-9 per component
        (components are unit-bounded), scale within relative 1e-9 (scale is
        unbounded under multiplicative composition), symbolic fields exact."""
        if not isinstance(other, Packet):
            return NotImplemented
        return (
            np.allclose(self.quaternion, other.quaternion, rtol=0.0, atol=1e-9)
            and self.field_a == other.field_a
            and self.field_b == other.field_b
            and self.field_c == other.field_c
            and self.field_d == other.field_d
            and self.parity == other.parity
            and np.isclose(self.scale, other.scale, rtol=1e-9, atol=0.0)
        )

    def __repr__(self) -> str:
        return (f"Packet(q={self.quaternion.round(4).tolist()}, "
                f"a={self.field_a}, b={self.field_b}, c={self.field_c}, "
                f"d={self.field_d}, p={self.parity}, s={self.scale:.4f})")


def identity_packet() -> Packet:
    """The two-sided identity element of the monoid: I such that I ⊗ p = p ⊗ I = p."""
    return Packet(
        quaternion=np.array([1.0, 0.0, 0.0, 0.0]),
        field_a=0, field_b=0, field_c=0, field_d=0, parity=0,
        scale=1.0,
    )


def packet_product(p1: Packet, p2: Packet,
                    form_table: Optional[np.ndarray] = None,
                    spin_table: Optional[np.ndarray] = None) -> Packet:
    """Compose two packets: p1 ⊗ p2 is itself a valid packet.

    Field-by-field combination:
        quaternion : Hamilton product (inherits S^3 group structure), then normalize
        field_a    : lookup table (default XOR, has identity 0)
        field_b    : max (lattice operation, has identity 0)
        field_c    : add mod 32 (Z/32Z additive group, has identity 0)
        field_d    : lookup table (default XOR, has identity 0)
        parity     : XOR (Z_2, has identity 0)
        scale      : multiply (positive reals under multiplication, has identity 1)

    Each per-field operation is associative with an identity element. Therefore
    the field-wise composition is associative with the identity_packet() as
    the two-sided identity.

    Custom tables are not re-validated here (this is the hot path); check
    them once with :func:`validate_monoid_table` before use.
    """
    if form_table is None:
        form_table = _FORM_TABLE
    if spin_table is None:
        spin_table = _SPIN_TABLE

    new_q = normalize_quaternion(hamilton_product(p1.quaternion, p2.quaternion))
    new_a = int(form_table[p1.field_a, p2.field_a])
    new_b = int(max(p1.field_b, p2.field_b))
    new_c = int((p1.field_c + p2.field_c) % DEFAULT_MOD)
    new_d = int(spin_table[p1.field_d, p2.field_d])
    new_p = (p1.parity ^ p2.parity) & 0x1
    new_s = float(p1.scale * p2.scale)

    return Packet(
        quaternion=new_q,
        field_a=new_a, field_b=new_b, field_c=new_c, field_d=new_d,
        parity=new_p, scale=new_s,
    )


def compose(packets: Iterable[Packet]) -> Packet:
    """Left-fold a sequence of packets from the identity:
    I ⊗ p_1 ⊗ p_2 ⊗ ... ⊗ p_n. Returns identity_packet() for an empty input."""
    return reduce(packet_product, packets, identity_packet())


def packet_power(p: Packet, n: int) -> Packet:
    """Compute p ⊗ p ⊗ ... ⊗ p, n times, in O(log n) products. p^0 = identity.

    Uses exponentiation by squaring, which is valid precisely because ⊗ is
    associative. The symbolic sub-fields are integer-exact under any
    association; the quaternion component may differ from the sequential
    fold by floating-point rounding on the order of machine epsilon, which
    is within the tolerance ``Packet.__eq__`` compares at.
    """
    if n < 0:
        raise ValueError("packet_power requires n >= 0")
    result = identity_packet()
    base = p
    while n > 0:
        if n & 1:
            result = packet_product(result, base)
        n >>= 1
        if n:
            base = packet_product(base, base)
    return result
