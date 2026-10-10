# Entangle Lab

An interactive introduction to quantum entanglement and the CHSH Bell test. Adjust two measurement directions, sample a singlet pair, and run a finite-shot simulation to compare the result with the classical bound.

## Try it

Open `index.html` in a modern browser. The experiment runs locally and needs no build step or account. For a local web server, run:

```sh
python -m http.server 8000
```

Then visit <http://localhost:8000>.

## Learn the idea

The [Entangle Lab field guide](docs/src/SUMMARY.md) is an mdBook for learners who are new to quantum computing. Build it with [mdBook](https://rust-lang.github.io/mdBook/):

```sh
cd docs
mdbook build
mdbook serve --open
```

The finished book is written to `docs/book/`, which is generated and ignored by Git.

## What the simulator does

- Shows the ideal joint outcome probabilities for a spin singlet at two chosen measurement angles.
- Samples one correlated pair of outcomes.
- Estimates four correlations from independently sampled pairs and combines them into the CHSH statistic.
- Compares the finite-shot estimate with the local hidden-variable bound `|S| ≤ 2` and quantum maximum `2√2`.

The model implements the ideal singlet probability distribution directly. It does not model a physical device, measurement loopholes, detector noise, or a full quantum circuit. Finite samples fluctuate, so an estimated score can fall on either side of a bound by chance.

## Project files

| File | Purpose |
| --- | --- |
| `index.html` | Semantic page structure and interactive lab controls |
| `styles.css` | Responsive visual system and accessible interaction states |
| `app.js` | Singlet probability model, sampling, and CHSH estimate |
| `docs/` | mdBook source and Catppuccin-inspired theme |
| `brag-output-20261010-211200/` | Narrated walkthrough video, poster, and composition source |

## License

MIT. See [LICENSE](LICENSE).
