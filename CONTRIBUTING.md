# Contributing

Contributions are welcome. This project is MIT-licensed and developed in the open.

## Ways to contribute

- **Alternative sub-field constructions.** The default operations (Hamilton product, XOR lookup tables, lattice max, modular addition, multiplicative scaling) are one choice. Other associative monoid operations on the same value spaces are valid and interesting.
- **Real-world dataset validation.** The stress test uses the TUM RGB-D Pioneer 360 sequence. Additional public quaternion datasets (EuRoC MAV, JIGSAWS, IMU recordings, motion capture) broaden the evidence base.
- **Hardware implementations.** Verilog/SystemVerilog references, FPGA synthesis numbers, ASIC characterization.
- **Theory.** A formal characterization of the topology-preservation property, group-theoretic analysis of the packet monoid, or identification of closely related prior work.
- **Bug reports and prior-art pointers.** If you find a defect or a reference that anticipates this construction, open an issue.

## Development setup

```bash
git clone https://github.com/consigcody94/quaternion-monoid-algebra
cd quaternion-monoid-algebra
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install numpy scipy gudhi persim
pip install cupy-cuda12x          # optional, for GPU tests
```

## Running the tests

```bash
python tests/run_all.py        # 8 algebraic-property tests
python tests/stress_tests.py   # 6 stress tests (one downloads a public dataset)
```

All 14 tests should pass. The GPU bit-exact test and the TUM real-data test will skip cleanly if CuPy or network access is unavailable, respectively.

## Pull request guidelines

- Keep changes focused. One concept per PR.
- Add or update tests for any behavioral change.
- Run the full test suite before submitting.
- Describe what the change does and why in the PR body.

## Code of conduct

Be civil and constructive. Technical disagreement is welcome; personal attacks are not.

## Provenance note

This project was developed by the author with AI as an engineering assistant. Contributions from any source, human or tool-assisted, are welcome under the same MIT license, with the same expectation of honest attribution.
