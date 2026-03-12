import { useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, useInView } from 'framer-motion';
import { AuroraText } from '@/components/ui/AuroraText';
import { ChalkMathIllustration } from '@/components/chalk/ChalkMathIllustration';
import { ChalkSineWaveIllustration } from '@/components/chalk/ChalkSineWaveIllustration';

const HEADING_WORDS = ['Turn', 'Lesson', 'Ideas', 'Into', 'Animated', 'Math', 'Videos'];
const AURORA_WORD = 'Animated';

export function HeroSection() {
  const navigate = useNavigate();
  const headingRef = useRef<HTMLParagraphElement>(null);
  const isInView = useInView(headingRef, { once: true, margin: '-100px' });

  return (
    <section className="relative min-h-screen flex flex-col items-center justify-start px-6 pt-24 pb-20 overflow-hidden">
      {/* Sine wave illustration */}
      <motion.div
        className="absolute left-8 hidden lg:block"
        style={{ width: 320, opacity: 0.18, pointerEvents: 'none', top: '40%', transform: 'translateY(-50%)' }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.18 }}
        transition={{ delay: 1.0, duration: 1.2 }}
      >
        <ChalkSineWaveIllustration />
      </motion.div>

      {/* Pythagorean illustration */}
      <motion.div
        className="absolute right-8 top-1/2 -translate-y-1/2 hidden lg:block"
        style={{ width: 340, opacity: 0.18, pointerEvents: 'none' }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.18 }}
        transition={{ delay: 1.0, duration: 1.2 }}
      >
        <ChalkMathIllustration />
      </motion.div>

      <div className="mx-auto max-w-5xl w-full flex flex-col items-center">
        <p
          ref={headingRef}
          className="text-6xl md:text-8xl leading-tight text-chalk-white m-0 text-center"
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
          className="mt-8 text-lg md:text-xl text-chalk-white/60 leading-relaxed text-center max-w-2xl"
          style={{ fontFamily: 'Inter, sans-serif' }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.6 }}
        >
          Describe your topic. Let AI plan and render the lesson. Watch it come to life in minutes.
        </motion.p>

        <motion.button
          onClick={() => navigate('/create')}
          className="mt-12 rounded-full border-2 border-chalk-orange bg-chalk-orange text-white px-12 py-4 text-xl transition-all hover:bg-chalk-orange/80 hover:border-chalk-orange/80 cursor-pointer"
          style={{ fontFamily: 'Patrick Hand, cursive' }}
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
