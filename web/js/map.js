/* Leaflet map: one accessible marker per LGA, coloured by the best-fit
   strategy traffic light. Tile failure never removes the markers. */

import { strategyList } from "./data.js";
import { rank, trafficLight } from "./scoring.js";
import { fill, strings } from "./strings.js";

let map = null;
let layer = null;
let fitted = false;
let tileWarningShown = false;

function css(name, fallback) {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}

function colourFor(key) {
  if (key === "strong") return css("--leaf", "#2E7D4F");
  if (key === "mixed") return css("--sun", "#F2A93B");
  return css("--soil", "#9A4F12");
}

function initMap() {
  if (map || typeof L === "undefined") return;
  map = L.map("map", {
    center: [10.3, 11.2],
    zoom: 8,
    scrollWheelZoom: false,
  });

  const tiles = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  });
  tiles.on("tileerror", () => {
    if (tileWarningShown) return;
    tileWarningShown = true;
    const note = document.querySelector("#map-note");
    if (note) note.textContent = strings.mapTilesFailed;
  });
  tiles.addTo(map);
  layer = L.layerGroup().addTo(map);
}

export function drawMap(data, state, scenario, weights, onSelect) {
  initMap();
  if (!map || !layer) return;

  layer.clearLayers();
  const bounds = [];
  const list = strategyList(state.existing, data.strategies);

  for (const entry of data.locations) {
    const metrics = data.metrics.locations[entry.id];
    if (!metrics || !metrics.scenarios?.[scenario]) continue;

    const ranked = rank(list, metrics, scenario, data.crops, weights);
    const top = ranked[0];
    if (!top) continue;
    const light = trafficLight(top.r.total);
    const selected = entry.id === state.location;
    bounds.push([entry.lat, entry.lon]);

    const marker = L.circleMarker([entry.lat, entry.lon], {
      radius: selected ? 12 : 9,
      color: selected ? css("--ink", "#14281D") : css("--forest", "#1F4D33"),
      weight: selected ? 4 : 2,
      fillColor: colourFor(light.key),
      fillOpacity: 0.9,
    });

    marker.bindTooltip(entry.name, { direction: "top", offset: [0, -8] });
    marker.bindPopup(popupContent(entry, top.s, light));
    marker.on("click", () => onSelect(entry.id));
    marker.addTo(layer);

    const element = marker.getElement?.();
    if (element) {
      element.setAttribute("role", "button");
      element.setAttribute("tabindex", "0");
      element.setAttribute(
        "aria-label",
        fill(strings.mapPopupBest, { name: entry.name, label: light.label }),
      );
      element.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect(entry.id);
        }
      });
    }
    if (selected) marker.bringToFront();
  }

  if (!fitted && bounds.length) {
    map.fitBounds(bounds, { padding: [28, 28] });
    fitted = true;
  }
  map.invalidateSize();
}

function popupContent(entry, strategy, light) {
  const container = document.createElement("div");
  container.className = "map-popup";

  const title = document.createElement("strong");
  title.textContent = entry.name;
  const best = document.createElement("p");
  best.textContent = fill(strings.mapPopupBest, {
    name: strategy.name,
    label: light.label,
  });
  const action = document.createElement("p");
  action.className = "map-popup-action";
  action.textContent = fill(strings.mapPopupSelect, { name: entry.name });

  container.append(title, best, action);
  return container;
}
