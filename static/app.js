const $ = (id) => document.getElementById(id);
let data = null,
  timer = null;
const pct = (x) => (100 * x).toFixed(1) + "%";
const colors = {
  gold: "#006a60",
  mint: "#456179",
  muted: "#3f4946",
  line: "#d4dfdb",
};
function context(id) {
  const c = $(id),
    g = c.getContext("2d");
  g.clearRect(0, 0, c.width, c.height);
  g.font = "18px system-ui";
  return [g, c.width, c.height];
}
function line(g, x1, y1, x2, y2, color, width = 2) {
  g.strokeStyle = color;
  g.lineWidth = width;
  g.beginPath();
  g.moveTo(x1, y1);
  g.lineTo(x2, y2);
  g.stroke();
}
function plot(
  id,
  series,
  {
    xLabel = "",
    yLabel = "",
    xMin = 0,
    xMax = 1,
    yMin = 0,
    yMax = 1,
    diagonal = false,
    threshold = null,
  } = {},
) {
  const [g, w, h] = context(id),
    l = 65,
    r = 25,
    t = 25,
    b = 50;
  const x = (v) => l + ((v - xMin) / (xMax - xMin)) * (w - l - r),
    y = (v) => h - b - ((v - yMin) / (yMax - yMin)) * (h - t - b);
  g.fillStyle = colors.muted;
  g.font = "16px system-ui";
  for (let i = 0; i <= 4; i++) {
    const v = yMin + ((yMax - yMin) * i) / 4;
    line(g, l, y(v), w - r, y(v), colors.line, 1);
    g.fillText(Math.round(v * 100) + "%", 8, y(v) + 5);
  }
  for (let i = 0; i <= 4; i++) {
    const v = xMin + ((xMax - xMin) * i) / 4;
    g.fillText(Math.round(v * 100) + "%", x(v) - 15, h - 27);
  }
  g.fillText(xLabel, l, h - 3);
  g.fillText(yLabel, l, 17);
  if (diagonal) {
    g.setLineDash([6, 6]);
    line(g, x(0), y(0), x(1), y(1), colors.muted);
    g.setLineDash([]);
  }
  if (threshold !== null) {
    g.setLineDash([6, 6]);
    line(g, l, y(threshold), w - r, y(threshold), colors.muted);
    g.setLineDash([]);
  }
  for (const s of series) {
    g.strokeStyle = s.color;
    g.lineWidth = 3;
    g.beginPath();
    s.points.forEach((p, i) =>
      i ? g.lineTo(x(p[0]), y(p[1])) : g.moveTo(x(p[0]), y(p[1])),
    );
    g.stroke();
    s.points.forEach((p) => {
      g.fillStyle = s.color;
      g.beginPath();
      g.arc(x(p[0]), y(p[1]), 4, 0, Math.PI * 2);
      g.fill();
    });
  }
}
function current(method) {
  return data.methods[method].rows.find((r) => r.id === $("case").value);
}
function renderCase() {
  if (!data) return;
  const c = data.cases.find((c) => c.id === $("case").value),
    draw = +$("draw").value;
  $("drawLabel").textContent = draw + 1;
  $("caseTruth").textContent =
    "Simulated label: ER " + (c.label ? "positive" : "negative");
  for (const method of ["random", "spatial"]) {
    const row = current(method),
      [g, w, h] = context(method + "Map"),
      selected = new Set(row.samples[draw]);
    const dx = w / 24,
      dy = h / 16;
    for (let i = 0; i < c.signal.length; i++) {
      const value = (c.signal[i] + 1) / 2;
      g.fillStyle = `rgb(${Math.round(82 + 133 * value)},${Math.round(57 + 83 * value)},${Math.round(133 + 37 * value)})`;
      g.fillRect((i % 24) * dx, Math.floor(i / 24) * dy, dx - 2, dy - 2);
      if (selected.has(i)) {
        g.strokeStyle = "#ffffff";
        g.lineWidth = 2.5;
        g.strokeRect(
          (i % 24) * dx + 2,
          Math.floor(i / 24) * dy + 2,
          dx - 6,
          dy - 6,
        );
      }
    }
    $("" + method + "Stats").innerHTML =
      `<div><span>This sample</span><strong>${pct(row.probabilities[draw])}</strong></div><div><span>Average ER probability</span><strong>${pct(row.mean)}</strong></div><div><span>Sampling variance</span><strong>${row.variance.toFixed(4)}</strong></div>`;
    const [t, tw, th] = context(method + "Trace"),
      left = 45,
      top = 10,
      bot = th - 28;
    const yy = (p) => bot - p * (bot - top);
    t.fillStyle = colors.muted;
    t.font = "13px system-ui";
    t.fillText("100%", 0, top + 10);
    t.fillText("0%", 12, bot);
    t.setLineDash([4, 5]);
    line(
      t,
      left,
      yy(data.threshold),
      tw - 10,
      yy(data.threshold),
      colors.muted,
      1,
    );
    t.setLineDash([]);
    row.probabilities.forEach((p, i) => {
      const x = left + (i * (tw - left - 20)) / (data.repeats - 1);
      if (i)
        line(
          t,
          left + ((i - 1) * (tw - left - 20)) / (data.repeats - 1),
          yy(row.probabilities[i - 1]),
          x,
          yy(p),
          method === "random" ? colors.gold : colors.mint,
        );
      t.fillStyle = i === draw ? "#006a60" : colors.muted;
      t.beginPath();
      t.arc(x, yy(p), i === draw ? 6 : 3, 0, 7);
      t.fill();
    });
    t.fillStyle = colors.muted;
    t.fillText("Sample 1", left, th - 3);
    t.fillText("Sample " + data.repeats, tw - 80, th - 3);
  }
}
function renderReview() {
  if (!data) return;
  const method = $("method").value,
    rate = +$("rate").value,
    m = data.methods[method],
    rules = {};
  for (const kind of ["confidence", "disagreement"])
    rules[kind] = m.curves[kind].find((r) => r.rate === rate);
  $("reviewCards").innerHTML = ["confidence", "disagreement"]
    .map((kind) => {
      const r = rules[kind],
        flag = new Set(r.flagged);
      return `<article class="card"><h3>${kind === "confidence" ? "Low confidence" : "High disagreement"}</h3><div class="review-number ${kind === "disagreement" ? "mint" : ""}">${pct(r.error_rate)} <small style="font-size:14px;color:var(--muted)">retained-case error</small></div><p>${r.flagged.length} flagged · ${r.retained} retained · ${r.errors} errors among retained cases</p><div class="dots">${m.rows.map((row) => `<span title="${row.id}${flag.has(row.id) ? ": flagged for review" : row.mean >= data.threshold !== Boolean(row.label) ? ": incorrect prediction" : ": correct prediction"}" class="dot ${flag.has(row.id) ? "flagged" : row.mean >= data.threshold !== Boolean(row.label) ? "error" : ""}"></span>`).join("")}</div><p class="caption">Each square is one test case. Red = incorrect. Outlined = flagged.</p></article>`;
    })
    .join("");
  plot(
    "risk",
    ["confidence", "disagreement"].map((kind) => ({
      color: kind === "confidence" ? colors.gold : colors.mint,
      points: m.curves[kind]
        .map((r) => [r.retained / 80, r.error_rate])
        .reverse(),
    })),
    {
      xLabel: "Fraction retained for classification",
      yLabel: "Error rate",
      xMin: 0.6,
      xMax: 1,
      yMax: Math.max(
        0.25,
        ...Object.values(m.curves)
          .flat()
          .map((r) => r.error_rate + 0.03),
      ),
    },
  );
  plot(
    "calibration",
    [
      {
        color: colors.mint,
        points: m.metrics.calibration.map((b) => [b.predicted, b.observed]),
      },
    ],
    {
      xLabel: "Average predicted probability",
      yLabel: "Observed positive fraction",
      diagonal: true,
    },
  );
  const mm = m.metrics;
  $("metrics").innerHTML =
    `<div><small>Test accuracy · before review</small><strong>${pct(mm.accuracy)}</strong><small>95% Wilson interval ${pct(mm.accuracy_ci[0])}–${pct(mm.accuracy_ci[1])}</small></div><div><small>AUROC · ranking discrimination</small><strong>${mm.auc.toFixed(3)}</strong><small>1.0 = perfect ranking; 0.5 = chance</small></div><div><small>Brier score · probability error</small><strong>${mm.brier.toFixed(3)}</strong><small>Lower is better</small></div><div><small>Errors by simulated class</small><strong>${mm.by_class["0"].errors} / ${mm.by_class["1"].errors}</strong><small>ER negative (${mm.by_class["0"].n}) / positive (${mm.by_class["1"].n})</small></div>`;
  const diff = rules.confidence.errors - rules.disagreement.errors;
  $("conclusion").textContent =
    diff === 0
      ? "In this simulated run, both review rules leave the same number of errors at the selected review rate. This result does not establish clinical benefit."
      : `In this simulated run, disagreement flags leave ${Math.abs(diff)} ${diff > 0 ? "fewer" : diff < 0 ? "more" : "additional"} ${Math.abs(diff) === 1 ? "error" : "errors"} than confidence flags at the same review rate. This result depends on the simulation and is not evidence of clinical benefit.`;
  const a = new Set(rules.confidence.flagged),
    b = new Set(rules.disagreement.flagged);
  $("rows").innerHTML = m.rows
    .map(
      (r) =>
        `<tr><td>${r.id}</td><td>${r.label ? "Positive" : "Negative"}</td><td>${pct(r.mean)}</td><td>${r.variance.toFixed(5)}</td><td>${a.has(r.id) ? "Review" : "Retain"}</td><td>${b.has(r.id) ? "Review" : "Retain"}</td></tr>`,
    )
    .join("");
}
async function run() {
  stop();
  $("run").disabled = true;
  $("status").textContent = "Running matched comparisons…";
  try {
    const q = new URLSearchParams({
      seed: $("seed").value,
      budget: $("budget").value,
      repeats: $("repeats").value,
    });
    if (window.DEMO_CACHE) {
      data = window.DEMO_CACHE[q.toString()];
      if (!data) throw Error("This setting is not in the offline demo.");
    } else {
      const response = await fetch("api/experiment?" + q);
      if (!response.ok)
        throw Error(
          "The experiment could not run. Check the server and try again.",
        );
      data = await response.json();
    }
    $("case").innerHTML = data.cases
      .map((c) => `<option>${c.id}</option>`)
      .join("");
    $("draw").max = data.repeats - 1;
    $("draw").value = 0;
    $("status").textContent = "240 simulated cases · model fixed";
    renderCase();
    renderReview();
  } catch (e) {
    $("status").textContent = e.message;
  } finally {
    $("run").disabled = false;
  }
}
function stop() {
  clearInterval(timer);
  timer = null;
  $("play").textContent = "Play samples";
}
$("run").onclick = run;
$("case").onchange = renderCase;
$("draw").oninput = renderCase;
$("method").onchange = renderReview;
$("rate").onchange = renderReview;
$("unstable").onclick = () => {
  if (!data) return;
  $("case").value = [...data.methods.random.rows].sort(
    (a, b) => b.variance - a.variance,
  )[0].id;
  renderCase();
};
$("play").onclick = () => {
  if (!data) return;
  if (timer) return stop();
  $("play").textContent = "Pause";
  timer = setInterval(() => {
    $("draw").value = (+$("draw").value + 1) % data.repeats;
    renderCase();
  }, 550);
};
$("present").onclick = () => {
  document.body.classList.toggle("presentation");
  $("present").textContent = document.body.classList.contains("presentation")
    ? "Exit presentation view"
    : "Presentation view";
};
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    document.body.classList.remove("presentation");
    $("present").textContent = "Presentation view";
  }
});
document.querySelectorAll("[data-tab]").forEach(
  (b) =>
    (b.onclick = () => {
      stop();
      document
        .querySelectorAll("[data-tab],.tab")
        .forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      const section = $(b.dataset.tab);
      section.classList.add("active");
      section.scrollIntoView({ block: "start" });
    }),
);
$("download").onclick = () => {
  if (!data) return;
  const a = document.createElement("a");
  let url;
  if (window.DEMO_CACHE) {
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    url = URL.createObjectURL(blob);
    a.href = url;
  } else {
    a.href =
      "api/experiment?" +
      new URLSearchParams({
        seed: data.seed,
        budget: data.budget,
        repeats: data.repeats,
        download: 1,
      });
  }
  a.download = `simulated-results-seed-${data.seed}-patches-${data.budget}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  if (url) setTimeout(() => URL.revokeObjectURL(url), 1000);
};
["budget", "repeats", "seed"].forEach(
  (id) =>
    ($(id).onchange = () => {
      $("status").textContent = "Settings changed · click Run comparison";
    }),
);
run();
