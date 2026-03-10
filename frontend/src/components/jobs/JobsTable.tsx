import { useNavigate } from 'react-router-dom';
import { Inbox } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { JobStatusBadge } from '@/components/jobs/JobStatusBadge';
import { formatDate, truncateId } from '@/utils/formatters';
import type { JobListItem, JobStatus } from '@/services/api';

interface JobsTableProps {
  jobs: JobListItem[];
  total: number;
  page: number;
  pageSize: number;
  loading: boolean;
  error: Error | null;
  onPageChange: (page: number) => void;
  onRetry: () => void;
}

function isClickable(status: JobStatus): boolean {
  return status === 'PLANNED' || status === 'RENDERED';
}

function getClickRoute(job: JobListItem): string | null {
  if (job.status === 'PLANNED') return `/create?job_id=${job.job_id}`;
  if (job.status === 'RENDERED') return `/lessons?job_id=${job.job_id}`;
  return null;
}

export function JobsTable({
  jobs, total, page, pageSize, loading, error, onPageChange, onRetry,
}: JobsTableProps) {
  const navigate = useNavigate();
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  if (error) {
    return (
      <div className="flex flex-col items-center py-16 text-center">
        <p className="text-brand-muted">Could not load jobs.</p>
        <Button variant="outline" className="mt-4" onClick={onRetry}>
          Retry
        </Button>
      </div>
    );
  }

  if (!loading && jobs.length === 0) {
    return (
      <div className="flex flex-col items-center py-16 text-center">
        <Inbox className="h-12 w-12 text-brand-muted" />
        <p className="mt-4 text-brand-muted">No jobs yet. Go create the first lesson video!</p>
        <Button
          onClick={() => navigate('/create')}
          className="mt-4 bg-brand-accent text-white hover:bg-brand-accent/90"
        >
          Create a Lesson
        </Button>
      </div>
    );
  }

  return (
    <div>
      <div className="overflow-x-auto rounded-lg border border-brand-border">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase text-brand-muted">
            <tr>
              <th className="px-4 py-3 font-medium">Job ID</th>
              <th className="px-4 py-3 font-medium">Topic</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-brand-border">
            {loading
              ? Array.from({ length: 3 }).map((_, i) => (
                  <tr key={i}>
                    <td className="px-4 py-3"><Skeleton className="h-4 w-20" /></td>
                    <td className="px-4 py-3"><Skeleton className="h-4 w-40" /></td>
                    <td className="px-4 py-3"><Skeleton className="h-5 w-28" /></td>
                    <td className="px-4 py-3"><Skeleton className="h-4 w-32" /></td>
                  </tr>
                ))
              : jobs.map((job) => {
                  const clickable = isClickable(job.status);
                  const route = getClickRoute(job);
                  return (
                    <tr
                      key={job.job_id}
                      onClick={route ? () => navigate(route) : undefined}
                      className={`${
                        clickable
                          ? 'cursor-pointer hover:bg-gray-50'
                          : ''
                      }`}
                    >
                      <td className="px-4 py-3 font-mono text-xs text-brand-muted">
                        <Tooltip>
                          <TooltipTrigger className="cursor-default">
                            {truncateId(job.job_id)}
                          </TooltipTrigger>
                          <TooltipContent>{job.job_id}</TooltipContent>
                        </Tooltip>
                      </td>
                      <td className="px-4 py-3 text-brand-text">{job.topic}</td>
                      <td className="px-4 py-3">
                        <JobStatusBadge status={job.status} />
                      </td>
                      <td className="px-4 py-3 text-brand-muted">{formatDate(job.created_at)}</td>
                    </tr>
                  );
                })}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="mt-4 flex items-center justify-center gap-4">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-brand-muted">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
