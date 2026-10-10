# A qubit in two minutes

A classical bit stores either `0` or `1`. A **qubit** is a two-level quantum system. Its pure state can be written

$$
|\psi\rangle = \alpha |0\rangle + \beta |1\rangle,
\qquad |\alpha|^2 + |\beta|^2 = 1.
$$

The complex numbers `α` and `β` are **amplitudes**. In a measurement using the `0`/`1` basis, the Born rule gives probability `|α|²` for `0` and `|β|²` for `1`. A superposition is not just a hidden classical choice between the two values; amplitudes can interfere when different operations are applied.

## Two qubits

Two qubits have four basis states: `|00⟩`, `|01⟩`, `|10⟩`, and `|11⟩`. A general pure state is

$$
|\Psi\rangle = c_{00}|00\rangle + c_{01}|01\rangle + c_{10}|10\rangle + c_{11}|11\rangle.
$$

If the state can be factored into one state for each qubit, `|Ψ⟩ = |u⟩ ⊗ |v⟩`, the pair is **separable**. If it cannot be factored that way, it is **entangled**.

## Check your intuition

The state `(|00⟩ + |11⟩)/√2` is entangled. Its measurement results are either `00` or `11`, each with probability `1/2`. It is not a product state: a product with a 50/50 result on the first qubit and a 50/50 result on the second would also assign probability to `01` and `10`.

Entangle Lab uses a different entangled state, the singlet, because its correlations have a simple rotational form.
