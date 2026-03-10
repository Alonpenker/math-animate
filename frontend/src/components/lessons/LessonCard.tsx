import { formatDate } from '@/utils/formatters';
import type { JobListItem } from '@/services/api';

interface LessonCardProps {
  job: JobListItem;
  onClick: () => void;
}

export function LessonCard({ job, onClick }: LessonCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-lg border border-brand-border p-5 text-left transition-all hover:shadow-md hover:-translate-y-0.5"
    >
      <h3 className="text-base font-semibold text-brand-text line-clamp-2">{job.topic}</h3>
      <div className="mt-4 flex items-end justify-between">
        <span className="text-xs text-brand-muted">{formatDate(job.updated_at)}</span>
        <span className="text-xs text-brand-muted">
          {job.number_of_scenes} scene{job.number_of_scenes !== 1 ? 's' : ''}
        </span>
      </div>
    </button>
  );
}
