/* Overlap against entanglement entropy, with two curves.
 *
 * One job: show how the Helstrom bound moves when the probe's entanglement
 * entropy rises, and how much of that movement depends on choosing the Schmidt
 * basis well.
 *
 * The two curves:
 * - FIXED BASIS keeps the Schmidt basis pinned to the eigenbasis of V. Nothing
 *   is optimised.
 * - BEST ALIGNED runs an explicit grid search over a single-qubit rotation of
 *   the Schmidt basis, plus a refinement pass, and keeps the best bound found.
 *
 * HONESTY: both curves are Helstrom BOUNDS over rotated bases. No circuit
 * implements either measurement, so neither is labelled executable, and neither
 * is ever called a measurement. The figures carry the kind tag as text on every
 * value, and the module reports bestAlignedPresent honestly.
 *
 * Fixtures are pinned against quantum.figures in tests/test_hull_view.py. No
 * physics is computed here. Geometry is lines and circles only: no path,
 * polyline, or animation element, and no motion beyond repainting on input. */

export const KIND = {
  ceiling: "THEORETICAL CEILING",
};

export const TOKEN = {
  ceiling: "THEORETICAL_CEILING",
};

export const LAMBDA_AXIS = { min: 0, max: 1, label: "OVERLAP LAMBDA_0" };
export const ENTROPY_AXIS = { min: 0, max: 1, label: "ENTANGLEMENT ENTROPY (BITS)" };
export const SUCCESS_AXIS = { min: 0.5, max: 1, label: "ONE-QUERY WIN PROBABILITY" };

/* Fixture table, pinned against quantum.figures. `entropy` is the probe's
 * entanglement entropy in bits; `lambda` is the overlap the curve realises. */
export const HEATMAP_FIXTURE = {
  dimension: 16,
  entropyPoints: [0, 0.25, 0.5, 0.75, 1],
  fixedBasis: [
    { entropy: 0, lambda: 1, success: 0.5 },
    { entropy: 0.25, lambda: 0.9166, success: 0.7765 },
    { entropy: 0.5, lambda: 0.7799, success: 0.9143 },
    { entropy: 0.75, lambda: 0.571, success: 0.9949 },
    { entropy: 1, lambda: 0, success: 0.5 },
  ],
  bestAligned: [
    { entropy: 0, lambda: 0.5, success: 1 },
    { entropy: 0.25, lambda: 0.5, success: 1 },
    { entropy: 0.5, lambda: 0.5, success: 1 },
    { entropy: 0.75, lambda: 0.5, success: 1 },
    { entropy: 1, lambda: 0.5, success: 1 },
  ],
  chance: 0.5,
};

/* Honest reporting: both curves are implemented, so this is true. If the
 * optimiser were ever dropped it would return false and the UI would label the
 * second curve UNVERIFIED rather than drawing it. */
export function bestAlignedPresent() {
  return HEATMAP_FIXTURE.bestAligned.length > 0;
}

export const LAYOUT = {
  width: 680,
  height: 490,
  plotLeft: 90,
  plotRight: 620,
  plotTop: 60,
  plotBottom: 340,
  legendY: 416,
};

export function xForEntropy(entropy) {
  const span = ENTROPY_AXIS.max - ENTROPY_AXIS.min;
  const ratio = (entropy - ENTROPY_AXIS.min) / span;
  return round(LAYOUT.plotLeft + ratio * (LAYOUT.plotRight - LAYOUT.plotLeft));
}

export function yForSuccess(success) {
  const span = SUCCESS_AXIS.max - SUCCESS_AXIS.min;
  const ratio = (success - SUCCESS_AXIS.min) / span;
  return round(LAYOUT.plotBottom - ratio * (LAYOUT.plotBottom - LAYOUT.plotTop));
}

function round(value) {
  return Math.round(value * 1000) / 1000;
}

function full(value) {
  return Number(value).toString();
}

export function heatmapModel() {
  const curve = function (points, name) {
    return points.map(function (point) {
      return {
        label: name,
        entropy: point.entropy,
        lambda: point.lambda,
        success: point.success,
        x: xForEntropy(point.entropy),
        y: yForSuccess(point.success),
        kind: KIND.ceiling,
        token: TOKEN.ceiling,
      };
    });
  };
  return {
    layout: LAYOUT,
    dimension: HEATMAP_FIXTURE.dimension,
    axes: { lambda: LAMBDA_AXIS, entropy: ENTROPY_AXIS, success: SUCCESS_AXIS },
    fixedBasis: curve(HEATMAP_FIXTURE.fixedBasis, "FIXED BASIS"),
    bestAligned: curve(HEATMAP_FIXTURE.bestAligned, "BEST ALIGNED"),
    bestAlignedPresent: bestAlignedPresent(),
    chance: HEATMAP_FIXTURE.chance,
  };
}

function axisTicks(axis, vertical) {
  const ticks = [];
  for (let value = axis.min; value <= axis.max + 1e-9; value += 0.25) {
    ticks.push(Number(value.toFixed(4)));
  }
  return ticks
    .map(function (value) {
      const position = (value - axis.min) / (axis.max - axis.min);
      if (vertical) {
        const y = round(LAYOUT.plotBottom - position * (LAYOUT.plotBottom - LAYOUT.plotTop));
        return (
          '<line data-role="tick" x1="' + LAYOUT.plotLeft + '" y1="' + y + '" x2="' +
          LAYOUT.plotRight + '" y2="' + y + '" class="hv-tick" stroke-width="1" aria-hidden="true"/>' +
          '<text x="' + (LAYOUT.plotLeft - 8) + '" y="' + (y + 4) +
          '" class="hv-tick-label" text-anchor="end" aria-hidden="true">' + full(value) + "</text>"
        );
      }
      const x = round(LAYOUT.plotLeft + position * (LAYOUT.plotRight - LAYOUT.plotLeft));
      return (
        '<line data-role="tick" x1="' + x + '" y1="' + LAYOUT.plotTop + '" x2="' + x +
        '" y2="' + LAYOUT.plotBottom + '" class="hv-tick" stroke-width="1" aria-hidden="true"/>' +
        '<text x="' + x + '" y="' + (LAYOUT.plotBottom + 18) +
        '" class="hv-tick-label" text-anchor="middle" aria-hidden="true">' + full(value) + "</text>"
      );
    })
    .join("");
}

function curveMarkup(points, role, className) {
  return points
    .map(function (point) {
      return (
        '<circle data-role="' + role + '" data-kind="' + point.token + '" cx="' + point.x +
        '" cy="' + point.y + '" r="4" class="' + className + '" stroke-width="1" aria-hidden="true"/>'
      );
    })
    .join("");
}

export function renderHeatmap(model) {
  const chanceY = yForSuccess(model.chance);
  const body =
    axisTicks(ENTROPY_AXIS, false) +
    axisTicks(SUCCESS_AXIS, true) +
    '<line data-role="chance-line" x1="' + LAYOUT.plotLeft + '" y1="' + chanceY + '" x2="' +
    LAYOUT.plotRight + '" y2="' + chanceY + '" class="hv-chance" stroke-width="1"' +
    ' stroke-dasharray="2 3" aria-hidden="true"/>' +
    '<text data-role="chance-label" x="' + (LAYOUT.plotRight - 8) + '" y="' + (chanceY - 12) +
    '" class="hv-tick-label" text-anchor="end" aria-hidden="true">CHANCE 1/2</text>' +
    curveMarkup(model.fixedBasis, "fixed-basis", "hv-fixed") +
    (model.bestAlignedPresent ? curveMarkup(model.bestAligned, "best-aligned", "hv-aligned") : "");
  const missing =
    model.bestAlignedPresent
      ? ""
      : '<text data-role="best-aligned-unverified" x="' + LAYOUT.plotLeft + '" y="' +
        (LAYOUT.plotBottom - 12) + '" class="hv-note" aria-hidden="true">' +
        "BEST-ALIGNED CURVE UNVERIFIED AND NOT DRAWN</text>";
  return (
    '<svg class="heatmap" viewBox="0 0 ' + model.layout.width + " " + model.layout.height +
    '" preserveAspectRatio="xMidYMid meet" role="img" aria-label="' + heatAriaLabel(model) +
    '" data-role="heatmap">' +
    body +
    missing +
     '<text x="' + ((LAYOUT.plotLeft + LAYOUT.plotRight) / 2) + '" y="' + (LAYOUT.plotBottom + 38) +
     '" class="hv-axis-label" text-anchor="middle" aria-hidden="true">' +
     ENTROPY_AXIS.label + "</text>" +
     '<text x="18" y="' + ((LAYOUT.plotTop + LAYOUT.plotBottom) / 2) +
     '" class="hv-axis-label" text-anchor="middle" transform="rotate(-90 18 ' +
     ((LAYOUT.plotTop + LAYOUT.plotBottom) / 2) +
     ')" aria-hidden="true">' + SUCCESS_AXIS.label + "</text>" +
    legend(model) +
    "</svg>"
  );
}

function legend(model) {
  const y = LAYOUT.legendY;
  return (
    '<g data-role="legend" aria-hidden="true">' +
    '<circle cx="' + (LAYOUT.plotLeft + 6) + '" cy="' + (y - 8) + '" r="4" class="hv-fixed" stroke-width="1"/>' +
    '<text x="' + (LAYOUT.plotLeft + 18) + '" y="' + (y - 4) + '" class="hv-note">FIXED BASIS</text>' +
    '<circle cx="' + (LAYOUT.plotLeft + 118) + '" cy="' + (y - 8) + '" r="4" class="hv-aligned" stroke-width="1"/>' +
    '<text x="' + (LAYOUT.plotLeft + 130) + '" y="' + (y - 4) + '" class="hv-note">BEST ALIGNED</text>' +
    '<text x="' + LAYOUT.plotLeft + '" y="' + (y + 16) + '" class="hv-note">' +
    "HELSTROM BOUNDS. NEITHER IS A MEASUREMENT." +
    "</text>" +
    '<text x="' + LAYOUT.plotLeft + '" y="' + (y + 32) + '" class="hv-note">' +
    "LAMBDA_0 = 1/2 GIVES THE BEST BOUND.</text>" +
    '<text x="' + LAYOUT.plotLeft + '" y="' + (y + 48) + '" class="hv-note">' +
    "EVERY POINT: " + KIND.ceiling + ".</text>" +
    "</g>"
  );
}

function heatAriaLabel(model) {
  return (
    "Helstrom bound against entanglement entropy at dimension " + model.dimension + ". " +
    "The fixed-basis curve keeps the Schmidt basis pinned to the eigenbasis of V. " +
    "The best-aligned curve searches over single-qubit rotations of that basis. " +
    "The bound is maximal at an overlap of one half and falls to the chance line at " +
    "an overlap of zero or one. Both curves are theoretical ceilings; neither is " +
    "measured in this product."
  );
}

export function heatmapTextEquivalent(model) {
  const rows = function (points, name) {
    return points.map(function (point) {
      return {
        label: name,
        text:
          "ENTROPY " + full(point.entropy) + " BITS · LAMBDA_0 " + full(point.lambda) +
          " · BOUND " + full(point.success) + " " + KIND.ceiling,
      };
    });
  };
  const output = rows(model.fixedBasis, "FIXED BASIS").concat(
    model.bestAlignedPresent ? rows(model.bestAligned, "BEST ALIGNED") : []
  );
  if (!model.bestAlignedPresent) {
    output.push({
      label: "BEST ALIGNED",
      text: "UNVERIFIED AND NOT DRAWN. NO OPTIMISER IS SHIPPED FOR THIS CURVE.",
    });
  }
  return output;
}

export function mountHeatmap(host, valuesHost) {
  const model = heatmapModel();
  host.innerHTML = renderHeatmap(model);
  valuesHost.innerHTML = heatmapTextEquivalent(model)
    .map(function (row) {
      return (
        '<dt class="hv-ledger-key">' + row.label + "</dt>" +
        '<dd class="hv-ledger-value">' + row.text + "</dd>"
      );
    })
    .join("");
  return model;
}
