# Attribution & Build Timeline

## Build window

All original work in this repository was built during the hackathon window:
**2026-10-10 11:16 IST → 2026-10-11 10:34 IST** (~23 hours).

Every commit on `main` falls inside that window. Verify with:

```sh
git log --reverse --format="%h | %aI | %s"
```

| Phase | Commits | When (IST) |
|---|---|---|
| Scaffold, claim ledger, science kernel, channels, engine, UI, web surface, test suites | `c35e7e8` → `5547e24` | Oct 10, 11:16–11:17 |
| Entangle Lab app, field guide, first walkthrough video, promo alignment | `2d31ac0` → `b219642` | Oct 10, 21:16–21:25 |
| Repo restructure (Trap to root, Lab to `entangle-lab/`), compliance scoping | `246c952` → `fd8372b` | Oct 10, 22:35–22:38 |
| Trap docs rebuild, traceable references, Lab as on-ramp, Trap launch video + polish | `131dbf4` → `bfc2c70` | Oct 11, 01:06–10:34 |

## Original work (built in-window)

- Entanglement Trap app (`index.html`, `main.js`, `main.css`)
- `quantum/` science kernel and engine, `channels/` pair registry
- `ui/` figures (fingerprint, sweep, hull, heatmap, gallery, expert drawer)
- `claims.json` provenance ledger and all 16 test suites
- Trap docs (`docs/src/`) and Entangle Lab app + guide (`entangle-lab/`)
- Launch video composition, storyboard, and screenshots captured from the app itself (`videos/entanglement-trap/`)

## Third-party components (not built here)

These are dependencies, services, fonts, and cited science — used, not authored,
during the window:

| Component | Use | License / source |
|---|---|---|
| JetBrains Mono (bundled woff2 + OFL text in `videos/entanglement-trap/assets/fonts/`) | Video typography | OFL-1.1 |
| Manrope + DM Mono (runtime link in `entangle-lab/index.html`) | Lab typography | Google Fonts (OFL) |
| GSAP 3.14.2 (jsDelivr CDN in `videos/entanglement-trap/index.html`) | Video animation | GreenSock license (free tier) |
| Hyperframes CLI 0.8.145 (`npx`, see `videos/entanglement-trap/package.json`) | Video render tooling | Upstream package license |
| Qollab / IonQ backend | Live quantum-job service the app bridges to | External service |
| Lien & Quintino (2026), arXiv:2605.31519 | Reproduced channel-discrimination result, cited — no discovery claimed | Cited paper |
| pytest, mdBook | Test runner and docs generator | MIT / MPL-2.0 |

No other vendored code, datasets, or media are included. The earlier Entangle Lab
walkthrough video and its music track were removed from the repository before
submission.
