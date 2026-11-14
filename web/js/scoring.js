/* Pure scoring functions. No DOM access, so this file runs under Node tests. */

export function scenarioKey(rainMult, tempDelta) {
  const signed = (value) => `${value >= 0 ? "+" : "-"}${Math.abs(value)}`;
  const rainPct = Math.round((rainMult - 1) * 100);
  return `rain${signed(rainPct)}_temp${signed(tempDelta)}`;
}

const frac = (counts, key) => counts[key] / counts.n_total;

export function scoreStrategy(sequence, loc, scenario, crops, weights) {
  if (!sequence.length) return { total: 0, parts: {} };

  const avg = (fn) =>
    sequence.reduce((sum, cropId) => sum + fn(cropId), 0) / sequence.length;
  const counts = (cropId) => loc.scenarios[scenario][cropId];
  const bare = loc.bare_share ?? 0.3;

  // Counts family changes around the cycle, including the wrap-around.
  const changes = sequence.filter(
    (cropId, index) =>
      crops[cropId].family !== crops[sequence[(index + 1) % sequence.length]].family,
  ).length;

  const parts = {
    climate: avg(
      (cropId) =>
        (frac(counts(cropId), "rain_ok") +
          frac(counts(cropId), "dry_ok") +
          frac(counts(cropId), "heat_ok")) /
        3,
    ),
    water: avg((cropId) => 1 - crops[cropId].water),
    soil: avg((cropId) => crops[cropId].n_fixing),
    erosion: avg((cropId) => crops[cropId].cover) * (1 - bare),
    pests: sequence.length > 1 ? changes / sequence.length : 0,
    income: avg((cropId) => crops[cropId].market),
  };

  let numerator = 0;
  let denominator = 0;
  for (const key in parts) {
    numerator += weights[key] * parts[key];
    denominator += weights[key];
  }

  return { total: denominator ? numerator / denominator : 0, parts };
}

export function rank(strategies, loc, scenario, crops, weights) {
  return strategies
    .map((strategy) => ({
      strategy,
      result: scoreStrategy(strategy.sequence, loc, scenario, crops, weights),
    }))
    .sort((a, b) => b.result.total - a.result.total);
}
