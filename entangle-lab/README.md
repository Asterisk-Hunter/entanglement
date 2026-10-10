# Entangle Lab

**Two particles. One shared story.** Entangle Lab is a browser-based teaching playground for the spin-singlet state and the CHSH Bell test. It is the no-backend learning on-ramp that accompanies the repository's Qollab submission, Entanglement Trap.

Move Alice's and Bob's analyzer sliders to see the singlet correlation

```text
E(a, b) = −cos(a − b)
```

Then sample individual outcome pairs or run a finite-shot CHSH estimate. The standard settings approach the quantum maximum `2√2`; local hidden-variable models obey `|S| ≤ 2` under the inequality's assumptions.

The app evaluates the ideal singlet probability distribution in JavaScript. It does not use a quantum backend, prepare physical particles, or model detector noise and experimental loopholes. A finite sample fluctuates and is not experimental evidence.

## Run it

From the repository root:

```sh
python -m http.server 8000
```

Open <http://localhost:8000/entangle-lab/>. You can also open this directory's `index.html` directly in a browser.

## Read the field guide

The nine-chapter [mdBook field guide](docs/src/SUMMARY.md) introduces the qubit, singlet, measurement probabilities, CHSH inequality, simulator, and model limits.

```sh
cd docs
mdbook build
mdbook serve --open
```

## The companion project

[Entanglement Trap](../README.md) is the repository's Qollab hackathon submission. It studies a different question: whether a maximally entangled probe helps distinguish a pair of quantum channels. Entangle Lab builds intuition about quantum correlations; Entanglement Trap examines probe resources in a channel-discrimination game.
