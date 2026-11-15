/* All user-facing English copy, in one place so another language can be
   added later without touching layout or scoring code. */

export const strings = {
  appName: "GonaSense",
  brandHome: "GonaSense home",
  appWordmark: { first: "Gona", second: "Sense" },
  challenge: "NASA Space Apps Challenge 2026 · Field Shift",
  tagline: "Gona (farm) plus Sense (satellite sensing)",
  lede:
    "Compare your current crop rotation with climate-tested alternatives, using 24 seasons of satellite rainfall, temperature and soil data.",
  skip: "Skip to content",

  demoBanner: "DEMO DATA: synthetic, not real NASA observations",
  nasaNote: "Data mode: NASA POWER and partners. No synthetic values are used in this build.",

  yourFarm: "Your farm",
  locationLabel: "Your local government area",
  locationHint: "Pick the LGA closest to your farm. One point represents the whole LGA.",
  rotationLabel: "Your current rotation",
  rotationHint: "Choose the crop you grow each year, in order. Add a third year if you rotate three crops.",
  yearLabel: "Year {n}",
  addYear: "Add a third year",
  removeYear: "Remove year {n}",
  remove: "Remove",
  cropLabel: "Crop for year {n}",

  prioritiesTitle: "What matters most to you?",
  prioritiesHint: "Move each slider from 1 (not important) to 5 (very important). The cards re-rank as you move them.",
  priority: {
    climate: "Reliable harvest",
    water: "Save water",
    soil: "Improve soil",
    erosion: "Reduce erosion",
    pests: "Fewer pests",
    income: "Earn income",
  },

  scenarioTitle: "Sensitivity test, not a forecast",
  scenarioHint: "Try less rain or more heat to see how the ranking reacts. These are what-if tests, not predictions.",
  rainLabel: "Rainfall",
  tempLabel: "Temperature",
  rainOptions: [
    { value: 0.8, label: "20% less" },
    { value: 0.9, label: "10% less" },
    { value: 1.0, label: "As observed" },
    { value: 1.1, label: "10% more" },
  ],
  tempOptions: [
    { value: 0, label: "No change" },
    { value: 1, label: "+1 °C" },
    { value: 2, label: "+2 °C" },
  ],

  mapTitle: "Gombe State at a glance",
  mapAria: "Map of Gombe State local government areas",
  mapHint: "Marker colour follows the best-fit strategy at each LGA. Select a marker to change the whole page.",
  mapTilesFailed: "Map tiles did not load, but the markers still show. You can still select an LGA.",
  mapPopupBest: "Best fit here: {name} ({label})",
  mapPopupSelect: "Show details for {name}",

  chartsTitle: "Season timing and greenness",
  onsetTitle: "When the rains start",
  onsetNote: "Each dot is one year.",
  onsetAxis: "Day of the year",
  onsetYearAxis: "Year",
  onsetMedian: "Median start: {date}",
  onsetMissing: "Season-start data is not available for this location.",
  onsetChartAria: "Scatter plot of rainfall onset day by year",
  ndviTitle: "Greenness through the year (NDVI)",
  ndviChartAria: "Line chart of average greenness across 36 ten-day periods",
  ndviAxis: "NDVI",
  ndviNote: "Each point is a 10-day period. Shaded periods look bare.",
  ndviMissing: "Greenness data not loaded for this build.",
  ndviDefaultShare: "The score uses a default bare-field share of 30%. Ask a local expert about your field.",
  ndviBare: "Shaded = bare (low greenness)",

  cardsTitle: "Strategies, best fit first",
  cardsHint: "Every card shows the same five things: why it was suggested, the evidence, benefits, information gaps, and risks needing local review.",
  existingName: "Your current rotation",
  existingBenefits: "A baseline you already know",
  existingGaps: "Soil condition and yield history on your farm",
  existingRisks: "If the same crop family repeats, pests and disease can build up",
  rankLabel: "Rank {n}",
  overallFit: "Overall fit",
  estimateTag: "estimate",
  provisionalNote: "Some crop inputs are estimates. Dry-spell and heat-day cutoffs are screening thresholds, not known biological limits; ask a local expert to review them.",
  whyTitle: "Why suggested",
  evidenceTitle: "Evidence",
  benefitsTitle: "Benefits",
  gapsTitle: "Information gaps",
  risksTitle: "Risks needing local review",
  askExpert: "Ask a local expert about: variety, soil type, local market, pests.",
  support: "This is a decision aid. Your experience and your extension officer's advice come first.",
  noEvidence: "No evidence is available for this crop in this scenario.",
  noOnset: "In {n} years the rains did not start reliably, so those seasons count as failures.",
  why: "Suggested because it scores well on {top1} and {top2}, but lower on {lowest}.",
  whyLowestFirst: "Suggested because it scores well on {top1}, but lower on {lowest}.",
  evidenceLine: "{crop}: in {ok} of {total} seasons, rainfall, dry spells and heat stayed within its screening thresholds.",
  evidenceNone: "{crop}: no seasons met all three limits in the years we could check.",
  sequenceThen: ", then ",
  scoreAria: "Overall fit {percent} percent. {label}.",
  criteriaAriaLabel: "Criteria scores",
  criteriaAria: "{label}: {percent} percent.",

  traffic: {
    strong: { label: "Strong fit", icon: "▲" },
    mixed: { label: "Mixed fit", icon: "◆" },
    weak: { label: "Weak fit", icon: "▼" },
  },

  scenarioMissingTitle: "This sensitivity case is missing",
  scenarioMissingBody: "The data file does not contain the scenario {key}. Choose another rainfall or temperature setting, or re-run the pipeline.",
  dataErrorTitle: "The data could not be loaded",
  dataErrorBody: "Check that the five JSON files exist in web/data and that the page is served by a local web server.",
  retry: "Try again",
  loading: "Loading data…",

  limitsTitle: "Data and limits",
  limitsIntro: "Read this before you use the ranking.",
  limitsSources: "Sources used: {sources}. Date range: {start} to {end}.",
  limitsResolution: "Resolution: results are for one point in each local government area and for 10-day periods. Satellite soil moisture is coarse (about 9 km or more) and cannot see a single field.",
  limitsSatellite: "Satellites versus ground data: satellites give a consistent long record almost everywhere but are estimates. Rain gauges and soil tests are more accurate locally. No ground stations were used in this tool. Ground validation would let us check the onset dates and the crop limits against real measurements.",
  limitsConfidence: "Confidence for this location: {label}. {reason}",
  limitsScenario: "The rainfall and temperature controls are sensitivity tests, not forecasts.",
  limitsProvisional: "Crop thresholds and scores are provisional until they are checked against IITA or FAO guidance and local experience.",
  limitsNdvi: "Greenness (NDVI) data is not loaded in this build, so the erosion score uses a default bare-field share of 30%.",
  limitsSecurity: "Parts of north-east Nigeria face security conditions that can limit access to farms. Local knowledge and safe access come before any recommendation here.",
  limitsSupport: "This is a decision aid. Your experience and your extension officer's advice come first.",
  limitsDataModeSynthetic: "This build is running on synthetic demo data. It must not be read as a statement about real weather.",
  limitsDataModeNasa: "This build uses real NASA POWER daily data for 2001 to 2024.",

  glossaryTitle: "Plain-language glossary",
  glossaryHint: "Tap a term to open its meaning.",
  glossaryDefinitions: "Plain-language definitions: ",
  glossaryLink: "Open the glossary entry for {term}",

  footer: "GonaSense · Built for the NASA Space Apps Challenge 2026. NASA POWER, geoBoundaries/GRID3, GADM. This tool supports, it does not replace, farmer judgment.",
  dataBadge: "{count} LGAs · {scenarios} sensitivity cases · {mode} data",
  modeSynthetic: "synthetic",
  modeNasa: "NASA",
  medianNone: "No reliable start found",
  dateUnknown: "not available",
  cropNames: {
    maize: "Maize",
    sorghum: "Sorghum",
    millet: "Millet",
    cowpea: "Cowpea",
    groundnut: "Groundnut",
  },
};

export function fill(template, values) {
  return template.replace(/\{(\w+)\}/g, (match, key) =>
    Object.prototype.hasOwnProperty.call(values, key) ? values[key] : match,
  );
}

export function formatDayOfYear(dayOfYear) {
  if (!Number.isFinite(dayOfYear)) return strings.dateUnknown;
  const date = new Date(Date.UTC(2001, 0, Math.round(dayOfYear)));
  return date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    timeZone: "UTC",
  });
}

export function formatPercent(value) {
  return `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%`;
}
