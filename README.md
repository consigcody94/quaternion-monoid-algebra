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

Installable Python package (`src/quaternion_monoid_algebra/`) with a scalar API, a vectorized batch API, and a CuPy GPU port. Three layers of validation in `tests/`: a pytest + Hypothesis property suite, the original 8-test property runner, and 6 stress tests (including real-data behavior on a public TUM RGB-D sequence). White paper in `paper/`. Use cases discussed in `examples/`.

## Install

```bash
pip install git+https://github.com/consigcody94/quaternion-monoid-algebra
```

or, for development:

```bash
git clone https://github.com/consigcody94/quaternion-monoid-algebra
cd quaternion-monoid-algebra
pip install -e .[test]
pip install gudhi            # optional: enables the topology-preservation test
pip install cupy-cuda12x     # optional: enables the GPU tests
```

## Validation summary

```
[Identity laws]           Left and right identity hold across 100 packets
[Associativity]           512 random triples, 0 violations
[Closure]                 500 random pairs, 0 invalid products
[Stability]               1000-step self-product chain stays unit-norm
[GPU bit-exact]           max GPU vs CPU diff on Hamilton product = 0.00e+00
[Topology preservation]   H₁ persistence ratio in target band [0.3, 5.0]

TOTAL: 8 of 8 property tests pass, plus 6 of 6 stress tests
       and a 49-test pytest + Hypothesis suite
```

Reproduce with:

```bash
pytest                          # property-based suite (Hypothesis-driven)
python tests/run_all.py         # the 8-test property runner above
python tests/stress_tests.py    # stress tests (downloads TUM data, SHA-256 verified)
python benchmarks/bench.py      # throughput benchmarks
```

A note on floating point: the symbolic sub-fields are integer-exact under any association. The quaternion sub-operation is associative exactly over the reals and up to rounding (~1e-16) in IEEE 754 arithmetic; packet equality compares the quaternion at absolute 1e-9 per component and the scale at relative 1e-9.

## Quick start

```python
from quaternion_monoid_algebra import packet_product, identity_packet, Packet
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

## Batch API

For throughput, hold N packets as a struct-of-arrays and compose them with vectorized NumPy kernels. Chain reduction runs as an O(log N)-depth pairwise tree, which is legal because ⊗ is associative:

```python
from quaternion_monoid_algebra import PacketArray, packet_product_batch, reduce_packets

pa = PacketArray.random(1_000_000)
pb = PacketArray.random(1_000_000)

pc = packet_product_batch(pa, pb)   # 1M elementwise compositions
head = reduce_packets(pa)           # chain head p₀ ⊗ p₁ ⊗ ... ⊗ pₙ₋₁, tree-reduced
```

Measured on a Ryzen 5700G (see `benchmarks/bench.py` to reproduce on your machine):

| tier | throughput |
|---|---|
| scalar `packet_product` (pure Python) | ~40 k ops/sec |
| batch `packet_product_batch` (NumPy) | ~3.6 M ops/sec |
| tree-reduce chain head (NumPy) | ~2.2 M packets/sec |

Custom sub-field operations can be swapped in via lookup tables; check a candidate table once with `validate_monoid_table(table)` (it verifies closure, the identity laws, and full associativity, with a counterexample on failure) before passing it to `packet_product`.

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
