# Entanglement Trap

Entanglement Trap is an interactive laboratory for one question in quantum information: **when does entanglement change how well two quantum channels can be distinguished?**

The lab compares a separable probe with a maximally entangled probe across three channel pairs. The results are deliberately not reduced to one slogan:

| Verdict | Comparison | Result |
| --- | --- | --- |
| HURTS | Identity vs. `V`, dimension 256 | `1.0` separable; `0.507781982421875` maximally entangled |
| HELPS | Identity vs. fully depolarizing qubit channel | `0.75` separable; `0.875` Bell-probe theoretical ceiling |
| NEUTRAL | Four-Pauli rotations at `θ = π/8` | `0.8535533905932737` for both optimal strategies |

These values have different evidence status. The main interactive run submits a four-circuit batch for the HURTS pair to the backend selected by Qollab. The resource gallery displays analytic claims and circuit descriptions without submitting backend jobs. HELPS `0.875` is a theoretical ceiling and has no implemented live measurement path. The Four-Pauli Bell discriminator is tested with exact statevector simulation, not hardware.

The book follows the same path as the project: start with the question, run the experiment, understand the comparison, inspect its evidence, then extend it. You do not need quantum-computing experience to begin, but the theory chapters introduce the notation as it becomes useful.

## Who this is for

- **Students** can use the HURTS case to challenge the intuition that a larger quantum resource must always help.
- **Educators** can use the first result as a short lecture segment: a quick surprise, followed by a discussion of output overlap and measurement.
- **Researchers** can inspect the assumptions and source records before reusing a numerical claim.

## Start here

1. Read [how channel discrimination works](channel-discrimination.md) for the game and success probability.
2. Read [the three results](results.md) for the precise comparisons and evidence labels.
3. Follow [Run the lab](run-the-lab.md) to use Qollab or reproduce the local test suite.
4. Follow [How to add a channel pair](add-a-pair.md) to extend the gallery.

## Scientific scope

The project reproduces and operationalizes prior channel-discrimination results. It does not claim a new theorem or quantum computational advantage. Small instances are classically simulable. The displayed strategy values are analytic, theoretical ceilings, or empirical measurements only where the interface labels them as such.

The machine-readable [claim ledger](../../claims.json) records formulas, values, dimensions, and whether each claim is safe to display. The code and tests are the executable source of the implementation details.

## A companion learning path

[Entangle Lab](../../entangle-lab/index.html) is the zero-backend on-ramp in this repository. Its singlet playground lets you change Alice's and Bob's measurement angles, sample one correlated outcome, and estimate the CHSH statistic from finite samples. Its [nine-chapter field guide](../../entangle-lab/docs/src/SUMMARY.md) builds the intuition used here. The Lab teaches quantum correlations; this book and the Qollab submission focus on channel discrimination.
