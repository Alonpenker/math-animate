import { useNavigate } from 'react-router-dom';
import { motion, } from 'framer-motion';
import { AuroraText } from '@/components/ui/AuroraText';
import Threads from '@/components/ui/Threads';

const HEADING_WORDS = ['Turn', 'Lesson', 'Ideas', 'Into', 'Animated', 'Math', 'Videos'];
const AURORA_WORD = 'Animated';
const ANIMATED_WORD_COLORS = [
  '#F5F0E8',
  '#F5F0E8',
  '#F4C8A5',
  '#E8924A',
  '#E8924A',
  '#F4C8A5',
  '#F5F0E8',
];

export function HeroSection() {
  const navigate = useNavigate();

  return (
    <section className="relative flex flex-col items-center justify-start overflow-hidden px-6 pt-16 pb-20">
      <div className="pointer-events-none absolute inset-0 translate-y-2 opacity-45">
        <Threads
          color={[0.91, 0.57, 0.29]}
          amplitude={0.55}
          distance={0.18}
          enableMouseInteraction={false}
        />
      </div>

      <div className="relative z-10 mx-auto max-w-5xl w-full flex flex-col items-center">
        <p
          className="m-0 -translate-y-8 text-center text-6xl leading-tight text-off-white md:text-8xl"
          style={{ overflow: 'hidden' }}
        >
          {HEADING_WORDS.map((word, i) => (
            <motion.span
              key={word}
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: i * 0.08, ease: 'easeOut' }}
              style={{ display: 'inline-block', marginRight: '0.25em' }}
            >
              {word === AURORA_WORD ? (
                <AuroraText colors={ANIMATED_WORD_COLORS} speed={10}>
                  {word}
                </AuroraText>
              ) : (
                word
              )}
            </motion.span>
          ))}
        </p>

        <motion.p
          className="mt-20 max-w-2xl text-center text-lg leading-relaxed text-off-white/60 md:text-xl"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.6 }}
        >
          Describe your topic. Let AI plan and render the lesson.<br></br>Watch it come to life in minutes.
        </motion.p>

        <motion.button
          onClick={() => navigate('/create')}
          className="mt-10 flex h-12 cursor-pointer items-center justify-center rounded-full border border-accent-orange bg-accent-orange px-7 text-base font-medium text-white transition-[background-color,border-color,transform,box-shadow] duration-150 ease-in-out hover:border-accent-orange/80 hover:bg-accent-orange/90 hover:shadow-[0_4px_18px_rgba(232,146,74,0.22)] active:scale-[0.98]"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2, duration: 0.6 }}
        >
          Try It Now
        </motion.button>
      </div>
    </section>
  );
}
