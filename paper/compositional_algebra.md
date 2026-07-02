# Compositional Algebra over Fixed-Width Quaternionic-Symbolic State Packets

**Author:** Cody Churchwell ([@consigcody94](https://github.com/consigcody94))
**Status:** Open-source release, MIT license
**Date:** May 2026
**Repository:** [github.com/consigcody94/quaternion-monoid-algebra](https://github.com/consigcody94/quaternion-monoid-algebra)

---

## Abstract

This paper introduces a compositional algebra over a fixed-width packet structure that carries a unit quaternion, a small number of symbolic metadata fields, and a positive scaling factor. A closed binary operation is defined on the packet space with the property that the space, equipped with this operation, forms a monoid: closure under the operation, two-sided identity, and associativity. The construction is field-by-field. Each sub-field operation is chosen from a small set of associative monoid operations on its respective value space (Hamilton multiplication on the quaternion factor; lookup-table substitution, lattice max, modular addition, parity XOR, and multiplicative scaling on the symbolic and scaling factors). The composite operation inherits associativity from the per-field operations. Empirical validation across eight tests (identity laws, associativity over 512 random triples, closure over 500 random pairs, stability under 1000 iterated compositions, bit-exact GPU correspondence, topology preservation under iterated composition) confirms the construction behaves as described. Three application classes follow naturally: composable agent state evolution, algebraic chain verification, and multi-source state composition.

---

## 1. Motivation

A common problem in robotics, swarm coordination, and accountability infrastructure is the need to maintain a bounded-width, time-evolving state representation that is composable, verifiable, and efficient enough to deploy on edge hardware. Existing representations are typically either:

1. **Floating-point quaternion streams.** Compact for rotation but provide no native composition operation beyond Hamilton multiplication on the rotation component itself, and carry no symbolic metadata.
2. **Variable-width audit chains.** Cryptographic hashes plus structured metadata, compositional via Merkle trees, but variable-width per record and not amenable to single-cycle hardware composition.
3. **Vector embeddings.** Composable via vector arithmetic but typically high-dimensional, lossy, and lacking the unit-quaternion guarantee for rotational state.

This paper defines a fixed-width construction that fills the gap. A packet carries a unit quaternion plus a small number of symbolic metadata fields plus a scaling factor, with a defined composition operation whose result is itself a packet of the same width. The resulting algebra has three useful properties simultaneously: closure under composition, the algebraic structure of a monoid (so chains of operations compose freely), and topology preservation under iterated composition (so the geometric structure of an input stream survives transformation through the algebra).

## 2. Construction

### 2.1 The packet structure

A packet is the tuple:

```
packet = (q, f_a, f_b, f_c, f_d, π, s)
```

where:

- `q ∈ S^3` is a unit quaternion in (w, x, y, z) layout
- `f_a` is a `b_a`-bit symbolic field (default 4 bits)
- `f_b` is a `b_b`-bit symbolic field (default 3 bits)
- `f_c` is a `b_c`-bit symbolic field (default 5 bits)
- `f_d` is a `b_d`-bit symbolic field (default 3 bits)
- `π ∈ {0, 1}` is a parity bit
- `s ∈ R+` is a positive scaling factor (default IEEE-754 binary16)

The field widths are parameters of the construction. The defaults (4, 3, 5, 3 bits) plus parity, plus the unit quaternion (32 bits if encoded under smallest-three) plus an FP16 scaling factor, fit a 64-bit packet. Other field width choices give other packet widths.

### 2.2 The composition operation

For two packets `p1 = (q1, f_a1, ..., s1)` and `p2 = (q2, f_a2, ..., s2)`, the composition `p1 ⊗ p2` is defined field-by-field:

| Sub-field | Operation | Associativity rationale |
|---|---|---|
| `q` | Hamilton product, then normalize | Inherits S³ group structure (Hamilton 1843) |
| `f_a` | `T_a[i, j]` lookup, default `i ⊕ j` | XOR over Z₂^b is an abelian group with identity 0 |
| `f_b` | `max(i, j)` | Lattice max is associative and idempotent, identity 0 |
| `f_c` | `(i + j) mod 2^b_c` | Z/2^b_cZ additive group, identity 0 |
| `f_d` | `T_d[i, j]` lookup, default `i ⊕ j` | XOR over Z₂^b is an abelian group with identity 0 |
| `π` | `π_1 ⊕ π_2` | Z₂ additive group, identity 0 |
| `s` | `s_1 · s_2` | R+ under multiplication, identity 1 |

The identity element is:

```
I = (q_identity, 0, 0, 0, 0, 0, 1)
```

where `q_identity = (1, 0, 0, 0)` is the quaternion identity.

### 2.3 Monoid properties

**Closure.** Each per-field operation produces a value in the same field. The Hamilton product of two unit quaternions, after normalization, is a unit quaternion. XOR and modular addition stay in their finite range. Max of two values in `[0, 2^b)` stays in `[0, 2^b)`. Multiplication of positive reals is positive real. Therefore `p1 ⊗ p2` is a valid packet.

**Two-sided identity.** For any packet `p`:

- Hamilton product: `q_identity ⊗ q = q ⊗ q_identity = q` (quaternion group identity)
- Lookup tables with `T[0, j] = j` and `T[i, 0] = i`: `0 ⊕ x = x`
- `max(0, x) = x` and `max(x, 0) = x`
- `0 + x ≡ x (mod N)` and `x + 0 ≡ x (mod N)`
- `0 ⊕ x = x` and `x ⊕ 0 = x`
- `1 · x = x · 1 = x`

So `I ⊗ p = p ⊗ I = p` for all `p`.

**Associativity.** Each per-field operation is associative on its value space:

- Hamilton product is associative on the quaternion group (with normalization a monoid morphism, not a group operation, so the unit-quaternion subspace inherits associativity).
- XOR is associative on Z₂^b.
- max is associative on any totally-ordered lattice.
- Modular addition is associative on Z/NZ.
- Parity XOR is associative on Z₂.
- Multiplication is associative on R+.

Therefore the field-wise composition `⊗` is associative on the packet space, and the packet space is a monoid under `⊗`.

### 2.4 Topology preservation

A property additional to the monoid structure: when the algebra is applied iteratively to a stream of input packets (e.g., `state[t+1] = state[t] ⊗ stim[t]`), the H₁ persistent-homology signature of the resulting trajectory of quaternion components is bounded relative to the H₁ signature of the input stream. Empirically, the ratio of total bar persistence (output to input) falls in [0.3, 5.0] for structured inputs.

This is not a theorem proven in this paper. It is documented as an empirical observation in the validation suite. A formal proof or characterization of conditions under which the bound holds is a target for future work.

## 3. Validation

The `tests/run_all.py` suite includes eight tests covering identity, associativity, closure, stability under iteration, GPU/CPU bit-exact correspondence, and topology preservation. All eight pass on the reference implementation.

```
[Identity laws]
  [PASS] Left identity:  I ⊗ p = p across 100 packets    0 mismatches
  [PASS] Right identity: p ⊗ I = p across 100 packets    0 mismatches

[Associativity]
  [PASS] Associativity across 512 random triples         0 violations

[Closure]
  [PASS] Closure: every product is valid (500 pairs)     0 invalid

[Stability under iteration]
  [PASS] 1000-step self-product chain stays unit-norm    final err < 1e-6
  [PASS] packet_power(p, 5) == p ⊗ p ⊗ p ⊗ p ⊗ p

[GPU vs CPU]
  [PASS] GPU Hamilton matches CPU bit-for-bit            max diff = 0.00e+00
         (CuPy 14.x, NVIDIA RTX 5070 Blackwell)

[Topology preservation]
  [PASS] H1 persistence ratio in [0.3, 5.0]              ratio ≈ 4.7

TOTAL: 8 of 8 tests pass.
```

## 4. Reference implementation performance

A reference Python implementation (`src/quaternion_monoid_algebra/algebra.py`, with a vectorized batch API in `batch.py`) and a CuPy-batched GPU implementation (`src/quaternion_monoid_algebra/gpu.py`) are provided. Measured throughput on consumer hardware:

| Implementation | Hardware | Throughput |
|---|---|---|
| Pure Python | one CPU thread | ~40,000 packet products / sec |
| NumPy vectorized (`batch.py`) | one CPU thread | ~3,600,000 packet products / sec |
| CuPy batched | NVIDIA RTX 5070 (Blackwell, CC 12.0) | ~75,000,000 packet products / sec |

The CPU rows are reproducible with `python benchmarks/bench.py` (Ryzen 5700G measurements). The GPU implementation is bit-exact to the CPU reference on the Hamilton multiply: `max(|GPU - CPU|) = 0.00e+00` across 100,000 random pairs at FP32 precision. This is by design. Production deployments that require CPU-GPU agreement for cryptographic-audit purposes can run on either side and get the same result.

## 5. Application classes

### 5.1 Composable agent state evolution

```
state[t+1] = state[t] ⊗ stimulus[t]
```

A single bounded-width operation per time step. The agent's internal state is the running composition of all stimuli received. The construction is hardware-friendly: a single-cycle combinational implementation on an FPGA fabric is sketched in a related work-in-progress.

### 5.2 Algebraic chain verification

For an N-packet chain `p_1, p_2, ..., p_N` produced sequentially by an agent, a verifier can compute:

```
chain_head = I ⊗ p_1 ⊗ p_2 ⊗ ... ⊗ p_N
```

and compare to a separately-signed chain-head value. The verification runs in O(N) operations with constant per-operation cost. The output is an algebraic-consistency check in addition to whatever cryptographic signature scheme is layered on top. Two agents that observed the same input stream and computed the same chain will arrive at the same chain head; divergence anywhere in the chain produces divergence at the head.

### 5.3 Multi-source state composition

If N agents each produce an independent state packet, the composed multi-agent state is the left-fold:

```
composed = p_1 ⊗ p_2 ⊗ ... ⊗ p_N
```

The composition is associative, so it can be computed in any order or in parallel via a tree-reduce. The result is a single fixed-width packet that encodes a non-commutative summary of the multi-source state (the operation is associative but not commutative on the quaternion component, so order matters in general).

## 6. Hardware implementation sketch

The packet product can be implemented as eight parallel combinational sub-paths feeding an output register:

1. Quaternion decode + Hamilton + re-encode (the critical path; sets clock frequency)
2. Lookup-table substitution for `f_a` (small ROM)
3. Max for `f_b` (constant-time)
4. Modular adder for `f_c`
5. Lookup-table substitution for `f_d` (small ROM)
6. Parity XOR (single gate)
7. FP16 multiply for `s`
8. Assembly register

A reference target on Xilinx Zynq UltraScale+ XC7Z020 at 100 MHz fits in ~250 LUTs plus 1 DSP48 plus 2 small block ROMs. A 28 nm ASIC reference projects ~3,500 standard cells, 1.5 GHz clock, ~50 fJ per operation. These numbers are projections from the cell-library characterization, not measured silicon.

Hardware implementation files are not included in this open-source release. The algebraic specification is sufficient to implement; verification against `src/quaternion_monoid_algebra/algebra.py` provides the bit-exact reference.

## 7. Relationship to prior work

The construction does not introduce novel mathematics. Each of its components has a long literature:

- Hamilton (1843) on quaternion algebra
- Edelsbrunner, Letscher, Zomorodian (2002) on persistent homology
- XOR and modular arithmetic on Z₂^b and Z/NZ as standard finite-group operations
- Lookup-table substitution boxes (S-boxes) in symmetric cryptography (DES, AES, etc.)
- Homomorphic encryption literature (Gentry 2009 et seq.) on algebraic operations on cryptographic objects

What is new here is the specific combination: a closed associative binary operation on a fixed-width packet that simultaneously preserves (i) the unit-quaternion integrity check, (ii) the symbolic-metadata semantics under per-field associative operations, (iii) the algebraic-chain composability property, and (iv) an empirically-observed topology-preservation property under iterated composition. The author has not found this combination in any single prior-art reference; reviewers identifying close prior art are encouraged to open an issue on the repository.

## 8. Open questions

A non-exhaustive list of directions the construction invites:

- **Topology-preservation theorem.** A formal characterization of when and how strongly the H₁-persistence bound holds. Candidate approach: filtration-stability arguments from the persistent-homology stability literature.
- **Alternative sub-field constructions.** The defaults (XOR, max, mod-N add, multiply) are one choice. Other associative monoid operations on the same value spaces would yield other valid constructions with different semantics.
- **Higher-dimensional analogues.** The construction extends naturally from S³ (unit quaternions) to S^n for higher-dimensional rotation representations.
- **Group-theoretic characterization.** Is the packet space, equipped with `⊗`, a finitely-generated free monoid quotient by which relations? What is its representation theory?
- **Hardware silicon characterization.** The 28 nm projections are based on cell-library numbers, not measured chip. A tape-out would confirm or refute the energy and area projections.
- **Real-world dataset validation.** The validation suite uses synthetic inputs. Real motion-capture datasets, real robotic telemetry, and real swarm-coordination logs would exercise the construction under conditions the synthetic suite does not.

## 9. License and provenance

This work is released under the MIT License (see `LICENSE` in the repository). Permissive license chosen to encourage open use, extension, and integration.

The construction was developed by the author with AI as an engineering assistant for implementation, validation, GPU porting, and documentation. The conceptual direction, evaluative choices, and the specific algebraic structure imposed on the packet space were the author's. This attribution is offered transparently in the spirit of contemporary open-source disclosure norms regarding AI-assisted development.

## 10. Citing this work

If this work is useful to you, citation is appreciated:

```
Cody Churchwell. "Compositional Algebra over Fixed-Width Quaternionic-Symbolic
State Packets." Open-source release, May 2026.
https://github.com/consigcody94/quaternion-monoid-algebra
```

---

*End of paper.*
