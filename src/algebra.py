"""Core compositional algebra over fixed-width quaternionic-symbolic packets.

A packet carries:
    - a unit quaternion (rotation in SO(3) lifted to S^3)
    - K small symbolic fields combined under associative monoid operations
    - a positive scaling factor combined multiplicatively

The construction is parameterized by the choice of symbolic-field combination
rules. Defaults below produce a closed associative binary operation with
two-sided identity, making the packet space a monoid.

References to "SHD-CCP" or any specific 64-bit field layout do not appear here.
This is the general construction. Concrete deployments choose specific bit
widths and sub-field counts.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import numpy as np


# ---------------------------------------------------------------------------
# Quaternion utilities
# ---------------------------------------------------------------------------

def normalize_quaternion(q: np.ndarray) -> np.ndarray:
    """Return q / ||q||. Accepts shape (4,) or (N, 4)."""
    q = np.asarray(q, dtype=np.float64)
    if q.ndim == 1:
        n = np.linalg.norm(q)
        return q / n if n > 0 else q
    n = np.linalg.norm(q, axis=-1, keepdims=True)
    n = np.where(n > 0, n, 1.0)
    return q / n


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
    size = 1 << n_bits
    t = np.zeros((size, size), dtype=np.int64)
    for i in range(size):
        for j in range(size):
            t[i, j] = i ^ j
    return t


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
    """
    quaternion: np.ndarray              # shape (4,), unit norm
    field_a: int = 0                    # 4-bit, default XOR lookup
    field_b: int = 0                    # 3-bit, default max
    field_c: int = 0                    # 5-bit, default add mod 32
    field_d: int = 0                    # 3-bit, default XOR lookup
    parity: int = 0                     # 1-bit, default XOR
    scale: float = 1.0                  # positive float, multiplicative

    def __post_init__(self):
        self.quaternion = normalize_quaternion(np.asarray(self.quaternion, dtype=np.float64))
        self.field_a = int(self.field_a) & 0xF
        self.field_b = int(self.field_b) & 0x7
        self.field_c = int(self.field_c) & 0x1F
        self.field_d = int(self.field_d) & 0x7
        self.parity = int(self.parity) & 0x1
        self.scale = float(self.scale)

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
        if not isinstance(other, Packet):
            return NotImplemented
        return (
            np.allclose(self.quaternion, other.quaternion, atol=1e-9)
            and self.field_a == other.field_a
            and self.field_b == other.field_b
            and self.field_c == other.field_c
            and self.field_d == other.field_d
            and self.parity == other.parity
            and np.isclose(self.scale, other.scale, atol=1e-9)
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


def packet_power(p: Packet, n: int) -> Packet:
    """Compute p ⊗ p ⊗ ... ⊗ p, n times. p^0 = identity_packet()."""
    if n < 0:
        raise ValueError("packet_power requires n >= 0")
    out = identity_packet()
    for _ in range(n):
        out = packet_product(out, p)
    return out
