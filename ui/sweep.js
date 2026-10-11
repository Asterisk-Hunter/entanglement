/* Win probability against dimension, over the flagship curves.
 *
 * One job: show that the separable curve is flat at 1, that the executable
 * max-entanglement curve falls toward the chance line as d grows, and where the
 * Helstrom ceiling sits above it. Dimensions go past the live execution cap on
 * purpose, so the high end carries the label that says its numbers are theory.
 *
 * HONESTY:
 * - the executable row is ANALYTIC, because the flagship strategy is executable
 *   at those dimensions;
 * - the ceiling is THEORETICAL CEILING everywhere;
 * - d=1024 is PRECOMPUTED: no 20-qubit path is ever executed, so the row is
 *   drawn from theory and labelled as such;
 * - d=256 is annotated with the statistics fact that its value is not
 *   resolvable from chance at 4000 trials, because the standard error there is
 *   larger than the gap to 1/2.
 *
 * Fixtures are pinned against quantum.figures in tests/test_hull_view.py. No
 * physics is computed here. Motion budget: none; no animation elements. */

export const KIND = {
  analytic: "ANALYTIC",
  ceiling: "THEORETICAL CEILING",
};

export const TOKEN = {
  analytic: "ANALYTIC",
  ceiling: "THEORETICAL_CEILING",
};

export const PRECOMPUTED = "PRECOMPUTED";
export const LIVE_KERNEL = "LIVE_KERNEL";

export const SUCCESS_AXIS = {
  min: 0.5,
  max: 1,
  chance: 0.5,
  chanceLabel: "CHANCE 1/2",
  label: "ONE-QUERY WIN PROBABILITY",
};

/* Fixture table, pinned against quantum.science and quantum.figures. */
export const SWEEP_FIXTURE = {
  trials: 4000,
  rows: [
    {
      d: 2,
      separable: 1,
      simple: 1,
      ceiling: 1,
      live: true,
      source: LIVE_KERNEL,
      standardError: 0,
      resolvableFromChance: true,
    },
    {
      d: 4,
      separable: 1,
      simple: 0.875,
      ceiling: 0.9330127018922193,
      live: true,
      source: LIVE_KERNEL,
      standardError: 0.005229125165837972,
      resolvableFromChance: true,
    },
    {
      d: 16,
      separable: 1,
      simple: 0.6171875,
      ceiling: 0.7420614591379635,
      live: true,
      source: LIVE_KERNEL,
      standardError: 0.007685491035772373,
      resolvableFromChance: true,
    },
    {
      d: 64,
      separable: 1,
      simple: 0.53076171875,
      ceiling: 0.6240195927061527,
      live: true,
      source: LIVE_KERNEL,
      standardError: 0.007890717911881432,
      resolvableFromChance: true,
    },
    {
      d: 256,
      separable: 1,
      simple: 0.507781982421875,
      ceiling: 0.5623778102448098,
      live: true,
      source: LIVE_KERNEL,
      standardError: 0.007904736566603367,
      resolvableFromChance: false,
    },
    {
      d: 1024,
      separable: 1,
      simple: 0.5019512176513672,
      ceiling: 0.5312347374838271,
      live: false,
      source: PRECOMPUTED,
      standardError: 0.007905633952278543,
      resolvableFromChance: false,
    },
  ],
};

export const LAYOUT = {
  width: 760,
  height: 480,
  axisLeft: 130,
  axisRight: 720,
  axisTop: 70,
  axisBottom: 320,
  columnPitch: 96,
  columnWidth: 74,
  legendY: 412,
};

export function columnX(index) {
  return round(
    LAYOUT.axisLeft + 40 + index * LAYOUT.columnPitch + LAYOUT.columnWidth / 2
  );
}

export function yForSuccess(value) {
  const span = SUCCESS_AXIS.max - SUCCESS_AXIS.min;
  const ratio = (value - SUCCESS_AXIS.min) / span;
  return round(LAYOUT.axisBottom - ratio * (LAYOUT.axisBottom - LAYOUT.axisTop));
}

function round(value) {
  return Math.round(value * 1000) / 1000;
}

function full(value) {
  return Number(value).toString();
}

/* Plot labels stay compact; the accessible ledger retains exact values. */
function plotValue(value) {
  return Number(value).toFixed(3).replace(/\.?0+$/, "");
}

export function sweepModel() {
  return {
    layout: LAYOUT,
    axis: SUCCESS_AXIS,
    trials: SWEEP_FIXTURE.trials,
    rows: SWEEP_FIXTURE.rows.map(function (row, index) {
      return {
        d: row.d,
        x: columnX(index),
        separable: row.separable,
        simple: row.simple,
        ceiling: row.ceiling,
        separableKind: KIND.analytic,
        separableToken: TOKEN.analytic,
        simpleKind: KIND.analytic,
        simpleToken: TOKEN.analytic,
        ceilingKind: KIND.ceiling,
        ceilingToken: TOKEN.ceiling,
        live: row.live,
        source: row.source,
        precomputed: row.source === PRECOMPUTED,
        standardError: row.standardError,
        resolvableFromChance: row.resolvableFromChance,
        separableY: yForSuccess(row.separable),
        simpleY: yForSuccess(row.simple),
        ceilingY: yForSuccess(row.ceiling),
      };
    }),
  };
}

function chanceLine(model) {
  const y = yForSuccess(SUCCESS_AXIS.chance);
  return (
    '<line data-role="chance-line" x1="' + LAYOUT.axisLeft + '" y1="' + y + '" x2="' +
    LAYOUT.axisRight + '" y2="' + y + '" class="sw-chance" stroke-width="1"' +
    ' stroke-dasharray="2 3" aria-hidden="true"/>' +
    '<text data-role="chance-label" x="' + LAYOUT.axisLeft + '" y="' + (y - 8) +
    '" class="sw-tick-label" aria-hidden="true">' + SUCCESS_AXIS.chanceLabel + "</text>"
  );
}

function column(model, row) {
  const note =
    row.precomputed
      ? '<text x="' + row.x + '" y="' + (LAYOUT.axisBottom + 54) +
        '" class="sw-kind" text-anchor="middle" aria-hidden="true">' + PRECOMPUTED + "</text>"
      : row.resolvableFromChance
        ? ""
        : '<text data-role="resolution-marker" x="' + row.x + '" y="' + (LAYOUT.axisBottom + 54) +
          '" class="sw-kind" text-anchor="middle" aria-hidden="true">&#8224;</text>';
  return (
    '<g data-role="sweep-column" data-d="' + row.d + '" data-source="' + row.source + '">' +
    '<line data-role="ceiling-mark" data-kind="' + row.ceilingToken + '" x1="' + row.x +
    '" y1="' + (row.ceilingY - 8) + '" x2="' + row.x + '" y2="' + (row.ceilingY + 8) +
    '" class="sw-ceiling" stroke-width="1" aria-hidden="true"/>' +
    (row.ceiling === row.separable ? "" :
      '<text data-role="ceiling-value" class="sw-value" x="' + row.x + '" y="' + (row.ceilingY - 14) +
      '" text-anchor="middle" aria-hidden="true">' + plotValue(row.ceiling) + "</text>") +
    '<circle data-role="analytic-mark" data-kind="' + row.simpleToken + '" cx="' + row.x +
    '" cy="' + row.simpleY + '" r="4" class="sw-mark" stroke-width="1" aria-hidden="true"/>' +
    (row.simple === row.separable ? "" :
      '<text data-role="simple-value" class="sw-value" x="' + row.x + '" y="' +
      (row.simpleY > LAYOUT.axisBottom - 24 ? row.simpleY - 12 : row.simpleY + 18) +
      '" text-anchor="middle" aria-hidden="true">' + plotValue(row.simple) + "</text>") +
    '<rect data-role="separable-mark" data-kind="' + row.separableToken + '" x="' +
    round(row.x - 22) + '" y="' + (row.separableY - 6) + '" width="44" height="12"' +
    ' class="sw-separable" stroke-width="1" aria-hidden="true"/>' +
    '<text data-role="separable-value" class="sw-value" x="' + row.x + '" y="' +
    (row.separableY - 12) + '" text-anchor="middle" aria-hidden="true">' +
    plotValue(row.separable) + "</text>" +
    '<text class="sw-column-label" x="' + row.x + '" y="' + (LAYOUT.axisBottom + 22) +
    '" text-anchor="middle" aria-hidden="true">d=' + row.d + "</text>" +
    '<text class="sw-kind" x="' + row.x + '" y="' + (LAYOUT.axisBottom + 38) +
    '" text-anchor="middle" aria-hidden="true">' + KIND.analytic + "</text>" +
    note +
    "</g>"
  );
}

function legend(model) {
  const y = LAYOUT.legendY;
  return (
    '<g data-role="legend" aria-hidden="true">' +
    '<rect x="130" y="' + (y - 16) + '" width="22" height="10" class="sw-separable" stroke-width="1"/>' +
    '<text x="160" y="' + (y - 7) + '" class="sw-note">SEPARABLE, FLAT AT 1</text>' +
    '<circle cx="' + (130 + 190) + '" cy="' + (y - 11) + '" r="4" class="sw-mark" stroke-width="1"/>' +
    '<text x="' + (130 + 200) + '" y="' + (y - 7) + '" class="sw-note">EXECUTABLE STRATEGY</text>' +
    '<line data-role="ceiling-mark" data-kind="' + TOKEN.ceiling + '" x1="' + (130 + 360) +
    '" y1="' + (y - 16) + '" x2="' + (130 + 360) + '" y2="' + (y - 6) +
    '" class="sw-ceiling" stroke-width="1"/>' +
    '<text x="' + (130 + 370) + '" y="' + (y - 7) + '" class="sw-note">' + KIND.ceiling + '</text>' +
    '<text x="130" y="' + (y + 18) + '" class="sw-note">' + KIND.analytic +
    ": executable strategy. " + KIND.ceiling + ": theory only.</text>" +
    '<text x="130" y="' + (y + 36) + '" class="sw-note">' + PRECOMPUTED +
    ": theory only, never executed; there is no 20-qubit live path.</text>" +
    '<text x="130" y="' + (y + 54) + '" class="sw-kind" aria-hidden="true">&#8224; BELOW CHANCE RESOLUTION</text>' +
    "</g>"
  );
}

export function renderSweep(model) {
  return (
    '<svg class="sweepview" viewBox="0 0 ' + model.layout.width + " " + model.layout.height +
    '" preserveAspectRatio="xMidYMid meet" role="img" aria-label="' + sweepAriaLabel(model) +
    '" data-role="sweep-view">' +
    chanceLine(model) +
    model.rows.map(function (row) {
      return column(model, row);
    }).join("") +
    legend(model) +
    "</svg>"
  );
}

function sweepAriaLabel(model) {
  const readings = model.rows
    .map(function (row) {
      return (
        "d=" + row.d + " separable " + full(row.separable) + " " + row.separableKind +
        ", executable " + full(row.simple) + " " + row.simpleKind +
        ", ceiling " + full(row.ceiling) + " " + row.ceilingKind +
        (row.precomputed ? ", precomputed and never executed" : "")
      );
    })
    .join(". ");
  return (
    "Win probability against dimension at 2, 4, 16, 64, 256 and 1024. " +
    "The separable strategy is flat at 1 across every dimension. " +
    "The executable maximal-entanglement strategy falls from 1 toward the chance line. " +
    "The Helstrom ceiling stays above it but also approaches the chance line. " +
    "At d = 1024 the numbers are precomputed theory only. " +
    "All values are analytic or labelled theoretical ceilings; none is measured here. " +
    "Readings: " + readings + "."
  );
}

export function sweepTextEquivalent(model) {
  return model.rows.map(function (row) {
    return {
      label: "d=" + row.d,
      text:
        "SEPARABLE " + full(row.separable) + " " + row.separableKind +
        ". EXECUTABLE " + full(row.simple) + " " + row.simpleKind +
        ". HELSTROM CEILING " + full(row.ceiling) + " " + row.ceilingKind +
        ". STANDARD ERROR AT " + full(model.trials) + " TRIALS " + full(row.standardError) +
        (row.precomputed ? ". PRECOMPUTED, THEORY ONLY, NEVER EXECUTED" : "") +
        (row.resolvableFromChance
          ? "."
          : ". NOT RESOLVABLE FROM CHANCE AT THIS MANY TRIALS"),
    };
  });
}

export function mountSweep(host, valuesHost) {
  const model = sweepModel();
  host.innerHTML = renderSweep(model);
  valuesHost.innerHTML = sweepTextEquivalent(model)
    .map(function (row) {
      return (
        '<dt class="sw-ledger-key">' + row.label + "</dt>" +
        '<dd class="sw-ledger-value">' + row.text + "</dd>"
      );
    })
    .join("");
  return model;
}
