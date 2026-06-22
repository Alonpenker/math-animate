interface PipelineNode {
  id: string;
  label: string;
  model?: string;
}

const NODES: PipelineNode[] = [
  { id: "request",            label: "Teacher Request",       model: "You" },
  { id: "generate_plan",      label: "generate_plan",         model: "owl-alpha" },
  { id: "load_knowledge",     label: "load_static_knowledge", model: "RAG + embeddings" },
  { id: "generate_code_plan", label: "generate_code_plan",    model: "owl-alpha" },
  { id: "generate_code",      label: "generate_code",         model: "gpt-oss-120b" },
  { id: "verify",             label: "verify",                model: "Python runtime" },
  { id: "fix_code",           label: "fix_code",              model: "owl-alpha" },
  { id: "render",             label: "render",                model: "Manim (Docker)" },
];


function NodeCard({ node }: { node: PipelineNode }) {
  const isUser = node.id === "request";
  return (
    <div className={`rounded-lg border px-3 py-2.5 text-center ${
      isUser ? "border-accent-orange/50 bg-accent-orange/8" : "border-border bg-[#221a12]"
    }`}>
      <div className="text-xs font-semibold text-off-white leading-tight">{node.label}</div>
      {node.model && (
        <div className="mt-0.5 text-[10px] text-off-white/35 leading-tight">{node.model}</div>
      )}
    </div>
  );
}

function HArrow({ dir }: { dir: "right" | "left" }) {
  return (
    <div className="flex items-center justify-center px-1 text-off-white/25 text-sm select-none">
      {dir === "right" ? "→" : "←"}
    </div>
  );
}

export function WorkflowDataFlow() {
  return (
    <div className="mt-6 relative">
      <div className="overflow-x-auto">
      <div
        className="min-w-140"
        style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr auto 1fr auto 1fr" }}
      >
        <NodeCard node={NODES[0]} />
        <HArrow dir="right" />
        <NodeCard node={NODES[1]} />
        <HArrow dir="right" />
        <NodeCard node={NODES[2]} />
        <HArrow dir="right" />
        <NodeCard node={NODES[3]} />

        <div className="col-span-6" />
        <div className="flex flex-col items-center py-0.5">
          <div className="w-px h-3 bg-off-white/20" />
          <svg width="8" height="5" viewBox="0 0 8 5" fill="currentColor" className="text-off-white/25">
            <path d="M4 5L0 0h8z" />
          </svg>
        </div>

        <NodeCard node={NODES[7]} />
        <HArrow dir="left" />

        <div
          className="col-span-3 rounded-lg border border-off-white/15 bg-[#271d12] px-4 py-2.5 flex items-center justify-center gap-3"
        >
          <div className="text-center">
            <div className="text-xs font-semibold text-off-white">{NODES[5].label}</div>
            <div className="text-[10px] text-off-white/35">{NODES[5].model}</div>
          </div>

          <div className="flex flex-col items-center gap-1 shrink-0">
            <span className="text-xs text-off-white/35">{"<->"}</span>
            <span className="text-[10px] leading-tight text-accent-orange/70 border border-accent-orange/30 rounded px-1">
              max 2×
            </span>
          </div>

          <div className="text-center">
            <div className="text-xs font-semibold text-off-white">{NODES[6].label}</div>
            <div className="text-[10px] text-off-white/35">{NODES[6].model}</div>
          </div>
        </div>

        <HArrow dir="left" />
        <NodeCard node={NODES[4]} />
      </div>
      </div>
      <p className="mt-2 text-right text-[10px] text-off-white/25 sm:hidden">scroll →</p>
    </div>
  );
}
