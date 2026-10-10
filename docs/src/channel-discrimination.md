# How channel discrimination works

Channel discrimination is a decision task. A referee chooses one of two quantum channels, `A` or `B`, with equal probability. You prepare a probe, the unknown channel acts once, and you measure the output to guess which channel was used. Your success probability is the fraction of correct guesses over many independent trials.

The probe may be a system alone (a **separable** strategy), or the system may be entangled with a reference register that the channel does not touch. A measurement can use the output and reference together. Entanglement can change the distinguishability of the two resulting states, but the direction and size of that change depend on the channel pair and measurement.

## A basic bound

For equal prior probabilities and output density matrices `ρ_A` and `ρ_B`, the optimal binary measurement has success probability

```text
P_success = 1/2 + 1/4 ||ρ_A - ρ_B||_1
```

Here `||·||_1` is the trace norm, the sum of the singular values. Identical outputs give success `1/2`, which is a random guess. Orthogonal outputs can be distinguished perfectly, giving success `1`.

The formula describes an optimal measurement for the stated output states. A strategy value in the gallery is labeled `ANALYTIC` when the stated value belongs to an implemented strategy. It is labeled `THEORETICAL_CEILING` when it is an optimum or bound without an implemented measurement path. The label therefore answers a practical question about the repository as well as a mathematical one.

## What the HURTS experiment changes

The flagship compares the identity channel `I` to

```text
V = 2 |0…0⟩⟨0…0| − I
```

on a `d`-dimensional system. At `d = 256`, the declared separable strategy distinguishes them perfectly. For the maximally entangled probe, the output overlap is

```text
overlap(d) = (2 − d) / d
```

The implemented simple measurement has success

```text
p_simple(d) = 1 − overlap(d)² / 2
```

which gives `0.507781982421875` at `d = 256`. The 0.508 result is only slightly above chance. The separate Helstrom ceiling for that probe is `0.5623778102448098`; it is not the same measurement or the headline executable strategy.

This example is a counterexample to the claim that maximal entanglement must improve every discrimination task. It does not establish that entanglement is generally harmful.

## Terminology used in the lab

- **Probe:** the input state, including any reference register.
- **Channel:** the unknown transformation applied to the system register.
- **Strategy:** a probe together with its measurement and decision rule.
- **Analytic value:** a formula-derived value for a stated strategy.
- **Theoretical ceiling:** a theoretical optimum or upper bound that is not presented as an implemented measurement result.
- **Empirical value:** a rate estimated from sampled outcomes. It is meaningful only with its backend and shot count.

The project keeps formula values separate from sampled rates in the code and claim ledger. Browse [the three results](results.md) for pair-specific qualifications.
