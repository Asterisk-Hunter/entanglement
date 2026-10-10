# Welcome to the lab

## Two observers. One shared quantum state.

Entangle Lab is a small interactive experiment about one of the clearest ways to see how quantum predictions differ from local classical ones. Alice and Bob each measure one particle from a shared **singlet state**. Their individual results are random. When they compare many results, the correlations depend on the angle between their measurement directions.

The field guide introduces the pieces in order. You can read it without a physics background beyond basic algebra. Each chapter connects one idea to a control or result in the simulator.

> **Start with the experiment.** Open the project page, leave Alice at `0°` and Bob at `45°`, then move either angle. The bars show the probabilities predicted by the ideal model. Click **Measure one pair** to draw one random outcome.

## What you will discover

- A qubit can have a state that is not a definite classical bit.
- A pair of qubits can share a state that cannot be described as two independent states.
- Measurement outcomes are random locally, while their joint statistics can be strongly correlated.
- The CHSH inequality gives a numerical test of one family of local hidden-variable models.
- Finite data fluctuates, and a browser simulation is not a laboratory experiment.

## A note on the model

The simulator samples the quantum probability distribution for an ideal two-spin singlet. It does not generate physical particles or prove a theorem from experimental data. The [model limits](limits.md) chapter explains what those distinctions mean.

This field guide covers the singlet and Bell-test teaching playground. The repository's companion [Entanglement Trap project](../../README.md) takes the next step into quantum channel discrimination; it has a separate [field guide](../../docs/src/SUMMARY.md).
