/* DOM rendering: controls, strategy cards, limits panel, glossary, errors.
   Every user-visible string comes from strings.js. */

import { strings, fill, formatPercent } from "./strings.js";
import { trafficLight } from "./scoring.js";
import { criterionLabel, evidenceLine, noOnsetLine, sequenceText, whySentence } from "./text.js";

const CRITERIA = ["climate", "water", "soil", "erosion", "pests", "income"];

export function el(tag, attrs = {}, text) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === undefined || value === null) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else node.setAttribute(key, value);
  }
  if (text !== undefined) node.textContent = text;
  return node;
}

export function clear(node) {
  if (node) node.replaceChildren();
}

function copyValue(key) {
  return key.split(".").reduce((value, part) => (value ? value[part] : undefined), strings);
}

/* Fill static headings and labels from strings.js so no page copy lives only
   in HTML. Runs before data is fetched, so the shell is readable even offline. */
export function applyStaticCopy() {
  document.querySelectorAll("[data-copy]").forEach((node) => {
    const value = copyValue(node.dataset.copy);
    if (typeof value === "string") node.textContent = value;
  });
  document.querySelectorAll("[data-copy-aria]").forEach((node) => {
    const value = copyValue(node.dataset.copyAria);
    if (typeof value === "string") node.setAttribute("aria-label", value);
  });
}

function option(value, label, selected) {
  const node = el("option", { value }, label);
  if (selected) node.selected = true;
  return node;
}

/* ----------------------------------------------------------------------- */
/* Controls                                                                */
/* ----------------------------------------------------------------------- */
export function buildControls(data, state, handlers) {
  const locationSelect = document.querySelector("#location-select");
  locationSelect.replaceChildren(
    ...data.locations.map((entry) => option(entry.id, entry.name, entry.id === state.location)),
  );
  locationSelect.value = state.location;
  locationSelect.disabled = false;
  locationSelect.addEventListener("change", () => handlers.onLocation(locationSelect.value));

  const addYear = document.querySelector("#add-year");
  if (addYear && !addYear.dataset.bound) {
    addYear.dataset.bound = "true";
    addYear.addEventListener("click", () => handlers.onAddYear?.());
  }

  renderRotation(data, state, handlers);
  renderPriorities(state, handlers);
  renderScenarioOptions(state, handlers);
}

export function syncControls(data, state) {
  const locationSelect = document.querySelector("#location-select");
  if (locationSelect && locationSelect.value !== state.location) {
    locationSelect.value = state.location;
  }

  const slots = document.querySelector("#rotation-slots");
  const selectCount = slots ? slots.querySelectorAll("select").length : -1;
  if (selectCount !== state.existing.length) {
    renderRotation(data, state, window.__gonaHandlers || {});
  } else if (slots) {
    slots.querySelectorAll("select").forEach((select, index) => {
      if (select.value !== state.existing[index]) select.value = state.existing[index];
    });
    updateRemoveButtons(state);
  }

  for (const key of CRITERIA) {
    const input = document.querySelector(`#weight-${key}`);
    const output = document.querySelector(`#weight-${key}-out`);
    if (input) input.value = state.weights[key];
    if (output) output.textContent = state.weights[key];
  }

  document.querySelectorAll('input[name="rain"]').forEach((input) => {
    input.checked = Number(input.value) === state.rain;
  });
  document.querySelectorAll('input[name="temp"]').forEach((input) => {
    input.checked = Number(input.value) === state.temp;
  });
}

export function renderRotation(data, state, handlers) {
  window.__gonaHandlers = handlers;
  const slots = document.querySelector("#rotation-slots");
  if (!slots) return;
  clear(slots);

  state.existing.forEach((cropId, index) => {
    const id = `crop-year-${index + 1}`;
    const wrapper = el("div", { class: "rotation-slot" });
    wrapper.append(
      el("label", { for: id }, fill(strings.cropLabel, { n: index + 1 })),
    );
    const select = el("select", { id, "data-slot": index });
    select.append(
      ...Object.entries(data.crops).map(([key, crop]) =>
        option(key, crop.name || strings.cropNames[key] || key, key === cropId)),
    );
    select.addEventListener("change", () => handlers.onRotationSlot?.(index, select.value));
    wrapper.append(select);

    if (state.existing.length > 2 && index === state.existing.length - 1) {
      const remove = el("button", {
        type: "button",
        class: "link-button",
        "data-remove": index,
        "aria-label": fill(strings.removeYear, { n: index + 1 }),
      }, strings.remove);
      remove.addEventListener("click", () => handlers.onRemoveYear?.(index));
      wrapper.append(remove);
    }
    slots.append(wrapper);
  });

  const add = document.querySelector("#add-year");
  if (add) add.hidden = state.existing.length >= 3;
}

function updateRemoveButtons(state) {
  document.querySelectorAll("[data-remove]").forEach((button) => {
    button.hidden = Number(button.dataset.remove) !== state.existing.length - 1;
  });
}

function renderPriorities(state, handlers) {
  const list = document.querySelector("#priorities-list");
  if (!list) return;
  clear(list);
  for (const key of CRITERIA) {
    const id = `weight-${key}`;
    const row = el("div", { class: "priority-row" });
    const label = el("label", { for: id });
    label.append(
      el("span", { class: "priority-name" }, strings.priority[key]),
      el("output", { id: `${id}-out`, for: id, "aria-live": "off" }, String(state.weights[key])),
    );
    const input = el("input", {
      id,
      type: "range",
      min: "1",
      max: "5",
      step: "1",
      value: state.weights[key],
      "aria-describedby": "priorities-hint",
    });
    input.addEventListener("input", () => {
      const output = document.querySelector(`#${id}-out`);
      if (output) output.textContent = input.value;
      handlers.onWeight?.(key, Number(input.value));
    });
    row.append(label, input);
    list.append(row);
  }
}

function renderScenarioOptions(state, handlers) {
  const rain = document.querySelector("#rain-options");
  const temp = document.querySelector("#temp-options");
  if (rain) {
    clear(rain);
    for (const item of strings.rainOptions) {
      rain.append(radioOption("rain", item.value, item.label, Number(item.value) === state.rain, handlers.onRain));
    }
  }
  if (temp) {
    clear(temp);
    for (const item of strings.tempOptions) {
      temp.append(radioOption("temp", item.value, item.label, Number(item.value) === state.temp, handlers.onTemp));
    }
  }
}

function radioOption(name, value, label, checked, onChange) {
  const wrapper = el("label", { class: "radio-chip" });
  const input = el("input", { type: "radio", name, value: String(value) });
  input.checked = checked;
  input.addEventListener("change", () => {
    if (input.checked) onChange?.(Number(value));
  });
  wrapper.append(input, el("span", {}, label));
  return wrapper;
}

/* ----------------------------------------------------------------------- */
/* Strategy cards                                                          */
/* ----------------------------------------------------------------------- */
export function renderCards(ranked, data, location, counts, noOnsetCount) {
  const cards = document.querySelector("#cards");
  const status = document.querySelector("#cards-status");
  if (!cards) return;
  clear(cards);
  if (status) status.textContent = "";

  ranked.forEach((entry, index) => {
    cards.append(renderCard(entry, index + 1, data, location, counts, noOnsetCount));
  });
  if (status) {
    status.textContent = `${ranked.length} strategies ranked for ${location.name}.`;
  }
}

function renderCard(entry, rankNumber, data, location, counts, noOnsetCount) {
  const { s: strategy, r: result } = entry;
  const parts = result.parts || {};
  const light = trafficLight(result.total);
  const provisional = sequenceHasProvisional(strategy.sequence, data.crops);

  const card = el("article", {
    class: "card",
    "aria-labelledby": `card-title-${strategy.id}`,
  });

  const header = el("div", { class: "card-head" });
  const ranking = el("span", { class: "rank", "aria-label": fill(strings.rankLabel, { n: rankNumber }) }, String(rankNumber));
  const titleWrap = el("div", { class: "card-title" });
  titleWrap.append(
    el("h3", { id: `card-title-${strategy.id}` }, strategy.name),
    el("p", { class: "chips" }, sequenceText(strategy.sequence, data.crops)),
  );
  const badge = el("span", { class: `badge badge-${light.key}` });
  badge.append(
    el("span", { class: "badge-icon", "aria-hidden": "true" }, light.icon),
    el("span", {}, light.label),
  );
  header.append(ranking, titleWrap, badge);
  card.append(header);

  const scoreRow = el("div", { class: "score-row" });
  scoreRow.append(el("span", { class: "score-label" }, strings.overallFit));
  const bar = el("span", {
    class: "bar bar-total",
    role: "progressbar",
    "aria-valuemin": "0",
    "aria-valuemax": "100",
    "aria-valuenow": String(Math.round(result.total * 100)),
    "aria-label": fill(strings.scoreAria, {
      percent: Math.round(result.total * 100),
      label: light.label,
    }),
  });
  const fillBar = el("span", { class: "bar-fill" });
  fillBar.style.width = `${Math.round(result.total * 100)}%`;
  bar.append(fillBar);
  scoreRow.append(bar);
  card.append(scoreRow);

  if (provisional) {
    const tagRow = el("p", { class: "tag-row" });
    tagRow.append(el("span", { class: "tag" }, strings.unverifiedTag));
    card.append(tagRow);
  }

  card.append(renderCriteria(parts));

  card.append(section(strings.whyTitle, el("p", {}, whySentence(parts))));

  const evidence = el("ul", { class: "plain-list" });
  for (const cropId of strategy.sequence) {
    evidence.append(el("li", {}, evidenceLine(cropId, counts[cropId], data.crops)));
  }
  const evidenceSection = section(strings.evidenceTitle, evidence);
  if (noOnsetCount > 0) {
    evidenceSection.append(el("p", { class: "note" }, noOnsetLine(noOnsetCount)));
  }
  card.append(evidenceSection);

  card.append(section(strings.benefitsTitle, bulletList(strategy.benefits)));
  card.append(section(strings.gapsTitle, bulletList(strategy.gaps)));

  const risksSection = section(strings.risksTitle, bulletList(strategy.risks));
  risksSection.append(el("p", { class: "ask-expert" }, strings.askExpert));
  card.append(risksSection);

  if (provisional) {
    card.append(el("p", { class: "provisional-note" }, strings.provisionalNote));
  }

  card.append(el("p", { class: "support" }, strings.support));
  return card;
}

function sequenceHasProvisional(sequence, crops) {
  return sequence.some((cropId) => crops[cropId]?.provisional === true);
}

function section(title, body) {
  const wrapper = el("section", { class: "card-section" });
  wrapper.append(el("h4", {}, title), body);
  return wrapper;
}

function bulletList(items) {
  const list = el("ul", { class: "plain-list" });
  for (const item of items || []) list.append(el("li", {}, item));
  return list;
}

function renderCriteria(parts) {
  const list = el("ul", { class: "criteria", "aria-label": strings.criteriaAriaLabel });
  for (const key of CRITERIA) {
    const value = parts[key] ?? 0;
    const percent = Math.round(value * 100);
    const row = el("li");
    row.append(el("span", { class: "crit-label" }, criterionLabel(key)));
    const bar = el("span", {
      class: "bar",
      role: "img",
      "aria-label": fill(strings.criteriaAria, { label: criterionLabel(key), percent }),
    });
    const inner = el("span", { class: `bar-fill crit-${key}` });
    inner.style.width = `${percent}%`;
    bar.append(inner);
    row.append(bar);
    list.append(row);
  }
  return list;
}

export function renderScenarioError(key) {
  const cards = document.querySelector("#cards");
  if (!cards) return;
  clear(cards);
  const panel = el("div", { class: "error-panel", role: "alert" });
  panel.append(
    el("h3", {}, strings.scenarioMissingTitle),
    el("p", {}, fill(strings.scenarioMissingBody, { key })),
  );
  cards.append(panel);
  const status = document.querySelector("#cards-status");
  if (status) status.textContent = "";
}

/* ----------------------------------------------------------------------- */
/* Limits and glossary                                                     */
/* ----------------------------------------------------------------------- */
export function renderLimits(document_, location, metrics) {
  const body = document.querySelector("#limits-body");
  if (!body) return;
  clear(body);

  const sources = (document_.sources_used || []).join("; ");
  const [startYear, endYear] = document_.years || [];
  const items = [
    fill(strings.limitsSources, { sources, start: startYear, end: endYear }),
    strings.limitsResolution,
    strings.limitsSatellite,
    fill(strings.limitsConfidence, {
      label: metrics.confidence,
      reason: metrics.confidence_reason,
    }),
    strings.limitsScenario,
    strings.limitsProvisional,
    document_.data_mode === "synthetic" ? strings.limitsDataModeSynthetic : strings.limitsDataModeNasa,
    strings.limitsSecurity,
    strings.limitsSupport,
  ];
  if (metrics.ndvi_dekad === null) items.splice(6, 0, strings.limitsNdvi);

  const list = el("ul", { class: "limits-list" });
  for (const item of items) list.append(el("li", {}, item));
  body.append(list);
  body.append(glossaryLinks(["NDVI", "Soil moisture", "Confidence label", "Sensitivity test", "Rainfall onset", "Dekad (10-day period)"]));
}

function glossaryLinks(terms) {
  const paragraph = el("p", { class: "glossary-links" });
  paragraph.append(el("span", {}, strings.glossaryDefinitions));
  terms.forEach((term, index) => {
    const slug = term.toLowerCase().replace(/[^a-z0-9]+/g, "-");
    const link = el("a", {
      href: `#glossary-${slug}`,
      "aria-label": fill(strings.glossaryLink, { term }),
    }, term);
    paragraph.append(link);
    if (index < terms.length - 1) paragraph.append(el("span", { "aria-hidden": "true" }, " · "));
  });
  return paragraph;
}

export function renderGlossary(entries) {
  const list = document.querySelector("#glossary-list");
  if (!list) return;
  clear(list);
  for (const entry of entries) {
    const slug = entry.term.toLowerCase().replace(/[^a-z0-9]+/g, "-");
    const item = el("details", { id: `glossary-${slug}`, class: "glossary-item" });
    item.append(
      el("summary", {}, entry.term),
      el("p", {}, entry.plain),
    );
    list.append(item);
  }
}

/* ----------------------------------------------------------------------- */
/* Status and errors                                                       */
/* ----------------------------------------------------------------------- */
export function setDataBadge(document_, locationCount, scenarioCount) {
  const badge = document.querySelector("#data-badge");
  if (!badge) return;
  badge.textContent = fill(strings.dataBadge, {
    count: locationCount,
    scenarios: scenarioCount,
    mode: document_.data_mode === "nasa" ? strings.modeNasa : strings.modeSynthetic,
  });
}

export function syncDemoBanner(document_) {
  const banner = document.querySelector("#demo-banner");
  if (!banner) return;
  banner.hidden = document_.data_mode !== "synthetic";
}

export function showFatalError(error, retry) {
  const existing = document.querySelector("#data-error");
  if (existing) existing.remove();

  const panel = el("section", { id: "data-error", class: "error-panel", role: "alert" });
  panel.append(
    el("h2", {}, strings.dataErrorTitle),
    el("p", {}, strings.dataErrorBody),
    el("p", { class: "error-detail" }, String(error?.message || error)),
  );
  const button = el("button", { type: "button", class: "button" }, strings.retry);
  button.addEventListener("click", () => {
    panel.remove();
    retry();
  });
  panel.append(button);

  const main = document.querySelector("#main");
  if (main) main.prepend(panel);
  const badge = document.querySelector("#data-badge");
  if (badge) badge.textContent = strings.dataErrorTitle;
}
