"""Example 2: Multi-source state composition (swarm or fleet).

N agents each produce an independent state packet. The composed multi-agent
state is the left-fold:
    composed = p_1 ⊗ p_2 ⊗ ... ⊗ p_N

Because ⊗ is associative, the composition can be computed in any order or as
a tree-reduce in parallel. It is NOT commutative on the quaternion factor,
so the order of agents matters in general.
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from functools import reduce
from src.algebra import Packet, packet_product, identity_packet


def compose_swarm(n_agents: int = 50, seed: int = 0):
    rng = np.random.default_rng(seed)
    agents = [Packet.random(rng) for _ in range(n_agents)]
    composed = reduce(packet_product, agents, identity_packet())
    return agents, composed


def tree_reduce_compose(agents):
    """Composition as a parallel tree-reduce — same result as left-fold by
    associativity, but parallelizable."""
    layer = list(agents)
    while len(layer) > 1:
        next_layer = []
        for i in range(0, len(layer) - 1, 2):
            next_layer.append(packet_product(layer[i], layer[i+1]))
        if len(layer) % 2 == 1:
            next_layer.append(layer[-1])
        layer = next_layer
    return layer[0] if layer else identity_packet()


if __name__ == "__main__":
    agents, left_fold = compose_swarm(n_agents=50, seed=0)
    tree = tree_reduce_compose(agents)
    print(f"Composed 50-agent swarm via left-fold and tree-reduce.")
    print(f"Left-fold result:  {left_fold}")
    print(f"Tree-reduce result: {tree}")
    print(f"Identical? {left_fold == tree}")
    print()
    print("(Associativity guarantees same result regardless of reduction order.")
    print(" Non-commutativity means changing agent order produces a different result.)")
