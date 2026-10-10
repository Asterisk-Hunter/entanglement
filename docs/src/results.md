# Three channel-pair results

The gallery is a set of comparisons, not three measurements of the same system. Each pair has its own channels, input strategies, dimensions, and evidence status.

## HURTS: Identity vs. `V`

The flagship compares `I` and `V = 2|0…0⟩⟨0…0| − I` at dimension `d = 256`.

| Probe strategy | Success | Status |
| --- | ---: | --- |
| Declared separable strategy | `1.0` | Analytic value; circuit is part of the live flagship batch. |
| Maximally entangled probe with the implemented simple measurement | `0.507781982421875` | Analytic value; circuit is part of the live flagship batch. |
| Maximally entangled probe, Helstrom optimum | `0.5623778102448098` | Theoretical ceiling; distinct from the implemented simple measurement. |

The main UI can also estimate benchmark rates from sampled results on the Qollab-selected backend. Those rates are empirical and must be read with the displayed dimension, shot count, backend, and confidence interval. Analytic values are not replaced by the sampled rate.

## HELPS: Identity vs. full depolarization

For one qubit, the second channel replaces its input with the maximally mixed state. The code derives success from the trace norm of the output-state difference.

| Probe strategy | Success | Status |
| --- | ---: | --- |
| Declared `|0⟩` separable probe | `0.75` | Analytic value. |
| Bell probe with its optimal Helstrom measurement | `0.875` | Theoretical ceiling; the corresponding live measurement strategy is not implemented. |

This pair shows a case where entanglement can help. The gallery computes and labels the comparison; it does not run this pair through the flagship live benchmark path.

## NEUTRAL: Four-Pauli rotations

At `θ = π/8`, the channels apply `R_P(+2θ)` and `R_P(−2θ)` for a Pauli generator `P`. The code uses `P = Z` for the reference implementation. Both an optimal separable `|+⟩` probe with a `Y`-basis readout and a Bell probe with the implemented Bell discriminator attain

```text
p*(θ) = 1/2 (1 + sin(2θ)) = 0.8535533905932737  when θ = π/8.
```

The Bell discriminator is tested against exact statevector probabilities. This is a local simulation check, not a hardware measurement. The equality is between optimal strategies; the restricted Bell readout with a product probe is not the optimal separable comparison.

## Read values with their labels

The claim ledger in `claims.json` records each value's kind, formula, dimension, source, and display safety. `ANALYTIC` means a formula-derived value for an implemented strategy. `THEORETICAL_CEILING` identifies a theoretical optimum without an implemented measurement path. `EMPIRICAL` is reserved for sampled run data. Do not compare values without checking both the strategy and its label.
