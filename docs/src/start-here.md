# Start here

## Run the page

You can open `index.html` directly in a modern browser. The page uses plain HTML, CSS, and JavaScript, so it has no installation step and makes no network requests for the simulation. The optional typefaces are fetched from Google Fonts; system fallbacks are used if they are unavailable.

For a local web server, run this command from the project root:

```sh
python -m http.server 8000
```

Open <http://localhost:8000>.

## Your first experiment

1. Find **The experiment**. Alice begins at `0°`, Bob at `45°`.
2. Read the expected correlation and the two joint-outcome probabilities.
3. Click **Measure one pair** a few times. Individual outcomes vary.
4. Set both axes to `0°`. The singlet predicts opposite results with probability `1` in the ideal model.
5. Find **The Bell test** and click **Run Bell test**. The four default settings are chosen to produce a CHSH value near the quantum maximum when there are enough samples.

Your measured number will not be exactly the theoretical value. The app draws a finite random sample, so a different run gives a slightly different result.

## Build the field guide

Install mdBook, then run:

```sh
cd docs
mdbook build
```

The site is generated at `docs/book/index.html`. To read the guide with live reload, use `mdbook serve --open` from the same directory.
