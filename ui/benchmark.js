/* Stage 2 (UNDERSTANDING): reveal the strategy evidence already gathered by
 * the single Qollab backend job. EMPIRICAL, ANALYTIC and THEORETICAL CEILING
 * remain separate everywhere. */

export const KIND_LABELS = {
  EMPIRICAL: "EMPIRICAL",
  ANALYTIC: "ANALYTIC",
  THEORETICAL_CEILING: "THEORETICAL CEILING",
};

export const STRATEGY_SLUGS = {
  SEPARABLE: "hurts-separable",
  MAX_ENTANGLEMENT: "hurts-max-entanglement",
};

export const IMPACT_CARD = "THIS PAIR FAVORS THE SEPARABLE PROBE.";

const FALLBACK_LABELS = {
  "live-remote": "LIVE REMOTE",
  "live-local": "LIVE LOCAL",
  precomputed: "PRECOMPUTED",
};

export function kindLabel(kind) {
  return KIND_LABELS[kind];
}

export function fallbackLabel(provenance) {
  return FALLBACK_LABELS[provenance] || provenance;
}

function sourceLabel(result) {
  return result.source_label || fallbackLabel(result.provenance);
}

export function readoutLines(result) {
  return [
    "TRIALS " +
      result.trials +
      " (" +
      result.shots_per_channel +
      " shots per channel, d=" +
      result.dimension +
      ")",
    "EMPIRICAL WIN RATE " + formatPercent(result.empirical_rate),
    "CI 95% [" + formatPercent(result.ci_low) + ", " + formatPercent(result.ci_high) + "]",
    "ANALYTIC EXECUTABLE VALUE " + formatPercent(result.analytic_value),
    "THEORETICAL CEILING " + formatPercent(result.ceiling),
    "SOURCE " + sourceLabel(result),
  ];
}

export function mustRevealImpact(result) {
  return Boolean(result) && result.probe_kind === "SEPARABLE";
}

export function impactBlock(result) {
  return [
    IMPACT_CARD,
    "Same dimension. Same channels. The probe changes how distinguishable the outputs are.",
  ];
}

export function benchmarkAnnouncement(result) {
  return (
    "Strategy tested over " +
    result.trials +
    " independent one-query trials. Empirical win rate " +
    formatPercent(result.empirical_rate) +
    ". Analytic executable value " +
    formatPercent(result.analytic_value) +
    ". Helstrom ceiling " +
    formatPercent(result.ceiling) +
    ". Source " +
    sourceLabel(result) +
    "."
  );
}

export function renderBenchmark(result, nodes) {
  nodes.readout.textContent = readoutLines(result).join("\n");
  const revealed = mustRevealImpact(result);
  const impact = impactBlock(result);
  nodes.impact.textContent = revealed ? impact[0] : "";
  nodes.impact.hidden = !revealed;
  if (nodes.impactContext) {
    nodes.impactContext.textContent = revealed ? impact[1] : "";
    nodes.impactContext.hidden = !revealed;
  }
  nodes.provenance.textContent =
    "SOURCE " +
    sourceLabel(result) +
    " | d=" +
    result.dimension +
    " | trials=" +
    result.trials;
}

function formatPercent(value) {
  return (Number(value) * 100).toFixed(1) + "%";
}
