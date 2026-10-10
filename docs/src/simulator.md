# How the simulator works

The app is deliberately small: `index.html` provides the controls, `styles.css` draws the interface, and `app.js` implements the probability model. There is no app server, account, or backend.

## One pair

The app converts angles from degrees to radians and evaluates

```text
E = −cos(θA − θB)
P(same) = (1 + E) / 2
P(opposite) = 1 − P(same)
```

When you click **Measure one pair**, JavaScript samples `A = +1` or `−1` with equal probability. It then samples Bob's result conditionally so that `P(B = +1 | A = a) = (1 + aE) / 2`. This reproduces the singlet joint distribution.

## Four setting pairs

The Bell test calls the same sampling rule for each of the four setting pairs. For each pair, it estimates the correlation as

```text
Ê = (number of equal outcomes − number of different outcomes) / number of pairs
```

That is equivalent to averaging `A × B`, because equal outcomes contribute `+1` and different outcomes contribute `−1`. The app combines the four estimates using the CHSH formula and displays the magnitude.

The random-number generator is JavaScript's `Math.random()`. It is suitable for a classroom visualization, not security or precision experimental work. Separate runs give different finite samples.

## Try these settings

| Alice | Bob | Ideal `|S|` | What to notice |
| --- | --- | ---: | --- |
| `0°`, `90°` | `45°`, `−45°` | `2√2` | The standard maximum-violation settings |
| `0°`, `90°` | `0°`, `90°` | `2` | Correlations combine to the classical bound |
| `0°`, `0°` | `0°`, `0°` | `2` | Aligned singlet results are always opposite |

These are theoretical values. A finite simulated run only estimates them.
