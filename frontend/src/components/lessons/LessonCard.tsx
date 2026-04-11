import { motion } from 'framer-motion';
import { formatDate } from '@/utils/formatters';
import type { JobListItem } from '@/services/api';

interface LessonCardProps {
  job: JobListItem;
  onClick: () => void;
}

export function LessonCard({ job, onClick }: LessonCardProps) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      className="w-full border border-border rounded-lg p-5 text-left cursor-pointer transition-colors hover:border-accent-orange/40"
      style={{ background: '#221a12' }}
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.15 }}
    >
      <h3 className="text-base text-off-white line-clamp-2 font-bold">
        {job.topic}
      </h3>
      <div className="mt-4 flex items-end justify-between">
        <span className="text-xs text-off-white/50">
          {formatDate(job.updated_at)}
        </span>
        <span className="text-xs text-off-white/50">
          {job.number_of_scenes} scene{job.number_of_scenes !== 1 ? 's' : ''}
        </span>
      </div>
    </motion.button>
  );
}
