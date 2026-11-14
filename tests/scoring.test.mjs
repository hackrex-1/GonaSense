import test from "node:test";
import assert from "node:assert/strict";

import { scoreStrategy, rank, scenarioKey } from "../web/js/scoring.js";

const crops = {
  maize: { family: "cereal", water: 0.75, n_fixing: 0.05, cover: 0.45, market: 0.8 },
  cowpea: { family: "legume", water: 0.3, n_fixing: 0.85, cover: 0.6, market: 0.7 },
  sorghum: { family: "cereal", water: 0.35, n_fixing: 0.05, cover: 0.55, market: 0.6 },
};

const counts = { rain_ok: 19, dry_ok: 15, heat_ok: 20, all_ok: 12, n_total: 24 };
const location = {
  bare_share: 0.3,
  scenarios: {
    "rain+0_temp+0": {
      maize: { ...counts },
      cowpea: { ...counts },
      sorghum: { ...counts },
    },
  },
};
const weights = { climate: 3, water: 3, soil: 3, erosion: 3, pests: 3, income: 3 };

test("continuous maize scores zero on pests", () => {
  const { parts } = scoreStrategy(["maize", "maize"], location, "rain+0_temp+0", crops, weights);
  assert.equal(parts.pests, 0);
});

test("maize then cowpea scores one on pests", () => {
  const { parts } = scoreStrategy(["maize", "cowpea"], location, "rain+0_temp+0", crops, weights);
  assert.equal(parts.pests, 1);
});

test("all-zero weights do not return NaN", () => {
  const zero = { climate: 0, water: 0, soil: 0, erosion: 0, pests: 0, income: 0 };
  const { total } = scoreStrategy(["maize", "cowpea"], location, "rain+0_temp+0", crops, zero);
  assert.equal(total, 0);
});

test("missing NDVI falls back to a neutral bare share", () => {
  const noNdvi = { ...location, bare_share: undefined };
  const { parts } = scoreStrategy(["maize"], noNdvi, "rain+0_temp+0", crops, weights);
  const expected = crops.maize.cover * (1 - 0.3);
  assert.ok(Math.abs(parts.erosion - expected) < 1e-12);
});

test("scenario keys match the pipeline naming", () => {
  assert.equal(scenarioKey(1.0, 0), "rain+0_temp+0");
  assert.equal(scenarioKey(0.8, 1), "rain-20_temp+1");
  assert.equal(scenarioKey(1.1, -1), "rain+10_temp-1");
});

test("rank orders strategies by total score", () => {
  const strategies = [
    { id: "mono", sequence: ["maize", "maize"] },
    { id: "mixed", sequence: ["maize", "cowpea"] },
  ];
  const ranked = rank(strategies, location, "rain+0_temp+0", crops, weights);
  assert.equal(ranked.length, 2);
  assert.equal(ranked[0].strategy.id, "mixed");
  assert.ok(ranked[0].result.total >= ranked[1].result.total);
});
