# Composition Brief: Entangle Lab

Create a 22-second, 1920x1080 landscape science short. Use the supplied real screenshots in `composition/assets/screenshots/` as the source of truth for the actual app UI. Do not invent results or alter the sampled value. The Bell-test capture shows 2,600 pairs per setting and |S| = 2.806.

Use a cinematic but clear visual language: ink background (#0b0e19), violet accent (#b99cff), pale text (#f2f0ff), Manrope typography. Keep screenshots large enough to recognize and use restrained depth, slow camera movement, and short clean transitions. Place concise labels around screenshots, never over important data. Create motion using one paused GSAP timeline registered under the composition ID. Keep the composition self-contained and local.

The narrative follows the actual flow: lab settings, single-pair measurement, finite-shot CHSH score, field guide. Voiceover is in `assets/voiceover/narration.wav`; keep it intelligible above music. Music is `assets/music/happy-beats-business-moves-vol-12-by-ende-dot-app.mp3`. Credit in `share-copy.txt`: “Happy Beats & Business Moves Vol. 12 by Sascha Ende, ENDE.APP, CC BY 4.0.” A quiet click and soft chime are in `assets/sfx/`. Music levels are automated with a short opening and closing fade and a slight score reveal lift. Use the pre-extracted bands in `assets/audio/music-data.js` to make the violet halo respond subtly to bass energy. Include one small atom emoji in the brand label as a restrained science accent.

Narration: “Two particles leave together. Alice turns her analyzer. Bob turns his. Each result looks random. But compare enough pairs, and a pattern appears that no local hidden-variable model can explain. Set the angles. Measure a pair. Run the Bell test. Quantum theory, one browser, zero lab coats required.”

Storyboard: 0 to 3s hook over the lab settings; 3 to 7s single pair with +1 and -1; 7 to 15s real CHSH result with |S| = 2.806 and classical bound 2; 15 to 22s field guide and closing identity. Hold all text long enough to read. End cleanly with no extra claims.
