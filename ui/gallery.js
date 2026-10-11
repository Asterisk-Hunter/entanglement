/* Runtime-generic Resource Lab renderer.
 *
 * Pair science comes from quantum.bridge.get_gallery -> channels.api registry.
 * This module contains no pair slug, formula, or hard-coded science snapshot.
 */

export const KIND_LABELS = {
  EMPIRICAL: "EMPIRICAL",
  ANALYTIC: "ANALYTIC",
  THEORETICAL_CEILING: "THEORETICAL CEILING",
};

const PROBE_KINDS = {
  SEPARABLE: "SEPARABLE",
  MAX_ENTANGLEMENT: "MAX_ENTANGLEMENT",
};

export function kindLabel(kind) {
  return KIND_LABELS[kind] === undefined ? String(kind) : KIND_LABELS[kind];
}

export function escapeHtml(text) {
  return String(text)
    .split("&").join("&amp;")
    .split("<").join("&lt;")
    .split(">").join("&gt;")
    .split('"').join("&quot;")
    .split("'").join("&#39;");
}

function strategyFor(strategies, probeKind) {
  return strategies.find(function (strategy) {
    return strategy.probe_kind === probeKind;
  }) || null;
}

function effectModel(pair) {
  const separable = strategyFor(pair.strategies || [], PROBE_KINDS.SEPARABLE);
  const entangled = strategyFor(pair.strategies || [], PROBE_KINDS.MAX_ENTANGLEMENT);
  if (!separable || !entangled) {
    return { token: "NOT CLASSIFIED", text: "THIS PAIR DOES NOT PUBLISH BOTH PROBE VALUES." };
  }

  const direction = entangled.analytic_value > separable.analytic_value
    ? "HELPS"
    : entangled.analytic_value < separable.analytic_value
      ? "HURTS"
      : "NEUTRAL";
  const isCeiling = entangled.bound_kind === "THEORETICAL_CEILING";
  const subject = isCeiling ? "THE MAX-ENTANGLEMENT THEORETICAL OPTIMUM" : "THE MAX-ENTANGLEMENT STRATEGY";
  const verb = direction === "HELPS" ? "IS HIGHER THAN" : direction === "HURTS" ? "IS LOWER THAN" : "MATCHES";
  return {
    token: direction,
    text: subject + " " + verb + " THE SEPARABLE VALUE.",
  };
}

export function cardModel(pair) {
  const effect = effectModel(pair);
  return {
    name: pair.name,
    slug: pair.slug,
    role: pair.role || "REGISTERED",
    citation: pair.citation,
    dimension: pair.dimension,
    effect: effect,
    strategies: (pair.strategies || []).map(function (strategy) {
      return {
        label: strategy.label,
        probeKind: strategy.probe_kind,
        value: strategy.analytic_value,
        valueText: String(strategy.analytic_value),
        displayValue: (Number(strategy.analytic_value) * 100).toFixed(1) + "%",
        kindToken: strategy.bound_kind,
        kindLabel: kindLabel(strategy.bound_kind),
      };
    }),
  };
}

export function renderCard(card, index) {
  const rows = card.strategies.map(function (row) {
    return (
      "<dt>" + escapeHtml(row.label) + "</dt>" +
      "<dd><span class=\"kind-tag\">" + escapeHtml(row.kindLabel) + "</span>" +
      "<span class=\"gallery-value\">" + escapeHtml(row.valueText) + "</span></dd>"
    );
  }).join("");
  const summaryRows = card.strategies.map(function (row) {
    return "<dt>" + escapeHtml(row.label) + "</dt>" +
      "<dd><span class=\"kind-tag\">" + escapeHtml(row.kindLabel) + "</span>" +
      "<span class=\"gallery-value\">" + escapeHtml(row.displayValue) + "</span></dd>";
  }).join("");

  return (
    "<li class=\"gallery-item\" data-effect=\"" + escapeHtml(card.effect.token) + "\">" +
    "<div class=\"gallery-body\">" +
    "<div class=\"gallery-heading\"><h3 class=\"gallery-name\">" + escapeHtml(card.name) + "</h3>" +
    "<button type=\"button\" class=\"gallery-select\" data-pair-index=\"" + index + "\">INSPECT</button></div>" +
    "<p class=\"gallery-meta\">" + escapeHtml(card.role) + " · d = " + escapeHtml(card.dimension) + " · " + escapeHtml(card.effect.token) + "</p>" +
    "<p class=\"label\">ONE-QUERY WIN PROBABILITY</p><dl class=\"gallery-rows\">" + summaryRows + "</dl>" +
    "<details class=\"figure-details gallery-details\"><summary>Exact values and source</summary><dl class=\"gallery-rows\">" + rows +
    "<dt>READING</dt><dd>" + escapeHtml(card.effect.text) + "</dd>" +
    "<dt>SOURCE</dt><dd>" + escapeHtml(card.citation) + "</dd></dl></details>" +
    "</div></li>"
  );
}

export function mountGallery(listNode, pairs, onSelect) {
  if (!listNode) return [];
  const safePairs = Array.isArray(pairs) ? pairs : [];
  const cards = safePairs.map(cardModel);
  listNode.innerHTML = cards.map(renderCard).join("");
  for (const button of listNode.querySelectorAll(".gallery-select")) {
    button.addEventListener("click", function () {
      const index = parseInt(button.getAttribute("data-pair-index"), 10);
      if (safePairs[index] && typeof onSelect === "function") {
        onSelect(safePairs[index]);
      }
    });
  }
  return cards;
}
