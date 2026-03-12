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

export function ChalkCircleIllustration() {
  return (
    <motion.svg
      viewBox="0 0 280 260"
      className="w-full max-w-xs"
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: '-60px' }}
      style={{ filter: 'drop-shadow(0 0 8px rgba(245,240,232,0.1))' }}
    >
      {/* Circle */}
      <motion.circle
        cx="130" cy="135" r="80"
        fill="none"
        stroke="#F5F0E8"
        strokeWidth="2.5"
        strokeLinecap="round"
        variants={draw}
        custom={0}
      />

      {/* Radius line */}
      <motion.line
        x1="130" y1="135" x2="210" y2="135"
        stroke="#7EC8C8"
        strokeWidth="2.5"
        strokeLinecap="round"
        variants={draw}
        custom={1}
      />

      {/* Center dot */}
      <motion.circle cx="130" cy="135" r="4" fill="#F5F0E8" variants={fadeIn(0.6)} />

      {/* Endpoint dot */}
      <motion.circle cx="210" cy="135" r="4" fill="#7EC8C8" variants={fadeIn(1.2)} />

      {/* Radius label */}
      <motion.text x="166" y="125" textAnchor="middle"
        fill="#7EC8C8" fontSize="14" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(1.5)}>r</motion.text>

      {/* Formula */}
      <motion.text x="130" y="50" textAnchor="middle"
        fill="#F5F0E8" fontSize="18" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(2.0)}>A = π · r²</motion.text>

      {/* Small tick at center label */}
      <motion.text x="130" y="152" textAnchor="middle"
        fill="#F5D76E" fontSize="12" fontFamily="Patrick Hand, cursive"
        variants={fadeIn(1.8)}>O</motion.text>
    </motion.svg>
  );
}
