# Measurement and probability

When Alice chooses a direction `θ_A` and Bob chooses `θ_B`, each receives one result, `+1` or `−1`. The joint probabilities for the singlet are

$$
P(A=a, B=b) = \frac{1 + ab E(\theta_A,\theta_B)}{4},
\qquad a,b \in \{-1,+1\}.
$$

Using `E = −cos(θ_A − θ_B)`, the probability that the two results are the **same** is

$$
P(\text{same}) = \frac{1+E}{2}
= \frac{1-\cos(\theta_A-\theta_B)}{2}.
$$

The probability that they are **opposite** is `1 − P(same)`. At `0°` separation, same outcomes have probability zero. At `90°`, both categories have probability `1/2`.

## Why one result is not the result

Every single measurement is random. Alice alone sees `+1` about half the time and `−1` about half the time, regardless of Bob's setting. The useful pattern appears in the joint data from many pairs.

This is why the app separates the expected distribution from a sampled result. The probability bars show the model's prediction. **Measure one pair** draws one example from that distribution. Repeating the click does not guarantee a balanced short run.

## Sampling rule used by the app

The code first draws Alice's result with equal probability for `+1` and `−1`. It then draws Bob's result with

$$
P(B=+1\mid A=a) = \frac{1+aE}{2}.
$$

This gives the joint probabilities above while keeping each local result unbiased. The same rule is applied independently to each simulated pair.
