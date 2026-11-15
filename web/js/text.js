/* Card copy builders. All wording lives in strings.js; these functions only
   choose a template and fill it with real numbers and criterion names. */

import { fill, strings } from "./strings.js";

const CRITERIA = ["climate", "water", "soil", "erosion", "pests", "income"];

export function criterionLabel(key) {
  return strings.priority[key] || key;
}

export function whySentence(parts) {
  const ordered = CRITERIA
    .map((key) => ({ key, value: parts[key] ?? 0 }))
    .sort((a, b) => b.value - a.value);
  const top1 = criterionLabel(ordered[0].key);
  const top2 = criterionLabel(ordered[1].key);
  const lowest = criterionLabel(ordered[ordered.length - 1].key);
  return fill(strings.why, { top1, top2, lowest });
}

export function evidenceLine(cropId, counts, crops) {
  const name = crops[cropId]?.name || strings.cropNames[cropId] || cropId;
  if (!counts || !Number.isFinite(counts.n_total) || counts.n_total <= 0) {
    return fill(strings.noEvidence, { crop: name });
  }
  return fill(strings.evidenceLine, {
    crop: name,
    ok: counts.all_ok,
    total: counts.n_total,
  });
}

export function noOnsetLine(count) {
  return count > 0 ? fill(strings.noOnset, { n: count }) : "";
}

export function sequenceText(sequence, crops) {
  const names = sequence.map(
    (crop) => crops[crop]?.name || strings.cropNames[crop] || crop,
  );
  if (names.length === 1) return names[0];
  if (names.length === 2) return `${names[0]}${strings.sequenceThen}${names[1]}`;
  return `${names.slice(0, -1).join(strings.sequenceThen)}${strings.sequenceThen}${names[names.length - 1]}`;
}
