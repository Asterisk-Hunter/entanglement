/* Expert evidence drawer for the selected generic ChannelPair.
 *
 * The inspector never submits a backend job. It renders the registry payload
 * and, only for the pair that actually ran, the cached hero execution metadata.
 */

import { KIND_LABELS, escapeHtml, kindLabel } from "./gallery.js";

const NOT_PUBLISHED = "NOT PUBLISHED";
const NOT_RUN = "NOT RUN";
const NOT_REPORTED = "NOT REPORTED";

function row(label, value, kindToken) {
  return {
    label: label,
    value: String(value),
    kindLabel: KIND_LABELS[kindToken] || String(kindToken),
  };
}

function theoryRow(label, value, kindToken) {
  return typeof value === "number"
    ? row(label, value, kindToken)
    : row(label, NOT_PUBLISHED, "NOT PUBLISHED");
}

function traceDistance(overlap) {
  if (typeof overlap !== "number") return null;
  return Math.sqrt(Math.max(0, 1 - overlap * overlap));
}

function runRows(pair, run) {
  if (!run || run.pair_slug !== pair.slug) {
    return [
      row("BACKEND", NOT_RUN, "NOT RUN"),
      row("SOURCE", NOT_RUN, "NOT RUN"),
      row("SHOTS / CHANNEL", NOT_RUN, "NOT RUN"),
      row("BACKEND JOBS", NOT_RUN, "NOT RUN"),
      row("ROUND SELECTION SEED", NOT_REPORTED, "NOT REPORTED"),
    ];
  }
  return [
    row("BACKEND", run.backend || NOT_REPORTED, "RUN METADATA"),
    row("SOURCE", run.source_label || NOT_REPORTED, "RUN METADATA"),
    row("SHOTS / CHANNEL", run.shots_per_channel ?? NOT_REPORTED, "EMPIRICAL"),
    row("BACKEND JOBS", run.total_backend_jobs ?? NOT_REPORTED, "RUN METADATA"),
    row("ROUND SELECTION SEED", run.round_selection_seed ?? NOT_REPORTED, "RUN METADATA"),
  ];
}

function circuitModel(pair) {
  const circuit = pair.circuit || {};
  return {
    totalQubits: circuit.total_qubits ?? NOT_REPORTED,
    systemQubits: circuit.system_qubits ?? NOT_REPORTED,
    channels: (circuit.channels || []).map(function (channel) {
      const available = channel.status === "AVAILABLE";
      return {
        channel: channel.channel,
        name: channel.name || channel.channel,
        status: channel.status || NOT_REPORTED,
        phase: channel.global_phase || NOT_REPORTED,
        text: available && Array.isArray(channel.instructions) && channel.instructions.length
          ? channel.instructions.join("\n")
          : available
            ? "NO INSTRUCTIONS. IDENTITY CHANNEL."
            : channel.limitation || "CIRCUIT NOT AVAILABLE IN THIS RUNTIME.",
      };
    }),
  };
}

export function expertModel(pair, run) {
  const bounds = pair.bounds || {};
  const rows = [
    theoryRow("OUTPUT STATE OVERLAP", bounds.overlap, "ANALYTIC"),
    theoryRow("TRACE DISTANCE", traceDistance(bounds.overlap), "ANALYTIC"),
  ];
  for (const strategy of pair.strategies || []) {
    rows.push(
      theoryRow(
        "STRATEGY · " + strategy.label,
        strategy.analytic_value,
        strategy.bound_kind
      )
    );
  }
  if (typeof bounds.helstrom_ceiling === "number") {
    rows.push(theoryRow("HELSTROM CEILING", bounds.helstrom_ceiling, "THEORETICAL_CEILING"));
  }
  return {
    pair: pair,
    rows: rows.concat(runRows(pair, run)),
    circuit: circuitModel(pair),
  };
}

function renderRows(rows) {
  return rows.map(function (item) {
    return (
      "<div class=\"expert-row\"><dt>" + escapeHtml(item.label) + "</dt>" +
      "<dd><span class=\"kind-tag\">" + escapeHtml(item.kindLabel) + "</span>" +
      "<span class=\"expert-value\">" + escapeHtml(item.value) + "</span></dd></div>"
    );
  }).join("");
}

function renderCircuits(circuit) {
  if (!circuit.channels.length) {
    return "<p class=\"expert-meta\">CIRCUIT DISCLOSURE: " + NOT_REPORTED + "</p>";
  }
  return circuit.channels.map(function (channel) {
    return (
      "<div class=\"expert-circuit\"><p class=\"label\">CHANNEL " + escapeHtml(channel.channel) +
      " · " + escapeHtml(channel.name) + " · " + escapeHtml(channel.status) + " · GLOBAL PHASE " + escapeHtml(channel.phase) +
      "</p><pre class=\"expert-gates\" tabindex=\"0\">" + escapeHtml(channel.text) + "</pre></div>"
    );
  }).join("");
}

export function renderExpert(model) {
  const pair = model.pair;
  return (
    "<div class=\"expert-body\">" +
    "<h3 class=\"expert-name\">" + escapeHtml(pair.name) + "</h3>" +
    "<p class=\"expert-meta\">EXPERIMENT " + escapeHtml(pair.slug) + " · d = " + escapeHtml(pair.dimension) +
    " · SYSTEM REGISTER " + escapeHtml(model.circuit.systemQubits) + " · PADDED WIDTH " + escapeHtml(model.circuit.totalQubits) + "</p>" +
    renderCircuits(model.circuit) +
    "<dl class=\"expert-rows\">" + renderRows(model.rows) + "</dl>" +
    "<p class=\"label\">SOURCE</p><p class=\"expert-source\">" + escapeHtml(pair.citation) + "</p>" +
    "<p class=\"expert-meta\">EMPIRICAL values come only from the cached live flagship run. ANALYTIC and THEORETICAL CEILING values are theory. A ceiling is not presented as an executed measurement.</p>" +
    "</div>"
  );
}

let mounted = null;

export function mountExpert(nodes, initialPair) {
  let pair = initialPair || null;
  let run = null;
  let model = pair ? expertModel(pair, run) : null;

  function render() {
    nodes.drawer.innerHTML = model
      ? renderExpert(model)
      : "<p class=\"expert-meta\">RESOURCE METADATA HAS NOT LOADED.</p>";
  }

  function setOpen(open) {
    nodes.drawer.hidden = !open;
    nodes.toggle.setAttribute("aria-expanded", open ? "true" : "false");
    nodes.announcer.textContent = open
      ? "EXPERT EVIDENCE OPEN" + (model ? ". " + model.pair.name + "." : ".")
      : "EXPERT EVIDENCE CLOSED.";
    if (open) nodes.drawer.focus();
  }

  nodes.toggle.addEventListener("click", function () {
    setOpen(nodes.toggle.getAttribute("aria-expanded") !== "true");
  });
  nodes.drawer.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      setOpen(false);
      nodes.toggle.focus();
    }
  });

  mounted = {
    update: function (nextPair, nextRun) {
      if (nextPair) pair = nextPair;
      if (nextRun !== undefined) run = nextRun;
      model = pair ? expertModel(pair, run) : null;
      render();
      return model;
    },
    open: function () {
      setOpen(true);
    },
  };
  render();
  return mounted;
}

export function update(pair, run) {
  return mounted ? mounted.update(pair, run) : null;
}
