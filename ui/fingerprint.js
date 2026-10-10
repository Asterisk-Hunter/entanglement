/* Paired output-state fingerprint figure for the proof stage.
 *
 * One job only: show that the probe stays MAXIMALLY entangled while the two
 * channel output states become harder to tell apart as d grows. The entanglement
 * indicator is fixed: a ring with the word MAXIMAL, drawn once, with no scale,
 * no percentage, no response to d, and no motion. Distinguishability is the only
 * quantity that changes along an axis here.
 *
 * Every number is a kernel fixture from quantum.science and is pinned against
 * the kernel by tests/test_visual_metrics.py. No physics is computed here.
 *
 * The renderer returns a markup string, so it can be asserted in tests without
 * a DOM. No path, polyline, polygon, or animation element is emitted: data is
 * lines, rects, and circles at 1px strokes. */

export const DIMENSIONS = [4, 16, 64, 256];

export const OVERLAP_AXIS = { min: -1, max: 1, label: "OVERLAP (SIGNED)" };
export const TRACE_AXIS = { min: 0, max: 1, label: "TRACE DISTANCE" };
export const SUCCESS_AXIS = {
  min: 0.5,
  max: 1,
  chance: 0.5,
  chanceLabel: "CHANCE 1/2",
  label: "ONE-QUERY WIN PROBABILITY",
};

/* Kernel fixtures. Trace distance is sqrt(1 - overlap^2) for the two output
   states; the whole table is verified against quantum.science in tests. */
export const METRICS = {
  4: {
    overlap: -0.5,
    traceDistance: 0.8660254037844386,
    executable: 0.875,
    ceiling: 0.9330127018922193,
  },
  16: {
    overlap: -0.875,
    traceDistance: 0.4841229182759271,
    executable: 0.6171875,
    ceiling: 0.7420614591379635,
  },
  64: {
    overlap: -0.96875,
    traceDistance: 0.24803918541230538,
    executable: 0.53076171875,
    ceiling: 0.6240195927061527,
  },
  256: {
    overlap: -0.9921875,
    traceDistance: 0.12475562048961962,
    executable: 0.507781982421875,
    ceiling: 0.5623778102448098,
  },
};

/* Machine tokens for data attributes. They keep the underscore form the bridge
   uses, so a consumer can match on them without parsing human text. */
export const TOKEN = {
  analytic: "ANALYTIC",
  ceiling: "THEORETICAL_CEILING",
  empirical: "EMPIRICAL",
};

/* Human labels, printed as text next to every value. */
export const KIND = {
  analytic: "ANALYTIC",
  ceiling: "THEORETICAL CEILING",
  empirical: "EMPIRICAL",
};

/* Geometry, fixed for every dimension. */
const LAYOUT = {
  width: 760,
  height: 420,
  columnStartX: 140,
  columnPitch: 150,
  columnWidth: 120,
  overlapY: 96,
  traceY: 190,
  successY: 286,
  legendY: 344,
};

const LOCK = {
  cx: 40,
  cy: 44,
  r: 16,
  textX: 66,
  textY: 48,
};

function position(axis, value) {
  const span = axis.max - axis.min;
  return ((value - axis.min) / span) * LAYOUT.columnWidth;
}

function round(value) {
  return Math.round(value * 1000) / 1000;
}

function full(value) {
  return Number(value).toString();
}

/* One model for the figure and for its text equivalent. */
export function figureModel() {
  const rows = DIMENSIONS.map(function (d, index) {
    const metrics = METRICS[d];
    const columnX = LAYOUT.columnStartX + index * LAYOUT.columnPitch;
    const traceSeparationPx = round(position(TRACE_AXIS, metrics.traceDistance));
    return {
      d: d,
      columnX: columnX,
      label: "d=" + d,
      overlap: metrics.overlap,
      overlapKind: KIND.analytic,
      overlapToken: TOKEN.analytic,
      overlapMarkX: round(columnX + position(OVERLAP_AXIS, metrics.overlap)),
      traceDistance: metrics.traceDistance,
      traceKind: KIND.analytic,
      traceToken: TOKEN.analytic,
      traceSeparationPx: traceSeparationPx,
      executable: metrics.executable,
      executableKind: KIND.analytic,
      executableToken: TOKEN.analytic,
      executableMarkX: round(columnX + position(SUCCESS_AXIS, metrics.executable)),
      ceiling: metrics.ceiling,
      ceilingKind: KIND.ceiling,
      ceilingToken: TOKEN.ceiling,
      ceilingMarkX: round(columnX + position(SUCCESS_AXIS, metrics.ceiling)),
      empiricalKind: KIND.empirical,
      empiricalToken: TOKEN.empirical,
      measuredHere: false,
    };
  });

  return {
    layout: LAYOUT,
    overlapX0: LAYOUT.columnStartX,
    traceX0: LAYOUT.columnStartX,
    successX0: LAYOUT.columnStartX,
    overlapWidth: LAYOUT.columnWidth,
    traceWidth: LAYOUT.columnWidth,
    lock: {
      heading: "ENTANGLEMENT",
      label: "MAXIMAL",
      cx: LOCK.cx,
      cy: LOCK.cy,
      r: LOCK.r,
      textX: LOCK.textX,
      textY: LOCK.textY,
      dimensionDependent: false,
      scale: null,
      percent: null,
    },
    axes: {
      overlap: OVERLAP_AXIS,
      trace: TRACE_AXIS,
      success: SUCCESS_AXIS,
    },
    rows: rows,
    measured: null,
  };
}

function axisLine(model, axis, y) {
  const width = model.layout.columnWidth;
  const span = axis.max - axis.min;
  const ticks = [];
  for (let value = axis.min; value <= axis.max + 1e-9; value += span) {
    ticks.push(value);
  }
  return (
    '<line x1="' + model.overlapX0 + '" y1="' + y + '" x2="' + (model.overlapX0 + width) +
    '" y2="' + y + '" class="fp-axis" stroke-width="1" aria-hidden="true"/>' +
    ticks
      .map(function (value) {
        const x = round(model.overlapX0 + position(axis, value));
        return (
          '<line x1="' + x + '" y1="' + (y - 4) + '" x2="' + x + '" y2="' + (y + 4) +
          '" class="fp-tick" stroke-width="1" aria-hidden="true"/>' +
          '<text x="' + x + '" y="' + (y + 18) + '" class="fp-tick-label" text-anchor="middle"' +
          ' aria-hidden="true">' + full(value) + "</text>"
        );
      })
      .join("")
  );
}

function overlapRow(model, row) {
  return (
    '<g data-role="overlap-row" data-d="' + row.d + '" data-kind="' + row.overlapToken + '">' +
    axisLine(model, OVERLAP_AXIS, model.layout.overlapY) +
    '<rect x="' + (row.overlapMarkX - 4) + '" y="' + (model.layout.overlapY - 4) +
    '" width="8" height="8" class="fp-mark-a" stroke-width="1" aria-hidden="true"/>' +
    '<text x="' + row.columnX + '" y="' + (model.layout.overlapY - 18) +
    '" class="fp-column-label" text-anchor="middle" aria-hidden="true">' + row.label + "</text>" +
    "</g>"
  );
}

function traceRow(model, row) {
  const y = model.layout.traceY;
  return (
    '<g data-role="trace-row" data-d="' + row.d + '" data-kind="' + row.traceToken + '">' +
    axisLine(model, TRACE_AXIS, y) +
    '<rect x="' + row.columnX + '" y="' + (y - 4) + '" width="8" height="8"' +
    ' class="fp-mark-a" stroke-width="1" aria-hidden="true"/>' +
    '<rect x="' + round(row.columnX + row.traceSeparationPx - 4) + '" y="' + (y - 4) +
    '" width="8" height="8" class="fp-mark-b" stroke-width="1" aria-hidden="true"/>' +
    "</g>"
  );
}

function successRow(model, row) {
  const y = model.layout.successY;
  const chanceX = round(row.columnX + position(SUCCESS_AXIS, SUCCESS_AXIS.chance));
  return (
    '<g data-role="success-row" data-d="' + row.d + '">' +
    axisLine(model, SUCCESS_AXIS, y) +
    '<line data-role="chance-line" x1="' + chanceX + '" y1="' + (y - 6) + '" x2="' + chanceX +
    '" y2="' + (y + 6) + '" class="fp-chance" stroke-width="1" stroke-dasharray="2 3"' +
    ' aria-hidden="true"/>' +
    '<line data-role="ceiling-mark" data-kind="' + row.ceilingToken + '" x1="' + row.ceilingMarkX +
    '" y1="' + (y - 8) + '" x2="' + row.ceilingMarkX + '" y2="' + (y + 8) +
    '" class="fp-reference" stroke-width="1" aria-hidden="true"/>' +
    '<circle data-role="analytic-mark" data-kind="' + row.executableToken + '" cx="' +
    row.executableMarkX + '" cy="' + y + '" r="4" class="fp-reference" stroke-width="1"' +
    ' aria-hidden="true"/>' +
    "</g>"
  );
}

function legend(model) {
  const y = model.layout.legendY;
  return (
    '<g data-role="legend" aria-hidden="true">' +
    '<text x="8" y="' + (y - 44) + '" class="fp-axis-label">' + OVERLAP_AXIS.label + "</text>" +
    '<text x="8" y="' + (y - 28) + '" class="fp-axis-label">' + TRACE_AXIS.label + "</text>" +
    '<text x="8" y="' + (y - 12) + '" class="fp-axis-label">' + SUCCESS_AXIS.label + "</text>" +
    '<line x1="8" y1="' + (y - 4) + '" x2="752" y2="' + (y - 4) + '" class="fp-axis"' +
    ' stroke-width="1"/>' +
    '<text x="8" y="' + (y + 12) +
    '" class="fp-note">square A and square B: the two channel output states, which move together' +
    " as the dimension grows</text>" +
    '<text x="8" y="' + (y + 28) + '" class="fp-note">CIRCLE: ' + KIND.analytic +
    " formula. VERTICAL TICK: " + KIND.ceiling + " (Helstrom optimum).</text>" +
    '<text x="8" y="' + (y + 44) + '" class="fp-note">' + KIND.empirical +
    ": not measured here. DASHED LINE: " + SUCCESS_AXIS.chanceLabel + "</text>" +
    "</g>"
  );
}

function ariaLabel(model) {
  const readings = model.rows
    .map(function (row) {
      return (
        "d=" + row.d +
        " signed overlap " + full(row.overlap) +
        ", trace distance " + full(row.traceDistance) +
        ", executable " + full(row.executable) +
        ", ceiling " + full(row.ceiling)
      );
    })
    .join(". ");
  return (
    "Paired output-state fingerprints at dimensions 4, 16, 64 and 256. " +
    "Entanglement stays MAXIMAL at every dimension. " +
    "OVERLAP (SIGNED) is read on a signed axis from minus one to one. " +
    "TRACE DISTANCE is read on a zero to one axis where the two channel output states converge. " +
    "The executable win probability approaches the CHANCE 1/2 line as the dimension grows. " +
    "All values in this figure are analytic or a labelled ceiling; none is measured. Readings: " +
    readings +
    "."
  );
}

export function renderFingerprint(model) {
  const lock =
    '<g data-role="entanglement-lock" aria-hidden="true">' +
    '<circle cx="' + model.lock.cx + '" cy="' + model.lock.cy + '" r="' + model.lock.r +
    '" class="fp-lock" stroke-width="2"/>' +
    '<text x="' + model.lock.textX + '" y="' + model.lock.textY +
    '" class="fp-lock-label">' + model.lock.label + "</text>" +
    '<text x="' + model.lock.cx + '" y="' + (model.lock.cy - 26) + '" class="fp-lock-heading">' +
    model.lock.heading + "</text>" +
    "</g>";
  const body = model.rows
    .map(function (row) {
      return overlapRow(model, row) + traceRow(model, row) + successRow(model, row);
    })
    .join("");
  return (
    '<svg class="fingerprint" viewBox="0 0 ' + model.layout.width + " " + model.layout.height +
    '" preserveAspectRatio="xMidYMid meet" role="img" aria-label="' + ariaLabel(model) +
    '" data-role="fingerprint">' +
    lock +
    body +
    legend(model) +
    "</svg>"
  );
}

/* Text equivalent of the figure: one row per dimension, kind-tagged. */
export function textEquivalent(model) {
  return model.rows.map(function (row) {
    return {
      label: row.label,
      kind: row.overlapKind,
      text:
        "OVERLAP (SIGNED) " + full(row.overlap) + " " + row.overlapKind +
        ". TRACE DISTANCE " + full(row.traceDistance) + " " + row.traceKind +
        ". EXECUTABLE WIN PROBABILITY " + full(row.executable) + " " + row.executableKind +
        ". HELSTROM CEILING " + full(row.ceiling) + " " + row.ceilingKind +
        ". EMPIRICAL: not measured in this figure.",
    };
  });
}

/* Fill the figure host and the value ledger. Called once, from main.js. */
export function mountFingerprint(figureHost, valuesHost) {
  const model = figureModel();
  figureHost.innerHTML = renderFingerprint(model);
  valuesHost.innerHTML = textEquivalent(model)
    .map(function (row) {
      return (
        '<dt class="fp-ledger-key">' + row.label + "</dt>" +
        '<dd class="fp-ledger-value">' + row.text + "</dd>"
      );
    })
    .join("");
  return model;
}
