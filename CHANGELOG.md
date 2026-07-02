# Changelog

## v0.2.0 — 2026-07-01

### Added
- **Installable package.** The library is now a proper Python package (`pip install -e .` or `pip install git+...`) named `quaternion_monoid_algebra`, with `pyproject.toml`, optional extras (`test`, `topology`, `gpu`, `dev`), and metadata.
- **Vectorized batch API** (`quaternion_monoid_algebra.batch`): `PacketArray` struct-of-arrays container, `packet_product_batch` for elementwise composition, and `reduce_packets` for O(log N)-depth tree reduction of a chain. Roughly 90× the scalar throughput on CPU (see `benchmarks/bench.py`).
- **`validate_monoid_table(table)`**: vets a custom Cayley table (closure, identity laws, full associativity) with a counterexample on failure, so alternative sub-field constructions can be checked before use.
- **`compose(packets)`**: left-fold convenience, `I ⊗ p₁ ⊗ ... ⊗ pₙ`.
- **pytest + Hypothesis property suite** (`tests/test_properties.py`, `tests/test_batch.py`): 49 tests driving the monoid laws with adversarial inputs, boundary-validation checks, batch-vs-scalar equivalence, and tree-reduce-vs-fold equivalence.
- **Benchmarks** (`benchmarks/bench.py`) measuring scalar, batch, tree-reduce, and GPU tiers.
- Ruff lint configuration and a lint job in CI.

### Changed
- **Package layout**: `src/algebra.py` → `src/quaternion_monoid_algebra/algebra.py` (same for `gpu.py`). Imports change from `from src.algebra import ...` to `from quaternion_monoid_algebra import ...`.
- **`packet_power` is now O(log n)** via exponentiation by squaring — valid precisely because ⊗ is associative. Symbolic fields are unchanged under any association; the quaternion may differ from the sequential fold by ~machine epsilon, within packet equality tolerance.
- **`make_xor_table` is vectorized** (was a Python double loop).
- CI now installs the package (`pip install -e .[test]`), runs pytest, and no longer masks stress-test failures (the old `|| true` suppressed genuine failures; the stress runner already exits 0 on a network-unavailable skip).

### Fixed
- **`Packet` now validates its inputs.** Previously a zero quaternion, a NaN/inf quaternion, or a zero/negative/non-finite scale was accepted silently, producing an invalid packet that broke the closure guarantee downstream. All are rejected with `ValueError` at construction.
- **Quaternion normalization is overflow/underflow-safe.** `normalize_quaternion`, `Packet`, and `PacketArray` now pre-scale by the largest-magnitude component before computing the norm, so quaternions with components above ~1e154 (whose naive sum of squares overflows to inf) or below ~1e-162 (whose naive sum of squares underflows to zero) normalize correctly instead of silently storing zeros or being falsely rejected.
- **Packet equality semantics are now precise and documented.** `Packet.__eq__` compares the quaternion at absolute 1e-9 per component and the scale at relative 1e-9. Previously numpy's default `rtol=1e-5` silently dominated the comparison, so e.g. scales 1000.0 and 1000.005 compared equal.

## v0.1.0 — 2026-05-18

Initial release: compositional algebra over fixed-width quaternion packets, 8-test property suite, 6 stress tests, GPU port, JOSS paper scaffolding, Zenodo DOI.
