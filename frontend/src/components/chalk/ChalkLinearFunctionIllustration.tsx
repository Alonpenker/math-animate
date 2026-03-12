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

export function ChalkLinearFunctionIllustration() {
  return (
    <motion.svg
      viewBox="0 0 300 260"
      className="w-full max-w-xs"
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: '-60px' }}
      style={{ filter: 'drop-shadow(0 0 8px rgba(245,240,232,0.1))' }}
    >
      {/* X axis */}
      <motion.line
        x1="30" y1="190" x2="270" y2="190"
        stroke="#F5F0E8" strokeWidth="2" strokeLinecap="round"
        variants={draw} custom={0}
      />
      {/* Y axis */}
      <motion.line
        x1="70" y1="30" x2="70" y2="220"
        stroke="#F5F0E8" strokeWidth="2" strokeLinecap="round"
        variants={draw} custom={0.5}
      />

      {/* Linear function line: y = 2x - 1, mapped to SVG coords */}
      {/* At x=70 (origin) y=190, going up-right */}
      <motion.line
        x1="30" y1="215" x2="260" y2="65"
        stroke="#7EC8C8" strokeWidth="2.5" strokeLinecap="round"
        variants={draw} custom={1}
      />

      {/* Rise/run triangle for slope illustration */}
      {/* Horizontal run */}
      <motion.line
        x1="120" y1="165" x2="200" y2="165"
        stroke="#E8924A" strokeWidth="1.8" strokeLinecap="round"
        strokeDasharray="4 3"
        variants={draw} custom={2}
      />
      {/* Vertical rise */}
      <motion.line
        x1="200" y1="165" x2="200" y2="113"
        stroke="#F5D76E" strokeWidth="1.8" strokeLinecap="round"
        strokeDasharray="4 3"
        variants={draw} custom={2.3}
      />

      {/* Run label */}
      <motion.text x="160" y="180" textAnchor="middle"
        fill="#E8924A" fontSize="12" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(2.0)}>run</motion.text>

      {/* Rise label */}
      <motion.text x="216" y="142" textAnchor="start"
        fill="#F5D76E" fontSize="12" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(2.3)}>rise</motion.text>

      {/* Axis labels */}
      <motion.text x="62" y="26" textAnchor="middle"
        fill="#F5F0E8" fontSize="12" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(1.5)}>y</motion.text>
      <motion.text x="276" y="186" textAnchor="start"
        fill="#F5F0E8" fontSize="12" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(1.5)}>x</motion.text>

      {/* Slope formula */}
      <motion.text x="80" y="55" textAnchor="start"
        fill="#F5F0E8" fontSize="17" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(2.6)}>m = rise / run</motion.text>

      {/* Dots on line */}
      <motion.circle cx="120" cy="165" r="3.5" fill="#F5F0E8" variants={fadeIn(1.8)} />
      <motion.circle cx="200" cy="113" r="3.5" fill="#F5F0E8" variants={fadeIn(2.4)} />
    </motion.svg>
  );
}
