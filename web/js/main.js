/* Entry point. Load data once, build controls, then update every view from
   in-memory state. No network request happens after init(). */

import { loadData, strategyList } from "./data.js";
import { state, setState, onUpdate } from "./state.js";
import { rank, scenarioKey } from "./scoring.js";
import {
  applyStaticCopy,
  buildControls,
  renderCards,
  renderGlossary,
  renderLimits,
  renderScenarioError,
  setDataBadge,
  showFatalError,
  syncControls,
  syncDemoBanner,
} from "./ui.js";
import { drawCharts } from "./charts.js";
import { drawMap } from "./map.js";

let DATA = null;
let wired = false;

function handlers() {
  return {
    onLocation: (id) => setState({ location: id }),
    onRotationSlot: (index, cropId) => {
      const existing = [...state.existing];
      existing[index] = cropId;
      setState({ existing });
    },
    onAddYear: () => {
      if (state.existing.length >= 3) return;
      setState({ existing: [...state.existing, "cowpea"] });
    },
    onRemoveYear: (index) => {
      if (state.existing.length <= 2) return;
      setState({ existing: state.existing.filter((_, item) => item !== index) });
    },
    onWeight: (key, value) => setState({ weights: { ...state.weights, [key]: value } }),
    onRain: (value) => setState({ rain: value }),
    onTemp: (value) => setState({ temp: value }),
  };
}

function validLocation(id) {
  return Boolean(DATA?.locations?.some((entry) => entry.id === id));
}

function readHash() {
  const id = window.location.hash.replace(/^#/, "");
  return validLocation(id) ? id : null;
}

function normaliseState() {
  if (!validLocation(state.location)) {
    state.location = DATA.locations[0]?.id || "gombe";
  }
  const crops = Object.keys(DATA.crops || {});
  state.existing = state.existing
    .filter((cropId) => crops.includes(cropId))
    .slice(0, 3);
  while (state.existing.length < 2 && crops.length) {
    state.existing.push(crops[0]);
  }
}

export function update() {
  if (!DATA) return;
  normaliseState();

  const location = DATA.locations.find((entry) => entry.id === state.location)
    || DATA.locations[0];
  const metrics = DATA.metrics?.locations?.[location.id];

  syncControls(DATA, state);

  if (!metrics) {
    showFatalError(new Error(`No metrics for ${location.name}.`), () => window.location.reload());
    return;
  }

  const key = scenarioKey(state.rain, state.temp);
  const counts = metrics.scenarios?.[key];
  if (!counts) {
    renderScenarioError(key);
    return;
  }

  const strategies = strategyList(state.existing, DATA.strategies);
  const ranked = rank(strategies, metrics, key, DATA.crops, state.weights);

  drawMap(DATA, state, key, state.weights, (id) => setState({ location: id }));
  drawCharts(location, metrics, DATA.metrics);
  renderCards(ranked, DATA, location, counts, (metrics.no_onset_years || []).length);
  renderLimits(DATA.metrics, location, metrics);

  document.title = `${location.name} · GonaSense`;
}

async function init() {
  applyStaticCopy();
  try {
    DATA = await loadData();
  } catch (error) {
    showFatalError(error, () => window.location.reload());
    return;
  }

  const fromHash = readHash();
  if (fromHash) state.location = fromHash;
  normaliseState();

  syncDemoBanner(DATA.metrics);
  const scenarios = DATA.metrics?.locations?.[state.location]?.scenarios || {};
  const scenarioCount = Object.keys(scenarios).filter((key) => key !== "base").length;
  setDataBadge(DATA.metrics, DATA.locations.length, scenarioCount);
  renderGlossary(DATA.glossary);

  buildControls(DATA, state, handlers());

  if (!wired) {
    onUpdate(update);
    window.addEventListener("hashchange", () => {
      const id = readHash();
      if (id && id !== state.location) setState({ location: id });
    });
    wired = true;
  }

  if (window.location.hash !== `#${state.location}`) {
    history.replaceState(null, "", `#${state.location}`);
  }
  update();
}

init();
