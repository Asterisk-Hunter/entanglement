/* Unit-circle eigenvalue view with the convex hull of the flagship spectrum.
 *
 * One job: show that the flagship spectrum of W = V is {+1, -1, -1, ...}, that
 * its convex hull is the whole diameter of the unit circle, and that the
 * maximally entangled probe reaches the centroid while a separable probe can
 * in principle reach the hull's nearest point to the origin.
 *
 * Honesty rules, enforced here and pinned by tests/test_hull_view.py:
 * - the max-ent point is labelled ANALYTIC because it is reachable;
 * - the separable hull-nearest point is labelled ANALYTIC because the shipped
 *   flagship product-probe discriminator attains it.
 *
 * Geometry is computed by pure functions in this module; the DOM work is in
 * mountHullView. Data is a fixture table pinned against quantum.figures, so no
 * physics is computed here. Every number carries its kind as text.
 *
 * Motion budget: none. No path, polyline, or animation element is emitted; the
 * drag interaction repaints the same hairlines and circles. */

export const KIND = {
  analytic: "ANALYTIC",
  ceiling: "THEORETICAL CEILING",
};

export const TOKEN = {
  analytic: "ANALYTIC",
  ceiling: "THEORETICAL_CEILING",
};

/* Fixture table. Pinned against quantum.figures in tests/test_hull_view.py. */
export const HULL_FIXTURE = {
  dimension: 16,
  radius: 1.0,
  /* Unit-circle eigenvalues, one entry per distinct point, with multiplicity. */
  eigenvalues: [
    { re: 1, im: 0, angle: 0, multiplicity: 1 },
    { re: -1, im: 0, angle: 3.141592653589793, multiplicity: 15 },
  ],
  /* Angular-ordered convex hull vertices, straight from centroid_and_hull. */
  hullVertices: [
    { re: 1, im: 0 },
    { re: -1, im: 0 },
  ],
  centroid: { re: -0.875, im: 0 },
  maxEnt: {
    re: -0.875,
    im: 0,
    modulus: 0.875,
    kind: KIND.analytic,
    token: TOKEN.analytic,
    label: "MAX-ENT PROBE REACHABLE POINT",
    attainedByCircuit: true,
  },
  separableHullNearest: {
    re: 0,
    im: 0,
    modulus: 0,
    kind: TOKEN.analytic,
    token: TOKEN.analytic,
    label: "SEPARABLE HULL-NEAREST POINT, EXECUTABLE",
    attainedByCircuit: true,
    success: 1.0,
  },
  /* Dragging is constrained to the circle, so the only free parameter is the
   * angle of the selected eigenvalue. Both are exact in radians. */
  drag: {
    step: 0.05235987755982988, /* 3 degrees, the keyboard nudge */
    minAngle: -3.141592653589793,
    maxAngle: 3.141592653589793,
  },
};

export const LAYOUT = {
  width: 460,
  height: 460,
  radius: 170,
  cx: 230,
  cy: 230,
  handleRadius: 9,
  centroidRadius: 7,
  boundRadius: 11,
  legendY: 432,
};

/* Pointer nudge: clamp to the configured angle window. */
export function clampAngle(angle) {
  const drag = HULL_FIXTURE.drag;
  if (!Number.isFinite(angle)) return 0;
  if (angle < drag.minAngle) return drag.minAngle;
  if (angle > drag.maxAngle) return drag.maxAngle;
  return angle;
}

/* Keyboard alternative to dragging: the arrow keys move the selected
 * eigenvalue along the circle by one step. Left and right walk the angle, up
 * and down walk it the other way, so the control works in either orientation. */
export function angleFromKey(key, currentAngle) {
  const step = HULL_FIXTURE.drag.step;
  if (key === "ArrowRight") return clampAngle(currentAngle + step);
  if (key === "ArrowLeft") return clampAngle(currentAngle - step);
  if (key === "ArrowUp") return clampAngle(currentAngle + step);
  if (key === "ArrowDown") return clampAngle(currentAngle - step);
  return currentAngle;
}

/* Convert an eigenvalue's angle into screen coordinates. The eigenvalue is
 * always on the circle, so the modulus is fixed by construction. */
export function angleToPoint(angle, layout) {
  const size = layout || LAYOUT;
  return {
    x: round(size.cx + size.radius * Math.cos(angle)),
    y: round(size.cy - size.radius * Math.sin(angle)),
  };
}

/* Screen coordinates back to an angle, for the pointer path. The result is
 * snapped onto the circle: only the direction matters. */
export function pointToAngle(x, y, layout) {
  const size = layout || LAYOUT;
  const dx = x - size.cx;
  const dy = size.cy - y;
  if (dx === 0 && dy === 0) return 0;
  return clampAngle(Math.atan2(dy, dx));
}

/* Move one eigenvalue to a new angle, leaving the others in place. */
export function moveEigenvalue(eigenvalues, index, angle) {
  const next = eigenvalues.map(function (item, position) {
    if (position !== index) return item;
    const snapped = clampAngle(angle);
    return {
      re: Math.cos(snapped),
      im: Math.sin(snapped),
      angle: snapped,
      multiplicity: item.multiplicity,
    };
  });
  return next;
}

/* The centroid of the current eigenvalue set, recomputed as the eigenvalues
 * move. This mirrors the kernel's definition: the mean of the spectrum. */
export function centroidOf(eigenvalues) {
  let re = 0;
  let im = 0;
  let total = 0;
  eigenvalues.forEach(function (item) {
    re += item.re * item.multiplicity;
    im += item.im * item.multiplicity;
    total += item.multiplicity;
  });
  if (total === 0) return { re: 0, im: 0 };
  return { re: re / total, im: im / total };
}

/* Convex hull of the current points, by the gift-wrapping (Jarvis march)
 * algorithm. The hull is what the separable probe can reach, so the figure draws
 * exactly what this returns. Kept in the module so it can be tested without a
 * DOM; no third-party geometry library is used. */
export function convexHull(points) {
  const sorted = points
    .map(function (point) {
      return { x: point.re, y: point.im };
    })
    .sort(function (first, second) {
      if (first.x !== second.x) return first.x - second.x;
      return first.y - second.y;
    });
  const unique = [];
  sorted.forEach(function (point) {
    const previous = unique[unique.length - 1];
    if (
      !previous ||
      Math.abs(previous.x - point.x) > 1e-12 ||
      Math.abs(previous.y - point.y) > 1e-12
    ) {
      unique.push(point);
    }
  });
  if (unique.length < 3) {
    return unique.map(function (point) {
      return { re: point.x, im: point.y };
    });
  }
  /* Andrew's monotone chain. Bounded by the input size, so it terminates even
   * when the point set is collinear or contains interior points. */
  const cross = function (origin, first, second) {
    return (
      (first.x - origin.x) * (second.y - origin.y) -
      (first.y - origin.y) * (second.x - origin.x)
    );
  };
  const build = function (source) {
    const stack = [];
    source.forEach(function (point) {
      while (
        stack.length >= 2 &&
        cross(stack[stack.length - 2], stack[stack.length - 1], point) <= 0
      ) {
        stack.pop();
      }
      stack.push(point);
    });
    stack.pop();
    return stack;
  };
  const chain = build(unique).concat(build(unique.slice().reverse()));
  return angularOrder(
    chain.map(function (point) {
      return { re: point.x, im: point.y };
    })
  );
}

/* Sort hull vertices by increasing angle, the same order the kernel returns. */
export function angularOrder(vertices) {
  return vertices.slice().sort(function (first, second) {
    return angleOf(first) - angleOf(second);
  });
}

export function angleOf(vertex) {
  return Math.atan2(vertex.im, vertex.re);
}

function round(value) {
  return Math.round(value * 1000) / 1000;
}

function full(value) {
  return Number(value).toString();
}

/* The whole figure as data, so the renderer and the tests read the same model. */
export function hullModel(state) {
  const eigenvalues = (state && state.eigenvalues) || HULL_FIXTURE.eigenvalues;
  const selected = state && typeof state.selected === "number" ? state.selected : 0;
  const centroid = centroidOf(eigenvalues);
  const hull = convexHull(eigenvalues);
  const nearest = nearestPointToOrigin(hull);
  return {
    layout: LAYOUT,
    dimension: HULL_FIXTURE.dimension,
    radius: HULL_FIXTURE.radius,
    eigenvalues: eigenvalues.map(function (item, index) {
      const point = angleToPoint(item.angle, LAYOUT);
      return {
        index: index,
        re: item.re,
        im: item.im,
        angle: item.angle,
        multiplicity: item.multiplicity,
        cx: point.x,
        cy: point.y,
        selected: index === selected,
      };
    }),
    selected: selected,
    hull: hull.map(function (vertex) {
      return { re: vertex.re, im: vertex.im, ...angleToPoint(angleOf(vertex), LAYOUT) };
    }),
    centroid: {
      re: centroid.re,
      im: centroid.im,
      modulus: Math.hypot(centroid.re, centroid.im),
      cx: round(LAYOUT.cx + LAYOUT.radius * centroid.re),
      cy: round(LAYOUT.cy - LAYOUT.radius * centroid.im),
      kind: KIND.analytic,
      token: TOKEN.analytic,
      label: "MAX-ENT PROBE REACHABLE POINT",
      attainedByCircuit: true,
    },
    separableNearest: {
      re: nearest.re,
      im: nearest.im,
      modulus: nearest.modulus,
      cx: round(LAYOUT.cx + LAYOUT.radius * nearest.re),
      cy: round(LAYOUT.cy - LAYOUT.radius * nearest.im),
      kind: KIND.analytic,
      token: TOKEN.analytic,
      label: "SEPARABLE HULL-NEAREST POINT, EXECUTABLE",
      attainedByCircuit: true,
    },
  };
}

/* Nearest point of the hull to the origin, over vertices and edges alike. */
export function nearestPointToOrigin(hull) {
  let best = hull[0];
  let bestDistance = Math.hypot(best.re, best.im);
  hull.forEach(function (vertex) {
    const distance = Math.hypot(vertex.re, vertex.im);
    if (distance < bestDistance) {
      bestDistance = distance;
      best = vertex;
    }
  });
  for (let index = 0; index < hull.length; index += 1) {
    const start = hull[index];
    const end = hull[(index + 1) % hull.length];
    const point = closestOnSegment(start, end);
    const distance = Math.hypot(point.re, point.im);
    if (distance < bestDistance) {
      bestDistance = distance;
      best = point;
    }
  }
  return { re: best.re, im: best.im, modulus: bestDistance };
}

export function closestOnSegment(start, end) {
  const dx = end.re - start.re;
  const dy = end.im - start.im;
  const denominator = dx * dx + dy * dy;
  if (denominator === 0) return { re: start.re, im: start.im };
  let t = -(start.re * dx + start.im * dy) / denominator;
  if (t < 0) t = 0;
  if (t > 1) t = 1;
  return { re: start.re + t * dx, im: start.im + t * dy };
}

/* --- rendering ---------------------------------------------------------- */

function hullEdge(hull) {
  if (hull.length < 2) return "";
  return hull
    .map(function (vertex, index) {
      const next = hull[(index + 1) % hull.length];
      return (
        '<line data-role="hull-edge" x1="' + vertex.x + '" y1="' + vertex.y +
        '" x2="' + next.x + '" y2="' + next.y +
        '" class="hv-hull" stroke-width="1" aria-hidden="true"/>'
      );
    })
    .join("");
}

export function renderHull(model) {
  const circle =
    '<circle data-role="unit-circle" cx="' + model.layout.cx + '" cy="' + model.layout.cy +
    '" r="' + model.layout.radius + '" class="hv-circle" stroke-width="1" aria-hidden="true"/>';
  const handles = model.eigenvalues
    .map(function (item) {
      return (
        '<circle data-role="eigenvalue" data-index="' + item.index + '"' +
        (item.selected ? ' data-selected="true"' : "") +
        ' cx="' + item.cx + '" cy="' + item.cy + '" r="' + model.layout.handleRadius +
        '" class="hv-eigenvalue" stroke-width="1" aria-hidden="true"/>'
      );
    })
    .join("");
  const centroid =
    '<g data-role="centroid" data-kind="' + model.centroid.token + '">' +
    '<circle cx="' + model.centroid.cx + '" cy="' + model.centroid.cy +
    '" r="' + model.layout.centroidRadius + '" class="hv-centroid" stroke-width="1" aria-hidden="true"/>' +
    '<text x="' + model.centroid.cx + '" y="' + (model.centroid.cy - 16) +
    '" class="hv-value" text-anchor="middle" aria-hidden="true">' + full(model.centroid.modulus) + "</text>" +
    '<text x="' + model.centroid.cx + '" y="' + (model.centroid.cy - 30) +
    '" class="hv-kind" text-anchor="middle" aria-hidden="true">' + KIND.analytic + "</text>" +
    "</g>";
  const bound =
    '<g data-role="separable-bound" data-kind="' + model.separableNearest.token + '">' +
    '<circle cx="' + model.separableNearest.cx + '" cy="' + model.separableNearest.cy +
    '" r="' + model.layout.boundRadius + '" class="hv-bound" stroke-width="1" aria-hidden="true"/>' +
    '<text x="' + model.separableNearest.cx + '" y="' + (model.separableNearest.cy + 26) +
    '" class="hv-value" text-anchor="middle" aria-hidden="true">' + full(model.separableNearest.modulus) + "</text>" +
    '<text x="' + model.separableNearest.cx + '" y="' + (model.separableNearest.cy + 40) +
    '" class="hv-kind" text-anchor="middle" aria-hidden="true">' + KIND.analytic + "</text>" +
    "</g>";
  return (
    '<svg class="hullview" viewBox="0 0 ' + model.layout.width + " " + model.layout.height +
    '" preserveAspectRatio="xMidYMid meet" role="img" aria-label="' + hullAriaLabel(model) +
    '" data-role="hull-view">' +
    circle +
    hullEdge(model.hull) +
    handles +
    centroid +
    bound +
    "</svg>"
  );
}

function hullAriaLabel(model) {
  return (
    "Unit-circle eigenvalue view for the identity-versus-V pair at dimension " +
    model.dimension +
    ". The spectrum has one eigenvalue at angle zero and " +
    (model.dimension - 1) + " at angle pi, so its convex hull is the whole diameter. " +
    "The centroid sits at " + full(model.centroid.modulus) + " and is the maximally entangled " +
    "probe's reachable point, labelled " + KIND.analytic + ". " +
    "The separable hull-nearest point sits at " + full(model.separableNearest.modulus) +
    " and is labelled " + KIND.analytic + ". The flagship separable probe and readout attain this point. " +
    "Drag an eigenvalue or use the arrow keys to move it around the circle."
  );
}

export function hullTextEquivalent(model) {
  return model.eigenvalues.map(function (item) {
    return {
      label: "EIGENVALUE " + item.index,
      text:
        "ANGLE " + full(item.angle) +
        " MULTIPLICITY " + full(item.multiplicity) +
        " " + KIND.analytic,
    };
  }).concat([
    {
      label: "HULL VERTICES",
      text:
        "CONVEX HULL " + full(model.hull.length) + " VERTICES, " +
        "THE SEPARABLE PROBE'S REACHABLE SET, " + KIND.analytic,
    },
    {
      label: "CENTROID",
      text:
        "MAX-ENT REACHABLE POINT " + full(model.centroid.modulus) + " " + KIND.analytic,
    },
    {
      label: "SEPARABLE NEAREST",
      text:
        "HULL-NEAREST POINT " + full(model.separableNearest.modulus) + " " + KIND.analytic +
        ", ATTAINED BY THE FLAGSHIP SEPARABLE STRATEGY",
    },
  ]);
}

/* --- DOM wiring --------------------------------------------------------- */

/* Mount the figure and wire the two interaction paths. Pointer events handle
 * the drag; the arrow keys on the same control handle keyboard use. Both update
 * the same state, so the figure behaves identically either way. */
export function mountHullView(host, valuesHost, initialState) {
  let state = initialState || { eigenvalues: HULL_FIXTURE.eigenvalues, selected: 0 };

  function repaint() {
    const model = hullModel(state);
    host.innerHTML = renderHull(model);
    valuesHost.innerHTML = hullTextEquivalent(model)
      .map(function (row) {
        return (
          '<dt class="hv-ledger-key">' + row.label + "</dt>" +
          '<dd class="hv-ledger-value">' + row.text + "</dd>"
        );
      })
      .join("");
    return model;
  }

  const model = repaint();

  function angleFromEvent(event) {
    const bounds = host.querySelector("svg").getBoundingClientRect();
    const scaleX = LAYOUT.width / (bounds.width || LAYOUT.width);
    const scaleY = LAYOUT.height / (bounds.height || LAYOUT.height);
    return pointToAngle(
      (event.clientX - bounds.left) * scaleX,
      (event.clientY - bounds.top) * scaleY,
      LAYOUT
    );
  }

  function beginDrag(event) {
    const target = event.target;
    if (!target.hasAttribute("data-index")) return;
    const index = Number(target.getAttribute("data-index"));
    if (!Number.isInteger(index) || !state.eigenvalues[index]) return;
    state = { eigenvalues: state.eigenvalues, selected: index };
    event.preventDefault();
    host.setPointerCapture(event.pointerId);

    function onMove(moveEvent) {
      const angle = angleFromEvent(moveEvent);
      state = {
        eigenvalues: moveEigenvalue(state.eigenvalues, state.selected, angle),
        selected: state.selected,
      };
      repaint();
    }

    function onEnd() {
      if (host.hasPointerCapture(event.pointerId)) host.releasePointerCapture(event.pointerId);
      host.removeEventListener("pointermove", onMove);
      host.removeEventListener("pointerup", onEnd);
      host.removeEventListener("pointercancel", onEnd);
      repaint();
    }

    host.addEventListener("pointermove", onMove);
    host.addEventListener("pointerup", onEnd);
    host.addEventListener("pointercancel", onEnd);
    repaint();
  }

  host.addEventListener("pointerdown", beginDrag);
  host.addEventListener("keydown", function (event) {
    const current = state.eigenvalues[state.selected];
    const next = angleFromKey(event.key, current.angle);
    if (next === current.angle) return;
    event.preventDefault();
    state = {
      eigenvalues: moveEigenvalue(state.eigenvalues, state.selected, next),
      selected: state.selected,
    };
    repaint();
  });

  return model;
}
