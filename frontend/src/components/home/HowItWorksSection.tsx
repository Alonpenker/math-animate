import { motion } from 'framer-motion';
import { Pencil, Brain, CheckCircle, Code, Play, BookOpen } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

interface Feature {
  icon: LucideIcon;
  title: string;
  description: string;
}

const FEATURES: Feature[] = [
  {
    icon: Pencil,
    title: 'Write Your Lesson Brief',
    description: 'Describe the topic, misconceptions, constraints, and examples in plain language.',
  },
  {
    icon: Brain,
    title: 'AI Plans Your Video',
    description: 'Our AI generates a structured scene-by-scene video plan for math learners.',
  },
  {
    icon: CheckCircle,
    title: 'You Stay in Control',
    description: 'Review the plan before rendering. Approve it or start fresh - your choice.',
  },
  {
    icon: Code,
    title: 'Code Is Generated',
    description: 'Manim animation code is automatically written and verified for your plan.',
  },
  {
    icon: Play,
    title: 'Videos Are Rendered',
    description: 'Each scene renders in an isolated container. No setup on your end.',
  },
  {
    icon: BookOpen,
    title: 'Watch and Share',
    description: 'Access all rendered lesson videos in the Lessons library, organized by topic.',
  },
];

export function HowItWorksSection() {
  return (
    <section className="pt-8 pb-20 px-6 relative overflow-hidden">
      <div className="mx-auto max-w-5xl" style={{ position: 'relative', zIndex: 1 }}>
        <motion.h2
          className="mb-4 text-center text-3xl md:text-4xl text-off-white"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          How It Works
        </motion.h2>
        <motion.p
          className="mb-12 text-center text-off-white/50 text-base"
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          Six steps from idea to video
        </motion.p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {FEATURES.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.08 }}
            >
              <Card className="border-border h-full" style={{ background: '#221a12' }}>
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold bg-off-white/10 text-off-white">
                      {i + 1}
                    </span>
                    <feature.icon className="h-6 w-6 text-off-white/70" />
                  </div>
                  <h3 className="mb-2 text-xl font-bold text-off-white">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-off-white/60 leading-relaxed">
                    {feature.description}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
