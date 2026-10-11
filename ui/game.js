/* Stage 1 (SURPRISE): reveal one independent one-query trial.
 *
 * A theoretical round is one hidden channel, one use, one outcome, one guess.
 * On Qollab the displayed round is sampled from the same batched independent
 * trials that power the benchmark, so the submission stays inside IonQ's
 * one-job-per-Run contract. It never presents a rate as if one shot measured it.
 */

export const PROBE_KINDS = {
  SEPARABLE: "SEPARABLE",
  MAX_ENTANGLEMENT: "MAX_ENTANGLEMENT",
};

const CHANNEL_NAMES = { A: "IDENTITY (A)", B: "V (B)" };

function channelName(channel) {
  return CHANNEL_NAMES[channel] || channel;
}

export function roundNarrative(result) {
  if (result && result.sampled_from_shared_batch) {
    const probe = result.probe_kind === PROBE_KINDS.SEPARABLE ? "separable" : "maximally entangled";
    return "This round used the " + probe + " probe: one independent one-query trial sampled from the shared batch. One outcome does not measure a rate.";
  }
  return "One round is one use of the hidden channel. It shows a single outcome. It does not measure a rate.";
}

export function roundLines(result) {
  var halves = result.outcome || [];
  return [
    "STRATEGY GUESSED " + channelName(result.guess),
    "ACTUAL CHANNEL " + channelName(result.hidden_channel),
    "MEASURED OUTCOME [" + halves.join(" | ") + "]",
    result.won ? "WIN" : "LOSE",
  ];
}

export function roundAnnouncement(result) {
  const sampling = result.sampled_from_shared_batch
    ? " This displayed result is one independent one-query trial sampled from the shared batch."
    : "";
  return (
    "Round over. You guessed " +
    channelName(result.guess) +
    ", the actual channel was " +
    channelName(result.hidden_channel) +
    ". " +
    (result.won ? "WIN" : "LOSE") +
    ". One outcome only, no rate shown." +
    sampling
  );
}

export function renderRound(result, nodes) {
  nodes.outcome.textContent = roundLines(result).join("\n");
  nodes.narrative.textContent = roundNarrative(result);
}
