# The singlet state

Entangle Lab models a pair of spin-½ systems in the **singlet state**:

$$
|\psi^-\rangle = \frac{|01\rangle - |10\rangle}{\sqrt{2}}.
$$

The minus sign is a relative phase. It matters for how the state behaves under rotations, even though measuring both particles in the computational basis gives `01` or `10`, each with probability `1/2`.

## What “shared” means

This is one joint state, not two particles carrying separate pure states. Neither particle alone has a definite spin along a chosen axis. If Alice and Bob measure along the **same** axis, their outcomes are always opposite in the ideal model. If their axes differ, the chance of agreement changes smoothly with the angle.

For measurement directions `a` and `b` in one plane, the ideal singlet correlation is

$$
E(a,b) = \langle A B \rangle = -\cos(\theta_a - \theta_b).
$$

Here each measurement result `A` and `B` is represented by `+1` or `−1`, and `E` is the average of the product `A × B` over many identically prepared pairs. At equal angles, `E = −1`: outcomes are opposite. At a right angle, `E = 0`: they are uncorrelated. At opposite directions, `E = +1`: the spin results agree.

The simulator takes the angle difference in degrees and evaluates this equation directly. It does not evolve a wavefunction through quantum gates.
