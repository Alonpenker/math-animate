import { motion } from 'framer-motion';
import { Pencil, Brain, CheckCircle, Code, Play, BookOpen } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { ChalkCircleIllustration } from '@/components/chalk/ChalkCircleIllustration';
import { ChalkLinearFunctionIllustration } from '@/components/chalk/ChalkLinearFunctionIllustration';

interface Feature {
  icon: LucideIcon;
  title: string;
  description: string;
  rotate: string;
  bgColor: string;
}

const FEATURES: Feature[] = [
  {
    icon: Pencil,
    title: 'Write Your Lesson Brief',
    description: 'Describe the topic, misconceptions, constraints, and examples in plain language.',
    rotate: '-1.5deg',
    bgColor: '#FFF9C4',
  },
  {
    icon: Brain,
    title: 'AI Plans Your Video',
    description: 'Our AI generates a structured scene-by-scene video plan for 8th-grade learners.',
    rotate: '1deg',
    bgColor: '#B3E5FC',
  },
  {
    icon: CheckCircle,
    title: 'You Stay in Control',
    description: 'Review the plan before rendering. Approve it or start fresh — your choice.',
    rotate: '-0.8deg',
    bgColor: '#C8E6C9',
  },
  {
    icon: Code,
    title: 'Code Is Generated',
    description: 'Manim animation code is automatically written and verified for your plan.',
    rotate: '1.5deg',
    bgColor: '#FFE0B2',
  },
  {
    icon: Play,
    title: 'Videos Are Rendered',
    description: 'Each scene renders in an isolated container. No setup on your end.',
    rotate: '-1deg',
    bgColor: '#F8BBD9',
  },
  {
    icon: BookOpen,
    title: 'Watch and Share',
    description: 'Access all rendered lesson videos in the Lessons library, organized by topic.',
    rotate: '1.2deg',
    bgColor: '#FFF9C4',
  },
];

export function HowItWorksSection() {
  return (
    <section className="pt-8 pb-20 px-6 relative overflow-hidden">
      {/* Background math illustrations*/}
      <motion.div
        style={{ position: 'absolute', left: '2%', bottom: '50%', width: '42rem', pointerEvents: 'none', zIndex: 0 }}
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 0.2 }}
        viewport={{ once: true, margin: '-80px' }}
        transition={{ duration: 1.0 }}
      >
        <ChalkCircleIllustration />
      </motion.div>
      <motion.div
        style={{ position: 'absolute', right: '-15%', bottom: '2%', width: '42rem', pointerEvents: 'none', zIndex: 0 }}
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 0.2 }}
        viewport={{ once: true, margin: '-80px' }}
        transition={{ duration: 1.0, delay: 0.3 }}
      >
        <ChalkLinearFunctionIllustration />
      </motion.div>

      <div className="mx-auto max-w-5xl" style={{ position: 'relative', zIndex: 1 }}>
        <motion.h2
          className="mb-4 text-center text-3xl md:text-4xl text-chalk-white"
          style={{ fontFamily: 'Patrick Hand, cursive' }}
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          How It Works
        </motion.h2>
        <motion.p
          className="mb-12 text-center text-chalk-white/50 text-base"
          style={{ fontFamily: 'Inter, sans-serif' }}
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
              className="rounded-sm p-6 shadow-md h-full cursor-default"
              style={{
                background: feature.bgColor,
                border: '1px solid rgba(0,0,0,0.06)',
                rotate: feature.rotate,
              }}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.08 }}
              whileHover={{
                rotate: 0,
                scale: 1.06,
                boxShadow: '0 8px 32px rgba(0,0,0,0.22), 0 2px 8px rgba(0,0,0,0.10)',
                transition: { type: 'spring', stiffness: 300, damping: 20 },
              }}
            >
                <div className="flex items-center gap-3 mb-3">
                  <span
                    className="flex h-8 w-8 items-center justify-center rounded-full text-sm font-bold"
                    style={{
                      background: 'rgba(26,35,38,0.1)',
                      color: '#1A2326',
                      fontFamily: 'Patrick Hand, cursive',
                    }}
                  >
                    {i + 1}
                  </span>
                  <feature.icon className="h-6 w-6" style={{ color: '#1A2326', opacity: 0.7 }} />
                </div>
                <h3
                  className="mb-2 text-xl font-bold text-board-dark"
                  style={{ fontFamily: 'Patrick Hand, cursive' }}
                >
                  {feature.title}
                </h3>
                <p
                  className="text-sm text-board-dark/80 leading-relaxed"
                  style={{ fontFamily: 'Inter, sans-serif' }}
                >
                  {feature.description}
                </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
