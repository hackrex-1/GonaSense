/* Pure scoring functions. No DOM access, so this file runs under Node tests.

   Mirrors the formula in docs/method.md and the pipeline's scenario names. */

import { strings } from "./strings.js";

const frac = (counts, key) => counts[key] / counts.n_total;

export function scoreStrategy(seq, loc, scen, crops, w) {
  if (!seq.length) return { total: 0, parts: {} };

  const avg = (fn) => seq.reduce((sum, crop) => sum + fn(crop), 0) / seq.length;
  const m = (crop) => loc.scenarios[scen][crop];
  const bare = loc.bare_share ?? 0.3; // mirror DEFAULT_BARE_SHARE
  const changes = seq.filter(
    (crop, index) => crops[crop].family !== crops[seq[(index + 1) % seq.length]].family,
  ).length;

  const parts = {
    climate: avg(
      (crop) =>
        (frac(m(crop), "rain_ok") + frac(m(crop), "dry_ok") + frac(m(crop), "heat_ok")) / 3,
    ),
    water: avg((crop) => 1 - crops[crop].water),
    soil: avg((crop) => crops[crop].n_fixing),
    erosion: avg((crop) => crops[crop].cover) * (1 - bare),
    pests: seq.length > 1 ? changes / seq.length : 0,
    income: avg((crop) => crops[crop].market),
  };

  let numerator = 0;
  let denominator = 0;
  for (const key in parts) {
    numerator += w[key] * parts[key];
    denominator += w[key];
  }
  return { total: denominator ? numerator / denominator : 0, parts };
}

export function rank(strategies, loc, scen, crops, w) {
  return strategies
    .map((s) => ({ s, r: scoreStrategy(s.sequence, loc, scen, crops, w) }))
    .sort((a, b) => b.r.total - a.r.total);
}

export const scenarioKey = (rainMult, tempDelta) =>
  `rain${Math.round((rainMult - 1) * 100) >= 0 ? "+" : ""}${Math.round((rainMult - 1) * 100)}_temp${tempDelta >= 0 ? "+" : ""}${tempDelta}`;

export function trafficLight(total) {
  const key = total >= 0.65 ? "strong" : total >= 0.45 ? "mixed" : "weak";
  return { key, label: strings.traffic[key].label, icon: strings.traffic[key].icon };
}
