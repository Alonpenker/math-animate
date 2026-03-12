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

export function ChalkSineWaveIllustration() {
  return (
    <motion.svg
      viewBox="0 0 300 260"
      className="w-full max-w-sm"
      initial="hidden"
      animate="visible"
      style={{ filter: 'drop-shadow(0 0 8px rgba(245,240,232,0.1))' }}
    >
      {/* X axis */}
      <motion.line
        x1="30" y1="140" x2="270" y2="140"
        stroke="#F5F0E8" strokeWidth="2" strokeLinecap="round"
        variants={draw} custom={0}
      />
      {/* Y axis */}
      <motion.line
        x1="30" y1="40" x2="30" y2="230"
        stroke="#F5F0E8" strokeWidth="2" strokeLinecap="round"
        variants={draw} custom={0.5}
      />

      {/* Sine wave */}
      <motion.path
        d="M 30 140 C 60 140, 70 60, 90 60 C 110 60, 120 140, 150 140 C 180 140, 190 220, 210 220 C 230 220, 240 140, 270 140"
        fill="none"
        stroke="#7EC8C8"
        strokeWidth="2.5"
        strokeLinecap="round"
        variants={draw}
        custom={1}
      />

      {/* Pi labels on x-axis */}
      <motion.text x="150" y="158" textAnchor="middle"
        fill="#F5D76E" fontSize="13" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(1.8)}>&#960;</motion.text>
      <motion.text x="270" y="158" textAnchor="middle"
        fill="#F5D76E" fontSize="13" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(2.0)}>2&#960;</motion.text>

      {/* Axis labels */}
      <motion.text x="22" y="35" textAnchor="middle"
        fill="#F5F0E8" fontSize="12" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(1.5)}>y</motion.text>
      <motion.text x="278" y="135" textAnchor="start"
        fill="#F5F0E8" fontSize="12" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(1.5)}>x</motion.text>

      {/* Equation */}
      <motion.text x="80" y="35" textAnchor="start"
        fill="#F5F0E8" fontSize="18" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(2.3)}>
        f(x) = sin(x)
      </motion.text>

      {/* Amplitude markers */}
      <motion.line
        x1="26" y1="60" x2="34" y2="60"
        stroke="#F5F0E8" strokeWidth="1.5" strokeLinecap="round"
        variants={draw} custom={2}
      />
      <motion.text x="20" y="64" textAnchor="end"
        fill="#F5D76E" fontSize="11" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(2.1)}>1</motion.text>

      <motion.line
        x1="26" y1="220" x2="34" y2="220"
        stroke="#F5F0E8" strokeWidth="1.5" strokeLinecap="round"
        variants={draw} custom={2.2}
      />
      <motion.text x="18" y="224" textAnchor="end"
        fill="#F5D76E" fontSize="11" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(2.3)}>-1</motion.text>

      {/* Decorative dots at key points */}
      <motion.circle cx="30" cy="140" r="3" fill="#F5F0E8" variants={fadeIn(0.3)} />
      <motion.circle cx="90" cy="60" r="3" fill="#E8924A" variants={fadeIn(1.5)} />
      <motion.circle cx="210" cy="220" r="3" fill="#E8924A" variants={fadeIn(2.0)} />
    </motion.svg>
  );
}
