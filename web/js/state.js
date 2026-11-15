/* In-memory state. No localStorage, no sessionStorage, no IndexedDB.
   The URL hash carries only the selected location id. */

export const state = {
  location: "gombe",
  existing: ["maize", "maize"],
  weights: { climate: 3, water: 3, soil: 3, erosion: 3, pests: 3, income: 3 },
  rain: 1.0,
  temp: 0,
};

const listeners = new Set();

export function onUpdate(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function setState(patch) {
  Object.assign(state, patch);
  const hash = `#${state.location}`;
  if (window.location.hash !== hash) {
    history.replaceState(null, "", hash);
  }
  for (const listener of listeners) listener(state);
}
