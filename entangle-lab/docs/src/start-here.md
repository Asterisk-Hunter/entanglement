# Start here

## Run the page

From the repository root, start a local server:

```sh
python -m http.server 8000
```

Open <http://localhost:8000/entangle-lab/>. Entangle Lab uses plain HTML, CSS, and JavaScript. It needs no installation or app backend. The page loads optional typefaces from Google Fonts when available and falls back to system fonts.

## Your first experiment

1. Find **The experiment**. Alice begins at `0°`, Bob at `45°`.
2. Read the expected correlation and the two joint-outcome probabilities.
3. Click **Measure one pair** a few times. Individual outcomes vary.
4. Set both axes to `0°`. The singlet predicts opposite results with probability `1` in the ideal model.
5. Find **The Bell test** and click **Run Bell test**. The four default settings are chosen to produce a CHSH value near the quantum maximum when there are enough samples.

Your measured number will not be exactly the theoretical value. The app draws a finite random sample, so a different run gives a slightly different result.

## Build the field guide

Install mdBook, then run this from the repository root:

```sh
cd entangle-lab/docs
mdbook build
```

The site is generated at `entangle-lab/docs/book/index.html`. To read the guide with live reload, run `mdbook serve --open` from `entangle-lab/docs`.
