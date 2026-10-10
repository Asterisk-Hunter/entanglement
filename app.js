const aliceAngle = document.querySelector("#alice-angle");
const bobAngle = document.querySelector("#bob-angle");
const $ = (selector) => document.querySelector(selector);
const rad = (degrees) => Number(degrees) * Math.PI / 180;
const correlation = (a, b) => -Math.cos(rad(a - b));

function paintPair() {
  const a = Number(aliceAngle.value);
  const b = Number(bobAngle.value);
  const delta = Math.abs(a - b);
  const expected = correlation(a, b);
  const same = (1 + expected) / 2;
  const opposite = 1 - same;

  $("#alice-value").value = `${a}°`;
  $("#bob-value").value = `${b}°`;
  $("#delta-value").textContent = `${delta}°`;
  $("#correlation-value").textContent = `${expected < 0 ? "−" : ""}${Math.abs(expected).toFixed(3)}`;
  $("#same-prob").textContent = `${(same * 100).toFixed(1)}%`;
  $("#opposite-prob").textContent = `${(opposite * 100).toFixed(1)}%`;
  $("#same-bar").style.width = `${same * 100}%`;
  $("#opposite-bar").style.width = `${opposite * 100}%`;
}

function samplePair(a, b) {
  const alice = Math.random() < 0.5 ? 1 : -1;
  const expected = correlation(a, b);
  const bob = Math.random() < (1 + alice * expected) / 2 ? 1 : -1;
  return [alice, bob];
}

function estimateCorrelation(a, b, shots) {
  let products = 0;
  for (let i = 0; i < shots; i += 1) {
    const [alice, bob] = samplePair(a, b);
    products += alice * bob;
  }
  return products / shots;
}

function runBellTest() {
  const angle = (selector) => Number($(selector).value);
  const shots = Number($("#shots").value);
  const e00 = estimateCorrelation(angle("#a0"), angle("#b0"), shots);
  const e01 = estimateCorrelation(angle("#a0"), angle("#b1"), shots);
  const e10 = estimateCorrelation(angle("#a1"), angle("#b0"), shots);
  const e11 = estimateCorrelation(angle("#a1"), angle("#b1"), shots);
  const s = Math.abs(e00 + e01 + e10 - e11);
  const position = Math.min(1, Math.max(0, s / 3));

  [["#e00", e00], ["#e01", e01], ["#e10", e10], ["#e11", e11]].forEach(([selector, value]) => {
    $(selector).textContent = `${value < 0 ? "−" : ""}${Math.abs(value).toFixed(3)}`;
  });
  $("#s-value").textContent = s.toFixed(3);
  $("#s-verdict").textContent = s > 2 ? "This sample exceeds the classical bound" : "This sample stays within the classical bound";
  $("#score-fill").style.width = `${position * 100}%`;
  $("#score-marker").style.left = `${position * 100}%`;
  $("#chsh-result").setAttribute("aria-label", `Estimated CHSH value ${s.toFixed(3)} from ${shots} pairs per setting`);
}

function runOnePair() {
  const [alice, bob] = samplePair(Number(aliceAngle.value), Number(bobAngle.value));
  $("#alice-result").textContent = `A · ${alice > 0 ? "+1" : "−1"}`;
  $("#bob-result").textContent = `B · ${bob > 0 ? "+1" : "−1"}`;
  $("#single-result").hidden = false;
}

aliceAngle.addEventListener("input", paintPair);
bobAngle.addEventListener("input", paintPair);
$("#measure-one").addEventListener("click", runOnePair);
$("#reset-angles").addEventListener("click", () => {
  aliceAngle.value = "0";
  bobAngle.value = "45";
  $("#single-result").hidden = true;
  paintPair();
});
$("#shots").addEventListener("input", () => {
  $("#shots-value").value = Number($("#shots").value).toLocaleString();
});
$("#run-chsh").addEventListener("click", runBellTest);
document.querySelectorAll(".setting-values input").forEach((input) => {
  input.addEventListener("change", () => {
    const value = Number(input.value);
    input.value = String(Math.min(Number(input.max), Math.max(Number(input.min), Number.isFinite(value) ? value : 0)));
  });
});
paintPair();
