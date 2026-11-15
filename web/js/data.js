/* Load the five JSON contracts once. After init() the page makes no data
   requests. Relative URLs keep the site working under a GitHub Pages sub-path. */

import { strings } from "./strings.js";

export const FILES = ["locations", "crops", "strategies", "metrics", "glossary"];

export async function loadData(base = "./data") {
  const responses = await Promise.all(
    FILES.map((name) => fetch(`${base}/${name}.json`, { cache: "no-store" })),
  );
  const payloads = await Promise.all(
    responses.map(async (response, index) => {
      if (!response.ok) {
        throw new Error(`Could not load ${FILES[index]}.json (HTTP ${response.status})`);
      }
      return response.json();
    }),
  );
  const data = Object.fromEntries(FILES.map((name, index) => [name, payloads[index]]));
  return resolveBase(data);
}

/* The base scenario is exported as a string alias. Resolve it once so the
   rest of the page can never accidentally read a string as a scenario map. */
export function resolveBase(data) {
  const metrics = data.metrics;
  if (!metrics || !metrics.locations) return data;
  for (const location of Object.values(metrics.locations)) {
    const scenarios = location.scenarios || {};
    const alias = scenarios.base;
    if (typeof alias === "string") {
      location.baseKey = alias;
      location.baseScenario = scenarios[alias] || null;
    } else {
      location.baseKey = "rain+0_temp+0";
      location.baseScenario = scenarios[location.baseKey] || null;
    }
  }
  return data;
}

/* The existing rotation is created in the UI; alternatives come from JSON. */
export function strategyList(existing, alternatives) {
  return [
    {
      id: "A",
      name: strings.existingName,
      sequence: [...existing],
      benefits: [strings.existingBenefits],
      gaps: [strings.existingGaps],
      risks: [strings.existingRisks],
    },
    ...alternatives,
  ];
}
