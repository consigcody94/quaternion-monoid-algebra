---
title: 'Quaternion-Monoid Algebra: A compositional algebra over fixed-width quaternionic-symbolic state packets'
tags:
  - Python
  - quaternions
  - monoid
  - compositional algebra
  - topological data analysis
  - state evolution
  - audit chains
authors:
  - name: Cody Churchwell
    affiliation: 1
affiliations:
  - name: Independent Researcher
    index: 1
date: 18 May 2026
bibliography: paper.bib
---

# Summary

`quaternion-monoid-algebra` defines and implements a compositional algebra over a fixed-width packet structure that carries a unit quaternion, a small number of symbolic metadata fields, and a positive scaling factor. The library provides a closed binary operation on the packet space with the property that the space, equipped with this operation, forms a monoid: it is closed under the operation, has a two-sided identity, and is associative. An additional empirically-observed property, topology preservation under iterated composition, is documented and tested. The package includes CPU and GPU reference implementations that agree bit-for-bit on the quaternion sub-operation, a vectorized batch API with associativity-based tree reduction, a layered validation suite (a property-based Hypothesis suite, an eight-test property runner, and seven stress tests) covering both the algebraic properties and practical stress conditions, and three worked application examples: composable agent-state evolution, multi-source state composition, and algebraic chain verification.

# Statement of need

Robotics, swarm coordination, and accountability-infrastructure applications frequently need a bounded-width, time-evolving state representation that is simultaneously composable, verifiable, and efficient enough for edge deployment. Existing options trade these against one another. Raw floating-point quaternion streams are compact for rotation but offer no composition operation beyond Hamilton multiplication on the rotation component and carry no symbolic metadata. Variable-width cryptographic audit chains compose via Merkle structures but are not fixed-width and are not amenable to single-cycle hardware composition. High-dimensional vector embeddings compose via vector arithmetic but are lossy and lack a unit-rotation guarantee.

This package fills the gap with a fixed-width construction whose composition operation produces a packet of the same width, gives the packet space a monoid structure (so chains of operations compose freely and associatively), and empirically preserves the topological signature of an input stream under iterated composition. The monoid structure means a chain of state updates can be summarized by a single composed packet, verified by recomputation, and reduced in parallel by any association. The fixed width means the operation maps cleanly onto bounded hardware. The construction is offered as an open, MIT-licensed reference so that the broader community can evaluate, extend, and apply it.

# Construction

A packet is a tuple of a unit quaternion, four small symbolic fields, a parity bit, and a positive scaling factor. The composition operation combines packets field-by-field: the quaternion via Hamilton product followed by renormalization; the symbolic fields via associative monoid operations on their respective value spaces (lookup-table substitution that defaults to XOR over $\mathbb{Z}_2^n$, lattice maximum, and modular addition over $\mathbb{Z}/N\mathbb{Z}$); the parity bit via XOR; and the scaling factor via multiplication over the positive reals. Each per-field operation is associative with an identity element, so the field-wise composition is associative with a two-sided identity, and the packet space is a monoid [@Hamilton1844]. The topology-preservation property is assessed using persistent homology [@Edelsbrunner2002] via the GUDHI library [@GUDHI].

# Validation

The validation suite has three layers: a property-based suite (77 tests driven by Hypothesis, covering the monoid laws under adversarial inputs, boundary validation, custom-table validation, batch-versus-scalar equivalence, and machine checks of the proved topology statements), eight algebraic-property tests (left and right identity, associativity over 512 random triples, closure over 500 random pairs, stability over a 1000-step self-product chain, power consistency, and bit-exact GPU/CPU correspondence), and seven stress tests (10,000-step long-horizon stability, single-bit avalanche sensitivity, distinguishability across 100 chains, real-data behavior on two public motion streams — the TUM RGB-D Pioneer 360 sequence and the EuRoC MAV Machine Hall 01 ground truth [@Burri2016] — field-saturation honesty, and scale stability). All tests pass on the reference implementation. The topology-preservation property is formally characterized in the repository's `paper/topology_notes.md`: composition with a common packet preserves persistence diagrams exactly (unit-quaternion translations are isometries), iterated composition is an isometric development with step lengths equal to stimulus offsets, and the bounded-H₁-ratio behavior under iterated composition is documented as an empirical property of the tested stimulus classes. The real-data test verifies behavior on the TUM RGB-D Pioneer 360 ground-truth sequence [@Sturm2012], downloaded at runtime with SHA-256 verification.

# Acknowledgements

This software was developed by the author with AI used as an engineering assistant for implementation, validation, GPU porting, and documentation. The conceptual direction and the specific algebraic structure imposed on the packet space were the author's.

# References
