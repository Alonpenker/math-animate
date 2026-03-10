import {
  Pencil, Brain, CheckCircle, Code, Play, BookOpen,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface Feature {
  icon: LucideIcon;
  title: string;
  description: string;
}

const FEATURES: Feature[] = [
  {
    icon: Pencil,
    title: 'Write Your Lesson Brief',
    description: 'Describe the topic, common misconceptions, constraints, and examples in plain language.',
  },
  {
    icon: Brain,
    title: 'AI Plans Your Video',
    description: 'Our AI generates a structured scene-by-scene video plan tailored to 8th-grade learners.',
  },
  {
    icon: CheckCircle,
    title: 'You Stay in Control',
    description: 'Review the plan before anything is rendered. Approve it or start fresh — your choice.',
  },
  {
    icon: Code,
    title: 'Code Is Generated',
    description: 'Manim animation code is automatically written and verified for your approved plan.',
  },
  {
    icon: Play,
    title: 'Videos Are Rendered',
    description: 'Each scene renders in an isolated container. No environment setup on your end.',
  },
  {
    icon: BookOpen,
    title: 'Watch and Share',
    description: 'Access all your rendered lesson videos in the Lessons library, organized by topic.',
  },
];

export function FeatureBlocks() {
  return (
    <section className="bg-white px-4 py-16">
      <div className="mx-auto max-w-5xl">
        <h2 className="mb-10 text-center text-2xl font-bold text-brand-text md:text-3xl">
          How It Works
        </h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="rounded-lg border border-brand-border p-6 transition-shadow hover:shadow-md"
            >
              <feature.icon className="mb-3 h-8 w-8 text-brand-light" />
              <h3 className="mb-2 text-lg font-semibold text-brand-text">
                {feature.title}
              </h3>
              <p className="text-sm leading-relaxed text-brand-muted">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
