# Topology preservation: formal notes

This note gives the formal backing for the "topology preservation" language
used in the README and white paper. It contains: an exact-preservation
theorem for composition with a common packet (proved), a Lipschitz
development bound for iterated composition (proved), and an explicit
demonstration of why iterated composition can *not* preserve persistent
homology universally — which is why the iterated-composition property is
stated as an empirical band over tested stimulus classes rather than a
theorem. Machine-checked counterparts of every proved statement are in
`tests/test_topology.py`.

## 1. Setup

Work in the quaternions $\mathbb{H} \cong \mathbb{R}^4$ with the Euclidean
inner product $\langle a, b\rangle = \mathrm{Re}(a\bar b)$. Unit quaternions
form the 3-sphere $S^3$. The validation suite measures distances with

$$d(p, q) = \arccos\left(\lvert\langle p, q\rangle\rvert\right),$$

the geodesic metric on the projective space $S^3/\{\pm 1\} \cong
\mathbb{RP}^3 \cong SO(3)$: the absolute value identifies $q$ and $-q$,
which encode the same rotation. All statements below are for this metric;
they hold verbatim for the chordal metric and for the sign-sensitive
$\arccos\langle p,q\rangle$ on $S^3$, by the same proofs.

The quaternion sub-field of the packet operation $g \otimes p$ maps the
quaternion component $q_p \mapsto q_g\, q_p$ (Hamilton product) followed by
renormalization. For unit inputs, $\lvert q_g q_p\rvert = \lvert
q_g\rvert\,\lvert q_p\rvert = 1$ exactly over the reals, so renormalization
is the identity and the induced map on quaternion components is exactly the
left translation $L_g: q \mapsto q_g\, q$. (In IEEE 754 arithmetic
renormalization corrects rounding at machine-epsilon scale; the tests
assert the statements below to $10^{-12}$.)

## 2. Translations are isometries

**Lemma 1.** For any unit quaternion $g$ and all $a, b \in \mathbb{H}$:
$\langle ga, gb\rangle = \langle a, b\rangle$ and $\langle ag, bg\rangle =
\langle a, b\rangle$.

*Proof.* Recall $\overline{xy} = \bar y\,\bar x$ and that the real part is
cyclic, $\mathrm{Re}(xy) = \mathrm{Re}(yx)$ (both equal the scalar part of
the product, and the scalar part of $xy$ and $yx$ coincide by direct
computation on the multiplication table). For left translation:

$$\langle ga, gb\rangle
  = \mathrm{Re}\!\left(ga\,\overline{gb}\right)
  = \mathrm{Re}\!\left(g\,a\bar b\,\bar g\right)
  = \mathrm{Re}\!\left(a\bar b\,\bar g g\right)
  = \mathrm{Re}\!\left(a \bar b\right)\lvert g\rvert^2
  = \langle a, b\rangle.$$

For right translation: $\langle ag, bg\rangle = \mathrm{Re}(a g \bar g \bar
b) = \mathrm{Re}(a\bar b)\lvert g\rvert^2 = \langle a, b\rangle$. $\square$

Since $d$ is a function of $\lvert\langle\cdot,\cdot\rangle\rvert$ alone,
Lemma 1 gives $d(gp, gq) = d(p, q) = d(pg, qg)$: left and right
translations by unit quaternions are isometries of $(\mathbb{RP}^3, d)$.

## 3. Exact preservation under common composition

**Theorem 1.** Let $P = \{p_1, \dots, p_n\}$ be any finite set of packets
and $g$ any packet. Write $Q(\cdot)$ for the quaternion component. Then the
configurations $\{Q(p_i)\}$ and $\{Q(g \otimes p_i)\}$ have identical
pairwise distance matrices under $d$, hence identical Vietoris–Rips
filtrations, hence **equal persistence diagrams in every homology
dimension**. The same holds for right composition $\{Q(p_i \otimes g)\}$.

*Proof.* By the setup discussion, $Q(g \otimes p_i) = L_{Q(g)} Q(p_i)$
exactly. By Lemma 1, $L_{Q(g)}$ is an isometry, so all pairwise distances
are unchanged. A Vietoris–Rips filtration is a function of the distance
matrix alone, and persistence diagrams are determined by the filtration.
$\square$

This is the formal content behind application class 3 (multi-source
composition): folding a common state into every member of a configuration
— a common prefix under left composition or suffix under right composition
— *exactly* preserves the configuration's topological signature, not
approximately.

## 4. Iterated composition: the development bound

Now consider the agent-evolution recurrence $q_t = q_{t-1} \cdot x_t$ with
$q_0 = 1$, so $q_t = x_1 x_2 \cdots x_t$ (the "development" of the stimulus
stream onto the group).

**Lemma 2 (subadditivity).** $d(1, ab) \le d(1, a) + d(1, b)$ for unit
quaternions $a, b$.

*Proof.* Triangle inequality through $a$: $d(1, ab) \le d(1, a) + d(a,
ab)$, and $d(a, ab) = d(1, b)$ by left-invariance (Lemma 1). $\square$

**Proposition 3 (Lipschitz development).** For $s < t$:

$$d(q_s, q_t) = d\!\left(1,\; x_{s+1} x_{s+2} \cdots x_t\right)
  \;\le\; \sum_{i=s+1}^{t} d(1, x_i),$$

with equality of the first two expressions exact (left-invariance) and, in
particular, **consecutive trajectory steps satisfy $d(q_{t-1}, q_t) = d(1,
x_t)$ exactly**: the trajectory's step lengths are precisely the stimulus
offsets from identity.

*Proof.* Cancel $q_s$ on the left by invariance; then induct on the window
length with Lemma 2. $\square$

Consequences: the trajectory's diameter is at most the smallest window sum
of stimulus offsets covering it (and never exceeds $\pi/2$, the diameter of
$\mathbb{RP}^3$); every Vietoris–Rips persistence interval of the
trajectory lies in $[0, \mathrm{diam}]$; small-offset streams produce
correspondingly tight trajectories. The map from streams to trajectories is
1-Lipschitz from "total stimulus variation" to trajectory path length.

## 5. Why iterated preservation cannot be a theorem

The empirical claim tested by the suite — the $H_1$ persistence ratio of
trajectory to input stream stays in a band $[0.3, 5.0]$ — cannot hold for
arbitrary streams, in either direction:

- **Ratio unbounded above.** Take the constant stream $x_t = x$ with
  rotation half-angle $\theta = \pi/m$. The input point *set* is a single
  point (total $H_1$ persistence $0$), while the trajectory $\{x^k\}$
  visits $m$ equally spaced points on a geodesic circle, whose Rips
  filtration carries a nonzero $H_1$ class. This is machine-checked in
  `tests/test_topology.py::test_constant_stream_inflates_h1`.

- **No universal positive lower bound.** Streams alternating between two
  orthogonal one-parameter subgroups can have input sets supported on two
  circles (nontrivial $H_1$) while the cumulative products spread
  quasi-uniformly over $S^3$, washing the trajectory's $H_1$ signal toward
  that of a random cloud.

The honest formal statement is therefore: **composition with a common
packet preserves persistence exactly (Theorem 1); iterated composition is
an isometric development whose step geometry is exactly the stimulus offset
geometry (Proposition 3); and the bounded-ratio property is an empirical
regularity of the structured stimulus classes tested** (multi-frequency
torus walks, and real robot/MAV pose streams: TUM RGB-D and EuRoC MAV in
the stress suite), not a universal law.

## 6. Test coverage of these statements

| Statement | Machine check |
|---|---|
| Lemma 1 / Theorem 1 (left) | `test_left_composition_preserves_distance_matrix` |
| Lemma 1 / Theorem 1 (right) | `test_right_composition_preserves_distance_matrix` |
| Theorem 1 (diagrams, via GUDHI) | `test_persistence_diagrams_equal_under_common_composition` |
| Lemma 2 | `test_subadditivity_of_identity_offset` |
| Prop 3 (step equality) | `test_trajectory_steps_equal_stimulus_offsets` |
| Prop 3 (window bound) | `test_window_distance_bounded_by_offset_sum` |
| §5 inflate example | `test_constant_stream_inflates_h1` |
| Empirical band | `tests/run_all.py::test_topology_preservation` |
