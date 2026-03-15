import { motion, useInView, type Transition } from 'framer-motion';
import { useRef } from 'react';

type MotionSpanInitial = React.ComponentProps<typeof motion.span>['initial'];
type MotionSpanAnimate = React.ComponentProps<typeof motion.span>['animate'];

interface SplitTextProps {
  text: string;
  className?: string;
  delay?: number;
  duration?: number;
  ease?: Transition['ease'];
  splitType?: 'words' | 'chars';
  from?: Record<string, unknown>;
  to?: Record<string, unknown>;
  threshold?: number;
  rootMargin?: string;
  textAlign?: 'left' | 'center' | 'right';
  onLetterAnimationComplete?: () => void;
}

export function SplitText({
  text,
  className = '',
  delay = 100,
  duration = 0.6,
  ease = 'easeOut',
  splitType = 'words',
  from = { opacity: 0, y: 40 },
  to = { opacity: 1, y: 0 },
  rootMargin = '-100px',
  textAlign = 'center',
  onLetterAnimationComplete,
}: SplitTextProps) {
  const ref = useRef<HTMLParagraphElement>(null);
  const isInView = useInView(ref, {
    once: true,
    margin: rootMargin as `${number}px`,
  });

  const items = splitType === 'chars' ? text.split('') : text.split(' ');

  return (
    <p
      ref={ref}
      className={className}
      style={{ textAlign, overflow: 'hidden' }}
    >
      {items.map((item, i) => (
        <motion.span
          key={i}
          initial={from as MotionSpanInitial}
          animate={(isInView ? to : from) as MotionSpanAnimate}
          transition={{
            duration,
            delay: i * (delay / 1000),
            ease,
          }}
          onAnimationComplete={
            i === items.length - 1 ? onLetterAnimationComplete : undefined
          }
          style={{
            display: 'inline-block',
            marginRight: splitType === 'words' ? '0.25em' : '0',
          }}
        >
          {item}
        </motion.span>
      ))}
    </p>
  );
}
