import { motion } from 'framer-motion';

const draw = {
  hidden: { pathLength: 0, opacity: 0 },
  visible: (i: number) => ({
    pathLength: 1,
    opacity: 1,
    transition: {
      pathLength: { delay: i * 0.3, type: 'spring' as const, duration: 1.5, bounce: 0 },
      opacity: { delay: i * 0.3, duration: 0.2 },
    },
  }),
};

const fadeIn = (delay: number) => ({
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { delay, duration: 0.5 } },
});

export function ChalkMathIllustration() {
  return (
    <motion.svg
      viewBox="0 0 320 280"
      className="w-full max-w-sm"
      initial="hidden"
      animate="visible"
      style={{ filter: 'drop-shadow(0 0 8px rgba(245,240,232,0.1))' }}
    >
      {/* Triangle - Base */}
      <motion.line x1="40" y1="220" x2="240" y2="220"
        stroke="#F5F0E8" strokeWidth="2.5" strokeLinecap="round"
        variants={draw} custom={0} />
      {/* Triangle - Vertical side */}
      <motion.line x1="240" y1="220" x2="240" y2="60"
        stroke="#F5F0E8" strokeWidth="2.5" strokeLinecap="round"
        variants={draw} custom={1} />
      {/* Triangle - Hypotenuse */}
      <motion.line x1="40" y1="220" x2="240" y2="60"
        stroke="#7EC8C8" strokeWidth="2.5" strokeLinecap="round"
        variants={draw} custom={2} />

      {/* Right angle mark */}
      <motion.path d="M 225 220 L 225 205 L 240 205"
        fill="none" stroke="#F5F0E8" strokeWidth="1.5" strokeLinecap="round"
        variants={draw} custom={3} />

      {/* Labels */}
      <motion.text x="130" y="242" textAnchor="middle"
        fill="#F5D76E" fontSize="14" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(1.5)}>a</motion.text>
      <motion.text x="255" y="145" textAnchor="start"
        fill="#F5D76E" fontSize="14" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(1.8)}>b</motion.text>
      <motion.text x="128" y="128" textAnchor="end"
        fill="#7EC8C8" fontSize="14" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(2.1)}>c</motion.text>

      {/* Equation */}
      <motion.text x="30" y="48" textAnchor="start"
        fill="#F5F0E8" fontSize="18" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(2.5)}>
        a² + b² = c²
      </motion.text>

      {/* Small decorative dots */}
      <motion.circle cx="40" cy="220" r="3.5" fill="#F5F0E8" variants={fadeIn(0.3)} />
      <motion.circle cx="240" cy="220" r="3.5" fill="#F5F0E8" variants={fadeIn(0.9)} />
      <motion.circle cx="240" cy="60" r="3.5" fill="#F5F0E8" variants={fadeIn(1.5)} />
    </motion.svg>
  );
}
