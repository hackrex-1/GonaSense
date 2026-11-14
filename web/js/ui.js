/* DOM rendering: controls, facts, cards, limits panel, glossary. */

import { strings } from "./strings.js";

const DAY_MS = 24 * 60 * 60 * 1000;

function el(tag, attrs = {}, text) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  return node;
}

export function renderLocationPicker(locations, selected, onSelect) {
  const select = document.querySelector("#location-select");
  if (!select) return;
  select.replaceChildren(
    ...locations.map((location) =>
      el("option", { value: location.id }, location.name),
    ),
  );
  select.value = selected;
  select.disabled = false;
  select.addEventListener("change", () => onSelect(select.value));
}

export function median(values) {
  const sorted = values.filter((value) => Number.isFinite(value)).sort((a, b) => a - b);
  if (!sorted.length) return null;
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2
    ? sorted[middle]
    : (sorted[middle - 1] + sorted[middle]) / 2;
}

export function onsetLabel(dayOfYear) {
  if (!Number.isFinite(dayOfYear)) return strings.noData;
  const date = new Date(Date.UTC(2001, 0, Math.round(dayOfYear)));
  return `${date.toLocaleDateString("en-GB", { day: "numeric", month: "long", timeZone: "UTC" })} (day ${Math.round(dayOfYear)})`;
}

export function renderFacts(location, metrics, crops, strategies) {
  const list = document.querySelector("#location-facts");
  if (!list) return;

  const onsets = Object.values(metrics.onset_by_year ?? {});
  const typical = median(onsets);
  const bare =
    typeof metrics.bare_share === "number"
      ? `${Math.round(metrics.bare_share * 100)}% of dekads`
      : "Not available yet (NDVI add-on pending)";

  const rows = [
    ["LGA", location.name],
    [strings.confidence, location.confidence],
    [strings.seasons, `${metrics.n_total} seasons, ${metrics.no_onset_years} with no onset`],
    [strings.medianOnset, onsetLabel(typical)],
    [strings.bareShare, bare],
    [strings.scenarios, `${Object.keys(metrics.scenarios).length} rainfall x temperature cases`],
    [strings.strategiesLoaded, `${strategies.length} tested rotations, ${Object.keys(crops).length} crops`],
  ];

  list.replaceChildren(
    ...rows.map(([term, value]) => {
      const wrapper = el("div");
      wrapper.append(el("dt", {}, term), el("dd", {}, value));
      return wrapper;
    }),
  );
}

export function setBadge(text, state = "ok") {
  const badge = document.querySelector("#data-badge");
  if (!badge) return;
  badge.textContent = text;
  badge.dataset.state = state;
}

export function showFatalError(error) {
  setBadge("Data failed to load", "error");
  const main = document.querySelector("#main");
  if (!main) return;
  const panel = el("section", { class: "panel", role: "alert" });
  panel.append(
    el("h2", {}, "Something went wrong"),
    el("p", {}, `The page could not load its data files. ${error.message}`),
  );
  main.prepend(panel);
}
