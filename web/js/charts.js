/* Chart.js onset dot plot and NDVI line with shaded bare periods.
   Charts read only the already-loaded JSON: no network calls. */

import { fill, formatDayOfYear, strings } from "./strings.js";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

let onsetChart = null;
let ndviChart = null;

function css(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function dekadLabels() {
  return Array.from({ length: 36 }, (_, index) => {
    const month = Math.floor(index / 3);
    const day = [1, 11, 21][index % 3];
    return `${day} ${MONTHS[month]}`;
  });
}

export function destroyCharts() {
  onsetChart?.destroy();
  ndviChart?.destroy();
  onsetChart = null;
  ndviChart = null;
}

export function drawCharts(location, metrics, dataDocument) {
  if (typeof Chart === "undefined") return;
  drawOnset(metrics);
  drawNdvi(metrics);
}

function drawOnset(metrics) {
  const canvas = document.querySelector("#onset-chart");
  const note = document.querySelector("#onset-note");
  if (!canvas) return;

  onsetChart?.destroy();
  onsetChart = null;

  const entries = Object.entries(metrics.onset_by_year || {})
    .map(([year, day]) => ({ x: Number(year), y: Number(day) }))
    .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y))
    .sort((a, b) => a.x - b.x);

  if (!entries.length) {
    canvas.hidden = true;
    const wrap = canvas.closest(".chart-wrap");
    if (wrap) wrap.hidden = true;
    if (note) note.textContent = strings.onsetMissing;
    return;
  }
  canvas.hidden = false;
  {
    const wrap = canvas.closest(".chart-wrap");
    if (wrap) wrap.hidden = false;
  }

  const days = entries.map((point) => point.y);
  const median = medianOf(days);
  const years = entries.map((point) => point.x);
  const firstYear = Math.min(...years);
  const lastYear = Math.max(...years);

  if (note) {
    note.textContent = `${strings.onsetNote} ${fill(strings.onsetMedian, {
      date: formatDayOfYear(median),
    })}`;
  }

  const ink = css("--ink") || "#14281D";
  const leaf = css("--leaf") || "#2E7D4F";
  const sun = css("--sun") || "#F2A93B";
  const lineColor = css("--sage") || "#8DB48E";

  onsetChart = new Chart(canvas.getContext("2d"), {
    type: "scatter",
    data: {
      datasets: [
        {
          label: strings.onsetTitle,
          data: entries,
          backgroundColor: leaf,
          borderColor: leaf,
          pointRadius: 5,
          pointHoverRadius: 7,
        },
        {
          type: "line",
          label: strings.onsetMedian.replace(": {date}", ""),
          data: [
            { x: firstYear - 0.6, y: median },
            { x: lastYear + 0.6, y: median },
          ],
          borderColor: sun,
          borderWidth: 2,
          borderDash: [6, 5],
          pointRadius: 0,
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 250 },
      scales: {
        x: {
          type: "linear",
          min: firstYear - 1,
          max: lastYear + 1,
          title: { display: true, text: strings.onsetYearAxis, color: ink },
          ticks: {
            color: ink,
            precision: 0,
            maxTicksLimit: 8,
            callback: (value) => String(Math.round(value)),
          },
          grid: { color: `${lineColor}55` },
        },
        y: {
          title: { display: true, text: strings.onsetAxis, color: ink },
          ticks: {
            color: ink,
            stepSize: 20,
            callback: (value) => formatDayOfYear(value).replace(/\s\d{4}$/, ""),
          },
          grid: { color: `${lineColor}55` },
        },
      },
      plugins: {
        legend: { labels: { color: ink, boxWidth: 12, usePointStyle: true } },
        tooltip: {
          callbacks: {
            label: (context) => {
              if (context.dataset.type === "line") {
                return `${strings.onsetMedian.replace("{date}", formatDayOfYear(context.parsed.y))}`;
              }
              return `${context.parsed.x}: ${formatDayOfYear(context.parsed.y)}`;
            },
          },
        },
      },
    },
  });
}

function drawNdvi(metrics) {
  const canvas = document.querySelector("#ndvi-chart");
  const note = document.querySelector("#ndvi-note");
  if (!canvas) return;

  ndviChart?.destroy();
  ndviChart = null;

  const values = metrics.ndvi_dekad;
  if (!Array.isArray(values) || values.length !== 36) {
    canvas.hidden = true;
    const wrap = canvas.closest(".chart-wrap");
    if (wrap) wrap.hidden = true;
    if (note) note.textContent = `${strings.ndviMissing} ${strings.ndviDefaultShare}`;
    return;
  }
  canvas.hidden = false;
  {
    const wrap = canvas.closest(".chart-wrap");
    if (wrap) wrap.hidden = false;
  }
  if (note) note.textContent = `${strings.ndviNote} ${strings.ndviBare}`;

  const ink = css("--ink") || "#14281D";
  const leaf = css("--leaf") || "#2E7D4F";
  const sun = css("--sun") || "#F2A93B";
  const grid = css("--sage") || "#8DB48E";
  const flags = metrics.bare_flags || null;

  const bareShade = {
    id: "bareShade",
    beforeDatasetsDraw(chart, _args, options) {
      if (!options?.flags) return;
      const { ctx, chartArea } = chart;
      const step = chartArea.width / options.flags.length;
      ctx.save();
      ctx.fillStyle = options.color;
      options.flags.forEach((flag, index) => {
        if (!flag) return;
        ctx.fillRect(chartArea.left + index * step, chartArea.top, step, chartArea.height);
      });
      ctx.restore();
    },
  };

  ndviChart = new Chart(canvas.getContext("2d"), {
    type: "line",
    data: {
      labels: dekadLabels(),
      datasets: [{
        label: strings.ndviTitle,
        data: values,
        borderColor: leaf,
        backgroundColor: `${leaf}33`,
        fill: true,
        tension: 0.35,
        spanGaps: true,
        pointRadius: 2,
        pointHoverRadius: 5,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 250 },
      scales: {
        x: {
          title: { display: true, text: strings.onsetAxis, color: ink },
          ticks: { color: ink, maxTicksLimit: 9, autoSkip: true },
          grid: { display: false },
        },
        y: {
          min: 0,
          max: 0.9,
          title: { display: true, text: strings.ndviAxis, color: ink },
          ticks: { color: ink, stepSize: 0.2 },
          grid: { color: `${grid}55` },
        },
      },
      plugins: {
        legend: { display: false },
        bareShade: { flags, color: `${sun}30` },
        tooltip: {
          callbacks: {
            label: (context) =>
              `${context.label}: ${Number(context.parsed.y).toFixed(2)}`,
          },
        },
      },
    },
    plugins: [bareShade],
  });
}

function medianOf(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2
    ? sorted[middle]
    : (sorted[middle - 1] + sorted[middle]) / 2;
}
