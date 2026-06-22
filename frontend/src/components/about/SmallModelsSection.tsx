const COMPARISON = [
  {
    col: "One large model, many retries",
    rows: [
      "Generic prompt",
      "No domain knowledge",
      "Fails → retry with same context",
      "Expensive + slow",
    ],
  },
  {
    col: "Small specialized models, one structured pass",
    rows: [
      "Stage-specific system prompt per step",
      "10–15 curated documents loaded per job",
      "Verify → fix loop capped at 2 iterations",
      "Fast + cost-efficient",
    ],
  },
];

export function SmallModelsSection() {
  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {COMPARISON.map((col, ci) => (
          <div
            key={col.col}
            className={`rounded-lg border p-5 space-y-3 ${
              ci === 0
                ? "border-border bg-[#1a1a1a]"
                : "border-off-white/20 bg-[#221a12]"
            }`}
          >
            <h3 className={`text-sm font-semibold ${ci === 0 ? "text-off-white/50" : "text-off-white"}`}>
              {col.col}
            </h3>
            <ul className="space-y-2">
              {col.rows.map((row) => (
                <li key={row} className="flex items-start gap-2 text-sm text-off-white/70">
                  <span className={`mt-0.5 shrink-0 ${ci === 0 ? "text-off-white/30" : "text-accent-orange"}`}>
                    {ci === 0 ? "–" : "✓"}
                  </span>
                  {row}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
