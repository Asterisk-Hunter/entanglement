---
format: 1920x1080
duration: 26s
message: "At d=256, maximum entanglement makes this channel-discrimination strategy perform worse than a separable probe."
arc: Question → One round → Reversal → Mechanism → Theoretical floor → Honesty and invitation
audience: Qollab hackathon judges, quantum information students, educators, and researchers
mode: autonomous
---

## Frame 1 — The bet

- type: hook
- persuasion: curiosity → choice
- scene: Two probe choices frame the question.
- duration: 3s
- src: compositions/frames/01-the-bet.html
- transition_in: cut
- status: animated
- poster: 1.5s
- blueprint: compose
- asset_candidates: assets/trap-bet.png — source UI crop with both probes and run settings
- focal: assets/trap-bet.png
- roles: assets/trap-bet.png = supporting

The root Entanglement Trap interface is the only product surface. The two probe cards are both visible; no image from `entangle-lab/` appears.

Scene 1 (0.0–0.7s): ink field; a thin amber measuring rule draws in from the left. Sparse centered layout, with the rule occupying the left third.

Scene 2 (0.7–1.8s): `trap-bet.png` arrives as a large, source-derived crop on the left 65% of the frame. The SEPARABLE and MAX ENTANGLEMENT cards remain side by side and legible. A single amber focus line passes between them; smooth, finite motion.

Scene 3 (1.8–3.0s): the right-side copy `WHICH PROBE WINS?` resolves in a dedicated gutter, at least 48px, then holds. No text sits over the app crop.

## Frame 2 — One round

- type: feature_showcase
- persuasion: interaction → constraint
- scene: d=256 and 2,000 shots, one play, one backend-job budget.
- duration: 4s
- src: compositions/frames/02-one-round.html
- transition_in: cut
- status: animated
- poster: 2s
- blueprint: cursor-ui-demo (Adapt)
- asset_candidates: assets/trap-round.png — source UI crop with settings and Qollab one-job budget
- focal: assets/trap-round.png
- roles: assets/trap-round.png = cutout

This is a static, source-derived preview of the app controls. It does not imply that this video sent a Qollab job or captured a hardware outcome.

Scene 1 (0.0–1.0s): the controls crop sits left of center; d=256 and 2,000 shots are already selected. A compact `ONE ROUND` label enters above the crop. Asymmetric 65/35 layout.

Scene 2 (1.0–2.2s): a cursor glides to `PLAY ONE ROUND` and depresses it once. The app's run-state line remains readable. In the right gutter, `SOURCE: QOLLAB · BACKEND JOBS=1` appears as the run contract.

Scene 3 (2.2–4.0s): `ONE ROUND. ONE OUTCOME.` lands in the gutter, followed by `BENCHMARKS ARE CACHED.` The frame holds on the one-job budget; no invented sampled outcome is shown.

## Frame 3 — The reversal

- type: benefit_highlight
- persuasion: surprise → proof
- scene: The paired analytic values resolve before the impact statement.
- duration: 5s
- src: compositions/frames/03-the-reversal.html
- transition_in: cut
- status: animated
- poster: 4s
- blueprint: dataviz-countup (Adapt)
- asset_candidates: assets/trap-benchmark.png — exact d=256 strategy values and impact card
- focal: assets/trap-benchmark.png
- roles: assets/trap-benchmark.png = cutout

The values are analytic closed-form strategy values, not measurements from a live backend run. Use a clean layer mask over the impact line already in the crop so the comparison is visible first and the sentence hits afterward.

Scene 1 (0.0–0.8s): `d=256 · ANALYTIC` appears in the left half, with the crop held at 1:1 scale and ample margin.

Scene 2 (0.8–1.8s): `MAX_ENTANGLEMENT   0.507781982421875` is revealed in pale text. Do not shorten the value.

Scene 3 (1.8–2.6s): `SEPARABLE   1.0000` arrives beneath it. Both exact values remain on screen together.

Scene 4 (2.6–5.0s): the amber mask clears and `MORE ENTANGLEMENT MADE YOU WORSE.` punches into the dedicated right gutter. Keep both numbers visible and readable for the full hold.

## Frame 4 — Why

- type: feature_showcase
- persuasion: explanation → trend
- scene: Near-identical outputs explain the collapse; the sweep shows the trend.
- duration: 5s
- src: compositions/frames/04-why.html
- transition_in: cut
- status: animated
- poster: 4s
- blueprint: dataviz-countup (Adapt)
- asset_candidates: assets/trap-mechanism.png — overlap and maximal-entanglement panel; assets/trap-sweep.png — sweep figure crop
- focal: assets/trap-mechanism.png
- roles: assets/trap-mechanism.png = cutout; assets/trap-sweep.png = cutout

Use two consecutive, tightly cropped source-derived panels, never side by side. Keep the exact signed overlap distinct from the magnitude explanation. All plotted rates are labeled ANALYTIC.

Scene 1 (0.0–2.0s): `trap-mechanism.png` enters left of a right-gutter callout. `MAXIMAL` and `-0.9921875` receive one amber underline, drawn once; the text holds.

Scene 2 (2.0–3.1s): the mechanism panel slides out as the sweep crop moves in along the same horizontal path. One matched-direction handoff, no slow camera pan.

Scene 3 (3.1–5.0s): `trap-sweep.png` holds large. The exact ladder appears in the separate right gutter: `d=4 → 0.875`, `d=16 → 0.6171875`, `d=64 → 0.53076171875`. Separable remains flat at 1; the max-ent points approach chance.

## Frame 5 — The floor

- type: social_proof
- persuasion: limit → trust
- scene: The ideal detector still has a strict theoretical ceiling.
- duration: 5s
- src: compositions/frames/05-the-floor.html
- transition_in: cut
- status: animated
- poster: 3.5s
- blueprint: dataviz-countup (Adapt)
- asset_candidates: assets/trap-floor.png — exact Helstrom ceiling claim card
- focal: assets/trap-floor.png
- roles: assets/trap-floor.png = cutout

This is a theoretical ceiling, not an empirical result. Keep the provenance tag attached to the value throughout the scene.

Scene 1 (0.0–1.0s): `THEORETICAL_CEILING` enters alone in the top-left evidence rail.

Scene 2 (1.0–2.4s): the exact value `0.5623778102448098` resolves at center, with a measured vertical rule and no count-up that could imply a measurement.

Scene 3 (2.4–5.0s): `EVEN AN OPTIMAL DETECTOR IS BOUNDED HERE.` settles below the value. Hold the figure and provenance label long enough to read.

## Frame 6 — Evidence, limits, invitation

- type: cta
- persuasion: provenance → honest close → action
- scene: The claim is cited, tested, limited, and linked to its source.
- duration: 4s
- src: compositions/frames/06-honesty-cta.html
- transition_in: cut
- status: animated
- poster: 3s
- blueprint: titlecard-reveal (Adapt)
- asset_candidates: assets/trap-benchmark.png — source identity and evidence context
- focal: assets/trap-benchmark.png
- roles: assets/trap-benchmark.png = supporting

Keep the evidence statement concrete: the project reproduces a cited result, separates analytic values from the theoretical ceiling, quarantines unsafe claims, and tests that boundary. No discovery or hardware-advantage claim.

Scene 1 (0.0–1.3s): three evidence tags appear in order: `ANALYTIC`, `EMPIRICAL`, `THEORETICAL_CEILING`. Then `LIEN & QUINTINO (2026) · REPRODUCED, NOT CLAIMED AS NEW` and `CLAIM QUARANTINE · REGRESSION TESTS` resolve beneath them.

Scene 2 (1.3–2.5s): two short lines land: `NO NEW THEOREM.` and `NO QUANTUM COMPUTATIONAL ADVANTAGE CLAIM.` Smaller supporting line: `SMALL INSTANCES ARE CLASSICALLY SIMULABLE.`

Scene 3 (2.5–4.0s): clean cut to the branded lockup: `ENTANGLEMENT TRAP`, `Two particles. One shared story.` is omitted because it belongs to the sibling teaching toy; show `Asterisk-Hunter/entanglement` and the direct repository URL `https://github.com/Asterisk-Hunter/entanglement` in a dedicated, high-contrast link rail. The final 1.5 seconds are an active lockup reveal and held URL, not a frozen screenshot. A local app run command is omitted until one exists at the repository root.

## Video direction

Silent 16:9, 1920×1080. Use only `#0b0e14`, `#e9b44c`, `#f2f0ff`, and readable muted text from the app palette. Every screenshot is a tight crop from Entanglement Trap's root HTML/CSS and every number comes from the supplied safe claims. Use platform monospace fonts so there is no missing web-font dependency. Main copy is at least 28px at output size; primary values and the hook are larger. Use one reveal at a time, long-tail deceleration, and still holds for reading. Never place motion copy over app copy. Do not include the sibling `entangle-lab/`, a fabricated empirical result, a four-Pauli advantage, or the quarantined unsafe numeric value. Use hard cuts between beats and matched-direction motion only for the mechanism-to-sweep handoff. Keep the final lockup active through the end of the 26-second cut.
