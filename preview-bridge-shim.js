// Local-preview support for preview.html. Qollab provides the real
// `quantum.bridge` module at runtime; this stub exists only so main.js
// loads outside Qollab. It exports the two entry names as inert objects,
// so callBridge() rejects honestly ("Qollab Python bridge is unavailable")
// while the analytic figures still mount from local fixtures. No numbers
// here; nothing is presented as run data. Not part of the submission.
export const get_experience = {};
export const get_gallery = {};
