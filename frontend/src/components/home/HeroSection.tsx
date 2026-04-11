import { useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, useInView } from 'framer-motion';
import { AuroraText } from '@/components/ui/AuroraText';

const HEADING_WORDS = ['Turn', 'Lesson', 'Ideas', 'Into', 'Animated', 'Math', 'Videos'];
const AURORA_WORD = 'Animated';

export function HeroSection() {
  const navigate = useNavigate();
  const headingRef = useRef<HTMLParagraphElement>(null);
  const isInView = useInView(headingRef, { once: true, margin: '-100px' });

  return (
    <section className="relative flex flex-col items-center justify-start px-6 pt-28 pb-24 overflow-hidden">
      <div className="mx-auto max-w-5xl w-full flex flex-col items-center">
        <p
          ref={headingRef}
          className="text-6xl md:text-8xl leading-tight text-off-white m-0 text-center"
          style={{ overflow: 'hidden' }}
        >
          {HEADING_WORDS.map((word, i) => (
            <motion.span
              key={word}
              initial={{ opacity: 0, y: 50 }}
              animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 50 }}
              transition={{ duration: 0.7, delay: i * 0.08, ease: 'easeOut' }}
              style={{ display: 'inline-block', marginRight: '0.25em' }}
            >
              {word === AURORA_WORD ? <AuroraText speed={10}>{word}</AuroraText> : word}
            </motion.span>
          ))}
        </p>

        <motion.p
          className="mt-8 text-lg md:text-xl text-off-white/60 leading-relaxed text-center max-w-2xl"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.6 }}
        >
          Describe your topic. Let AI plan and render the lesson. Watch it come to life in minutes.
        </motion.p>

        <motion.button
          onClick={() => navigate('/create')}
          className="mt-12 rounded-full border-2 border-accent-orange bg-accent-orange text-white px-12 py-4 text-xl transition-all hover:bg-accent-orange/80 hover:border-accent-orange/80 cursor-pointer"
          whileHover={{ scale: 1.06 }}
          whileTap={{ scale: 0.97 }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2, duration: 0.5 }}
        >
          Try It Now
        </motion.button>
      </div>
    </section>
  );
}
