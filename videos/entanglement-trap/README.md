# Entanglement Trap video

This directory contains the editable source and the rendered 26-second video for the root Entanglement Trap app. It does not contain or depict the sibling Entangle Lab app.

## Review

- [`renders/video.mp4`](renders/video.mp4) is the deliverable.
- [`STORYBOARD.md`](STORYBOARD.md) records timing, exact claims, and shot intent.
- [`BRIEF.md`](BRIEF.md) records the locked scope and capture limitations.
- [`compositions/frames/`](compositions/frames/) contains the six editable scenes.
- The per-frame snapshot review files are generated locally and ignored by Git.

The interface imagery comes from the root app's HTML, CSS, UI renderers, and registered HURTS pair metadata. The imagery is a static editorial preview: no Qollab backend job was submitted to produce this film. The expert evidence image uses `ui/expert.js` with the registry payload and no run metadata.

## Render

Use Node.js and npm, then run these commands from this directory:

```sh
npm run check
npm run dev
npm run render
```

The scripts pin HyperFrames `0.8.145`. `npm run render` writes `renders/video.mp4`. This package is only for editing this video; it does not run the Qollab-injected app at the repository root.

## Refresh the expert drawer crop

From the repository root, use Python 3.12 with `requirements.txt` installed, plus Playwright and Chromium. Then run:

```sh
python3.12 videos/entanglement-trap/capture/export-expert-fixture.py
videos/entanglement-trap/capture/capture-expert-crop.sh
```

The script serves the repository locally and refreshes the source-rendered expert drawer image in both asset directories. The other six source crops are retained as named capture artifacts. JetBrains Mono is bundled under `assets/fonts/`; its OFL license is included alongside the font files.
