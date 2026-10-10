# Documentation maintenance

The book source lives in `src/`. Keep its navigation in `src/SUMMARY.md` and its title, language, and output settings in `book.toml`.

Build and serve from this directory:

```sh
mdbook build
mdbook serve --open
```

Before changing a scientific value or evidence label, check the corresponding implementation, test, and record in `../claims.json`. Keep examples runnable, describe what a command proves, and distinguish a local simulation from a Qollab backend measurement. Update this guide and the root README when commands or project behavior change.

Generated output goes to `book/` and is ignored by Git. The source pages are the maintained documentation.
