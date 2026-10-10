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

export const IMPACT_CARD = "MORE ENTANGLEMENT MADE YOU WORSE.";

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
  const comparison = result && result.comparison;
  if (!comparison || !comparison.separable || !comparison.max_entanglement) {
    return [
      IMPACT_CARD,
      "Same dimension. Same one-query task. Compare the two verified strategies above.",
    ];
  }

  const sep = comparison.separable;
  const max = comparison.max_entanglement;
  return [
    IMPACT_CARD,
    "MAX ENTANGLEMENT · EMPIRICAL " +
      formatPercent(max.empirical_rate) +
      " · ANALYTIC " +
      formatPercent(max.analytic_value) +
      " · CEILING " +
      formatPercent(max.ceiling),
    "SEPARABLE · EMPIRICAL " +
      formatPercent(sep.empirical_rate) +
      " · ANALYTIC " +
      formatPercent(sep.analytic_value),
    "Same dimension. Same channel-discrimination task. Entanglement stayed maximal; distinguishability collapsed.",
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
  nodes.impact.textContent = revealed ? impactBlock(result).join("\n") : "";
  nodes.impact.hidden = !revealed;
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
