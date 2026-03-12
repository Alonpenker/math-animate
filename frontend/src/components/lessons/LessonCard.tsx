import { motion } from 'framer-motion';
import { formatDate } from '@/utils/formatters';
import type { JobListItem } from '@/services/api';

interface LessonCardProps {
  job: JobListItem;
  onClick: () => void;
}

const STICKY_COLORS = [
  '#FFF9C4', // pale yellow
  '#FFECB3', // warm yellow
  '#B3E5FC', // light blue
  '#BBDEFB', // sky blue
  '#C8E6C9', // mint green
  '#DCEDC8', // lime green
  '#F8BBD9', // pink
  '#F0BBE4', // lavender pink
  '#FFE0B2', // peach
  '#E1BEE7', // light purple
  '#D1C4E9', // soft violet
  '#FFCCBC', // salmon
];

/**
 * Deterministic pseudo-random number from a string seed.
 * Returns a float in [0, 1).
 */
function seededRandom(seed: string): number {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    const char = seed.charCodeAt(i);
    hash = ((hash << 5) - hash + char) | 0;
  }
  // Use a second pass for better distribution
  hash = Math.abs(hash ^ (hash >>> 16));
  return (hash % 10000) / 10000;
}

/**
 * Returns a deterministic rotation in the range [-10, +10] degrees.
 */
function getRotation(jobId: string): string {
  const rand = seededRandom(jobId + '_rot');
  const angle = rand * 6 - 3; // range: -10 to +10
  return `${angle.toFixed(1)}deg`;
}

/**
 * Returns a deterministic color from the STICKY_COLORS palette.
 */
function getColor(jobId: string): string {
  const rand = seededRandom(jobId + '_col');
  const index = Math.floor(rand * STICKY_COLORS.length);
  return STICKY_COLORS[index];
}

export function LessonCard({ job, onClick }: LessonCardProps) {
  const bgColor = getColor(job.job_id);
  const rotate = getRotation(job.job_id);

  return (
    <motion.button
      type="button"
      onClick={onClick}
      className="w-full rounded-sm p-5 text-left"
      style={{
        background: bgColor,
        boxShadow: '2px 4px 12px rgba(0,0,0,0.15)',
        border: '1px solid rgba(0,0,0,0.06)',
        cursor: 'pointer',
        rotate,
      }}
      whileHover={{ rotate: '0deg', scale: 1.03 }}
      transition={{ duration: 0.15 }}
    >
      <h3
        className="text-base text-board-dark line-clamp-2 font-bold"
        style={{ fontFamily: 'Patrick Hand, cursive' }}
      >
        {job.topic}
      </h3>
      <div className="mt-4 flex items-end justify-between">
        <span className="text-xs text-board-dark/50" style={{ fontFamily: 'Inter, sans-serif' }}>
          {formatDate(job.updated_at)}
        </span>
        <span className="text-xs text-board-dark/50" style={{ fontFamily: 'Inter, sans-serif' }}>
          {job.number_of_scenes} scene{job.number_of_scenes !== 1 ? 's' : ''}
        </span>
      </div>
    </motion.button>
  );
}
