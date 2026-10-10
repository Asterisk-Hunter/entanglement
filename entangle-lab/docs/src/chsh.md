# The CHSH Bell test

The CHSH test uses two possible measurement settings for Alice (`a₀`, `a₁`) and two for Bob (`b₀`, `b₁`). A setting pair is used on many separately prepared pairs. For each pair of settings, estimate the correlation `E` by averaging the products of the two outcomes.

One common CHSH combination is

$$
S = E(a_0,b_0) + E(a_0,b_1) + E(a_1,b_0) - E(a_1,b_1).
$$

For local hidden-variable models that satisfy the usual assumptions of the Bell test, `|S| ≤ 2`. Quantum theory predicts that `|S|` can reach `2√2`, but not exceed it. The CHSH form was proposed as an experimentally testable version of Bell's argument by Clauser, Horne, Shimony, and Holt in 1969.

## Why local models stop at 2

For a deterministic local model, each hidden state assigns an answer `A₀, A₁, B₀, B₁ ∈ {−1,+1}` to the four possible settings. Its CHSH expression for that hidden state is

$$
C = A_0B_0 + A_0B_1 + A_1B_0 - A_1B_1
= A_0(B_0+B_1) + A_1(B_0-B_1).
$$

If `B₀` and `B₁` agree, the first parenthesis is `±2` and the second is `0`. If they disagree, the first is `0` and the second is `±2`. Therefore `C` is always `+2` or `−2`. Averaging over any distribution of hidden states gives `|S| ≤ 2`. Stochastic local models can be represented as mixtures of deterministic responses, so they obey the same bound.

## Settings that expose the difference

For the singlet, `E(a,b) = −cos(a−b)`. Choose Alice's angles `a₀ = 0°`, `a₁ = 90°`, and Bob's `b₀ = 45°`, `b₁ = −45°`. The four ideal correlations combine to

$$
S = -\frac{1}{\sqrt{2}} - \frac{1}{\sqrt{2}}
    - \frac{1}{\sqrt{2}} - \frac{1}{\sqrt{2}}
  = -2\sqrt{2}.
$$

The app displays `|S|`, so the ideal magnitude is `2√2 ≈ 2.828`. In a run, the four values are estimated from random samples and the result fluctuates around this value. Increase the number of pairs to see the estimates usually settle closer to the prediction.

## What a violation tells us

A measured violation rules out the family of local hidden-variable explanations under the experiment's assumptions. It does not show that Alice can send a faster-than-light message. Her local outcomes remain random, and changing Bob's measurement choice does not change Alice's local outcome statistics.

Real experiments must address how settings are chosen, how events are detected, and whether the observations are statistically independent. The browser simulation assumes an ideal source and measurement process, so it illustrates the prediction rather than closing those experimental loopholes.
