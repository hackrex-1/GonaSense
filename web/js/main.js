/* Entry point: load data once, wire the location control, then update. */

import { loadData } from "./data.js";
import { state, setState, onUpdate } from "./state.js";
import {
  renderLocationPicker,
  renderFacts,
  setBadge,
  showFatalError,
} from "./ui.js";

let DATA = null;

function update() {
  if (!DATA) return;
  const location = DATA.locations.find((entry) => entry.id === state.location);
  if (!location) return;
  const metrics = DATA.metrics[location.id];
  renderFacts(location, metrics, DATA.crops, DATA.strategies);
  document.title = `${location.name} · Gombe Rotation Advisor`;
}

function syncHash() {
  if (window.location.hash.slice(1) !== state.location) {
    history.replaceState(null, "", `#${state.location}`);
  }
}

function readHash(locations) {
  const fromHash = window.location.hash.slice(1);
  return locations.some((entry) => entry.id === fromHash) ? fromHash : null;
}

async function init() {
  DATA = await loadData();
  const fromHash = readHash(DATA.locations);
  if (fromHash) state.location = fromHash;

  if (!DATA.metrics[state.location]) {
    state.location = DATA.locations[0].id;
  }

  setBadge(`${DATA.locations.length} LGAs loaded · ${DATA.strategies.length} strategies`);
  renderLocationPicker(DATA.locations, state.location, (id) => setState({ location: id }));

  onUpdate(() => {
    syncHash();
    update();
  });

  window.addEventListener("hashchange", () => {
    const id = readHash(DATA.locations);
    if (id && id !== state.location) setState({ location: id });
  });

  syncHash();
  setBadge("Data loaded · offline-ready", "ok");
  update();
}

init().catch(showFatalError);
