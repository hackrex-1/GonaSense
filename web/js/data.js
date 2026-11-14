/* Load every JSON contract once. No network request happens after init(). */

const FILES = ["locations", "crops", "strategies", "metrics", "glossary"];

export async function loadData(base = "./data") {
  const entries = await Promise.all(
    FILES.map(async (name) => {
      const response = await fetch(`${base}/${name}.json`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`Could not load ${name}.json (HTTP ${response.status})`);
      }
      return [name, await response.json()];
    }),
  );
  return Object.fromEntries(entries);
}
