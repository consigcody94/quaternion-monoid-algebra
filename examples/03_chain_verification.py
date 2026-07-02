"""Example 3: Algebraic chain verification.

A producer emits a sequence of packets p_1, p_2, ..., p_N and signs the
running composition chain_head = I ⊗ p_1 ⊗ p_2 ⊗ ... ⊗ p_N. A verifier
recomputes the chain and compares to the signed head.

Tampering with any packet anywhere in the chain produces a different head
(under non-commutativity of the quaternion component, and additionally under
the XOR / mod / multiply sub-field operations on the symbolic factors).
"""

import os
import sys
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import numpy as np
from quaternion_monoid_algebra import Packet, packet_product, identity_packet


def produce_chain(n: int, seed: int = 0):
    rng = np.random.default_rng(seed)
    packets = [Packet.random(rng) for _ in range(n)]
    head = identity_packet()
    for p in packets:
        head = packet_product(head, p)
    return packets, head


def verify_chain(packets, claimed_head):
    head = identity_packet()
    for p in packets:
        head = packet_product(head, p)
    return head == claimed_head


def tamper(packets, index: int):
    rng = np.random.default_rng(99)
    tampered = list(packets)
    tampered[index] = Packet.random(rng)
    return tampered


if __name__ == "__main__":
    packets, head = produce_chain(n=100)
    print(f"Produced 100-packet chain. Verifier confirms head: {verify_chain(packets, head)}")

    # Tamper somewhere in the middle
    tampered = tamper(packets, index=42)
    print("After tampering with packet 42 of 100,")
    print(f"  verifier recomputes head and compares: matches? {verify_chain(tampered, head)}")
    print()
    print("Note: this provides algebraic consistency. For full tamper-evidence")
    print("the chain head should additionally be cryptographically signed.")
