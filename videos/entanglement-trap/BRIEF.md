---
workflow: product-launch-video
flow: automation
storyboard: no
message: "At d=256, maximum entanglement makes this channel-discrimination strategy perform worse than a separable probe."
destination: hackathon-demo
aspect: 1920x1080
language: en
length: 26s
audience: Qollab hackathon judges, quantum information students, educators, and researchers
angle: counterintuitive-result-with-executable-evidence
narration: no
---

## Intent

A 26-second, silent product reveal for Entanglement Trap, the channel-discrimination app at the repository root. The hook is the reversal: maximum entanglement performs worse than a separable probe for this specific channel pair at d=256. The video shows the inputs, one-job workflow, analytic benchmark, mechanism, theoretical ceiling, provenance labels, citation, and limits. Type and UI should feel like the amber instrument panel in the app.

## Assets

- `../../index.html` and `../../main.css` — root Entanglement Trap interface and visual system; use source-derived tight crops, not the sibling teaching toy.
- `../../claims.json` — canonical claim ledger; use only records marked safe for demonstration and preserve their numeric values verbatim.
- `../../ui/sweep.js` — executable sweep figure renderer and pinned data fixtures.
- `https://github.com/Asterisk-Hunter/entanglement` — public source repository and CTA destination.

## Customizations

- Six scenes at 0–3, 3–7, 7–12, 12–17, 17–22, and 22–26 seconds.
- Use only the supplied amber-on-ink identity. Keep all display copy at least 28 px at 1080p; load no unrequested external fonts.
- Preserve the exact numeric claims from the user brief. Never show the quarantined unsafe value.
- Keep source, backend-job budget, evidence-kind labels, citation, and claim limits visible in the story.
- No voiceover, music, or sound effects. Make the cut understandable with on-screen text alone.

## Notes

The guessed public Qollab project URL is unpublished or incorrect (the page returns “Project not found”). This is a source-code-driven product reveal, not a claim of a live Qollab session. The job line describes the app's one-job-per-run contract. The benchmark values shown are analytic, and the Helstrom ceiling is theoretical. No hardware job was sent to create the video.

The requested `npm i && npm run dev` command is not currently valid at the repository root: the app is a Qollab-injected fragment and the repository has no root `package.json`. Do not present it as a working command unless the local runner is made real. The actual reachable CTA is the GitHub repository.
