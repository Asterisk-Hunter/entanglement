# What the model leaves out

Entangle Lab is an ideal mathematical simulator. It is useful for exploring the relation between measurement angles, probabilities, correlations, and the CHSH statistic. It leaves out important parts of real quantum experiments.

## No physical device

The app computes the ideal singlet distribution directly. It does not prepare particles, run a quantum circuit on hardware, or record detector events. The display is a visualization of a model.

## No noise or experimental loopholes

Real experiments must account for imperfect state preparation, measurement error, loss, detector efficiency, finite timing, and the independence of random setting choices. The app assumes perfect preparation and measurement, and it samples setting pairs separately by construction. It cannot establish that a laboratory experiment is loophole-free.

## Finite-sample variation

Each run uses pseudorandom samples and a finite number of pairs per setting. An estimated `|S|` may be above or below both `2` and the quantum prediction. Such a result is sampling variation in the demo, not evidence that the underlying mathematical bounds changed.

The slider changes the number of pairs **for each of the four setting combinations**. It is not a single total spread across all four combinations.

## Scope of the conclusion

The CHSH bound applies to local hidden-variable models with the assumptions used in deriving the inequality. A violation constrains those models. It does not permit faster-than-light communication, and it does not select a unique interpretation of quantum mechanics.

When presenting the project, call it an interactive simulation of the ideal singlet CHSH prediction. Do not describe it as a physical Bell test or as experimental evidence collected by the project.
