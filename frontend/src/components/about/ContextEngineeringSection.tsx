interface ContextCard {
  title: string;
  stage: string;
  description: string;
}

const CARDS: ContextCard[] = [
  {
    title: "System Prompts",
    stage: "all LLM stages",
    description:
      "Four stage-specific prompts (plan, code-plan, codegen, fix) that define the model's role, output format, and constraints.",
  },
  {
    title: "Manim Skill & Rules",
    stage: "code-plan, codegen, fix",
    description:
      "Core reference for SafeScene structure, layout composition, and animation patterns. Loaded at every code stage to keep output consistent with the project's conventions.",
  },
  {
    title: "Visual Kit API",
    stage: "code-plan, codegen, fix",
    description:
      "The complete SafeScene helper contract: every layout utility, animation helper, and template hook the model can call.",
  },
  {
    title: "Scene Templates",
    stage: "code-plan, codegen, fix",
    description:
      "Reusable VisualTemplate subclasses (number lines, fraction models, coordinate planes) retrieved when the plan calls for a matching visual type.",
  },
];

export function ContextEngineeringSection() {
  return (
    <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
      {CARDS.map((card) => (
        <div
          key={card.title}
          className="rounded-lg border border-border bg-[#221a12] p-5"
        >
          <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
            <h3 className="text-base font-semibold text-off-white">{card.title}</h3>
            <span className="text-xs text-off-white/50 border border-border rounded-full px-2 py-0.5 bg-off-white/5 whitespace-nowrap">
              {card.stage}
            </span>
          </div>
          <p className="text-sm text-off-white/60 leading-relaxed">{card.description}</p>
        </div>
      ))}
    </div>
  );
}
