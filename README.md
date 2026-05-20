# Quaternion-Monoid Algebra

[![DOI](https://zenodo.org/badge/1243952950.svg)](https://doi.org/10.5281/zenodo.20301069)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A compositional algebra over fixed-width quaternionic-symbolic state packets. Defines a closed associative binary operation with two-sided identity on a packet space whose elements carry a unit-quaternion rotation plus symbolic metadata plus a scaling factor. Implements the construction on CPU and GPU with bit-exact correspondence between the two implementations.

The result is that a packet space which would otherwise be a passive data container becomes an active algebraic element — composable, chainable, and admitting a single-cycle hardware implementation.

## What this is

Given a fixed-width packet structure of the form:

```
packet = (quaternion, symbolic_fields..., scaling_factor)
```

this library defines a binary operation `packet_product` (denoted `⊗`) such that for any two packets `p1` and `p2`:

- `p1 ⊗ p2` is itself a valid packet of the same width (**closure**)
- there exists a packet `I` such that `I ⊗ p = p ⊗ I = p` for all `p` (**two-sided identity**)
- `(a ⊗ b) ⊗ c = a ⊗ (b ⊗ c)` for all valid triples (**associativity**)
- iterating the operation `state[t+1] = state[t] ⊗ stim[t]` preserves the H₁ persistent-homology signature of the input stream within a bounded ratio (**topology preservation**)

Together, closure + associativity + identity make the packet space a **monoid**. Topology preservation is an additional empirical property documented by the validation suite.

## Why this might be useful

Three application classes the construction supports natively:

1. **Composable agent state evolution.** `state[t+1] = state[t] ⊗ stimulus[t]` is a single bounded-width operation per time step. On a CPU/GPU pipeline it runs at tens to hundreds of millions of operations per second. On a single-cycle FPGA reference design it runs at the clock rate of the fabric.

2. **Algebraic chain verification.** For an N-packet chain produced sequentially, the verifier can compute `I ⊗ p₁ ⊗ p₂ ⊗ ... ⊗ pₙ` and compare to a signed chain-head packet. This is an alternative to Merkle-tree-style O(log n) verification with O(n) operations at constant per-operation cost, with an additional algebraic-consistency check beyond cryptographic verification.

3. **Multi-source state composition.** Combining N independently-evolving state packets via left-fold composition yields a single composed-state packet that algebraically encodes the multi-source state.

## Status

Reference implementation in Python (`src/`). Eight validation tests in `tests/` covering identity, associativity, closure, stability under iteration, GPU/CPU bit-exact correspondence, and topology preservation. White paper in `paper/`. Use cases discussed in `examples/`.

## Validation summary

```
[Identity laws]           Left and right identity hold across 100 packets
[Associativity]           512 random triples, 0 violations
[Closure]                 500 random pairs, 0 invalid products
[Stability]               1000-step self-product chain stays unit-norm
[GPU bit-exact]           max GPU vs CPU diff on Hamilton product = 0.00e+00
[Topology preservation]   H₁ persistence ratio in target band [0.3, 5.0]

TOTAL: 8 of 8 tests pass
```

Reproduce with:

```bash
python -m venv venv && source venv/bin/activate    # or venv\Scripts\activate on Windows
pip install numpy scipy gudhi persim
pip install cupy-cuda12x nvidia-cuda-nvrtc-cu12     # for GPU tests; optional
python tests/run_all.py
```

## Quick start

```python
from src.algebra import packet_product, identity_packet, Packet
import numpy as np

p1 = Packet.random()
p2 = Packet.random()
I = identity_packet()

p3 = packet_product(p1, p2)          # ⊗
assert packet_product(I, p3) == p3   # left identity
assert packet_product(p3, I) == p3   # right identity

# Associativity
a, b, c = Packet.random(), Packet.random(), Packet.random()
assert packet_product(packet_product(a, b), c) == packet_product(a, packet_product(b, c))

# Agent state evolution
state = identity_packet()
for stim in stimulus_stream:
    state = packet_product(state, stim)
```

## Paper

A standalone write-up of the construction and its properties is in [`paper/compositional_algebra.md`](paper/compositional_algebra.md). It covers the field-by-field construction, the proof sketches for associativity of each sub-field operation, the topology-preservation claim, and the three application classes above.

## Use case examples

Generic examples (no domain-specific framing) in `examples/`:

- `01_agent_state.py` — composable state evolution under a stream of stimuli
- `02_swarm_composition.py` — multi-agent state combination
- `03_chain_verification.py` — algebraic audit-chain alternative to Merkle verification

## Author and provenance

This work is by Cody Churchwell ([@consigcody94](https://github.com/consigcody94)). The construction was developed with AI as an engineering assistant for implementation, validation, GPU porting, and documentation. The conceptual direction, evaluative choices, and the specific algebraic structure imposed on the packet space were the author's. Released under MIT license to encourage open use and extension. If you build on it, an attribution is appreciated but not required.

## Contributing

PRs welcome. Particularly interested in:

- Alternative sub-field constructions (other than Hamilton, lookup-table substitution, lattice max, mod-N addition, multiplicative scaling) that preserve associativity
- Real-world dataset validation results
- Hardware implementations (Verilog/SystemVerilog references, ASIC synthesis numbers)
- Theoretical results about the topology-preservation property
- Connections to existing algebraic-structure literature this construction may be related to

## License

MIT — see [`LICENSE`](LICENSE).
