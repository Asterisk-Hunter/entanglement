# Limits and sources

## Limits

- The project reproduces and operationalizes prior results. It does not claim discovery of the underlying theorem.
- The showcased instances are small enough to simulate classically. The project claims no quantum computational advantage.
- The central interactive benchmark is the Identity-vs-`V` pair. The other pairs are displayed in the resource gallery as analytic comparisons; they do not share the flagship live execution path.
- HELPS `0.875` is a Bell-probe Helstrom ceiling. Its attaining measurement is not implemented as a live Qollab strategy.
- Four-Pauli exact-statevector tests verify the declared discriminator locally. They do not establish hardware performance.
- The actual Qollab browser runtime test is skipped in the local suite. A local pass therefore does not replace a live platform smoke test.
- Finite-shot estimates fluctuate. A measured benchmark should be interpreted with its shot count and uncertainty, not as an exact analytic value.

## Sources

The in-project citations identify the research claims used by each pair. The claim ledger also records the source and formula next to the value.

- Kristin Sundal Lien and Marco Túlio Quintino, “Entanglement in quantum channel discrimination: sometimes less is more,” arXiv:2605.31519 (2026). [arXiv record](https://arxiv.org/abs/2605.31519). The project identifies this preprint as the source of its flagship comparison.
- G. M. D'Ariano, P. Lo Presti, and M. G. A. Paris, “Improved discrimination of unitary transformations by entangled probes,” *Journal of Optics B: Quantum and Semiclassical Optics* 4 (2002), S273–S276. [arXiv:quant-ph/0204050](https://arxiv.org/abs/quant-ph/0204050).
- Satyaki Manna, Anandamay Das Bhowmik, and Debashis Saha, “Limitation of maximally entangled probes for single-shot distinguishability of unitaries,” *Physical Review A* 112, 042215 (2025). [doi:10.1103/bsxv-q9x7](https://doi.org/10.1103/bsxv-q9x7). This result concerns two unitary channels; the project uses it as context for the unitary comparison, not as a source for the depolarizing-channel calculation.

The HELPS and Four-Pauli implementations also include their derivation and limitations in the module documentation in `channels/`. Read those notes alongside the numerical claim; a citation alone does not establish that a particular circuit implements an optimum.

## Claim ledger

[`claims.json`](https://github.com/Asterisk-Hunter/entanglement/blob/main/claims.json) is the structured source for numeric claims. It distinguishes reproducible values from a historical printed value retained for audit. The historical HURTS value `0.5078125` is marked unsafe for display; the formula gives `0.507781982421875`, which is the value used in the interface.
