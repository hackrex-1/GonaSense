import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { scoreStrategy, rank, scenarioKey, trafficLight } from "../web/js/scoring.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const data = (name) => JSON.parse(fs.readFileSync(path.join(here, "..", "web", "data", name), "utf8"));

const crops = data("crops.json");
const strategies = data("strategies.json");
const metrics = data("metrics.json");
const location = metrics.locations.gombe;
const weights = { climate: 3, water: 3, soil: 3, erosion: 3, pests: 3, income: 3 };
const scenario = "rain+0_temp+0";

test("continuous maize scores zero on pests", () => {
  const { parts } = scoreStrategy(["maize", "maize"], location, scenario, crops, weights);
  assert.equal(parts.pests, 0);
});

test("maize then cowpea scores one on pests", () => {
  const { parts } = scoreStrategy(["maize", "cowpea"], location, scenario, crops, weights);
  assert.equal(parts.pests, 1);
});

test("all-zero weights return total 0 and no NaN", () => {
  const zero = { climate: 0, water: 0, soil: 0, erosion: 0, pests: 0, income: 0 };
  const { total, parts } = scoreStrategy(["maize", "cowpea"], location, scenario, crops, zero);
  assert.equal(total, 0);
  for (const value of Object.values(parts)) assert.ok(Number.isFinite(value));
});

test("missing NDVI falls back to the neutral bare share", () => {
  const noNdvi = { ...location, bare_share: null };
  const { parts } = scoreStrategy(["maize"], noNdvi, scenario, crops, weights);
  assert.ok(Math.abs(parts.erosion - crops.maize.cover * (1 - 0.3)) < 1e-12);
});

test("raising only the water weight lifts the drought-tolerant mix above maize", () => {
  const waterFirst = { climate: 1, water: 5, soil: 1, erosion: 1, pests: 1, income: 1 };
  const list = [
    { id: "A", name: "Your current rotation", sequence: ["maize", "maize"] },
    ...strategies,
  ];
  const ranked = rank(list, location, scenario, crops, waterFirst);
  assert.equal(ranked[0].s.id, "C");

  const maizeRank = ranked.findIndex((entry) => entry.s.id === "A");
  assert.ok(maizeRank > ranked.findIndex((entry) => entry.s.id === "D"));
});

test("scenario keys match the Python key format", () => {
  assert.equal(scenarioKey(1.0, 0), "rain+0_temp+0");
  assert.equal(scenarioKey(0.9, 1), "rain-10_temp+1");
  assert.equal(scenarioKey(0.8, 0), "rain-20_temp+0");
  assert.equal(scenarioKey(1.1, 2), "rain+10_temp+2");
});

test("ranking is ordered by total score, with structure the UI can render", () => {
  const ranked = rank(strategies, location, scenario, crops, weights);
  assert.equal(ranked.length, strategies.length);
  for (let index = 1; index < ranked.length; index += 1) {
    assert.ok(ranked[index - 1].r.total >= ranked[index].r.total);
  }
  assert.ok(ranked[0].s.name);
  assert.ok(ranked[0].r.parts.climate >= 0 && ranked[0].r.parts.climate <= 1);
});

test("traffic lights pair a colour key with a text label", () => {
  assert.equal(trafficLight(0.7).key, "strong");
  assert.equal(trafficLight(0.5).key, "mixed");
  assert.equal(trafficLight(0.2).key, "weak");
  for (const total of [0.7, 0.5, 0.2]) {
    assert.ok(trafficLight(total).label.length > 0);
    assert.ok(trafficLight(total).icon.length > 0);
  }
});
