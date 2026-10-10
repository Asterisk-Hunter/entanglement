/* Entanglement Trap — Qollab submission controller.
 *
 * Qollab's IonQ backends allow one backend job per project Run. The first live
 * interaction calls quantum.bridge.get_experience exactly once. That one
 * four-circuit job supplies a sampled one-query round plus BOTH strategy
 * benchmarks. Every later hero click only reveals cached evidence.
 *
 * The Resource Lab uses get_gallery, a metadata-only bridge call that performs
 * zero backend jobs.
 */

import * as bridge from "quantum.bridge";
import { PROBE_KINDS, renderRound, roundAnnouncement } from "./ui/game.js";
import { benchmarkAnnouncement, renderBenchmark } from "./ui/benchmark.js";
import { METRICS, mountFingerprint } from "./ui/fingerprint.js";
import { mountHullView } from "./ui/hull.js";
import { mountHeatmap } from "./ui/heatmap.js";
import { mountSweep } from "./ui/sweep.js";
import * as gallery from "./ui/gallery.js";
import * as expert from "./ui/expert.js";

const nodes = {
  outcome: document.getElementById("round-outcome"),
  narrative: document.getElementById("round-narrative"),
  readout: document.getElementById("benchmark-readout"),
  impact: document.getElementById("impact"),
  provenance: document.getElementById("provenance"),
  state: document.getElementById("run-state"),
  error: document.getElementById("bridge-error"),
  announcer: document.getElementById("announcer"),
  run: document.getElementById("run"),
  strategy: document.getElementById("strategy"),
  compareSeparable: document.getElementById("compare-separable"),
  trials: document.getElementById("trials"),
  dimension: document.getElementById("dimension"),
  mechanism: document.getElementById("mechanism"),
  mechanismSummary: document.getElementById("mechanism-summary"),
  mechanismOverlap: document.getElementById("mechanism-overlap"),
  mechanismTrace: document.getElementById("mechanism-trace"),
  mechanismSuccess: document.getElementById("mechanism-success"),
  galleryList: document.getElementById("gallery-list"),
  galleryState: document.getElementById("gallery-state"),
  expertToggle: document.getElementById("expert-toggle"),
  expertDrawer: document.getElementById("expert-drawer"),
};

let experience = null;
let benchmarkRevealed = false;
let selectedPair = null;

/* Qollab injects the selected device as a bare `backend` global. Every read of
 * it goes through this probe, so a missing injection reports itself honestly
 * instead of throwing a ReferenceError, and so run metadata can record what the
 * runtime actually provided. */
function backendProbe() {
  const bare = typeof backend;
  const scoped = typeof globalThis.backend;
  return {
    present: bare !== "undefined" && bare !== "null",
    text:
      "backend typeof=" + bare +
      " · globalThis.backend typeof=" + scoped,
  };
}

function callBridge(name, args) {
  if (!bridge[name] || typeof bridge[name].callPromisingKwargs !== "function") {
    return Promise.reject(new Error("Qollab Python bridge is unavailable"));
  }
  const probe = backendProbe();
  if (!probe.present) {
    return Promise.reject(
      new Error("Qollab did not inject a backend (" + probe.text + ")")
    );
  }
  return bridge[name]
    .callPromisingKwargs(backend, args)
    .then(function (proxy) {
      try {
        return proxy.toJs({
          dict_converter: Object.fromEntries,
          create_pyproxies: false,
        });
      } finally {
        if (proxy && typeof proxy.destroy === "function") {
          proxy.destroy();
        }
      }
    });
}

function selectedProbe() {
  const checked = document.querySelector('input[name="probe"]:checked');
  return checked ? checked.value : PROBE_KINDS.MAX_ENTANGLEMENT;
}

function selectedShots() {
  return parseInt(nodes.trials.value, 10);
}

function selectedDimension() {
  return parseInt(nodes.dimension.value, 10);
}

function reportBridgeFailure(error) {
  const detail = error && error.message ? " " + error.message : "";
  // Qollab's IonQ backends allow ONE backend job per project Run. A failed run
  // may already have consumed it, so this Run cannot retry. The copy says so and
  // shows no number, because no verified result exists.
  nodes.error.textContent =
    "RUN FAILED BEFORE A COMPLETE EVIDENCE PAYLOAD WAS PRODUCED." +
    detail +
    " NO FALLBACK NUMBER IS PRESENTED AS LIVE DATA. This Qollab Run allows ONE BACKEND JOB," +
    " so a new run is needed to try again; if the heavy setting was the cause, start a NEW QOLLAB RUN" +
    " with a smaller dimension.";
  nodes.state.textContent = "RUN FAILED · NO VERIFIED RESULT · THIS RUN'S JOB IS SPENT";
  nodes.run.textContent = "RUN CLOSED · START A NEW QOLLAB RUN";
  nodes.run.disabled = true;
  nodes.trials.disabled = true;
  nodes.dimension.disabled = true;
}

function selectedBenchmark() {
  if (!experience) return null;
  return experience.benchmarks[selectedProbe()] || null;
}

function percent(value, digits) {
  return (Number(value) * 100).toFixed(digits) + "%";
}

function renderMechanism() {
  if (!experience) return;
  const metrics = METRICS[experience.dimension];
  if (!metrics) {
    nodes.mechanism.hidden = true;
    return;
  }

  const overlapMagnitude = Math.abs(metrics.overlap);
  nodes.mechanismSummary.textContent =
    "THE OUTPUTS BECAME " + percent(overlapMagnitude, 2) + " OVERLAPPING.";
  nodes.mechanismOverlap.textContent = percent(overlapMagnitude, 2) + " · ANALYTIC";
  nodes.mechanismTrace.textContent = percent(metrics.traceDistance, 2) + " · ANALYTIC";
  nodes.mechanismSuccess.textContent = percent(metrics.executable, 2) + " · ANALYTIC";
  nodes.mechanism.hidden = false;
}

function renderSelectedBenchmark() {
  const result = selectedBenchmark();
  if (!result) return;

  result.comparison = {
    separable: experience.benchmarks.SEPARABLE,
    max_entanglement: experience.benchmarks.MAX_ENTANGLEMENT,
  };
  result.source_label = experience.source_label;

  renderBenchmark(result, nodes);
  renderMechanism();
  nodes.announcer.textContent = benchmarkAnnouncement(result);
  nodes.provenance.textContent =
    "SOURCE " + experience.source_label +
    " | backend=" + experience.backend +
    " | d=" + experience.dimension +
    " | backend jobs=" + experience.total_backend_jobs +
    " | smoke: " + backendProbe().text;

  nodes.compareSeparable.disabled = selectedProbe() === PROBE_KINDS.SEPARABLE;
}

const expertController = expert.mountExpert(
  {
    toggle: nodes.expertToggle,
    drawer: nodes.expertDrawer,
    announcer: nodes.announcer,
  },
  null,
);

function selectGalleryPair(pair, openInspector) {
  selectedPair = pair;
  expert.update(selectedPair, experience);
  if (openInspector) expertController.open();
}

function loadGallery() {
  nodes.galleryState.textContent = "LOADING REGISTRY · ZERO BACKEND JOBS";
  callBridge("get_gallery", {})
    .then(function (result) {
      if (!result || result.kind !== "GalleryResult" || result.total_backend_jobs !== 0) {
        throw new Error("bridge returned an invalid gallery payload");
      }
      const pairs = Array.isArray(result.pairs) ? result.pairs : [];
      const initial = pairs.find(function (pair) {
        return pair.role === "FLAGSHIP";
      }) || pairs[0] || null;
      gallery.mountGallery(nodes.galleryList, pairs, function (pair) {
        selectGalleryPair(pair, true);
      });
      if (initial) selectGalleryPair(initial, false);
      nodes.galleryState.textContent =
        pairs.length + " REGISTERED PAIRS · METADATA ONLY · 0 BACKEND JOBS";
    })
    .catch(function (error) {
      const detail = error && error.message ? " · " + error.message : "";
      nodes.galleryState.textContent = "RESOURCE LAB METADATA UNAVAILABLE" + detail;
    });
}

document.getElementById("round-form").addEventListener("submit", function (event) {
  event.preventDefault();

  if (experience) {
    nodes.state.textContent = "EVIDENCE CACHED · NO SECOND BACKEND JOB SENT";
    return;
  }

  const shots = selectedShots();
  const dimension = selectedDimension();
  nodes.error.textContent = "";

  // Smoke step: record what the Qollab runtime actually injected, before any
  // bridge call. This is run metadata, not a measurement.
  const probe = backendProbe();
  console.log(
    "[entanglement-trap] Qollab backend probe · " +
    probe.text +
    " · bridge=" +
    typeof bridge +
    " · callPromisingKwargs=" +
    typeof bridge.get_experience.callPromisingKwargs
  );

  nodes.state.textContent =
    "RUNNING ONE QOLLAB JOB · 4 CIRCUITS · d=" +
    dimension +
    " · " +
    shots +
    " SHOTS / CHANNEL";
  nodes.provenance.textContent =
    "SOURCE: NOT RUN | PROVENANCE: NOT RUN | SMOKE: " + probe.text;
  nodes.run.disabled = true;
  nodes.trials.disabled = true;
  nodes.dimension.disabled = true;

  callBridge("get_experience", {
    probe_kind: selectedProbe(),
    shots: shots,
    d: dimension,
    rng_seed: null,
  })
    .then(function (result) {
      if (!result || result.kind !== "ExperienceResult" || result.total_backend_jobs !== 1) {
        throw new Error("bridge returned an invalid experience payload");
      }
      experience = result;
      renderRound(result.round, nodes);
      nodes.announcer.textContent = roundAnnouncement(result.round);
      nodes.state.textContent = "JOB COMPLETE · EVIDENCE CACHED · NO SECOND JOB NEEDED";
      nodes.strategy.disabled = false;
      nodes.run.textContent = "ROUND COMPLETE";
      nodes.provenance.textContent =
        "SOURCE " + result.source_label +
        " | backend=" + result.backend +
        " | d=" + result.dimension +
        " | backend jobs=" + result.total_backend_jobs +
        " | smoke: " + probe.text;
      if (selectedPair) expert.update(selectedPair, experience);
    })
    .catch(reportBridgeFailure);
});

nodes.strategy.addEventListener("click", function () {
  if (!experience) {
    nodes.error.textContent = "PLAY ONE ROUND FIRST. No strategy result is fabricated before a run.";
    return;
  }
  benchmarkRevealed = true;
  renderSelectedBenchmark();
});

nodes.compareSeparable.addEventListener("click", function () {
  if (!experience) return;
  const separable = document.getElementById("probe-sep");
  separable.checked = true;
  benchmarkRevealed = true;
  renderSelectedBenchmark();
  nodes.announcer.textContent =
    "Comparison switched to the separable probe using the same cached quantum job. " +
    benchmarkAnnouncement(experience.benchmarks.SEPARABLE);
});

for (const input of document.querySelectorAll('input[name="probe"]')) {
  input.addEventListener("change", function () {
    if (benchmarkRevealed) renderSelectedBenchmark();
  });
}

mountFingerprint(
  document.getElementById("fingerprint"),
  document.getElementById("figure-values"),
);

/* The proof-stage figures are pure fixture rendering. They submit zero
 * backend jobs and make no bridge call; the numbers are pinned against the
 * kernel by the Python test suite. */
mountSweep(
  document.getElementById("sweep"),
  document.getElementById("sweep-values"),
);

const hullHost = document.getElementById("hull");
const hullValues = document.getElementById("hull-values");
mountHullView(hullHost, hullValues);
hullHost.setAttribute("tabindex", "0");
hullHost.setAttribute("role", "application");
hullHost.setAttribute("aria-label", "Interactive eigenvalue circle. Use arrow keys to move the selected eigenvalue, or drag it with a pointer.");

mountHeatmap(
  document.getElementById("heatmap"),
  document.getElementById("heatmap-values"),
);

loadGallery();
