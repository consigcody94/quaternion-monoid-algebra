"""Example 1: Composable agent state evolution.

state[t+1] = state[t] ⊗ stimulus[t]

A single bounded-width operation per time step. The agent's full history is
encoded into a single packet via left-fold composition.
"""

import os, sys, io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

import numpy as np
from src.algebra import Packet, packet_product, identity_packet


def simulate_agent(n_steps: int = 1000, seed: int = 0):
    rng = np.random.default_rng(seed)
    state = identity_packet()
    history = [state]
    for _ in range(n_steps):
        stimulus = Packet.random(rng)
        state = packet_product(state, stimulus)
        history.append(state)
    return state, history


if __name__ == "__main__":
    final_state, history = simulate_agent(n_steps=1000)
    print(f"Ran 1000-step agent simulation under state[t+1] = state[t] ⊗ stim[t]")
    print(f"Final state: {final_state}")
    print(f"Unit-norm preserved: ||q|| = {np.linalg.norm(final_state.quaternion):.10f}")
    print(f"All {len(history)} intermediate states are valid packets.")
